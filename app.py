from flask import Flask, render_template, jsonify, request
from analysis import preprocess_text_data, merge_sentiment_and_price, get_plots
import pandas as pd
import json
import praw
import ccxt
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

app = Flask(__name__)

load_dotenv()  # Load environment variables from .env file

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
user_agent = os.getenv("USER_AGENT")

def get_kraken_data(symbol='BTC/EUR', timeframe='1d', since=None):
    kraken = ccxt.kraken()

    if since is None:
        since = kraken.parse8601((datetime.utcnow() - timedelta(days=360)).isoformat())

    # Fetch OHLCV (Open/High/Low/Close/Volume) data
    ohlcv = kraken.fetch_ohlcv(symbol, timeframe, since)

    # Convert the data to a Pandas DataFrame for easier manipulation
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['symbol'] = symbol
    # Convert the timestamp to a readable date
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

    return df

def get_top_posts(search_query, time_filter):
    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent
    )

    res = []
    if search_query == 'Bitcoin OR BTC':
        symbol = "BTC"
    elif search_query == 'Monero OR XMR ':
        symbol = 'XMR'
    elif search_query == 'Ethereum OR ETH':
        symbol = 'ETH'
    else:
        symbol = search_query

    subreddit_names = ['Bitcoin', 'CryptoCurrency', 'CryptoMarkets']
    for subreddit_name in subreddit_names:
        results = reddit.subreddit(subreddit_name).search(search_query, sort='top', time_filter=time_filter,limit=None)

        for submission in results:
            posted_time = datetime.utcfromtimestamp(submission.created_utc).strftime('%Y-%m-%d %H:%M:%S')
            res.append([str(submission.title), str(submission.selftext), str(submission.score), posted_time,symbol])

    return pd.DataFrame(columns=['title','text','upvotes','timestamp','symbol'],data=res)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        crypto_pair = request.form['crypto_pair']
        days_range = int(request.form['days_range'])
        return render_template('dashboard.html', crypto_pair=pair, days_range=days)
    return render_template('index.html')

@app.route('/dashboard',methods=['GET'])
def dashboard():
    crypto_pair = request.args.get('pair', 'BTC/EUR')
    days = request.args.get('days', 'week')
    # Fetch data based on the user inputs
    if crypto_pair[:3] == 'BTC':
        search_query = 'Bitcoin OR BTC'
    elif crypto_pair[:3] == 'ETH':
        search_query = 'Ethereum OR ETH'
    elif crypto_pair[:3] == 'XMR':
        search_query = 'Monero OR XMR'
    elif crypto_pair[:3] == 'ADA':
        search_query = 'ADA OR Cardano'
    else:
        search_query = crypto_pair[:3]

    reddit_data = get_top_posts(search_query, time_filter=days)
    price_data =  get_kraken_data(crypto_pair,timeframe='1d', since=7)
    price_data = price_data.rename(columns={"timestamp": "Date"})
    price_data['Date'] = pd.to_datetime(price_data['Date'])
    # Perform preprocessing and analysis
    daily_sentiment = preprocess_text_data(reddit_data)

    # Filter posts from the past day
    reddit_data['timestamp'] = pd.to_datetime(reddit_data['timestamp'])  # Convert to datetime
    reddit_data['Hastext'] = reddit_data['text'].apply(lambda x: 0 if x.strip() == '' else 1)
    # Get data in JSON format
    sentiment_price_data = merge_sentiment_and_price(daily_sentiment, price_data).to_dict(orient='records')
    posts_per_day_data = reddit_data.groupby(reddit_data['timestamp'].dt.date)['Hastext'].sum().reset_index().to_dict(orient='records')
    sentiment_distribution_data = daily_sentiment['SentimentCategory'].value_counts().reset_index().to_dict(orient='records')
    top_posts_data = reddit_data.sort_values(by='upvotes', ascending=False).head(10).to_dict(orient='records')

    return render_template('dashboard.html', sentiment_price_data=sentiment_price_data,
                           posts_per_day_data=posts_per_day_data,
                           sentiment_distribution_data=sentiment_distribution_data,
                           top_posts_data=top_posts_data,pair=crypto_pair, days=days)


# Add an API endpoint to fetch data for plots asynchronously
@app.route('/get_data', methods=['GET'])
def get_data():
    # Retrieve parameters from the URL
    crypto_pair = request.args.get('pair', 'BTC/EUR')
    days = request.args.get('days', 'week')
    # Fetch data
    if crypto_pair[:3] == 'BTC':
        search_query = 'Bitcoin OR BTC'
    elif crypto_pair[:3] == 'ETH':
        search_query = 'Ethereum OR ETH'
    elif crypto_pair[:3] == 'XMR':
        search_query = 'Monero OR XMR'
    elif crypto_pair[:3] == 'ADA':
        search_query = 'ADA OR Cardano'
    else:
        search_query = crypto_pair[:3]
    reddit_data = get_top_posts(search_query, time_filter=days)
    price_data =  get_kraken_data(crypto_pair,timeframe='1d', since=7)
    price_data = price_data.rename(columns={"timestamp": "Date"})
    price_data['Date'] = pd.to_datetime(price_data['Date'])

    # Perform preprocessing and analysis
    daily_sentiment = preprocess_text_data(reddit_data)
    # Filter posts from the past day
    reddit_data['timestamp'] = pd.to_datetime(reddit_data['timestamp'])  # Convert to datetime
    reddit_data['Hastext'] = reddit_data['text'].apply(lambda x: 0 if x.strip() == '' else 1)

    # Get data in JSON format
    sentiment_price_data = merge_sentiment_and_price(daily_sentiment, price_data).to_dict(orient='records')
    posts_per_day_data = reddit_data.groupby(reddit_data['timestamp'].dt.date)['Hastext'].sum().reset_index().to_dict(orient='records')
    sentiment_distribution_data = daily_sentiment['SentimentCategory'].value_counts().reset_index().to_dict(orient='records')
    top_posts_data = reddit_data.sort_values(by='upvotes', ascending=False).head(10).to_dict(orient='records')

    # Convert NaN values to None before converting to JSON
    sentiment_price_data = json.loads(json.dumps(sentiment_price_data, default=str))
    posts_per_day_data = json.loads(json.dumps(posts_per_day_data, default=str))
    sentiment_distribution_data = json.loads(json.dumps(sentiment_distribution_data, default=str))
    top_posts_data = json.loads(json.dumps(top_posts_data, default=str))

    return jsonify(
        sentiment_price_data=sentiment_price_data,
        posts_per_day_data=posts_per_day_data,
        sentiment_distribution_data=sentiment_distribution_data,
        top_posts_data=top_posts_data
    )

if __name__ == '__main__':
    app.run(debug=True)
