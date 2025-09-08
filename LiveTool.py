import json
import os
import sys
import configparser
import requests
import urllib3
import difflib
import time
from urllib.parse import urlencode
from discord_webhook import DiscordWebhook
from operator import itemgetter

location = sys.path[0]

config = configparser.ConfigParser()
config.read(os.path.join(location, "config.ini"))

with open(os.path.join(location, 'LiveTool.json')) as json_file:
    data = json.load(json_file)
title = data['title']
game_title = data['game']
suffix = data['suffix']
streams = []
streams.append(data['twitchUrl'])
data['youtube'] and streams.append(data['ytUrl'])
stream_url = ' | '.join(streams)


"""IGDB"""
if data['igdb']:
    try:
        http = urllib3.PoolManager()

        """ Refresh access token """
        refresh_args = urlencode({
            'client_id': config['TWITCH']['client_id'],
            'client_secret': config['TWITCH']['client_secret'],
            'grant_type': 'client_credentials',
        })
        refresh_url = 'https://id.twitch.tv/oauth2/token?' + refresh_args
        refresh_request = http.request(
            'POST',
            refresh_url
        )
        new_token = json.loads(refresh_request.data)['access_token']
        config.set('IGDB', 'token', 'Bearer ' + new_token)
        with open(os.path.join(location, "config.ini"), 'w') as cnf_file:
            config.write(cnf_file)

        igdb_request = http.request(
            'POST',
            'https://api.igdb.com/v4/games',
            body='search "' + game_title +
            '"; fields name,category,cover.image_id,release_dates.y,genres.name,themes.name,involved_companies.company.name, involved_companies.developer;',
            headers={
                'Content-Type': 'application/json',
                'Authorization': config['IGDB']['token'],
                'Client-ID': config['TWITCH']['client_id']})
        games_data = json.loads(igdb_request.data)

        """ Get a list without non-games as [title, coverId], and a list with just title """
        games_list = []
        games_list_with_meta = []
        genres = []
        developers = []
        for elem in games_data:
            if elem['category'] in [0, 3, 4, 8]:  # [game, bundle, standalone_expansion, remake]
                games_list.append(elem['name'])

                if 'release_dates' in elem:
                    y_values = [item['y'] for item in elem['release_dates']
                                if 'y' in item and isinstance(item['y'], (int, float))]
                    smallest_y = min(y_values) if y_values else '???'
                    release_year = smallest_y
                else:
                    release_year = '???'

                if 'genres' in elem:
                    for genre in elem['genres']:
                        genres.append(genre['name'])

                if 'themes' in elem:
                    for theme in elem['themes']:
                        genres.append(theme['name'])

                if 'involved_companies' in elem:
                    for comp in elem['involved_companies']:
                        if (comp['developer']):
                            developers.append(comp['company']['name'])

                cover = elem['cover']['image_id'] if 'cover' in elem else 'nocover'
                games_list_with_meta.append(
                    [elem['name'], cover, release_year])

        """ Set game_title and game_cover_id based on index of the closest matching title """
        best_matches = difflib.get_close_matches(game_title, games_list, 3, 0)
        best_index = games_list.index(best_matches[0])
        game_title = games_list_with_meta[best_index][0]
        game_cover_id = games_list_with_meta[best_index][1]
        game_year = str(games_list_with_meta[best_index][2])

        """ Set game title in file for OBS """
        with open(config['LOCAL']['meta_path'] + '/gametitle.txt', 'w') as game_title_file:
            game_title_file.write(game_title + ' (' + game_year + ')')

        """ Set genres and developers from IGDB """
        if (data['bottomText'] == 'IGDB'):
            with open(config['LOCAL']['meta_path'] + '/bottomtext.txt', 'w') as bottom_text_file:
                bottom_text_file.write(
                    'DEVELOPED BY: ' + ', '.join(list(dict.fromkeys(developers))) + '\nGENRES: ' + ', '.join(list(dict.fromkeys(genres))))

        game_cover_url = 'https://images.igdb.com/igdb/image/upload/t_cover_big/' + \
            game_cover_id + '.jpg'
        game_cover_res = requests.get(game_cover_url)
        with open(config['LOCAL']['meta_path'] + '/cover.png', 'wb') as game_cover_file:
            game_cover_file.write(game_cover_res.content)

        print('Game metadata fetched (' + game_title + ')')
    except Exception as e:
        print("IGDB ERROR")
        print(e)

"""TWITCH"""
if data['twitch']:
    try:
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
            new_refresh_token = json.loads(refresh_request.data)[
                'refresh_token']
            config.set('TWITCH', 'oauth_token', 'Bearer ' + new_token)
            config.set('TWITCH', 'refresh_token', new_refresh_token)
            with open(os.path.join(location, "config.ini"), 'w') as cnf_file:
                config.write(cnf_file)

        """" Get game id """
        game_id_args = urlencode({
            'name': 'Retro' if data['retro'] else game_title
        })
        game_id_url = 'https://api.twitch.tv/helix/games?' + game_id_args
        game_id_request = http.request(
            'GET',
            game_id_url,
            headers={
                'Client-ID': config['TWITCH']['client_id'],
                'Authorization': config['TWITCH']['oauth_token']
            }
        )
        game_id_json = json.loads(game_id_request.data)
        game_id = game_id_json['data'][0]['id']

        """ Set new stream info """
        title_with_suffix = title + ' | ' + suffix if suffix != '' else title
        twitch_args = urlencode({
            'broadcaster_id': config['TWITCH']['user_id']
        })
        twitch_update_url = 'https://api.twitch.tv/helix/channels?' + twitch_args
        twitch_request = http.request(
            'PATCH',
            twitch_update_url,
            headers={
                'Client-ID': config['TWITCH']['client_id'],
                'Authorization': config['TWITCH']['oauth_token'],
                'Content-Type': 'application/json'
            },
            body=json.dumps({
                'game_id': game_id,
                'title': title_with_suffix
            })
        )

        print('Twitch info changed')
    except Exception as e:
        print("TWITCH ERROR")
        print(e)


"""DISCORD"""
if data['discord']:
    try:
        discord_message = title + ": " + stream_url
        webhook = DiscordWebhook(
            url=config['DISCORD']['webhook_url'], content=discord_message)
        webhook.execute()
        print('Discord message posted')
    except Exception as e:
        print("DISCORD ERROR")
        print(e)


print('Exiting...')
time.sleep(3)
exit()
