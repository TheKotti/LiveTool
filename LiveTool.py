import json
import os
import sys
import configparser
import twitter
import urllib3
from urllib.parse import urlencode
from discord_webhook import DiscordWebhook

location = sys.path[0]

config = configparser.ConfigParser()
config.read(os.path.join(location, "config.ini"))

with open(os.path.join(location, 'LiveTool.json')) as json_file:
    data = json.load(json_file)
title = data['title']
game = data['game']
url = data['url']

"""TWITCH"""
if data['twitch']:
    http = urllib3.PoolManager()
    encoded_args = urlencode({
        'channel[status]': title,
        'channel[game]': game,
        'channel[message]': 'asdfasdfasdfs'
    })
    url = 'https://api.twitch.tv/kraken/channels/' + \
        config['TWITCH']['user_id'] + '?' + encoded_args

    r = http.request(
        'PUT',
        url,
        headers={
            'Client-ID': config['TWITCH']['client_id'],
            'Accept': 'application/vnd.twitchtv.v5+json',
            'Authorization': config['TWITCH']['oauth_token']
        }
    )
    print(json.loads(r.data.decode('utf-8')))


"""DISCORD"""
if data['discord']:
    discord_message = title + ": " + url
    webhook = DiscordWebhook(
        url=config['DISCORD']['webhook_url'], content=discord_message)
    webhook.execute()


"""TWITTER"""
if data['twitter']:
    tweet = title + "\n\n" + url
    twitterApi = twitter.Api(consumer_key=config['TWITTER']['consumer_key'],
                             consumer_secret=config['TWITTER']['consumer_secret'],
                             access_token_key=config['TWITTER']['access_token_key'],
                             access_token_secret=config['TWITTER']['access_token_secret'])

    twitterApi.PostUpdate(tweet)

exit()
