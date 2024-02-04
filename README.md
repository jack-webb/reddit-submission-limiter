# reddit-submission-limiter (RSL)
- Limits the number of submissions per user to a subreddit in a given timeframe, by reporting, filtering and removing excess posts. 
- Uses a rolling window to count posts in a specified number of hours, with adjustable thresholds. 
- Enable, disable and modify parameters live from your subreddit wiki (think old Automoderator).

Uses PRAW and Redis.

### Requirements
- A reddit user and accompanying script app with scopes for reporting and removing posts. See the [PRAW documentation](https://praw.readthedocs.io/en/latest/index.html) for details on this.
- A local [Redis](https://redis.io/) server. Support is not provided for password-protected instances.
- Python 3 and [Pipenv](https://pipenv.pypa.io/en/latest/)

### Installation
1. Set up the remote configuration (See 'Remote Configuration' below)
2. Copy `localconfig.example.py` to `localconfig.py`
3. Fill in **all** the values. 
   - **Subreddit** is _just_ the sub's name (i.e. `AskReddit`, not `/r/AskReddit`)
   - **Config wiki page** is everything after `/r/subreddit/wiki/` in the URL of your page
4. Run `pipenv install`
5. Run `pipenv run python -m app.main`

### Remote Configuration
Core functionality of the bot is managed from your subreddit wiki, using a JSON object with the configurable parameters. The bot loads config from this page on launch, or when messaged with 'reload' as the subject.

#### Setup
1. Create a new wiki page on your subreddit. Make sure your bot account has access to read this page.
2. Copy the contents of `wiki-config-example.json` to your new wiki page, fill in the contents, and hit save.
3. Run the bot and check the log for a message confirming the config was loaded.

#### Live updating configuration
1. Make and save your changes to the wiki page
2. Message the bot account with the subject 'reload'. 

The bot will reload the config from the wiki page and send a modmail confirming a successful reload.


### Custom remove/report messages
You can specify custom remove and report messages in your configuration. The following parameters can be used to give your messages some context. Add the parameter name inside braces (`{ }`) in your message string.
- `post_ids` - A list of post IDs from a given user in the period, in the form `['abcd', 'wxyz', '1234']`
- `num_posts` - The number of posts from a given user in the period
- `period` - The number of hours in which posts are counted (same as PERIOD_HOURS in config)
- `report_threshold` - The number of posts before new posts are reported (same as REPORT_THRESHOLD config)
- `remove_threshold` - The number of posts before new posts are removed (same as REMOVE_THRESHOLD config)

For example:
```json
{
  "report_message": "User posted {num_posts} times in the last {period} hours | {post_ids}",
  "remove_message": "User exceeded limit of {remove_threshold} posts in {period}h"
}
```

### Userscript
There is a companion userscript that will turn IDs in report reasons into clickable reddit links. Paste the contents of `userscript.js` into a new userscript in your manager (e.g. [Violentmonkey](https://violentmonkey.github.io/)), replace the bot username constant, then save.