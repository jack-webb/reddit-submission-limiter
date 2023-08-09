import json
from praw.models import Subreddit, WikiPage

from app.SubredditConfig import SubredditConfig

# todo Support config refresh, background thread or something
# todo Use class instead of dict for configuration
# todo Expect wikipage not to be public, account for that in perms
class RemoteConfig:

    def __init__(self, subreddit: Subreddit, config_page: str):
        self.subreddit = subreddit
        self.wikipage = subreddit.wiki[config_page]
        self.config = None
        self.refresh_config()

    # todo error handling
    def get(self, key: str):
        return self.config[key]

    def refresh_config(self) -> bool:
        config_dict = self._get_remote_config(self.wikipage)
        print("CONFIG IS BEING UPDATED WITH: ", config_dict)
        self.config = SubredditConfig(config_dict)
        return True

    def _get_remote_config(self, wikipage: WikiPage):
        try:
            config = json.loads(wikipage.content_md)
            if is_valid(config):
                return config
        except json.JSONDecodeError:
            raise InvalidConfig("The config is not valid JSON.")


def is_valid(config: dict) -> bool:
    required_keys = [
        "enabled", "period_hours", "report_all", "send_modmail",
        "report_threshold", "remove_threshold", "report_message",
        "remove_message", "modmail_subject", "modmail_message"
    ]

    for key in required_keys:
        if key not in config:
            raise InvalidConfig(f"{key} is missing in the configuration.")

    # Validate specific types and constraints
    if not isinstance(config["enabled"], bool):
        raise InvalidConfig("enabled must be a boolean ('True' or 'False').")
    if not isinstance(config["period_hours"], int):
        raise InvalidConfig("period_hours must be an integer.")
    if not isinstance(config["report_all"], bool):
        raise InvalidConfig("report_all must be a boolean ('True' or 'False').")
    if not isinstance(config["send_modmail"], bool):
        raise InvalidConfig("send_modmail must be a boolean.")
    if not isinstance(config["report_threshold"], int):
        raise InvalidConfig("report_threshold must be an integer.")
    if not isinstance(config["remove_threshold"], int):
        raise InvalidConfig("remove_threshold must be an integer.")

    # Validate the allowed parameters in subjects and messages
    # allowed_params = ["post_ids", "num_posts", "period", "report_threshold", "remove_threshold"]
    # for key in ["report_message", "remove_message", "modmail_subject", "modmail_message"]:
        # if any(param not in allowed_params for param in config[key].format_map({}).keys()):
            # raise InvalidConfig(f"{key} contains invalid parameters.")

    return True


class InvalidConfig(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
