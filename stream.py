#!/usr/bin/env python
# encoding: utf-8

import tweepy
import json
import time
import configparser
import argparse

#Configuration initialization
config = configparser.ConfigParser()

parser = argparse.ArgumentParser(description='Export tweets that match the search query')
subparsers = parser.add_subparsers(help='Add configuration from Ini file or through arguments')

parser_file = subparsers.add_parser('file', help='Adding configuration from a file (Default: Ini/Default.ini)')
parser_file.add_argument('cmd', const='file', action='store_const')
parser_file.add_argument('-i', '--ini_file', default='Ini/Default.ini', help='Path to the Ini file  (Default: Ini/Default.ini)')

parser_line = subparsers.add_parser('line', help='Adding configuration from a arguments in the command line')
parser_line.add_argument('cmd', const='line', action='store_const')
parser_line.add_argument('-s', '--search', required=True, help='Twitter search filter')
parser_line.add_argument('-ck', '--consumer_key', required=True, help='Twitter consumer key obtained from your Twitter account')
parser_line.add_argument('-cs', '--consumer_secret', required=True, help='Twitter consumer secret obtained from your Twitter account')
parser_line.add_argument('-ak', '--access_key', required=True, help='Twitter access key obtained from your Twitter account')
parser_line.add_argument('-as', '--access_secret', required=True, help='Twitter access_secret obtained from your Twitter account')
parser_line.add_argument('-o', '--output_filename', required=True, help='Name of the results output file')
parser_line.add_argument('-b', '--backup_ini_file_name', help='Name of the Ini file to backup from this request parameters')

args = parser.parse_args()
elements = vars(args)

#Configuration

if elements['cmd'] == 'file':
    #mettre une condition de verification de i, si i n'existe pas, i est forcement dans Ini/
    config.read(elements['ini_file'])

    output_filenane = config['DEFAULT']['output_filename']
    search_query = config['DEFAULT']['search']

    consumer_key = config['Twitter']['consumer_key']
    consumer_secret = config['Twitter']['consumer_secret']
    access_key = config['Twitter']['access_key']
    access_secret = config['Twitter']['access_secret']

elif elements['cmd'] == 'line':
    output_filenane = elements['output_filename']
    search_query = elements['search']

    consumer_key = elements['consumer_key']
    consumer_secret = elements['consumer_secret']
    access_key = elements['access_key']
    access_secret = elements['access_secret']

    if elements['backup_ini_file_name'] != None:
        if elements['backup_ini_file_name'] !=  'Ini/Default.ini':
            config['DEFAULT'] = {'output_filename': output_filenane, 'search': search_query}
            config['Twitter'] =  {'consumer_key': consumer_key, 'consumer_secret': consumer_secret, 'access_key': access_key, 'access_secret': access_secret }
            with open('Ini/' + elements['backup_ini_file_name'], 'w') as configFile:
                config.write(configFile)
        else:
            print('You cannot overwrite the Default Ini file')
            exit
else:
    print('Sorry this command is invalid')
    exit

print(search_query)

#Twitter connection
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_key, access_secret)
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
#refer http://docs.tweepy.org/en/v3.2.0/api.html#API
#tells tweepy.API to automatically wait for rate limits to replenish

#Twitter search terms
users =tweepy.Cursor(api.search,q=search_query, tweet_mode='extended').items()
count = 0
errorCount=0

#Result file
file = open(output_filenane, 'wb')

#Processing
data = []
while True:
    try:
        user = next(users)
        count += 1
        #use count-break during dev to avoid twitter restrictions
        #if (count>10):
        #    break
    except tweepy.TweepError:
        #catches TweepError when rate limiting occurs, sleeps, then restarts.
        #nominally 15 minnutes, make a bit longer to avoid attention.
        print "sleeping...."
        time.sleep(60*16)
        user = next(users)
    except StopIteration:
        break
    try:
        print "Writing to JSON tweet number:"+str(count)
        #json.dump(user._json,file,sort_keys = True,indent = 4)
        data.append(user._json)
    except UnicodeEncodeError:
        errorCount += 1
        print "UnicodeEncodeError,errorCount ="+str(errorCount)

json.dump(data,file,sort_keys = True,indent = 4)
print "completed, errorCount ="+str(errorCount)+" total tweets="+str(count)

    #todo: write users to file, search users for interests, locations etc.

"""
http://docs.tweepy.org/en/v3.5.0/api.html?highlight=tweeperror#TweepError
NB: RateLimitError inherits TweepError.
http://docs.tweepy.org/en/v3.2.0/api.html#API  wait_on_rate_limit & wait_on_rate_limit_notify
NB: possibly makes the sleep redundant but leave until verified.

"""
