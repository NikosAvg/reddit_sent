from flask import Flask, render_template, jsonify, request
from analysis import preprocess_text_data, merge_sentiment_and_price, get_plots
import sqlite3
import pandas as pd
import json
from datetime import datetime, timedelta

app = Flask(__name__)
def fetch_data_from_sqlite(db_path, table_name, symbol, days_range):
    conn = sqlite3.connect(db_path)

    # Calculate the start date based on days_range
    start_date = datetime.now() - timedelta(days=days_range)
    start_date_str = start_date.strftime('%Y-%m-%d %H:%M:%S')  # Format as needed

    # Use a WHERE clause to filter data based on symbol and date range
    query = f'SELECT * FROM {table_name} WHERE symbol=\'{symbol}\' AND timestamp >= \'{start_date_str}\';'
    df = pd.read_sql_query(query, conn)
    conn.close()

    return df

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
    days_range = int(request.args.get('days', 7))
    # Fetch data based on the user inputs
    reddit_data = fetch_data_from_sqlite('reddit_data.db', 'reddit_data', crypto_pair[:3], days_range)
    price_data = fetch_data_from_sqlite('kraken_data.db', 'kraken_data', crypto_pair,  days_range)
    price_data = price_data.rename(columns={"timestamp": "Date"})
    price_data['Date'] = pd.to_datetime(price_data['Date'])

    # Perform preprocessing and analysis
    daily_sentiment = preprocess_text_data(reddit_data)

    # Filter posts from the past day
    reddit_data['timestamp'] = pd.to_datetime(reddit_data['timestamp'])  # Convert to datetime
    start_date = datetime.now() - timedelta(days=days_range)
    filtered_posts = reddit_data[reddit_data['timestamp'] > start_date]
    filtered_posts['Hastext'] = filtered_posts['text'].apply(lambda x: 0 if x.strip() == '' else 1)
    # Get data in JSON format
    sentiment_price_data = merge_sentiment_and_price(daily_sentiment, price_data).to_dict(orient='records')
    posts_per_day_data = filtered_posts.groupby(filtered_posts['timestamp'].dt.date)['Hastext'].sum().reset_index().to_dict(orient='records')
    sentiment_distribution_data = daily_sentiment['SentimentCategory'].value_counts().reset_index().to_dict(orient='records')
    top_posts_data = filtered_posts.sort_values(by='upvotes', ascending=False).head(10).to_dict(orient='records')

    return render_template('dashboard.html', sentiment_price_data=sentiment_price_data,
                           posts_per_day_data=posts_per_day_data,
                           sentiment_distribution_data=sentiment_distribution_data,
                           top_posts_data=top_posts_data,pair=crypto_pair, days=days_range)



# Add an API endpoint to fetch data for plots asynchronously
@app.route('/get_data', methods=['GET'])
def get_data():
    # Retrieve parameters from the URL
    pair = request.args.get('pair', 'BTC/EUR')
    days = int(request.args.get('days', 7))
    # Fetch data from SQLite
    reddit_data = fetch_data_from_sqlite('reddit_data.db', 'reddit_data', pair[:3], days)
    price_data = fetch_data_from_sqlite('kraken_data.db', 'kraken_data', pair, days)
    price_data = price_data.rename(columns={"timestamp": "Date"})
    price_data['Date'] = pd.to_datetime(price_data['Date'])

    # Perform preprocessing and analysis
    daily_sentiment = preprocess_text_data(reddit_data)

    # Filter posts from the past day
    reddit_data['timestamp'] = pd.to_datetime(reddit_data['timestamp'])  # Convert to datetime
    start_date = datetime.now() - timedelta(days=days)
    filtered_posts = reddit_data[reddit_data['timestamp'] > start_date]
    filtered_posts['Hastext'] = filtered_posts['text'].apply(lambda x: 0 if x.strip() == '' else 1)

    # Get data in JSON format
    sentiment_price_data = merge_sentiment_and_price(daily_sentiment, price_data).to_dict(orient='records')
    posts_per_day_data = filtered_posts.groupby(filtered_posts['timestamp'].dt.date)['Hastext'].sum().reset_index().to_dict(orient='records')
    sentiment_distribution_data = daily_sentiment['SentimentCategory'].value_counts().reset_index().to_dict(orient='records')
    top_posts_data = filtered_posts.sort_values(by='upvotes', ascending=False).head(10).to_dict(orient='records')

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
    app.run(debug=False)
