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
REPORT_THRESHOLD = 2
REMOVE_THRESHOLD = 3

# Customise the messages to your liking.
# The following parameters are available to add context:
# post_ids - A list of post IDs in the form ['abcd', 'wxyz', '1234']
# num_posts - The number of posts from a given user in the period
# period - The number of hours in which posts are counted (same as PERIOD_HOURS above)
# report_threshold - The number of posts before new posts are reported (same as REPORT_THRESHOLD above)
# remove_threshold - The number of posts before new posts are removed (same as REMOVE_THRESHOLD above)
REPORT_MESSAGE = "Excessive Posting ({num_posts} in {period}h, max {report_threshold}) | IDs: {post_ids}"
REMOVE_MESSAGE = "(Auto) Excessive Posting ({num_posts} in {period}h, max {report_threshold}) | IDs: {post_ids}"
MODMAIL_MESSAGE = ""  # Unused, see issue #2 (https://github.com/jack-webb/reddit-submision-limiter/issues/2)
