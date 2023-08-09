CLIENT_ID = ""
CLIENT_SECRET = ""
USERNAME = ""
PASSWORD = ""
REDIRECT_URI = ""
USER_AGENT = ""

REDIS_HOST = "localhost"
REDIS_PORT = 6379

SUBREDDIT = ""
PERIOD_HOURS = 24
REPORT_ALL = True
SEND_MODMAIL = True
REPORT_THRESHOLD = 2
REMOVE_THRESHOLD = 3

REPORT_MESSAGE = "Excessive Posting ({num_posts} in {period}h, max {report_threshold}) | IDs: {post_ids}"
REMOVE_MESSAGE = "(Auto) Excessive Posting ({num_posts} in {period}h, max {report_threshold}) | IDs: {post_ids}"
MODMAIL_SUBJECT = "Posts removed"
MODMAIL_MESSAGE = "{num_posts} were removed with IDs {post_ids}"
