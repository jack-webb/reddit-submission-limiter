from typing import List, Set, Iterator
import praw
import prawcore
import redis
import logging
import localconfig
import time
from praw.models import Submission, Subreddit

from app.InboxHandler import InboxHandler
from app.RemoteConfig import RemoteConfig

"""
Reddit Submission Limiter by Jack Webb
https://github.com/jack-webb/reddit-submision-limiter
Released under MIT license, see LICENSE file
"""

logging.basicConfig(level=logging.DEBUG)

r = redis.Redis(host=localconfig.REDIS_HOST, port=localconfig.REDIS_PORT, decode_responses=True)
reddit = praw.Reddit(client_id=localconfig.CLIENT_ID,
                     client_secret=localconfig.CLIENT_SECRET,
                     username=localconfig.USERNAME,
                     password=localconfig.PASSWORD,
                     redirect_uri=localconfig.REDIRECT_URI,
                     user_agent=localconfig.USER_AGENT)

rc = RemoteConfig(reddit.subreddit(localconfig.SUBREDDIT), localconfig.CONFIG_WIKI_PAGE, reddit.user.me().name)

def main():
    subreddit: Subreddit = reddit.subreddit(localconfig.SUBREDDIT)
    check_subreddit_instance(subreddit)
    check_bot_moderation_permissions(subreddit)

    check_custom_messages()
    check_redis()
    check_reddit_user_scopes()

    bot_ready: str = f"RSL is logged in as {reddit.user.me().name} and listening in /r/{subreddit.display_name}"
    logging.info(bot_ready)

    config_ready: str = (f"RSL is using the configuration from https://reddit.com/r/{subreddit.display_name}/wiki/rsl-configuration/")
    logging.info(config_ready)

    inbox_handler_ready: str = (f"RSL is listening for configuration updates. Send a message to /u/{reddit.user.me().name} "
                                f"with the subject 'reload' after updating the configuration page.")
    inbox_handler = InboxHandler(subreddit, rc)
    logging.info(inbox_handler_ready)

    div_length = max(len(bot_ready), len(config_ready), len(inbox_handler_ready)) - 4
    logging.info(f"=>{'~' * div_length}<=")  # Pretty divider for post-init logs

    while True:
        try:
            inbox_stream = reddit.inbox.stream(skip_existing=True, pause_after=-1)
            submission_stream = subreddit.stream.submissions(skip_existing=True, pause_after=-1)
            while True:
                check_inbox(inbox_stream, inbox_handler)
                check_submissions(submission_stream)
        except Exception as e:
            logging.warning(f"Server error: {e}")
            logging.warning("Restarting streams...")


def check_inbox(stream, inbox_handler):
    for message in stream:
        if message is None:
            logging.info("No inbox messages in stream")
            break
        logging.debug(f"Received message from {message.author}!!!")
        inbox_handler.handle(message)

def check_submissions(stream):
    for post in stream:
        if post is None:
            logging.info("No submissions in stream")
            break

        if post.created_utc < time.time() - rc.config.PERIOD_HOURS * 60 * 60:
            # Ignore stream items older than the period
            continue

        if not rc.config.ENABLED:
            # The bot has been disabled from the remote config
            # Skip this submission entirely
            # todo Should we apply this at the remove/report level instead, to maintain tracking?
            continue

        author: str = post.author.name
        num_user_posts: int = r.rpush(author, post.id)
        logging.info(f"New Post from {author}, who has made {num_user_posts} posts")

        if num_user_posts == 1:
            r.expire(author, rc.config.PERIOD_HOURS * 60 * 60)

        elif num_user_posts >= rc.config.REMOVE_THRESHOLD:
            logging.info(f"{author} has exceeded remove_threshold ({rc.config.REMOVE_THRESHOLD})")
            first, extra = get_redis_posts(author)
            if rc.config.REPORT_ALL:
                remove_posts([first] + extra)
                if rc.config.SEND_MODMAIL:
                    send_modmail([first] + extra)
            else:
                remove_posts(extra)
                if rc.config.SEND_MODMAIL:
                    send_modmail(extra)

        elif num_user_posts >= rc.config.REPORT_THRESHOLD:
            logging.info(f"{author} has exceeded report_threshold ({rc.config.REPORT_THRESHOLD})")
            first, extra = get_redis_posts(author)
            if rc.config.REPORT_ALL:
                report_posts([first] + extra)
            else:
                report_posts(extra)

def get_redis_posts(author: str) -> (str, str):
    """Return user's first and other post IDs

    Retrieve the user's first and other post IDs from Redis,
    then return them as a tuple in the form (first, extra)

    :param author: The username to get posts for
    :return: Tuple of the first and other post IDs
    """
    return r.lindex(author, 0), r.lrange(author, 1, -1)


