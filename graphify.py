from py2neo import Graph, Path, Node, Relationship
from datetime import datetime, date, time, tzinfo, timedelta
import json
import configparser
import argparse

#Configuration initialization
config = configparser.ConfigParser()

parser = argparse.ArgumentParser(description='Import tweets in a Graph DB')
subparsers = parser.add_subparsers(help='Add configuration from Ini file or through arguments')

parser_file = subparsers.add_parser('file', help='Adding configuration from a file (Default: Ini/Default.ini)')
parser_file.add_argument('cmd', const='file', action='store_const')
parser_file.add_argument('-i', '--ini_file', default='Ini/Default.ini', help='Path to the Ini file  (Default: Ini/Default.ini)')

parser_line = subparsers.add_parser('line', help='Adding configuration from a arguments in the command line')
parser_line.add_argument('cmd', const='line', action='store_const')
parser_line.add_argument('-type', '--db_type', default='Neo4j', help='For future use: indicate db type')
parser_line.add_argument('-proto', '--protocol', default='bolt', help='For future use: indicate protocol to connect to db')
parser_line.add_argument('-lang', '--language', default='cypher', help='For future use: indicate language to query the db')
parser_line.add_argument('-server', '--server_name', default='localhost', help='FQDN of the db server')
parser_line.add_argument('-port', '--server_port', default='7687', help='server socket hosting the db service')
parser_line.add_argument('-pwd', '--db_password', required=True, help='service password to access the db')
parser_file.add_argument('-set', '--result_set', default='Output/search.json', help='Result set file from streaming script  (Default: Output/search.json)')
parser_line.add_argument('-name', '--conference_name', required=True, help='Name of the conference for the master node')
parser_line.add_argument('-loc', '--conference_location', required=True, help='Location of the conference for the master node')
parser_line.add_argument('-time', '--conference_time_zone', required=True, help='Number of (+/-) hours from UTC reference of the conference\'s timezone')
parser_line.add_argument('-start', '--conference_start_date', required=True, help='First day of the conference in dd/mm/yyyy format')
parser_line.add_argument('-end', '--conference_end_date', required=True, help='Last day of the conference in dd/mm/yyyy format')
parser_line.add_argument('-purge', '--purge_before_import', default='false', help='Indicate if the graph must be deleted before importing (Default: false)')
parser_line.add_argument('-fname', '--filter_organizer_twitter_screename', help='Twitter screename that helps to filter out organizer twweets and retweets')
parser_line.add_argument('-fhash', '--filter_conference_hashtag', help='Hashtag of the conference')
parser_line.add_argument('-b', '--backup_ini_file_name', help='Name of the Ini file to backup from this request parameters')

args = parser.parse_args()
elements = vars(args)

#Configuration
if elements['cmd'] == 'file':
	#mettre une condition de verification de i, si i n'existe pas, i est forcement dans Ini/
	config.read(elements['ini_file'])

	db_type = config['Graph']['db_type']
	protocol = config['Graph']['protocol']
	language = config['Graph']['language']
	server_name = config['Graph']['server_name']
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

	db_type = elements['db_type']
	protocol = elements['protocol']
	language = elements['language']
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
			config['Graph'] = {'db_type': db_type, 'protocol': protocol, 'language': language, 'server_name': server_name, 'server_port': server_port, 'db_password': db_password }
			config['Processing'] = {'result_set': result_set, 'conference_name': conference_name, 'conference_location': conference_location, 'conference_time_zone': conference_time_zone, 'conference_start_date': conference_start_date, 'conference_end_date': conference_end_date}
			config['Misc'] =  {'purge_before_import': purge_before_import, 'filter_conference_hashtag': filter_conference_hashtag }
			with open('Ini/' + elements['backup_ini_file_name'], 'w') as configFile:
				config.write(configFile)
        else:
            print('You cannot overwrite the Default Ini file')
            exit

else:
    print('Sorry this command is invalid')
    exit

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
class Quoted(Relationship): pass
class ReplyTo(Relationship): pass
class LocatedAt(Relationship): pass

#Connect to db
graph = Graph(protocol + '://' + server_name + ':' + server_port, password=db_password)
print("Initialiazing...")

if purge_before_import == 'true':
	graph.delete_all()

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

prec_start = datetime(int(start_t[2]), 01, 01, 0, 0, 0, tzinfo=EDT())
prec_end = datetime(int(start_t[2]), int(start_t[1]), int(start_t[0])-1, 23, 59, 59, tzinfo=EDT())
dates.append([prec_start, prec_end])
prec = Node("Time", name="Pre-Conference", start=prec_start.strftime("%d/%m/%Y %H:%M:%S %z"), end=prec_end.strftime("%d/%m/%Y %H:%M:%S %z"))
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
	day = Node("Time", name="Day #" + k, start=start_d.strftime("%d/%m/%Y %H:%M:%S %z"), end=end_d.strftime("%d/%m/%Y %H:%M:%S %z"))
	graph.merge(day, "Time", "name")
	objs.append(day)
	obj = PartOf(day, idv)
	graph.merge(obj)
	i+=1
	j+1

posc_start = datetime(int(end_t[2]), int(end_t[1]), int(end_t[0]), 0, 0, 0, tzinfo=EDT())
posc_end = datetime(int(end_t[2]), 12, 31, 23, 59, 59, tzinfo=EDT())
dates.append([posc_start, posc_end])
posc = Node("Time", name="Post-Conference", start=posc_start.strftime("%d/%m/%Y %H:%M:%S %z"), end=posc_end.strftime("%d/%m/%Y %H:%M:%S %z"))
graph.merge(posc, "Time", "name")
objs.append(posc)
obj = PartOf(posc, idv)
graph.merge(obj)

