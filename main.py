from typing import List, Set, Iterator
import praw
import prawcore
import redis
import logging
import config
import time
from praw.models import Submission, Subreddit

"""
Reddit Submission Limiter by Jack Webb
https://github.com/jack-webb/reddit-submision-limiter
Released under MIT license, see LICENSE file
"""

logging.basicConfig(level=logging.INFO)

r = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, decode_responses=True)
reddit = praw.Reddit(client_id=config.CLIENT_ID,
                     client_secret=config.CLIENT_SECRET,
                     username=config.USERNAME,
                     password=config.PASSWORD,
                     redirect_uri=config.REDIRECT_URI,
                     user_agent=config.USER_AGENT)


def main():
    check_custom_messages()
    check_redis()
    check_reddit_user_scopes()
    subreddit: Subreddit = reddit.subreddit(config.SUBREDDIT)
    check_subreddit_instance(subreddit)

    ready: str = f"RSL is logged in as {reddit.user.me().name} and listening in /r/{subreddit.display_name}"
    logging.info(ready)
    logging.info(f"=>{'~' * (len(ready) - 4)}<=")  # Pretty divider for post-init logs

    for post in subreddit.stream.submissions(skip_existing=True):
        if post.created_utc < time.time() - config.PERIOD_HOURS * 60 * 60:
            # Ignore stream items older than the period
            continue

        author: str = post.author.name
        num_user_posts: int = r.rpush(author, post.id)
        logging.debug(f"NEW POST: {author} has made {num_user_posts} posts")

        if num_user_posts == 1:
            r.expire(author, config.PERIOD_HOURS * 60 * 60)

        elif num_user_posts >= config.REMOVE_THRESHOLD:
            logging.info(f"{author} exceeded REMOVE_THRESHOLD ({config.REMOVE_THRESHOLD})")
            first, extra = get_redis_posts(author)
            if config.REPORT_ALL:
                remove_posts([first] + extra)
                if config.SEND_MODMAIL:
                    send_modmail([first] + extra)
            else:
                remove_posts(extra)
                if config.SEND_MODMAIL:
                    send_modmail(extra)

        elif num_user_posts >= config.REPORT_THRESHOLD:
            logging.info(f"{author} exceeded REPORT_THRESHOLD ({config.REPORT_THRESHOLD})")
            first, extra = get_redis_posts(author)
            if config.REPORT_ALL:
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
        post.mod.remove(spam=False, mod_note=config.REMOVE_MESSAGE.format(**message_parameters))


def report_posts(post_ids: List[str]):
    """Report posts by ID

    :param post_ids: List of post IDs to report
    """
    logging.info(f"Reporting {len(post_ids)} posts")
    posts: Iterator[Submission] = reddit.info([i if i.startswith('t3_') else f't3_{i}' for i in post_ids])
    message_parameters = generate_message_params(post_ids)
    for post in posts:
        logging.debug(f"Reporting post {post.id} ({post.title})")
        post.report(config.REPORT_MESSAGE.format(**message_parameters))


def send_modmail(post_ids: List[str]):
    logging.info(f"Sending modmail to {config.SUBREDDIT}")
    message_parameters = generate_message_params(post_ids)
    reddit.subreddit(config.SUBREDDIT).message(
        config.MODMAIL_SUBJECT.format(**message_parameters),
        config.MODMAIL_MESSAGE.format(**message_parameters)
    )


def generate_message_params(post_ids: List[str]) -> dict:
    return {
        "post_ids": str(post_ids),
        "num_posts": len(post_ids),
        "period": config.PERIOD_HOURS,
        "report_threshold": config.REPORT_THRESHOLD,
        "remove_threshold": config.REMOVE_THRESHOLD,
    }


# Set up checks
def check_custom_messages():
    fake_params = generate_message_params([])

    try:
        config.REPORT_MESSAGE.format(**fake_params)
    except KeyError as e:
        raise InvalidMessageParameterException(f"{e} in REPORT_MESSAGE is not a valid message parameter")
    try:
        config.REMOVE_MESSAGE.format(**fake_params)
    except KeyError as e:
        raise InvalidMessageParameterException(f"{e} in REMOVE_MESSAGE is not a valid message parameter")
    try:
        config.MODMAIL_SUBJECT.format(**fake_params)
    except KeyError as e:
        raise InvalidMessageParameterException(f"{e} in MODMAIL_SUBJECT is not a valid message parameter")
    try:
        config.MODMAIL_MESSAGE.format(**fake_params)
    except KeyError as e:
        raise InvalidMessageParameterException(f"{e} in MODMAIL_MESSAGE is not a valid message parameter")


def check_redis():
    r.ping()
    logging.debug(f"Connected to redis on {config.REDIS_HOST}:{config.REDIS_PORT}")


def check_reddit_user_scopes():
    scopes: dict = reddit.auth.scopes()
    required_scopes: Set[str] = {"modposts", "report", "privatemessages"}
    if scopes == {"*"}:
        logging.debug(f"Logged into reddit as {config.USERNAME} with all scopes")
    elif all(scope in scopes for scope in required_scopes):
        logging.debug(f"Logged into reddit as {config.USERNAME} with sufficient scopes")
    else:
        missing_scopes: Set[str] = set(scopes) - required_scopes
        if len(missing_scopes) == len(required_scopes):
            raise MissingScopesException(f"Logged into reddit as {config.USERNAME}, but all scopes are missing. The "
                                         f"bot will not work without these scopes. See the RSL documentation and "
                                         f"https://github.com/reddit-archive/reddit/wiki/OAuth2-Quick-Start-Example\n"
                                         f"Required scopes {required_scopes}, or *")
        else:
            logging.warning(f"Logged into reddit as {config.USERNAME}, but some scopes are missing. Some functionality "
                            f"will be unavailable. Missing {missing_scopes}")


def check_subreddit_instance(subreddit: praw.models.Subreddit):
    try:
        subreddit.created_utc
    except (prawcore.exceptions.Redirect, prawcore.exceptions.NotFound) as e:
        logging.error(f"Cannot find subreddit {config.SUBREDDIT}")
        raise e
    else:
        logging.debug(f"Successfully connected to subreddit {subreddit.display_name}")

    if "modposts" in reddit.auth.scopes() and config.USERNAME not in subreddit.moderator():
        logging.warning(f"{config.USERNAME} has post removal scope, but is not a moderator of "
                        f"{subreddit.display_name}. They will not be able to remove submission to the sub.")


class MissingScopesException(Exception):
    pass


class InvalidMessageParameterException(Exception):
    pass


if __name__ == "__main__":
    main()