def remove_posts(post_ids: List[str]):
    """Removes posts by ID (as a moderator)

    :param post_ids: List of post IDs to remove
    """
    logging.info(f"Removing {len(post_ids)} posts")
    posts: Iterator[Submission] = reddit.info([i if i.startswith('t3_') else f't3_{i}' for i in post_ids])
    message_parameters = generate_message_params(post_ids)
    for post in posts:
        logging.debug(f"Removing post {post.id} ({post.title})")
        post.mod.remove(spam=False, mod_note=rc.config.REMOVE_MESSAGE.format(**message_parameters)[100:])


def report_posts(post_ids: List[str]):
    """Report posts by ID

    :param post_ids: List of post IDs to report
    """
    logging.info(f"Reporting {len(post_ids)} posts")
    posts: Iterator[Submission] = reddit.info([i if i.startswith('t3_') else f't3_{i}' for i in post_ids])
    message_parameters = generate_message_params(post_ids)
    for post in posts:
        logging.debug(f"Reporting post {post.id} ({post.title})")
        post.report(rc.config.REPORT_MESSAGE.format(**message_parameters))


def send_modmail(post_ids: List[str]):
    logging.info(f"Sending modmail to {localconfig.SUBREDDIT}")
    message_parameters = generate_message_params(post_ids)
    reddit.subreddit(localconfig.SUBREDDIT).message(
        rc.config.MODMAIL_SUBJECT.format(**message_parameters),
        rc.config.MODMAIL_MESSAGE.format(**message_parameters)
    )


def generate_message_params(post_ids: List[str]) -> dict:
    return {
        "post_ids": str(post_ids),
        "num_posts": len(post_ids),
        "period": rc.config.PERIOD_HOURS,
        "report_threshold": rc.config.REPORT_THRESHOLD,
        "remove_threshold": rc.config.REMOVE_THRESHOLD,
    }


# This needs to be added to the remote config validation
def check_custom_messages():
    pass
    # fake_params = generate_message_params([])

    # try:
    #     rc.config.REPORT_MESSAGE.format(**fake_params)
    # except KeyError as e:
    #     raise InvalidMessageParameterException(f"{e} in REPORT_MESSAGE is not a valid message parameter")
    # try:
    #     rc.config.REMOVE_MESSAGE.format(**fake_params)
    # except KeyError as e:
    #     raise InvalidMessageParameterException(f"{e} in REMOVE_MESSAGE is not a valid message parameter")
    # try:
    #     rc.config.MODMAIL_SUBJECT.format(**fake_params)
    # except KeyError as e:
    #     raise InvalidMessageParameterException(f"{e} in MODMAIL_SUBJECT is not a valid message parameter")
    # try:
    #     rc.config.MODMAIL_MESSAGE.format(**fake_params)
    # except KeyError as e:
    #     raise InvalidMessageParameterException(f"{e} in MODMAIL_MESSAGE is not a valid message parameter")


def check_redis():
    r.ping()
    logging.debug(f"Connected to redis on {localconfig.REDIS_HOST}:{localconfig.REDIS_PORT}")


def check_reddit_user_scopes():
    scopes: dict = reddit.auth.scopes()
    required_scopes: Set[str] = {"modposts", "report", "privatemessages", "wikiread"}
    if scopes == {"*"}:
        logging.debug(f"Logged into reddit as {localconfig.USERNAME} with all (*) scopes")
    elif all(scope in scopes for scope in required_scopes):
        logging.debug(f"Logged into reddit as {localconfig.USERNAME} with all required scopes")
    else:
        missing_scopes: Set[str] = set(scopes) - required_scopes
        if len(missing_scopes) == len(required_scopes):
            raise MissingScopesException(f"Logged into reddit as {localconfig.USERNAME}, but with no required scopes. The "
                                         f"bot will not work without these scopes. See the RSL documentation and "
                                         f"https://github.com/reddit-archive/reddit/wiki/OAuth2-Quick-Start-Example\n"
                                         f"Required scopes {required_scopes}, or all with *")
        else:
            logging.warning(f"Logged into reddit as {localconfig.USERNAME}, but some scopes are missing. Some functionality "
                            f"will be unavailable. Missing {missing_scopes}")


def check_subreddit_instance(subreddit: praw.models.Subreddit):
    try:
        subreddit.created_utc
    except (prawcore.exceptions.Redirect, prawcore.exceptions.NotFound) as e:
        logging.error(f"Cannot find subreddit {localconfig.SUBREDDIT}")
        raise e
    else:
        logging.debug(f"Successfully connected to subreddit {subreddit.display_name}")

def check_bot_moderation_permissions(subreddit: praw.models.Subreddit):
    bot_moderation_permissions = None
    for user in subreddit.moderator():
        if user.name == localconfig.USERNAME:
            bot_moderation_permissions = user.mod_permissions
            break

    if "modposts" in reddit.auth.scopes() and "posts" not in bot_moderation_permissions:
        logging.warning(f"{localconfig.USERNAME} has post removal scope, but is not a moderator of "
                        f"{subreddit.display_name}. They will not be able to remove submissions in this subreddit.")

class MissingScopesException(Exception):
    pass


class InvalidMessageParameterException(Exception):
    pass


if __name__ == "__main__":
    main()
