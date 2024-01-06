import praw
import pandas as pd
from datetime import datetime, timedelta
import sqlite3
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
user_agent = os.getenv("USER_AGENT")

def get_latest_timestamp_from_sqlite(db_path, table_name='reddit_data'):
    conn = sqlite3.connect(db_path)
    query = f'SELECT MAX(timestamp) as latest_timestamp FROM {table_name};'
    result = conn.execute(query).fetchone()
    conn.close()
    return result[0] if result[0] else None

def update_reddit_data_in_sqlite(db_path, table_name='reddit_data'):
    latest_timestamp = get_latest_timestamp_from_sqlite(db_path, table_name)

    reddit = praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent)
    subreddit_names = ['Bitcoin', 'CryptoCurrency', 'CryptoMarkets']
    search_querys = ['Bitcoin','Etherium','Dot','ADA','XMR']

    for subreddit_name in subreddit_names:
        subreddit = reddit.subreddit(subreddit_name)
        for search_query in search_querys:
            results = subreddit.search(search_query, sort='new', time_filter='day', limit=None)
            if search_query == 'Bitcoin':
                symbol = "BTC"
            elif search_query == 'Monero':
                symbol = 'XMR'
            elif search_query == 'Ethereum':
                symbol = 'ETH'
            else:
                symbol = search_query

            data = []
            for submission in results:
                latest_timestamp_datetime = datetime.utcfromtimestamp(latest_timestamp) if latest_timestamp else None
                print(submission.created_utc,latest_timestamp)
                if latest_timestamp_datetime and submission.created_utc <= latest_timestamp_datetime:
                    continue

                data.append({
                    'title': submission.title,
                    'text': submission.selftext,
                    'upvotes': submission.score,
                    'timestamp': datetime.utcfromtimestamp(submission.created_utc),
                    'symbol': symbol
                })

    reddit_data = pd.DataFrame(data)
    reddit_data['timestamp'] = pd.to_datetime(reddit_data['timestamp'])

    with open('utils/stopwords.txt', 'r') as file:
        # Read the content of the file and split it into lines
        lines = file.readlines()

    # Remove newline characters from each line and create a list
    stopwords = [line.strip() for line in lines]
    stopwords_set = set(stopwords)
    reddit_data['text'] = reddit_data['text'].apply(lambda words: ' '.join(word.lower() for word in word_tokenize(words) if word.lower() not in stopwords))

    conn = sqlite3.connect(db_path)
    reddit_data.to_sql(table_name, conn, if_exists='append', index=False)
    conn.close()

    print(f'Reddit data has been updated in {db_path}, table: {table_name}')

# Example usage:
db_path_reddit = 'reddit_data.db'
table_name_reddit = 'reddit_data'
