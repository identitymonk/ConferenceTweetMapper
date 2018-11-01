# ConferenceTweetMapper
## General usage
This repository contains three Python scripts:
- archive.py

   This script allows to search Twitter for a particular conference hashtag and to return all the resulting tweets in a JSON file
   
- graphify.py

   This script takes a JSON file containing Tweets and to transform them to graph oriented object representing another view of the timeline of Tweets, Retweets, Quote, Hashtag, and Handles. In case of Retweet/Quote/Reply, this script will also drills for original tweet even if outside the scope of the file.
   
- stream.py

   This script allows to search Twitter for a particular conference hashtag and to transform them to graph oriented object representing another view of the timeline of Tweets, Retweets, Quote, Hashtag, and Handles. In case of Retweet/Quote/Reply, this script will also drills for original tweet even if outside the scope of the search filter.
   
## Pre-requisites

In order to use those scripts you must have:
- Python 2.7 installed (only version tested so far)
- Pip installed
- Python packages installed:

   * tweepy
   * json
   * time
   * configparser
   * argparse
   * py2neo
   * asyncio
       * and Microsoft Visual C++ Build Tools if you compile it on Windows, after adding cl.exe in your Path
   
- Neo4j Db installed, configured, and ready for connection

   I won't detail here how to do this part, there are plenty of good tutorials on the Web

## archive.py
This script can be used as follow:

```
usage: archive.py [-h] {file,line} ...

Export tweets that match the search query

positional arguments:
  {file,line}  Add configuration from Ini file or through arguments
    file       Adding configuration from a file (Default: Ini/Default.ini)
    line       Adding configuration from a arguments in the command line

optional arguments:
  -h, --help   show this help message and exit
```

The file subcommand supports the following syntax:

```
usage: stream.py file [-h] [-i INI_FILE]

positional arguments:
  cmd

optional arguments:
  -h, --help            show this help message and exit
  -i INI_FILE, --ini_file INI_FILE
                        Path to the Ini file (Default: Ini/Default.ini)
```

The line subcommand supports the following syntax:

```
usage: stream.py line [-h] -s SEARCH -ck CONSUMER_KEY -cs CONSUMER_SECRET -ak
                      ACCESS_KEY -as ACCESS_SECRET -o OUTPUT_FILENAME
                      [-b BACKUP_INI_FILE_NAME]

positional arguments:
  cmd

optional arguments:
  -h, --help            show this help message and exit
  -s SEARCH, --search SEARCH
                        Twitter search filter
  -ck CONSUMER_KEY, --consumer_key CONSUMER_KEY
                        Twitter consumer key obtained from your Twitter account
  -cs CONSUMER_SECRET, --consumer_secret CONSUMER_SECRET
                        Twitter consumer secret obtained from your Twitter account
  -ak ACCESS_KEY, --access_key ACCESS_KEY
                        Twitter access key obtained from your Twitter account
  -as ACCESS_SECRET, --access_secret ACCESS_SECRET
                        Twitter access_secret obtained from your Twitter account
  -o OUTPUT_FILENAME, --output_filename OUTPUT_FILENAME
                        Name of the results output file
  -b BACKUP_INI_FILE_NAME, --backup_ini_file_name BACKUP_INI_FILE_NAME
                        Name of the Ini file to backup from this request parameters
```
 
## graphify.py
This script can be used as follow:

```
usage: graphify.py [-h] {file,line} ...

Import tweets in a Graph DB

positional arguments:
  {file,line}  Add configuration from Ini file or through arguments
    file       Adding configuration from a file (Default: Ini/Default.ini)
    line       Adding configuration from a arguments in the command line

optional arguments:
  -h, --help   show this help message and exit
```

The file subcommand supports the following syntax:

```
usage: graphify.py file [-h] [-i INI_FILE]

positional arguments:
  cmd

optional arguments:
  -h, --help            show this help message and exit
  -i INI_FILE, --ini_file INI_FILE
                        Path to the Ini file (Default: Ini/Default.ini)
```

The line subcommand supports the following syntax:

