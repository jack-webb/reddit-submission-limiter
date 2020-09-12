from typing import List
import praw
import redis
import logging
import config
import time

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
    subreddit = reddit.subreddit(config.SUBREDDIT)

    for post in subreddit.stream.submissions():
        if post.created_utc < time.time() - config.PERIOD_HOURS * 60 * 60:
            # Ignore stream items older than the period
            continue

        author = post.author.name
        num_user_posts = r.rpush(author, post.id)
        logging.info(f"NEW POST: {author} has made {num_user_posts} posts this period")

        if num_user_posts == 1:
            r.expire(author, config.PERIOD_HOURS * 60 * 60)
        elif num_user_posts >= config.REMOVE_THRESHOLD:
            logging.info(f"{author} exceeded REMOVE THRESHOLD ({config.REMOVE_THRESHOLD})")
            first, extra = get_redis_posts(author)
            remove_posts(extra)
        elif num_user_posts >= config.REPORT_THRESHOLD:
            logging.info(f"{author} exceeded REPORT THRESHOLD ({config.REPORT_THRESHOLD})")
            first, extra = get_redis_posts(author)
            report_posts(extra)
            send_modmail(author)


def get_redis_posts(author: str) -> (str, str):
    return r.lindex(author, 0), r.lrange(author, 1, -1)


def remove_posts(post_ids: List[str]):
    logging.info(f"Removing {len(post_ids)} posts")
    for post in reddit.info([i if i.startswith('t3_') else f't3_{i}' for i in post_ids]):
        post.mod.remove(spam=False, mod_note=config.REMOVE_REASON)


def report_posts(post_ids: List[str]):
    logging.info(f"Reporting {len(post_ids)} posts")
    for post in reddit.info([i if i.startswith('t3_') else f't3_{i}' for i in post_ids]):
        print(post)
        print(post.title)
        post.report(config.REPORT_MESSAGE)


def send_modmail(author: str):
    pass


if __name__ == "__main__":
    main()
