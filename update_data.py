from price_data_todb_final import update_kraken_data_in_sqlite
from text_data_to_db_final import update_reddit_data_in_sqlite

def update_databases():
    symbols = ['BTC/EUR', 'ETH/EUR', 'XMR/EUR', 'ADA/EUR', 'DOT/EUR']
    db_path_kraken = 'db/kraken_data.db'
    table_name_kraken = 'kraken_data'

    db_path_reddit = 'db/reddit_data.db'
    table_name_reddit = 'reddit_data'

    for symbol in symbols:
        update_kraken_data_in_sqlite(db_path_kraken, table_name_kraken, symbol)

    update_reddit_data_in_sqlite(db_path_reddit, table_name_reddit)

if __name__ == "__main__":
    update_databases()