```
usage: graphify.py line [-h] [-type DB_TYPE] [-proto PROTOCOL]
                        [-lang LANGUAGE] [-server SERVER_NAME]
                        [-port SERVER_PORT] -pwd DB_PASSWORD [-set RESULT_SET]
                        -name CONFERENCE_NAME -loc CONFERENCE_LOCATION -time
                        CONFERENCE_TIME_ZONE -start CONFERENCE_START_DATE -end
                        CONFERENCE_END_DATE [-purge PURGE_BEFORE_IMPORT]
                        [-fname FILTER_ORGANIZER_TWITTER_SCREENAME]
                        [-fhash FILTER_CONFERENCE_HASHTAG]
                        [-b BACKUP_INI_FILE_NAME]

positional arguments:
  cmd

optional arguments:
  -h, --help            show this help message and exit
  -type DB_TYPE, --db_type DB_TYPE
                        For future use: indicate db type
  -proto PROTOCOL, --protocol PROTOCOL
                        For future use: indicate protocol to connect to db
  -lang LANGUAGE, --language LANGUAGE
                        For future use: indicate language to query the db
  -server SERVER_NAME, --server_name SERVER_NAME
                        FQDN of the db server
  -port SERVER_PORT, --server_port SERVER_PORT
                        server socket hosting the db service
  -pwd DB_PASSWORD, --db_password DB_PASSWORD
                        service password to access the db
  -set RESULT_SET, --result_set RESULT_SET
                        Result set file from streaming script (Default: Output/search.json)
  -name CONFERENCE_NAME, --conference_name CONFERENCE_NAME
                        Name of the conference for the master node
  -loc CONFERENCE_LOCATION, --conference_location CONFERENCE_LOCATION
                        Location of the conference for the master node
  -time CONFERENCE_TIME_ZONE, --conference_time_zone CONFERENCE_TIME_ZONE
                        Number of (+/-) hours from UTC reference of the conference's timezone
  -start CONFERENCE_START_DATE, --conference_start_date CONFERENCE_START_DATE
                        First day of the conference in dd/mm/yyyy format
  -end CONFERENCE_END_DATE, --conference_end_date CONFERENCE_END_DATE
                        Last day of the conference in dd/mm/yyyy format
  -purge PURGE_BEFORE_IMPORT, --purge_before_import PURGE_BEFORE_IMPORT
                        Indicate if the graph must be deleted before importing (Default: false)
  -fname FILTER_ORGANIZER_TWITTER_SCREENAME, --filter_organizer_twitter_screename FILTER_ORGANIZER_TWITTER_SCREENAME
                        Twitter screename that helps to filter out organizer tweets and retweets
  -fhash FILTER_CONFERENCE_HASHTAG, --filter_conference_hashtag FILTER_CONFERENCE_HASHTAG
                        Hashtag of the conference
  -b BACKUP_INI_FILE_NAME, --backup_ini_file_name BACKUP_INI_FILE_NAME
                        Name of the Ini file to backup from this request parameters
```

## stream.py
This script can be used as follow:

```
usage: stream.py [-h] {file,line} ...

Export tweets that match the search query

positional arguments:
  {file,line}  Add configuration from Ini file or through arguments
    file       Adding configuration from a file (Default: Ini/Default.ini)
    line       Adding configuration from a arguments in the command line

optional arguments:
  -h, --help   show this help message and exit
```

The file subcommand supports the following syntax:

```
usage: stream.py file [-h] [-i INI_FILE]

positional arguments:
  cmd

optional arguments:
  -h, --help            show this help message and exit
  -i INI_FILE, --ini_file INI_FILE
                        Path to the Ini file (Default: Ini/Default.ini)
```

The line subcommand supports the following syntax:

```
usage: stream.py file [-h] [-i INI_FILE]

positional arguments:
  cmd

optional arguments:
  -h, --help            show this help message and exit
  -i INI_FILE, --ini_file INI_FILE
                        Path to the Ini file (Default: Ini/Default.ini)

(base) C:\Users\User\Documents\Git\Work\ConferenceTweetMapper>python stream.py line -h
usage: stream.py line [-h] -s SEARCH -ck CONSUMER_KEY -cs CONSUMER_SECRET -ak
                      ACCESS_KEY -as ACCESS_SECRET -o OUTPUT_FILENAME
                      [-type DB_TYPE] [-proto PROTOCOL] [-lang LANGUAGE]
                      [-server SERVER_NAME] [-port SERVER_PORT] -pwd
                      DB_PASSWORD [-set RESULT_SET] -name CONFERENCE_NAME -loc
                      CONFERENCE_LOCATION -time CONFERENCE_TIME_ZONE -start
                      CONFERENCE_START_DATE -end CONFERENCE_END_DATE
                      [-purge PURGE_BEFORE_IMPORT]
                      [-fname FILTER_ORGANIZER_TWITTER_SCREENAME]
                      [-fhash FILTER_CONFERENCE_HASHTAG]
                      [-b BACKUP_INI_FILE_NAME]

positional arguments:
  cmd

optional arguments:
  -h, --help            show this help message and exit
  -s SEARCH, --search SEARCH
                        Twitter search filter
  -ck CONSUMER_KEY, --consumer_key CONSUMER_KEY
                        Twitter consumer key obtained from your Twitter account
  -cs CONSUMER_SECRET, --consumer_secret CONSUMER_SECRET
                        Twitter consumer secret obtained from your Twitter account
  -ak ACCESS_KEY, --access_key ACCESS_KEY
                        Twitter access key obtained from your Twitter account
  -as ACCESS_SECRET, --access_secret ACCESS_SECRET
                        Twitter access_secret obtained from your Twitter account
  -o OUTPUT_FILENAME, --output_filename OUTPUT_FILENAME
                        Name of the results output file
  -type DB_TYPE, --db_type DB_TYPE
                        For future use: indicate db type
  -proto PROTOCOL, --protocol PROTOCOL
                        For future use: indicate protocol to connect to db
  -lang LANGUAGE, --language LANGUAGE
                        For future use: indicate language to query the db
  -server SERVER_NAME, --server_name SERVER_NAME
                        FQDN of the db server
  -port SERVER_PORT, --server_port SERVER_PORT
                        server socket hosting the db service
  -pwd DB_PASSWORD, --db_password DB_PASSWORD
                        service password to access the db
  -set RESULT_SET, --result_set RESULT_SET
                        Result set file from streaming script (Default: Output/search.json)
  -name CONFERENCE_NAME, --conference_name CONFERENCE_NAME
                        Name of the conference for the master node
  -loc CONFERENCE_LOCATION, --conference_location CONFERENCE_LOCATION
                        Location of the conference for the master node
  -time CONFERENCE_TIME_ZONE, --conference_time_zone CONFERENCE_TIME_ZONE
                        Number of (+/-) hours from UTC reference of the conference's timezone
  -start CONFERENCE_START_DATE, --conference_start_date CONFERENCE_START_DATE
                        First day of the conference in dd/mm/yyyy format
  -end CONFERENCE_END_DATE, --conference_end_date CONFERENCE_END_DATE
                        Last day of the conference in dd/mm/yyyy format
  -purge PURGE_BEFORE_IMPORT, --purge_before_import PURGE_BEFORE_IMPORT
                        Indicate if the graph must be deleted before importing (Default: false)
  -fname FILTER_ORGANIZER_TWITTER_SCREENAME, --filter_organizer_twitter_screename FILTER_ORGANIZER_TWITTER_SCREENAME
                        Twitter screename that helps to filter out organizer tweets and retweets
  -fhash FILTER_CONFERENCE_HASHTAG, --filter_conference_hashtag FILTER_CONFERENCE_HASHTAG
                        Hashtag of the conference
  -b BACKUP_INI_FILE_NAME, --backup_ini_file_name BACKUP_INI_FILE_NAME
                        Name of the Ini file to backup from this request parameters
```

