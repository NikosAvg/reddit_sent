# Import the necessary libraries
import praw
import sqlite3
from datetime import datetime, timedelta

def get_reddit_data(subreddit_names, search_query, time_filter='year'):
    # Reddit API credentials
    reddit = praw.Reddit(
        client_id='5vJYLIH8zauys8zbKRkFmw',
        client_secret='iMJ81HDvQGTZRa6lyzFlpvYbJXM-lQ',
        user_agent='ComputersAndPunches'
    )

    res = []
    if search_query == 'Bitcoin':
        symbol = "BTC"
    elif search_query == 'Monero':
        symbol = 'XMR'
    elif search_query == 'Ethereum':
        symbol = 'ETH'
    else:
        symbol = search_query

    for subreddit_name in subreddit_names:
        subreddit = reddit.subreddit(subreddit_name)
        results = subreddit.search(search_query, sort='new', time_filter=time_filter)

        for submission in results:
            posted_time = datetime.utcfromtimestamp(submission.created_utc).strftime('%Y-%m-%d %H:%M:%S')
            res.append([str(submission.title), str(submission.selftext), str(submission.score), posted_time,symbol])

    return res


def save_reddit_data_to_sqlite(data, db_path):
    # SQLite database setup
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create a table in SQLite database
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reddit_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            text TEXT,
            upvotes INTEGER,
            timestamp DATETIME,
            symbol TEXT
        )
    ''')
    conn.commit()

    # Insert data into the SQLite database
    cursor.executemany('''
        INSERT INTO reddit_data (title, text, upvotes, timestamp, symbol)
        VALUES (?, ?, ?, ?,?)
    ''', data)
    conn.commit()

    print(f'Data has been saved to {db_path}')

# Specify the subreddits and search query
subreddit_names = ['Bitcoin', 'CryptoCurrency', 'CryptoMarkets']
search_querys = ['BTC','Bitcoin','ETH','Ethereum','DOT','ADA','XMR','Monero']
time_filter = 'day'
db_path = 'reddit_data.db'

for search_query in search_querys:
    reddit_data = get_reddit_data(subreddit_names, search_query, time_filter)
    save_reddit_data_to_sqlite(reddit_data, db_path)
