from typing import List, Iterator
import praw
import redis
import logging
import config
import time
from praw.models import Submission, Subreddit

logging.basicConfig(level=logging.INFO)

r = redis.Redis(host="localhost", port=6379, decode_responses=True)
reddit = praw.Reddit(client_id=config.CLIENT_ID,
                     client_secret=config.CLIENT_SECRET,
                     username=config.USERNAME,
                     password=config.PASSWORD,
                     redirect_uri=config.REDIRECT_URI,
                     user_agent=config.USER_AGENT)


def main():
    logging.info(f"Logged in as {config.USERNAME}")
    subreddit: Subreddit = reddit.subreddit(config.SUBREDDIT)

    for post in subreddit.stream.submissions():
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
            _, extra = get_redis_posts(author)
            remove_posts(extra)

        elif num_user_posts >= config.REPORT_THRESHOLD:
            logging.info(f"{author} exceeded REPORT_THRESHOLD ({config.REPORT_THRESHOLD})")
            _, extra = get_redis_posts(author)
            report_posts(extra)
            send_modmail_notif(author)


def get_redis_posts(author: str) -> (str, str):
    """Return user's first and extra post IDs

    Retrieve the user's first and extra post IDs from Redis,
    then return them as a tuple in the form (first, extra)

    :param author: The username to get posts for
    :return: Tuple of the first and extra post IDs
    """
    return r.lindex(author, 0), r.lrange(author, 1, -1)


def remove_posts(post_ids: List[str]):
    """Removes posts by ID (as a moderator)

    :param post_ids: List of post IDs to remove
    """
    logging.info(f"Removing {len(post_ids)} posts")
    posts: Iterator[Submission] = reddit.info([i if i.startswith('t3_') else f't3_{i}' for i in post_ids])
    for post in posts:
        logging.debug(f"Removing post {post.id} ({post.title})")
        post.mod.remove(spam=False, mod_note=config.REMOVE_REASON)


def report_posts(post_ids: List[str]):
    """Report posts by ID

    :param post_ids: List of post IDs to report
    """
    logging.info(f"Reporting {len(post_ids)} posts")
    posts: Iterator[Submission] = reddit.info([i if i.startswith('t3_') else f't3_{i}' for i in post_ids])
    for post in posts:
        logging.debug(f"Reporting post {post.id} ({post.title})")
        post.report(config.REPORT_MESSAGE)


def send_modmail_notif(author: str):
    pass


if __name__ == "__main__":
    main()
