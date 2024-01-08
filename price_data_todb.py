import ccxt
import pandas as pd
from datetime import datetime, timedelta
import sqlite3

def get_kraken_data(symbol='BTC/EUR', timeframe='1d', since=None):
    kraken = ccxt.kraken()

    # Set the since parameter to fetch data from the past week
    if since is None:
        since = kraken.parse8601((datetime.utcnow() - timedelta(days=360)).isoformat())

    # Fetch OHLCV (Open/High/Low/Close/Volume) data
    ohlcv = kraken.fetch_ohlcv(symbol, timeframe, since)

    # Convert the data to a Pandas DataFrame for easier manipulation
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['symbol'] = symbol
    print(df.head())
    # Convert the timestamp to a readable date
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

    return df

def save_kraken_data_to_sqlite(data, db_path, table_name='kraken_data'):
    # Save the data to an SQLite database
    conn = sqlite3.connect(db_path)
    data.to_sql(table_name, conn, if_exists='append', index=False)
    conn.close()

    print(f'Data has been saved to {db_path}, table: {table_name}')

symbols = ['BTC/EUR','ETH/EUR','XMR/EUR','ADA/EUR','DOT/EUR']
timeframe = '1d'
for symbol in symbols:
    kraken_data = get_kraken_data(symbol, timeframe)
    db_path = 'kraken_data.db'
    table_name = 'kraken_data'

    kraken_data = get_kraken_data(symbol, timeframe)
    save_kraken_data_to_sqlite(kraken_data, db_path, table_name)
