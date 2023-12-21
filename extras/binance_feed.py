# Libraries
import pandas as pd
import logging
from binance.client import Client
import sqlite3
from datetime import datetime
from pathlib import Path

def connect_to_binance():

    # Get the absolute path to the directory of the current file.
    dir_path = Path(__file__).parent.resolve()
    db_path = dir_path / '..' / 'dbs' / 'trading_data.db'

    # Binance Client
    client = Client()

    # Logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # Get the absolute path to the parent directory of the current file.
    parent_dir = Path(__file__).parent.parent.resolve()

    # Create a logs directory if it doesn't exist
    log_dir = parent_dir / 'logs'
    log_dir.mkdir(exist_ok=True)

    # Set up logging to a file in the logs directory, overwriting the file each time.
    log_file = log_dir / 'binance_feed.log'
    handler = logging.FileHandler(log_file, mode='w')  # 'w' means overwrite the file each time.

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Functions
    def convert_to_float(data):
        # Convert formats to floats 
        columns = ["open", "high", "low", "close", "volume", "num_trades"]
        for col in columns:
            data[col] = data[col].astype(float)
        return data

    def get_trading_pairs():
        # Screen available pairs - Using USDT pairs.
        try:
            info = client.get_exchange_info()
            return [symbol["symbol"] for symbol in info["symbols"] 
            if symbol["status"] == "TRADING" 
            and "USDT" in symbol["symbol"] 
            and "UPUSDT" not in symbol["symbol"] 
            and "DOWNUSDT" not in symbol["symbol"]]
        except Exception as e:
            logger.error(f"Error retrieving trading pairs: {e}")
            return []

    def get_historical_data(symbol, start_date, end_date=None, interval="1d", limit=1000):
        klines = client.get_historical_klines(symbol, interval, start_str=start_date, end_str=end_date, limit=limit)
        data = pd.DataFrame(klines, columns=["open_time", "open", "high", "low", "close", "volume", "close_time", "quote_volume", "num_trades", "taker_buy_base_volume", "taker_buy_quote_volume", "ignore"])
        data = data.drop(["quote_volume","taker_buy_base_volume", "taker_buy_quote_volume", "ignore"], axis=1)
        data = convert_to_float(data)
        data["open_time"] = pd.to_datetime(data["open_time"], unit='ms')
        data["close_time"] = pd.to_datetime(data["close_time"], unit='ms')
        return data

    def create_table(c, pair):
        # Create a table for each pair - Adding prefix to avoid issue with token/coin starting with integers
        table_name = "pair_" + pair
        c.execute(f'''CREATE TABLE IF NOT EXISTS {table_name} (
            open_time TIMESTAMP,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume REAL,
            close_time TIMESTAMP,
            num_trades INTEGER
        )''')

    trading_pairs = get_trading_pairs()

    # Update the main part of the script
    if trading_pairs:
        with sqlite3.connect(str(db_path)) as conn:
            c = conn.cursor()
            for pair in trading_pairs:
                create_table(c, pair)
                try:
                    table_name = "pair_" + pair
                    c.execute(f"SELECT MAX(open_time) FROM {table_name}")
                    latest_timestamp = c.fetchone()[0]
                    if latest_timestamp:
                        latest_timestamp = pd.to_datetime(latest_timestamp)
                        start_date = latest_timestamp.strftime("%m-%d-%Y")
                    else:
                        start_date = '01-01-2017'
                    
                    data = get_historical_data(pair, start_date)
                    
                    # Check if the last row has an unclosed candlestick and drop it if necessary
                    current_time_utc = datetime.utcnow()
                    if not data.empty and data.iloc[-1]["close_time"] > current_time_utc:
                        data = data.iloc[:-1]

                    
                    if not data.empty:
                        # Exclude rows with the same timestamp as the latest timestamp in the database
                        data = data[data['open_time'] != latest_timestamp]

                        data.to_sql(table_name, conn, if_exists='append', index=False)
                        rows_added = len(data)
                        logger.info(f"Adding trading pair: {pair} - Rows added: {rows_added}")
                    else:
                        logger.info(f"Adding trading pair: {pair} - No new rows added")
                except Exception as e:
                    logger.error(f"Error retrieving data for {pair}: {e}")