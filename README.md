# Twitter

tweets.py gets daily tweets and runs sentiment analysis based on two different methods: textblob and vader. The daily tweets are stored in a csv and the accumulated tweets are stored in a sqlite database. Also, a daily summary of the of the average sentiment is written out and kept for each day.

### Running tweets.py

To run the project, use the following. This defaults to running on the current day and getting today's
2,000 tweets and SPY ticker price.

python tweets.py

OPTIONAL SWITCHES:

To run and specify the number of tweets, use -t switch

python main.py -t=<number_of_tweets>

To run and a number of days in the past (max = 7), the number of days to subtract (0-7), use -s switch

python main.py -s=<days_to_subtract>