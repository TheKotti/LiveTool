import json
import os
import sys
import configparser
import twitter

location = sys.path[0]

config = configparser.ConfigParser()
config.read(os.path.join(location, "config.ini"))

with open(os.path.join(location, 'LiveTool.json')) as json_file:
    data = json.load(json_file)

"""TWITTER"""
if data['twitter']:
    try:
        twitterApi = twitter.Api(consumer_key=config['TWITTER']['consumer_key'],
                                 consumer_secret=config['TWITTER']['consumer_secret'],
                                 access_token_key=config['TWITTER']['access_token_key'],
                                 access_token_secret=config['TWITTER']['access_token_secret'])

        twitterApi.DestroyStatus(config['TWITTER']['last_tweet'])
        print('Tweet deleted')
    except:
        print("TWITTER ERROR")