## Ini file example
In the Ini folder you should find a Default.ini file describing the format expected for a global Ini file:

```
#Default initialization filter
#All dates shall be in format dd/mm/yyyy

[DEFAULT]
output_filename = Output/search.json
search = #Identiverse

[Twitter]
consumer_key = <your_consumer_key>
consumer_secret = <your_consumer_secret>
access_key = <your_access_key>
access_secret = <your_access_secret>

[Graph]
db_type = Neo4j
protocol = bolt
language = cypher
server_name = localhost
server_port = 7687
db_password = Identiverse

[Processing]
result_set = Output/search.json
conference_name = Identiverse 2018
conference_location = Boston
conference_time_zone = -4
conference_start_date = 24/06/2018
conference_end_date = 27/06/2018

[Misc]
purge_before_import = false
filter_organizer_twitter_screename = Identiverse
filter_conference_hashtag = Identiverse
```

## General limitations and advices
Using those scripts, you understand that:
- Having two scripts allows to separate the two operations independently
- Scripts do not check for file existence at the time of exporting (results and configuration), so be careful if you don't want one to be overwritten
- Twitter search public API will not return unindexed results, some results older than 7 days, or maybe all the results you may get by using the UI version of it
- stream.py search filter aims has been designed to target conference hashtag... but it is a standard Twitter search filter supporting all the options Twitter allows
- graphify.py does only support Neo4j, bolt protocol, and cipher language as for now

## Example of the result
If successful you should be able to use Neo4j tools to visualize and drill your Tweet Graph:
![Tweet Graph](https://github.com/identitymonk/ConferenceTweetMapper/blob/master/Screencap/TweetGraph.PNG "Tweet Graph view")

Example of the drilling of a Retweet/Quote/Reply:
![Tweet Graph](https://github.com/identitymonk/ConferenceTweetMapper/blob/master/Screencap/Drilling.PNG "Drilling")

Here are some interesting [Cipher request examples](https://github.com/identitymonk/ConferenceTweetMapper/blob/master/Cipher examples/Commands.md)

## Roadmap
- Follow RT, Reply, Quote up and down a la treeverse <- Partially solved, will need script Expand
- Script Redox: Merge similar RT into only one RT-Tweet
- Script Expand: Import all the retweets by retweets_of_status_id and replies by in_reply_to_status_id Prenium Search parameters
- Script Append: Continue an import or update an import with a list of tweets. Look before if tweet is alredy imported or not.
- Switch script function to Async https://www.aeracode.org/2018/02/19/python-async-simplified/
- Think about KPIs: Tweet rate, Top for User/Tweet/Hashtag/Mention
- WebUI to see Graph online
- Update logging to console to be more dynamic
- ~~Better date management~~
- ~~Change the Post and Pre conference period id to something speciifc to the conference upload to prevent cross mapping~~
- ~~Change the Days of conference period id to something speciifc to the conference upload to prevent cross mapping~~
- ~~Correct name attribue of object Source to remove href~~
