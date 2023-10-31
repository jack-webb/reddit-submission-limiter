import json
import logging
from typing import Union, Optional

from praw.models import Subreddit

from app.SubredditConfig import SubredditConfig


# todo Expect the config wikipage not to be public, need to account for that in bot perms
#      Otherwise, remote config is working!!
# todo handling if the config page doesn't exist
# todo (better) handling if the config page is empty

class RemoteConfig:

    def __init__(self, subreddit: Subreddit, config_page: str, bot_name: str):
        self.subreddit = subreddit
        self.config_page = config_page
        self.bot_name = bot_name
        self.config = None
        self.load_config()

    def load_config(self, reload: bool = False):
        logging.info("Loading configuration from wiki")
        config_dict = self._get_remote_config()
        self.config = SubredditConfig(config_dict)
        logging.info("Configuration loaded successfully\n" + "\n".join(
            (f"{key}: {value}" for key, value in config_dict.items())))
        if reload:
            self.subreddit.message("Updated configuration for" + self.bot_name,
                                   "The configuration has been successfully updated")  # todo Subreddit messages not working?

    def _get_remote_config(self) -> Optional[dict]:
        try:
            config_page = self.subreddit.wiki[self.config_page]
            config = json.loads(config_page.content_md)
            if self.validate(config):
                return config
        except json.JSONDecodeError:
            self.subreddit.message("Invalid configuration for " + self.bot_name, "The config is not valid JSON.")
            logging.info("Invalid JSON in remote config, refresh failed")

    def validate(self, config: dict) -> Union[list, bool]:
        problems = []

        required_keys = [
            "enabled", "period_hours", "report_all", "send_modmail",
            "report_threshold", "remove_threshold", "report_message",
            "remove_message", "modmail_subject", "modmail_message"
        ]

        for key in required_keys:
            if key not in config:
                problems.append(f"{key} is missing in the configuration")

        # Validate specific types and constraints
        if not isinstance(config["enabled"], bool):
            problems.append("enabled must be a boolean ('true' or 'false')")
        if not isinstance(config["period_hours"], int):
            problems.append("period_hours must be an integer")
        if not isinstance(config["report_all"], bool):
            problems.append("report_all must be a boolean ('True' or 'False')")
        if not isinstance(config["send_modmail"], bool):
            problems.append("send_modmail must be a boolean")
        if not isinstance(config["report_threshold"], int):
            problems.append("report_threshold must be an integer")
        if not isinstance(config["remove_threshold"], int):
            problems.append("remove_threshold must be an integer")

        if problems:
            self.subreddit.message("Invalid configuration for " + self.bot_name, "\n- ".join(problems))
            logging.info("Invalid configuration, refresh failed" + str(problems))

        return not problems


class InvalidConfig(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
