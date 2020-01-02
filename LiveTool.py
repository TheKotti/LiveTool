import json
import os
import sys
import configparser
import twitter
import urllib3
import datetime
from urllib.parse import urlencode
from discord_webhook import DiscordWebhook
from google.oauth2.credentials import Credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow

location = sys.path[0]

config = configparser.ConfigParser()
config.read(os.path.join(location, "config.ini"))

with open(os.path.join(location, 'LiveTool.json')) as json_file:
    data = json.load(json_file)
title = data['title']
game = data['game']
streams = []
data['twitch'] and streams.append(data['twitchUrl'])
data['youtube'] and streams.append(data['ytUrl'])
stream_url = ' | '.join(streams)


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

"""YOUTUBE"""
if data['youtube']:
    """If no refresh token is set, create one"""
    if config['YOUTUBE']['refresh_token'] == 'refresh_token':
        yt_scopes = ['https://www.googleapis.com/auth/youtube']
        yt_secrets = 'youtube_secret.json'
        flow = InstalledAppFlow.from_client_secrets_file(
            yt_secrets, yt_scopes)
        credentials = flow.run_console()
        config.set('YOUTUBE', 'refresh_token', credentials.refresh_token)
        with open(os.path.join(location, "config.ini"), 'w') as cnf_file:
            config.write(cnf_file)

    yt_credentials = Credentials(
        None,
        refresh_token=config['YOUTUBE']['refresh_token'],
        token_uri="https://accounts.google.com/o/oauth2/token",
        client_id=config['YOUTUBE']['client_id'],
        client_secret=config['YOUTUBE']['client_secret'],
    )

    youtube = build('youtube', 'v3', credentials=yt_credentials)
    timeNow = datetime.datetime.now().isoformat()[:-6] + '000Z'

    list_broadcasts_request = youtube.liveBroadcasts().list(
        part='id,snippet',
        maxResults=1,
        mine=True,
        broadcastType='all'
    )

    list_broadcasts_response = list_broadcasts_request.execute()
    broadcast_snippet = list_broadcasts_response['items'][0]['snippet']
    broadcast_snippet['title'] = title

    update_broadcast_request = youtube.liveBroadcasts().update(
        part='id,snippet',
        body=dict(
            snippet=broadcast_snippet,
            id=list_broadcasts_response['items'][0]['id']
        )
    ).execute()


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
