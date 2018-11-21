import tweepy
from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener
import time as time2
from py2neo import Graph, Path, Node, Relationship
from datetime import datetime, date, time, tzinfo, timedelta
import json
import configparser
import argparse
import binascii
import asyncio

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
parser_line.add_argument('-type', '--db_type', default='Neo4j', help='For future use: indicate db type')
parser_line.add_argument('-proto', '--protocol', default='bolt', help='For future use: indicate protocol to connect to db')
parser_line.add_argument('-lang', '--language', default='cypher', help='For future use: indicate language to query the db')
parser_line.add_argument('-sec', '--secure', default='False', help='Flag for secure connection')
parser_line.add_argument('-server', '--server_name', default='localhost', help='FQDN of the db server')
parser_line.add_argument('-port', '--server_port', default='7687', help='server socket hosting the db service')
parser_line.add_argument('-pwd', '--db_password', required=True, help='service password to access the db')
parser_line.add_argument('-set', '--result_set', default='Output/search.json', help='Result set file from streaming script  (Default: Output/search.json)')
parser_line.add_argument('-name', '--conference_name', required=True, help='Name of the conference for the master node')
parser_line.add_argument('-loc', '--conference_location', required=True, help='Location of the conference for the master node')
parser_line.add_argument('-time', '--conference_time_zone', required=True, help='Number of (+/-) hours from UTC reference of the conference\'s timezone')
parser_line.add_argument('-start', '--conference_start_date', required=True, help='First day of the conference in dd/mm/yyyy format')
parser_line.add_argument('-end', '--conference_end_date', required=True, help='Last day of the conference in dd/mm/yyyy format')
parser_line.add_argument('-purge', '--purge_before_import', default='false', help='Indicate if the graph must be deleted before importing (Default: false)')
parser_line.add_argument('-fname', '--filter_organizer_twitter_screename', help='Twitter screename that helps to filter out organizer tweets and retweets')
parser_line.add_argument('-fhash', '--filter_conference_hashtag', help='Hashtag of the conference')
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

    db_type = config['Graph']['db_type']
    protocol = config['Graph']['protocol']
    language = config['Graph']['language']
    server_name = config['Graph']['server_name']
	secure = config['Graph']['secure']
    server_port = config['Graph']['server_port']
    db_password = config['Graph']['db_password']

    result_set = config['Processing']['result_set']
    conference_name = config['Processing']['conference_name']
    conference_location = config['Processing']['conference_location']
    conference_time_zone = config['Processing']['conference_time_zone']
    conference_start_date = config['Processing']['conference_start_date']
    conference_end_date = config['Processing']['conference_end_date']

    purge_before_import = config['Misc']['purge_before_import']
    filter_organizer_twitter_screename = config['Misc']['filter_organizer_twitter_screename']
    filter_conference_hashtag = config['Misc']['filter_conference_hashtag']

elif elements['cmd'] == 'line':
    output_filenane = elements['output_filename']
    search_query = elements['search']

    consumer_key = elements['consumer_key']
    consumer_secret = elements['consumer_secret']
    access_key = elements['access_key']
    access_secret = elements['access_secret']

    db_type = elements['db_type']
    protocol = elements['protocol']
    language = elements['language']
	secure = elements['secure']
    server_name = elements['server_name']
    server_port = elements['server_port']
    db_password = elements['db_password']

    result_set = elements['result_set']
    conference_name = elements['conference_name']
    conference_location = elements['conference_location']
    conference_time_zone = elements['conference_time_zone']
    conference_start_date = elements['conference_start_date']
    conference_end_date = elements['conference_end_date']

    purge_before_import = elements['purge_before_import']
    filter_organizer_twitter_screename = elements['filter_organizer_twitter_screename']
    filter_conference_hashtag = elements['filter_conference_hashtag']

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

#Initialization of time zone translation as Twitter returns results in UTC
class EDT(tzinfo):
	def utcoffset(self, dt):
		return timedelta(hours=int(conference_time_zone))

	def dst(self, dt):
		return timedelta(hours=1)

class UTC(tzinfo):
	def utcoffset(self, dt):
		return timedelta(hours=0)

#Load classes for Graph objects
class PartOf(Relationship): pass
class RelatesTo(Relationship): pass
class RefersTo(Relationship): pass
class Mentions(Relationship): pass
class Using(Relationship): pass
class AuthoredBy(Relationship): pass
class RetweetedBy(Relationship): pass
class QuotedBy(Relationship): pass
class ReplyBy(Relationship): pass
class ReplyTo(Relationship): pass
class RetweetOf(Relationship): pass
class QuoteOf(Relationship): pass
class ReplyOf(Relationship): pass
class LocatedAt(Relationship): pass

#Connect to db
if secure == 'True':
	graph = Graph(protocol + '://' + server_name + ':' + server_port, password=db_password, secure=True)
else:
	graph = Graph(protocol + '://' + server_name + ':' + server_port, password=db_password)

print("Initialiazing...")

if purge_before_import == 'True':
    print("Purging DB...")
    graph.delete_all()
    print("Purge completed...")

#Managing dates
start_t = conference_start_date.split('/')
end_t = conference_end_date.split('/')

