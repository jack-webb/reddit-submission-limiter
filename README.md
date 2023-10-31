# reddit-submission-limiter (RSL)
Limits the number of submissions per user to a subreddit in a given timeframe. Uses PRAW and Redis.

### Requirements
- A reddit user and accompanying script app with scopes for reporting and removing posts. See the [PRAW documentation](https://praw.readthedocs.io/en/latest/index.html) for details on this.
- A local [Redis](https://redis.io/) server. Support is not provided for password-protected instances.
- Python 3 and [Pipenv](https://pipenv.pypa.io/en/latest/)

### Configuring and Running RSL
1. Copy `config.example.py` to `config.py`\*
2. Fill in **all** config values. Subreddit should just be the sub's name (i.e. `AskReddit`, not `/r/AskReddit`)
3. Run `pipenv install`
4. Run `pipenv run python -m main`

\* I'm lazy so whilst this is under development, this might be imported as `localconfig` in the source. If you're getting errors, call your config `localconfig.py` instead.

### Custom remove/report messages
You can specify custom remove and report messages in your config. The following parameters can be used to give your messages some context. Add the parameter name inside braces (`{ }`) in your message string.
- `post_ids` - A list of post IDs from a given user in the period, in the form `['abcd', 'wxyz', '1234']`
- `num_posts` - The number of posts from a given user in the period
- `period` - The number of hours in which posts are counted (same as PERIOD_HOURS in config)
- `report_threshold` - The number of posts before new posts are reported (same as REPORT_THRESHOLD config)
- `remove_threshold` - The number of posts before new posts are removed (same as REMOVE_THRESHOLD config)
