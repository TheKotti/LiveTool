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
stream_url = data['url']


"""TWITCH"""
if data['twitch']:
    http = urllib3.PoolManager()

    """Refresh OAuth token"""
    refresh_args = urlencode({
        'client_id': config['TWITCH']['client_id'],
        'client_secret': config['TWITCH']['client_secret'],
        'grant_type': 'refresh_token',
        'refresh_token': config['TWITCH']['refresh_token']
    })
    refresh_url = 'https://id.twitch.tv/oauth2/token?' + refresh_args
    refresh_request = http.request(
        'POST',
        refresh_url
    )
    new_token = json.loads(refresh_request.data)['access_token']
    config.set('TWITCH', 'oauth_token', 'OAuth ' + new_token)
    with open(os.path.join(location, "config.ini"), 'w') as cnf_file:
        config.write(cnf_file)

    """Set new stream info"""
    twitch_args = urlencode({
        'channel[status]': title,
        'channel[game]': game
    })
    twitch_udpate_url = 'https://api.twitch.tv/kraken/channels/' + \
        config['TWITCH']['user_id'] + '?' + twitch_args

    twitch_request = http.request(
        'PUT',
        twitch_udpate_url,
        headers={
            'Client-ID': config['TWITCH']['client_id'],
            'Accept': 'application/vnd.twitchtv.v5+json',
            'Authorization': config['TWITCH']['oauth_token']
        }
    )
    print(json.loads(twitch_request.data.decode('utf-8')))


"""DISCORD"""
if data['discord']:
    discord_message = title + ": " + stream_url
    webhook = DiscordWebhook(
        url=config['DISCORD']['webhook_url'], content=discord_message)
    webhook.execute()


"""TWITTER"""
if data['twitter']:
    tweet = title + "\n\n" + stream_url
    twitterApi = twitter.Api(consumer_key=config['TWITTER']['consumer_key'],
                             consumer_secret=config['TWITTER']['consumer_secret'],
                             access_token_key=config['TWITTER']['access_token_key'],
                             access_token_secret=config['TWITTER']['access_token_secret'])

    twitterApi.PostUpdate(tweet)

exit()
