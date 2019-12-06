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

"""IGDB"""
if data['igdb']:
    http = urllib3.PoolManager()
    igdb_request = http.request(
        'GET',
        'https://api-v3.igdb.com/games',
        body='search "' + game + '"; fields name;',
        headers={'Content-Type': 'application/json', 'user-key': config['IGDB']['user_key']})
    games_data = json.loads(igdb_request.data)
    games_list = []
    for elem in games_data:
        games_list.append(elem['name'].upper())
    if game.upper() not in games_list and len(games_list) > 0:
        game = games_list[0]
print(game)


"""TWITCH"""
if data['twitch']:
    http = urllib3.PoolManager()

    """ Refresh OAuth token """
    if config['TWITCH']['refresh_token'] != 'refresh_token':
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
        new_refresh_token = json.loads(refresh_request.data)['refresh_token']
        config.set('TWITCH', 'oauth_token', 'OAuth ' + new_token)
        config.set('TWITCH', 'refresh_token', new_refresh_token)
        with open(os.path.join(location, "config.ini"), 'w') as cnf_file:
            config.write(cnf_file)

    """ Set new stream info """
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
