import re
import datetime
from datetime import timedelta

from config import *

import numpy as np
import pandas as pd
import tweepy
import argparse
from sqlalchemy import create_engine

from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


def clean_tweet(tweet):
    return ' '.join(re.sub('(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)', ' ', tweet).split())

def stream(data, file_name, days_to_subtract = 0, tweets_to_get = 100):
    num_tweets = 0
    sum = 0

    auth = tweepy.OAuthHandler(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
    auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth)

    places = api.geo_search(query="USA",granularity="country")
    place_id = places[0].id

    dt = datetime.datetime.now() - timedelta(days=days_to_subtract)

    search_date = dt.strftime("%Y-%m-%d")
    print("Day: ", search_date)

    df = pd.DataFrame(columns = ['tweets', 'tweets_clean', "textblob", 'vader',  'sentiment', 'sentiment_label',
                                'user_name', 'user_statuses_count', 
                                'user_followers', 'user_location', 
                                'fav_count', 'rt_count', 'tweet_date', 'lat', 'lng', 'place', 'country'])

    for tweet in tweepy.Cursor(api.search, tweet_mode="extended", q="place:%s" % place_id, count=100, until=search_date, lang='en').items():
    # for tweet in tweepy.Cursor(api.search, tweet_mode="extended", q=('kentucky derby OR Kentucky Dervy'), count=100, until=search_date, lang='en').items():
        
        print(num_tweets, end='\r')
        
        df.loc[num_tweets, 'tweets'] = tweet.full_text
        cleaned = clean_tweet(tweet.full_text)
        df.loc[num_tweets, 'tweets_clean'] = cleaned

        analysis = TextBlob(cleaned)

        vader = SentimentIntensityAnalyzer()
        score = vader.polarity_scores(tweet.full_text)
        #Averaging the 2 different kinds of sentiment analyis to get score
        avg = (analysis.sentiment.polarity + score['compound']) / 2
        df.loc[num_tweets, 'sentiment'] = avg
        sum += avg

        if avg > 0.5:
            df.loc[num_tweets, 'sentiment_label'] = 'positive'
        elif avg < -0.5:
            df.loc[num_tweets, 'sentiment_label'] = 'negative'
        else:
            df.loc[num_tweets, 'sentiment_label'] = 'neutral'

        df.loc[num_tweets, 'textblob'] = analysis.sentiment.polarity
        df.loc[num_tweets, 'vader'] = score['compound']
        df.loc[num_tweets, 'user_name'] = tweet.user.name
        df.loc[num_tweets, 'user_statuses_count'] = tweet.user.statuses_count
        df.loc[num_tweets, 'user_followers'] = tweet.user.followers_count
        df.loc[num_tweets, 'user_location'] = tweet.user.location
        df.loc[num_tweets, 'fav_count'] = tweet.favorite_count
        df.loc[num_tweets, 'rt_count'] = tweet.retweet_count
        df.loc[num_tweets, 'tweet_date'] = tweet.created_at
        if tweet.coordinates is not None:
            if len(tweet.coordinates) > 1:
                df.loc[num_tweets, 'lat'] = tweet.coordinates['coordinates'][0]
                df.loc[num_tweets, 'lng'] = tweet.coordinates['coordinates'][1]
        if tweet.place:
            df.loc[num_tweets, 'place'] = tweet.place.full_name
            df.loc[num_tweets, 'country'] = tweet.place.country
        if num_tweets >= tweets_to_get:
            break
        num_tweets += 1

    if num_tweets > 0:
        overall = sum / num_tweets
        summary_table = pd.DataFrame({"Date": [search_date], "Sentiment": [overall]})
        print(summary_table)

    print(f'Number of new tweets: {num_tweets}')

    # Write out tweets to csv
    df.to_csv('{}.csv'.format(file_name))

    # Write out tweets to sqlite
    engine = create_engine('sqlite:///tweets.sqlite', echo=False)

    # Write out tweets to Azure postgres 
    # engine = create_engine(f'postgresql://{DBUSER}:{DBPW}@ppexample.postgres.database.azure.com:5432/example?sslmode=require')

    df.to_sql('tweets', con=engine, index=False, if_exists='append')


def main(days = 0, tweets = 2000):
    if (days > 7):
        print("Error: maximum number of days to subtract is 7.")
        return

    stream(['patientpoint'], 'my_tweets', days, tweets)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Tweets')
    parser.add_argument('--subtract', '-s',
        action='store', type=int,
        help='-s=[days to subtract]')

    parser.add_argument('--tweets', '-t',
        action='store', type=int,
        help='-t=[tweets to get]')

    args = parser.parse_args()

    days = 0
    if args.subtract:
        days = args.subtract 

    tweets = 100
    if args.tweets:
        tweets = args.tweets 
        print(args.tweets)

    main(days, tweets)
