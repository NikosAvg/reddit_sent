import ccxt
import pandas as pd
from datetime import datetime, timedelta
import sqlite3

def get_latest_timestamp_from_sqlite(db_path, table_name='kraken_data'):
    conn = sqlite3.connect(db_path)
    query = f'SELECT MAX(timestamp) as latest_timestamp FROM {table_name};'
    result = conn.execute(query).fetchone()
    conn.close()
    return result[0] if result[0] else None

def update_kraken_data_in_sqlite(db_path, table_name='kraken_data',symbol):
    latest_timestamp = get_latest_timestamp_from_sqlite(db_path, table_name)
    since = latest_timestamp or (datetime.utcnow() - timedelta(days=1)).isoformat()

    kraken = ccxt.kraken()
    ohlcv = kraken.fetch_ohlcv(symbol, '1d', since=kraken.parse8601(since))
    kraken_data = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    kraken_data['timestamp'] = pd.to_datetime(kraken_data['timestamp'], unit='ms')
    kraken_data['symbol'] = symbol
    conn = sqlite3.connect(db_path)
    kraken_data.to_sql(table_name, conn, if_exists='append', index=False)
    conn.close()

    print(f'Kraken data has been updated in {db_path}, table: {table_name}')

symbols = ['BTC/EUR','ETH/EUR','XMR/EUR','ADA/EUR','DOT/EUR']
timeframe = '1d'
for symbol in symbols:
    db_path = 'kraken_data.db'
    table_name = 'kraken_data'
    update_kraken_data_in_sqlite(db_path, table_name,symbol)