#Building Conference scope
dates = []
objs = []
idv_start = datetime(int(start_t[2]), int(start_t[1]), int(start_t[0]), 0, 0, 0, tzinfo=EDT())
idv_end = datetime(int(end_t[2]), int(end_t[1]), int(end_t[0]), 23, 59, 59, tzinfo=EDT())
idv = Node("Conference", name=conference_name, start=idv_start.strftime("%d/%m/%Y %H:%M:%S %z"), end=idv_end.strftime("%d/%m/%Y %H:%M:%S %z"), location=conference_location)
graph.merge(idv, "Conference", "name")

prec_start = datetime(int(start_t[2]), 1, 1, 0, 0, 0, tzinfo=EDT())
prec_end = datetime(int(start_t[2]), int(start_t[1]), int(start_t[0])-1, 23, 59, 59, tzinfo=EDT())
dates.append([prec_start, prec_end])
prec = Node("Time", name="Pre-Conference of " + conference_name, start=prec_start.strftime("%d/%m/%Y %H:%M:%S %z"), end=prec_end.strftime("%d/%m/%Y %H:%M:%S %z"))
graph.merge(prec, "Time", "name")
objs.append(prec)
obj = PartOf(prec, idv)
graph.merge(obj)

#Building conference schedule
i = int(start_t[0])
j = 0

while i < (int(end_t[0]) + 1):
    start_d = datetime(int(start_t[2]), int(start_t[1]), i, 0, 0, 0, tzinfo=EDT())
    end_d = datetime(int(start_t[2]), int(start_t[1]), i, 23, 59, 59, tzinfo=EDT())
    dates.append([start_d, end_d])
    k = j+1
    k = str(k)
    day = Node("Time", name="Day #" + k + " of " + conference_name, start=start_d.strftime("%d/%m/%Y %H:%M:%S %z"), end=end_d.strftime("%d/%m/%Y %H:%M:%S %z"))
    graph.merge(day, "Time", "name")
    objs.append(day)
    obj = PartOf(day, idv)
    graph.merge(obj)
    i+=1
    j+=1

posc_start = datetime(int(end_t[2]), int(end_t[1]), int(end_t[0]), 0, 0, 0, tzinfo=EDT())
posc_end = datetime(int(end_t[2]), 12, 31, 23, 59, 59, tzinfo=EDT())
dates.append([posc_start, posc_end])
posc = Node("Time", name="Post-Conference of " + conference_name, start=posc_start.strftime("%d/%m/%Y %H:%M:%S %z"), end=posc_end.strftime("%d/%m/%Y %H:%M:%S %z"))
graph.merge(posc, "Time", "name")
objs.append(posc)
obj = PartOf(posc, idv)
graph.merge(obj)

#start Twitter handle
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_key, access_secret)
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, parser=tweepy.parsers.JSONParser())


print('Initialization completed...')

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