#Importing data
print("Importing data...")
with open(result_set) as f:
    datas = json.load(f)

### Process tweets
for data in datas:
	if 'retweeted_status' in data:
		print("got a retweet")
		if data['user']['screen_name'] != filter_organizer_twitter_screename:
			tweet = Node("Tweet", name=data['retweeted_status']['full_text'], tweet_id=data['retweeted_status']['id_str'])
			graph.merge(tweet, "Tweet", "tweet_id")

			obj = Node("User", name="@" + data['user']['screen_name'], real_name=data['user']['name'], id=data['user']['id_str'], description=data['user']['description'])
			graph.merge(obj, "User", "name")

			rel = RetweetedBy(tweet, obj)
			graph.merge(rel)

			obj2 = Node("Location", name=data['user']['location'])
			graph.merge(obj, "Location", "name")

			rel = LocatedAt(obj, obj2)
			graph.merge(rel)
	elif 'quoted_status' in data:
		print("got a quote")
		tweet = Node("Tweet", name=data['full_text'], tweet_id=data['id_str'], created_at=data['created_at'], favorites=data['favorite_count'], retweets=data['retweet_count'])
		graph.merge(tweet, "Tweet", "tweet_id")

		obj = Node("Source", name=data['source'])
		graph.merge(obj, "Source", "name")

		rel = Using(tweet, obj)
		graph.merge(rel)

		obj = Node("User", name="@" + data['user']['screen_name'], real_name=data['user']['name'], id=data['user']['id_str'], description=data['user']['description'])
		graph.merge(obj, "User", "name")

		rel = AuthoredBy(tweet, obj)
		graph.merge(rel)

		obj2 = Node("Location", name=data['user']['location'])
		graph.merge(obj, "Location", "name")

		rel = LocatedAt(obj, obj2)
		graph.merge(rel)

		obj = Node("Tweet", name=data['quoted_status']['full_text'], tweet_id=data['quoted_status']['id_str'])
		graph.merge(obj, "Tweet", "tweet_id")

		rel = Quoted(tweet, obj)
		graph.merge(rel)

	elif data['in_reply_to_status_id'] != None:
		print("got a reply")
		tweet = Node("Tweet", name=data['full_text'], tweet_id=data['id_str'], created_at=data['created_at'], favorites=data['favorite_count'], retweets=data['retweet_count'])
		graph.merge(tweet, "Tweet", "tweet_id")

		obj = Node("Source", name=data['source'])
		graph.merge(obj, "Source", "name")

		rel = Using(tweet, obj)
		graph.merge(rel)

		obj = Node("User", name="@" + data['user']['screen_name'], real_name=data['user']['name'], id=data['user']['id_str'], description=data['user']['description'])
		graph.merge(obj, "User", "name")

		rel = AuthoredBy(tweet, obj)
		graph.merge(rel)

		obj2 = Node("Location", name=data['user']['location'])
		graph.merge(obj, "Location", "name")

		rel = LocatedAt(obj, obj2)
		graph.merge(rel)

		obj = Node("Tweet", tweet_id=data['in_reply_to_status_id_str'])
		graph.merge(obj, "Tweet", "tweet_id")

		rel = ReplyTo(tweet, obj)
		graph.merge(rel)

	else:
		print("got a tweet")
		tweet = Node("Tweet", name=data['full_text'], tweet_id=data['id_str'], created_at=data['created_at'], favorites=data['favorite_count'], retweets=data['retweet_count'])
		graph.merge(tweet, "Tweet", "tweet_id")
		t1 = datetime.strptime(data['created_at'], "%a %b %d %H:%M:%S +0000 %Y")
		t2 = datetime(t1.year, t1.month, t1.day, t1.hour, t1.minute, t1.second, tzinfo=UTC())

		i = 0
		for day_time in dates:
			if (t2 >= day_time[0]) and (t2 < day_time[1]) :
				rel = RelatesTo(tweet, objs[i])
				graph.merge(rel)
				i+=1

		obj = Node("Source", name=data['source'])
		graph.merge(obj, "Source", "name")

		rel = Using(tweet, obj)
		graph.merge(rel)

		obj = Node("User", name="@" + data['user']['screen_name'], real_name=data['user']['name'], id=data['user']['id_str'], description=data['user']['description'])
		graph.merge(obj, "User", "name")

		rel = AuthoredBy(tweet, obj)
		graph.merge(rel)

		obj2 = Node("Location", name=data['user']['location'])
		graph.merge(obj, "Location", "name")

		rel = LocatedAt(obj, obj2)
		graph.merge(rel)

		for hashtag in data['entities']['hashtags']:
			if hashtag['text'].upper() != filter_conference_hashtag.upper():
				obj = Node("Hashtag", name="#" + hashtag['text'].upper())
				graph.merge(obj, "Hashtag", "name")

				rel = RefersTo(tweet, obj)
				graph.merge(rel)

		for user_mention in data['entities']['user_mentions']:
			if user_mention['screen_name'] != "Identiverse" and user_mention['screen_name'] != filter_organizer_twitter_screename:
				obj = Node("User", name="@" + user_mention['screen_name'], id=user_mention['id_str'])
				graph.merge(obj, "User", "name")

				rel = Mentions(tweet, obj)
				graph.merge(rel)
