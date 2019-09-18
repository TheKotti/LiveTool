# LiveTool

Update Twitch, Discord and Twitter from a local file. LiveTool.json determines the stream title, game, stream url and which platforms will be updated.

- Twitch updates stream title and game
- Discord posts a message with title and url
- Twitter posts a tweet with title and url

Create config.ini in the root folder and add in the following info:

```
[TWITTER]
consumer_key = twitter_consumer_key
consumer_secret = twitter_consumer_secret
access_token_key = twitter_access_token_key
access_token_secret = twitter_access_token_secret

[TWITCH]
oauth_token = OAuth oauth_token
client_id = client_id
user_id = user_id

[DISCORD]
webhook_url = webhook_url

```
