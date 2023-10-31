import logging

from praw.models import Subreddit

from app import RemoteConfig


class InboxHandler:
    def __init__(self, subreddit: Subreddit, remote_config: RemoteConfig):
        self.subreddit = subreddit
        self.remote_config = remote_config

    def handle(self, message):
        logging.debug(f"Handling message from {message.author}")

        if message.author not in self.subreddit.moderator():  # todo Add check for posts permission?
            logging.info(f"Message from non-moderator {message.author} ignored")
            return

        if message.subject.lower() == "reload":
            self.remote_config.load_config(reload=True)
        else:
            logging.info(f"Message from {message.author} with subject {message.subject} was not a recognised command")
            message.reply(
                "I don't understand that command. Try setting the subject to 'reload' to update the configuration.")