async def graph_load(datas):
    print('Drilling...')
    #data = datas[0]
    #tweets = tweepy.Cursor(api.search,q=drill_query, tweet_mode='extended').items()
    for data in datas:
        label = "----Drilling--"
        print(label + 'Tweet ' + data['id_str'])
        if data['user']['screen_name'] != filter_organizer_twitter_screename:
            print(label + 'Process Tweet user')

            user = Node("User", name="@" + data['user']['screen_name'], real_name=data['user']['name'], id=data['user']['id_str'], description=data['user']['description'])
            graph.merge(user, "User", "name")

            if ('location' in data['user']) and (data['user']['location'] is not None):
                location = Node("Location", name=data['user']['location'])
                graph.merge(location, "Location", "name")

                rel = LocatedAt(user, location)
                graph.merge(rel)

                graph.run("MATCH (Location {name: {a}})<-[r:LOCATED_AT]-() WITH Location, Count(r) as Total SET Location.habitants = Total", a=data['user']['location'])

            if 'retweeted_status' in data:
                print(label + "Got a retweet/quote")
                if 'extended_tweet' in data['retweeted_status']:
                    print(label + '--Retweet/Quote--Extended')
                    tweet = Node("Tweet", name=data['retweeted_status']['extended_tweet']['full_text'], tweet_id=data['id_str'], created_at=data['created_at'], favorites=data['favorite_count'], retweets=data['retweet_count'])
                    graph.merge(tweet, "Tweet", "tweet_id")

                    for hashtag in data['retweeted_status']['extended_tweet']['entities']['hashtags']:
                        if hashtag['text'].upper() != filter_conference_hashtag.upper():
                            obj = Node("Hashtag", name="#" + hashtag['text'].upper())
                            graph.merge(obj, "Hashtag", "name")

                            rel = RefersTo(tweet, obj)
                            graph.merge(rel)

                            graph.run("MATCH (Hashtag {name: {a}})<-[r:REFERS_TO]-() WITH Hashtag, Count(r) as Total SET Hashtag.mentioned = Total",a="#" + hashtag['text'].upper())

                    for user_mention in data['retweeted_status']['extended_tweet']['entities']['user_mentions']:
                        if user_mention['screen_name'] != filter_organizer_twitter_screename:
                            obj = Node("User", name="@" + user_mention['screen_name'], id=user_mention['id_str'])
                            graph.merge(obj, "User", "name")

                            rel = Mentions(tweet, obj)
                            graph.merge(rel)

                            graph.run("MATCH (User {id: {a}})<-[r:MENTIONS]-() WITH User, Count(r) as Total SET User.mentioned = Total",a=user_mention['id_str'])

                else:
                    print(label + '--Retweet/Quote--Simple')
                    if 'full_text' in data:
                        tweet = Node("Tweet", name=data['full_text'], tweet_id=data['id_str'], created_at=data['created_at'], favorites=data['favorite_count'], retweets=data['retweet_count'])
                    else:
                        tweet = Node("Tweet", name=data['text'], tweet_id=data['id_str'], created_at=data['created_at'], favorites=data['favorite_count'], retweets=data['retweet_count'])

                    graph.merge(tweet, "Tweet", "tweet_id")

                    for hashtag in data['entities']['hashtags']:
                        if hashtag['text'].upper() != filter_conference_hashtag.upper():
                            obj = Node("Hashtag", name="#" + hashtag['text'].upper())
                            graph.merge(obj, "Hashtag", "name")

                            rel = RefersTo(tweet, obj)
                            graph.merge(rel)

                            graph.run("MATCH (Hashtag {name: {a}})<-[r:REFERS_TO]-() WITH Hashtag, Count(r) as Total SET Hashtag.mentioned = Total",a="#" + hashtag['text'].upper())

                    for user_mention in data['entities']['user_mentions']:
                        if user_mention['screen_name'] != filter_organizer_twitter_screename:
                            obj = Node("User", name="@" + user_mention['screen_name'], id=user_mention['id_str'])
                            graph.merge(obj, "User", "name")

                            rel = Mentions(tweet, obj)
                            graph.merge(rel)

                            graph.run("MATCH (User {id: {a}})<-[r:MENTIONS]-() WITH User, Count(r) as Total SET User.mentioned = Total",a=user_mention['id_str'])

                print(label + '--Retweet/Quote--Source')
                source = Node("Source", name=data['source'].split('>')[1].split('<')[0])
                graph.merge(source, "Source", "name")

                rel = Using(tweet, source)
                graph.merge(rel)

                graph.run("MATCH (Source {name: {a}})<-[r:USING]-() WITH Source, Count(r) as Total SET Source.used = Total", a=data['source'].split('>')[1].split('<')[0])

                print(label + '--Retweet/Quote--Author')
                rel = AuthoredBy(tweet, user)
                graph.merge(rel)

                graph.run("MATCH (User {name: {a}})<-[r:AUTHORED_BY]-() WITH User, Count(r) as Total SET User.tweets = Total", a="@" + data['user']['screen_name'])

                nextTweet =  Node("Tweet", tweet_id=data['retweeted_status']['id_str'])
                graph.merge(nextTweet, "Tweet", "tweet_id")

                if data['is_quote_status'] == True:
                    print(label + "--Retweet/quote--In fact, got a quote")
                    rel = QuoteOf(tweet, nextTweet)
                    graph.merge(rel)

                    rel = QuotedBy(nextTweet, user)
                    graph.merge(rel)

                    graph.run("MATCH (Tweet {id: {a}})-[r:QUOTED_BY]->() WITH Tweet, Count(r) as Total SET Tweet.quoted = Total", a=data['retweeted_status']['id_str'])
                    graph.run("MATCH ()-[r:QUOTED_BY]->(User {name: {a}}) WITH User, Count(r) as Total SET User.quotes = Total", a="@" + data['user']['screen_name'])

                else:
                    print(label + "--Retweet/quote--In fact, got a retweet")
                    rel = RetweetOf(tweet, nextTweet)
                    graph.merge(rel)

                    rel = RetweetedBy(nextTweet, user)
                    graph.merge(rel)

                    graph.run("MATCH (Tweet {id: {a}})-[r:RETWEETED_BY]->() WITH Tweet, Count(r) as Total SET Tweet.retweeted = Total", a=data['retweeted_status']['id_str'])
                    graph.run("MATCH ()-[r:QUOTED_BY]->(User {name: {a}}) WITH User, Count(r) as Total SET User.retweets = Total", a="@" + data['user']['screen_name'])

                print(label + "--Retweet/quote--Drilling " + data['retweeted_status']['id_str'])
                #graph_load(api.statuses_lookup(int(binascii.hexlify(data['retweeted_status']['id_str']))))
                #graph_load("retweets_of_status_id:" + data['retweeted_status']['id_str'])
                next_ids = []
                next_ids.append(data['retweeted_status']['id_str'])
                await(graph_load(api.statuses_lookup(next_ids)))

            elif data['in_reply_to_status_id'] != None:
                print(label + "Got a reply")
                if 'full_text' in data:
                    tweet = Node("Tweet", name=data['full_text'], tweet_id=data['id_str'], created_at=data['created_at'], favorites=data['favorite_count'], retweets=data['retweet_count'])
                else:
                    tweet = Node("Tweet", name=data['text'], tweet_id=data['id_str'], created_at=data['created_at'], favorites=data['favorite_count'], retweets=data['retweet_count'])

                graph.merge(tweet, "Tweet", "tweet_id")

                if 'extended_tweet' in data:
                    print(label + "--Reply--Extended")
                    tweet = Node("Tweet", name=data['extended_tweet']['full_text'], tweet_id=data['id_str'], created_at=data['created_at'], favorites=data['favorite_count'], retweets=data['retweet_count'])
                    graph.merge(tweet, "Tweet", "tweet_id")

                    for hashtag in data['extended_tweet']['entities']['hashtags']:
                        if hashtag['text'].upper() != filter_conference_hashtag.upper():
                            obj = Node("Hashtag", name="#" + hashtag['text'].upper())
                            graph.merge(obj, "Hashtag", "name")

                            rel = RefersTo(tweet, obj)
                            graph.merge(rel)

                            graph.run("MATCH (Hashtag {name: {a}})<-[r:REFERS_TO]-() WITH Hashtag, Count(r) as Total SET Hashtag.mentioned = Total",a="#" + hashtag['text'].upper())

                    for user_mention in data['extended_tweet']['entities']['user_mentions']:
                        if user_mention['screen_name'] != filter_organizer_twitter_screename:
                            obj = Node("User", name="@" + user_mention['screen_name'], id=user_mention['id_str'])
                            graph.merge(obj, "User", "name")

                            rel = Mentions(tweet, obj)
                            graph.merge(rel)

                            graph.run("MATCH (User {id: {a}})<-[r:MENTIONS]-() WITH User, Count(r) as Total SET User.mentioned = Total",a=user_mention['id_str'])
                else:
                    print(label + "--Reply--Simple")
                    if 'full_text' in data:
                        tweet = Node("Tweet", name=data['full_text'], tweet_id=data['id_str'], created_at=data['created_at'], favorites=data['favorite_count'], retweets=data['retweet_count'])
                    else:
                        tweet = Node("Tweet", name=data['text'], tweet_id=data['id_str'], created_at=data['created_at'], favorites=data['favorite_count'], retweets=data['retweet_count'])

                    graph.merge(tweet, "Tweet", "tweet_id")

                    for hashtag in data['entities']['hashtags']:
                        if hashtag['text'].upper() != filter_conference_hashtag.upper():
                            obj = Node("Hashtag", name="#" + hashtag['text'].upper())
                            graph.merge(obj, "Hashtag", "name")

                            rel = RefersTo(tweet, obj)
                            graph.merge(rel)

                            graph.run("MATCH (Hashtag {name: {a}})<-[r:REFERS_TO]-() WITH Hashtag, Count(r) as Total SET Hashtag.mentioned = Total",a="#" + hashtag['text'].upper())

                    for user_mention in data['entities']['user_mentions']:
                        if user_mention['screen_name'] != filter_organizer_twitter_screename:
                            obj = Node("User", name="@" + user_mention['screen_name'], id=user_mention['id_str'])
                            graph.merge(obj, "User", "name")

                            rel = Mentions(tweet, obj)
                            graph.merge(rel)

                            graph.run("MATCH (User {id: {a}})<-[r:MENTIONS]-() WITH User, Count(r) as Total SET User.mentioned = Total",a=user_mention['id_str'])

                print(label + "--Reply--Source")
                source = Node("Source", name=data['source'].split('>')[1].split('<')[0])
                graph.merge(source, "Source", "name")

                rel = Using(tweet, source)
                graph.merge(rel)

                graph.run("MATCH (Source {name: {a}})<-[r:USING]-() WITH Source, Count(r) as Total SET Source.used = Total", a=data['source'].split('>')[1].split('<')[0])

                print(label + "--Reply--Author")
                rel = AuthoredBy(tweet, user)
                graph.merge(rel)

                graph.run("MATCH (User {name: {a}})<-[r:AUTHORED_BY]-() WITH User, Count(r) as Total SET User.tweets = Total", a="@" + data['user']['screen_name'])

                obj = Node("Tweet", tweet_id=data['in_reply_to_status_id_str'])
                graph.merge(obj, "Tweet", "tweet_id")

                rel = ReplyTo(tweet, obj)
                graph.merge(rel)

                graph.run("MATCH (Tweet {tweet_id: {a}})<-[r:REPLY_TO]-() WITH Tweet, Count(r) as Total SET Tweet.replied = Total", a=data['in_reply_to_status_id_str'])
                if 'full_text' in data:
                    graph.run("MATCH ()<-[r:REPLY_TO]-(Tweet {name: {a}}) WITH Tweet, Count(r) as Total SET Tweet.replying = Total", a=data['full_text'])
                else:
                    graph.run("MATCH ()<-[r:REPLY_TO]-(Tweet {name: {a}}) WITH Tweet, Count(r) as Total SET Tweet.replying = Total", a=data['text'])

                print(label + '--Reply--Drilling ' + data['in_reply_to_status_id_str'])
                #graph_load(api.statuses_lookup(int(binascii.hexlify(data['in_reply_to_status_id_str']))))
                #graph_load("in_reply_to_status_id:" + data['in_reply_to_status_id_str'])
                next_ids = []
                next_ids.append(data['in_reply_to_status_id_str'])
                await(graph_load(api.statuses_lookup(next_ids)))

            else:
                print(label + "Got a tweet")
                #print(data)
                if hasattr(data,'extended_tweet'):
                    print(label + '--Tweet--Extended')
                    tweet = Node("Tweet", name=data['extended_tweet']['full_text'], tweet_id=data['id_str'], created_at=data['created_at'], favorites=data['favorite_count'], retweets=data['retweet_count'])

                    graph.merge(tweet, "Tweet", "tweet_id")

                    for hashtag in data['extended_tweet']['entities']['hashtags']:
                        if hashtag['text'].upper() != filter_conference_hashtag.upper():
                            obj = Node("Hashtag", name="#" + hashtag['text'].upper())
                            graph.merge(obj, "Hashtag", "name")

                            rel = RefersTo(tweet, obj)
                            graph.merge(rel)

                            graph.run("MATCH (Hashtag {name: {a}})<-[r:REFERS_TO]-() WITH Hashtag, Count(r) as Total SET Hashtag.mentioned = Total",a="#" + hashtag['text'].upper())

                    for user_mention in data['extended_tweet']['entities']['user_mentions']:
                        if user_mention['screen_name'] != filter_organizer_twitter_screename:
                            obj = Node("User", name="@" + user_mention['screen_name'], id=user_mention['id_str'])
                            graph.merge(obj, "User", "name")

                            rel = Mentions(tweet, obj)
                            graph.merge(rel)

                            graph.run("MATCH (User {id: {a}})<-[r:MENTIONS]-() WITH User, Count(r) as Total SET User.mentioned = Total",a=user_mention['id_str'])

                else:
                    print(label + '--Tweet--Simple')
                    if 'full_text' in data:
                        tweet = Node("Tweet", name=data['full_text'], tweet_id=data['id_str'], created_at=data['created_at'], favorites=data['favorite_count'], retweets=data['retweet_count'])
                    else:
                        tweet = Node("Tweet", name=data['text'], tweet_id=data['id_str'], created_at=data['created_at'], favorites=data['favorite_count'], retweets=data['retweet_count'])

                    graph.merge(tweet, "Tweet", "tweet_id")

                    for hashtag in data['entities']['hashtags']:
                        if hashtag['text'].upper() != filter_conference_hashtag.upper():
                            obj = Node("Hashtag", name="#" + hashtag['text'].upper())
                            graph.merge(obj, "Hashtag", "name")

                            rel = RefersTo(tweet, obj)
                            graph.merge(rel)

                            graph.run("MATCH (Hashtag {name: {a}})<-[r:REFERS_TO]-() WITH Hashtag, Count(r) as Total SET Hashtag.mentioned = Total",a="#" + hashtag['text'].upper())

                    for user_mention in data['entities']['user_mentions']:
                        if user_mention['screen_name'] != filter_organizer_twitter_screename:
                            obj = Node("User", name="@" + user_mention['screen_name'], id=user_mention['id_str'])
                            graph.merge(obj, "User", "name")

                            rel = Mentions(tweet, obj)
                            graph.merge(rel)

                            graph.run("MATCH (User {id: {a}})<-[r:MENTIONS]-() WITH User, Count(r) as Total SET User.mentioned = Total",a=user_mention['id_str'])

                print(label + '--Tweet--Date')
                t1 = datetime.strptime(data['created_at'], "%a %b %d %H:%M:%S +0000 %Y")
                t2 = datetime(t1.year, t1.month, t1.day, t1.hour, t1.minute, t1.second, tzinfo=UTC())

                i = 0

                for day_time in dates:
                    if (t2 >= day_time[0]) and (t2 < day_time[1]):
                        rel = RelatesTo(tweet, objs[i])
                        graph.merge(rel)
                    i+=1

                print(label + '--Tweet--Source')
                source = Node("Source", name=data['source'].split('>')[1].split('<')[0])
                graph.merge(source, "Source", "name")

                rel = Using(tweet, source)
                graph.merge(rel)

                graph.run("MATCH (Source {name: {a}})<-[r:USING]-() WITH Source, Count(r) as Total SET Source.used = Total", a=data['source'].split('>')[1].split('<')[0])

                print(label + '--Tweet--Author')
                rel = AuthoredBy(tweet, user)
                graph.merge(rel)

                graph.run("MATCH (User {name: {a}})<-[r:AUTHORED_BY]-() WITH User, Count(r) as Total SET User.tweets = Total", a="@" + data['user']['screen_name'])

#Importing data
print("Importing data...")
with open(result_set) as f:
    datas = json.load(f)

### Process tweets
for data in datas:
	try:
		print('Load a tweet')
		#graph_load(json_data)

		print('Tweet Loading')
		if data['user']['screen_name'] != filter_organizer_twitter_screename:
			print('Process Tweet user')

			user = Node("User", name="@" + data['user']['screen_name'], real_name=data['user']['name'], id=data['user']['id_str'], description=data['user']['description'])
			graph.merge(user, "User", "name")

			if ('location' in data['user']) and (data['user']['location'] is not None):
				location = Node("Location", name=data['user']['location'])
				graph.merge(location, "Location", "name")

				rel = LocatedAt(user, location)
				graph.merge(rel)

				graph.run("MATCH (Location {name: {a}})<-[r:LOCATED_AT]-() WITH Location, Count(r) as Total SET Location.habitants = Total", a=data['user']['location'])

			if 'retweeted_status' in data:
				print("got a retweet/quote")
				if 'extended_tweet' in data['retweeted_status']:
					print('--Retweet/Quote--Extended')
					tweet = Node("Tweet", name=data['retweeted_status']['extended_tweet']['full_text'], tweet_id=data['id_str'], created_at=data['created_at'], favorites=data['favorite_count'], retweets=data['retweet_count'])
					graph.merge(tweet, "Tweet", "tweet_id")

					for hashtag in data['retweeted_status']['extended_tweet']['entities']['hashtags']:
						if hashtag['text'].upper() != filter_conference_hashtag.upper():
							obj = Node("Hashtag", name="#" + hashtag['text'].upper())
							graph.merge(obj, "Hashtag", "name")

							rel = RefersTo(tweet, obj)
							graph.merge(rel)

							graph.run("MATCH (Hashtag {name: {a}})<-[r:REFERS_TO]-() WITH Hashtag, Count(r) as Total SET Hashtag.mentioned = Total",a="#" + hashtag['text'].upper())

					for user_mention in data['retweeted_status']['extended_tweet']['entities']['user_mentions']:
						if user_mention['screen_name'] != filter_organizer_twitter_screename:
							obj = Node("User", name="@" + user_mention['screen_name'], id=user_mention['id_str'])
							graph.merge(obj, "User", "name")

							rel = Mentions(tweet, obj)
							graph.merge(rel)

							graph.run("MATCH (User {id: {a}})<-[r:MENTIONS]-() WITH User, Count(r) as Total SET User.mentioned = Total",a=user_mention['id_str'])

				else:
                                    print('--Retweet/Quote--Simple')
                                    if 'full_text' in data:
                                        tweet = Node("Tweet", name=data['full_text'], tweet_id=data['id_str'], created_at=data['created_at'], favorites=data['favorite_count'], retweets=data['retweet_count'])
                                    else:
                                        tweet = Node("Tweet", name=data['text'], tweet_id=data['id_str'], created_at=data['created_at'], favorites=data['favorite_count'], retweets=data['retweet_count'])
                                    graph.merge(tweet, "Tweet", "tweet_id")

                                    for hashtag in data['entities']['hashtags']:
                                        if hashtag['text'].upper() != filter_conference_hashtag.upper():
                                            obj = Node("Hashtag", name="#" + hashtag['text'].upper())
                                            graph.merge(obj, "Hashtag", "name")

                                            rel = RefersTo(tweet, obj)
                                            graph.merge(rel)

                                            graph.run("MATCH (Hashtag {name: {a}})<-[r:REFERS_TO]-() WITH Hashtag, Count(r) as Total SET Hashtag.mentioned = Total",a="#" + hashtag['text'].upper())

                                    for user_mention in data['entities']['user_mentions']:
                                        if user_mention['screen_name'] != filter_organizer_twitter_screename:
                                            obj = Node("User", name="@" + user_mention['screen_name'], id=user_mention['id_str'])
                                            graph.merge(obj, "User", "name")

                                            rel = Mentions(tweet, obj)
                                            graph.merge(rel)

                                            graph.run("MATCH (User {id: {a}})<-[r:MENTIONS]-() WITH User, Count(r) as Total SET User.mentioned = Total",a=user_mention['id_str'])

				print('--Retweet/Quote--Source')
				source = Node("Source", name=data['source'].split('>')[1].split('<')[0])
				graph.merge(source, "Source", "name")

				rel = Using(tweet, source)
				graph.merge(rel)

				graph.run("MATCH (Source {name: {a}})<-[r:USING]-() WITH Source, Count(r) as Total SET Source.used = Total", a=data['source'].split('>')[1].split('<')[0])

				print('--Retweet/Quote--Author')
				rel = AuthoredBy(tweet, user)
				graph.merge(rel)

				graph.run("MATCH (User {name: {a}})<-[r:AUTHORED_BY]-() WITH User, Count(r) as Total SET User.tweets = Total", a="@" + data['user']['screen_name'])

				nextTweet =  Node("Tweet", tweet_id=data['retweeted_status']['id_str'])
				graph.merge(nextTweet, "Tweet", "tweet_id")

				if data['is_quote_status'] == True:
					print("--Retweet/quote--In fact, got a quote")
					rel = QuoteOf(tweet, nextTweet)
					graph.merge(rel)

					rel = QuotedBy(nextTweet, user)
					graph.merge(rel)

					graph.run("MATCH (Tweet {id: {a}})-[r:QUOTED_BY]->() WITH Tweet, Count(r) as Total SET Tweet.quoted = Total", a=data['retweeted_status']['id_str'])
					graph.run("MATCH ()-[r:QUOTED_BY]->(User {name: {a}}) WITH User, Count(r) as Total SET User.quotes = Total", a="@" + data['user']['screen_name'])

				else:
					print("--Retweet/quote--In fact, got a retweet")
					rel = RetweetOf(tweet, nextTweet)
					graph.merge(rel)

					rel = RetweetedBy(nextTweet, user)
					graph.merge(rel)

					graph.run("MATCH (Tweet {id: {a}})-[r:RETWEETED_BY]->() WITH Tweet, Count(r) as Total SET Tweet.retweeted = Total", a=data['retweeted_status']['id_str'])
					graph.run("MATCH ()-[r:QUOTED_BY]->(User {name: {a}}) WITH User, Count(r) as Total SET User.retweets = Total", a="@" + data['user']['screen_name'])

				print("--Retweet/quote--Drilling " + data['retweeted_status']['id_str'])
				#graph_load(api.statuses_lookup(int(binascii.hexlify(data['retweeted_status']['id_str']))))
				#graph_load("retweets_of_status_id:" + data['retweeted_status']['id_str'])
				next_ids = []
				next_ids.append(data['retweeted_status']['id_str'])
				loop.run_until_complete(graph_load(api.statuses_lookup(next_ids)))

			elif data['in_reply_to_status_id'] != None:
				print("got a reply")
				if 'full_text' in data:
				    tweet = Node("Tweet", name=data['full_text'], tweet_id=data['id_str'], created_at=data['created_at'], favorites=data['favorite_count'], retweets=data['retweet_count'])
				else:
				    tweet = Node("Tweet", name=data['text'], tweet_id=data['id_str'], created_at=data['created_at'], favorites=data['favorite_count'], retweets=data['retweet_count'])

				graph.merge(tweet, "Tweet", "tweet_id")

				if 'extended_tweet' in data:
					print("--Reply--Extended")
					tweet = Node("Tweet", name=data['extended_tweet']['full_text'], tweet_id=data['id_str'], created_at=data['created_at'], favorites=data['favorite_count'], retweets=data['retweet_count'])
					graph.merge(tweet, "Tweet", "tweet_id")

					for hashtag in data['extended_tweet']['entities']['hashtags']:
						if hashtag['text'].upper() != filter_conference_hashtag.upper():
							obj = Node("Hashtag", name="#" + hashtag['text'].upper())
							graph.merge(obj, "Hashtag", "name")

							rel = RefersTo(tweet, obj)
							graph.merge(rel)

							graph.run("MATCH (Hashtag {name: {a}})<-[r:REFERS_TO]-() WITH Hashtag, Count(r) as Total SET Hashtag.mentioned = Total",a="#" + hashtag['text'].upper())

					for user_mention in data['extended_tweet']['entities']['user_mentions']:
						if user_mention['screen_name'] != filter_organizer_twitter_screename:
							obj = Node("User", name="@" + user_mention['screen_name'], id=user_mention['id_str'])
							graph.merge(obj, "User", "name")

							rel = Mentions(tweet, obj)
							graph.merge(rel)

							graph.run("MATCH (User {id: {a}})<-[r:MENTIONS]-() WITH User, Count(r) as Total SET User.mentioned = Total",a=user_mention['id_str'])
				else:
					print("--Reply--Simple")
					if 'full_text' in data:
					    tweet = Node("Tweet", name=data['full_text'], tweet_id=data['id_str'], created_at=data['created_at'], favorites=data['favorite_count'], retweets=data['retweet_count'])
					else:
					    tweet = Node("Tweet", name=data['text'], tweet_id=data['id_str'], created_at=data['created_at'], favorites=data['favorite_count'], retweets=data['retweet_count'])
					graph.merge(tweet, "Tweet", "tweet_id")

					for hashtag in data['entities']['hashtags']:
						if hashtag['text'].upper() != filter_conference_hashtag.upper():
							obj = Node("Hashtag", name="#" + hashtag['text'].upper())
							graph.merge(obj, "Hashtag", "name")

							rel = RefersTo(tweet, obj)
							graph.merge(rel)

							graph.run("MATCH (Hashtag {name: {a}})<-[r:REFERS_TO]-() WITH Hashtag, Count(r) as Total SET Hashtag.mentioned = Total",a="#" + hashtag['text'].upper())

					for user_mention in data['entities']['user_mentions']:
						if user_mention['screen_name'] != filter_organizer_twitter_screename:
							obj = Node("User", name="@" + user_mention['screen_name'], id=user_mention['id_str'])
							graph.merge(obj, "User", "name")

							rel = Mentions(tweet, obj)
							graph.merge(rel)

							graph.run("MATCH (User {id: {a}})<-[r:MENTIONS]-() WITH User, Count(r) as Total SET User.mentioned = Total",a=user_mention['id_str'])

				print("--Reply--Source")
				source = Node("Source", name=data['source'].split('>')[1].split('<')[0])
				graph.merge(source, "Source", "name")

				rel = Using(tweet, source)
				graph.merge(rel)

				graph.run("MATCH (Source {name: {a}})<-[r:USING]-() WITH Source, Count(r) as Total SET Source.used = Total", a=data['source'].split('>')[1].split('<')[0])

				print("--Reply--Author")
				rel = AuthoredBy(tweet, user)
				graph.merge(rel)

				graph.run("MATCH (User {name: {a}})<-[r:AUTHORED_BY]-() WITH User, Count(r) as Total SET User.tweets = Total", a="@" + data['user']['screen_name'])

				obj = Node("Tweet", tweet_id=data['in_reply_to_status_id_str'])
				graph.merge(obj, "Tweet", "tweet_id")

				rel = ReplyTo(tweet, obj)
				graph.merge(rel)

				graph.run("MATCH (Tweet {tweet_id: {a}})<-[r:REPLY_TO]-() WITH Tweet, Count(r) as Total SET Tweet.replied = Total", a=data['in_reply_to_status_id_str'])
				if 'full_text' in data:
				    graph.run("MATCH ()<-[r:REPLY_TO]-(Tweet {name: {a}}) WITH Tweet, Count(r) as Total SET Tweet.replying = Total", a=data['full_text'])
				else:
				    graph.run("MATCH ()<-[r:REPLY_TO]-(Tweet {name: {a}}) WITH Tweet, Count(r) as Total SET Tweet.replying = Total", a=data['text'])

				print('--Reply--Drilling ' + data['in_reply_to_status_id_str'])
				#graph_load(api.statuses_lookup(int(binascii.hexlify(data['in_reply_to_status_id_str']))))
				#graph_load("in_reply_to_status_id:" + data['in_reply_to_status_id_str'])
				next_ids = []
				next_ids.append(data['in_reply_to_status_id_str'])
				loop.run_until_complete(graph_load(api.statuses_lookup(next_ids)))

			else:
				print("got a tweet")
				#print(data)
				if hasattr(data,'extended_tweet'):
					print('--Tweet--Extended')
					tweet = Node("Tweet", name=data['extended_tweet']['full_text'], tweet_id=data['id_str'], created_at=data['created_at'], favorites=data['favorite_count'], retweets=data['retweet_count'])

					graph.merge(tweet, "Tweet", "tweet_id")

					for hashtag in data['extended_tweet']['entities']['hashtags']:
						if hashtag['text'].upper() != filter_conference_hashtag.upper():
							obj = Node("Hashtag", name="#" + hashtag['text'].upper())
							graph.merge(obj, "Hashtag", "name")

							rel = RefersTo(tweet, obj)
							graph.merge(rel)

							graph.run("MATCH (Hashtag {name: {a}})<-[r:REFERS_TO]-() WITH Hashtag, Count(r) as Total SET Hashtag.mentioned = Total",a="#" + hashtag['text'].upper())

					for user_mention in data['extended_tweet']['entities']['user_mentions']:
						if user_mention['screen_name'] != filter_organizer_twitter_screename:
							obj = Node("User", name="@" + user_mention['screen_name'], id=user_mention['id_str'])
							graph.merge(obj, "User", "name")

							rel = Mentions(tweet, obj)
							graph.merge(rel)

							graph.run("MATCH (User {id: {a}})<-[r:MENTIONS]-() WITH User, Count(r) as Total SET User.mentioned = Total",a=user_mention['id_str'])

				else:
					print('--Tweet--Simple')
					if 'full_text' in data:
					    tweet = Node("Tweet", name=data['full_text'], tweet_id=data['id_str'], created_at=data['created_at'], favorites=data['favorite_count'], retweets=data['retweet_count'])
					else:
					    tweet = Node("Tweet", name=data['text'], tweet_id=data['id_str'], created_at=data['created_at'], favorites=data['favorite_count'], retweets=data['retweet_count'])
					graph.merge(tweet, "Tweet", "tweet_id")

					for hashtag in data['entities']['hashtags']:
						if hashtag['text'].upper() != filter_conference_hashtag.upper():
							obj = Node("Hashtag", name="#" + hashtag['text'].upper())
							graph.merge(obj, "Hashtag", "name")

							rel = RefersTo(tweet, obj)
							graph.merge(rel)

							graph.run("MATCH (Hashtag {name: {a}})<-[r:REFERS_TO]-() WITH Hashtag, Count(r) as Total SET Hashtag.mentioned = Total",a="#" + hashtag['text'].upper())

					for user_mention in data['entities']['user_mentions']:
						if user_mention['screen_name'] != filter_organizer_twitter_screename:
							obj = Node("User", name="@" + user_mention['screen_name'], id=user_mention['id_str'])
							graph.merge(obj, "User", "name")

							rel = Mentions(tweet, obj)
							graph.merge(rel)

							graph.run("MATCH (User {id: {a}})<-[r:MENTIONS]-() WITH User, Count(r) as Total SET User.mentioned = Total",a=user_mention['id_str'])

				print('--Tweet--Date')
				t1 = datetime.strptime(data['created_at'], "%a %b %d %H:%M:%S +0000 %Y")
				t2 = datetime(t1.year, t1.month, t1.day, t1.hour, t1.minute, t1.second, tzinfo=UTC())

				i = 0

				for day_time in dates:
					if (t2 >= day_time[0]) and (t2 < day_time[1]):
						rel = RelatesTo(tweet, objs[i])
						graph.merge(rel)
					i+=1

				print('--Tweet--Source')
				source = Node("Source", name=data['source'].split('>')[1].split('<')[0])
				graph.merge(source, "Source", "name")

				rel = Using(tweet, source)
				graph.merge(rel)

				graph.run("MATCH (Source {name: {a}})<-[r:USING]-() WITH Source, Count(r) as Total SET Source.used = Total", a=data['source'].split('>')[1].split('<')[0])

				print('--Tweet--Author')
				rel = AuthoredBy(tweet, user)
				graph.merge(rel)

				graph.run("MATCH (User {name: {a}})<-[r:AUTHORED_BY]-() WITH User, Count(r) as Total SET User.tweets = Total", a="@" + data['user']['screen_name'])

	#except AttributeError:
	#	print('Got an attribute error')
	#	print(data)
	#	print(AttributeError)

	except KeyError:
		print('Got a key error')
		print(data)
		print(KeyError)
