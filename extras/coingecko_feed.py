import sqlite3
import requests
from pathlib import Path
import logging
import time

def connect_to_coingecko():
    # Logger setup
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    parent_dir = Path(__file__).parent.parent.resolve()
    log_dir = parent_dir / 'logs'
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / 'coingecko_feed.log'
    handler = logging.FileHandler(log_file, mode='w')  # 'w' means overwrite the file each time.

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    COINGECKO_API_URL = "https://api.coingecko.com/api/v3/coins/markets"
    PARAMS = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 250,
        "page": 4,
        "sparkline": "false",
        "price_change_percentage": "1h,24h,7d,14d,30d,200d,1y",
        "locale": "en",
    }

    dir_path = Path(__file__).parent.resolve()
    db_path = dir_path / '..' / 'dbs' / 'coingecko.db'

    def fetch_data(url, params, page):
        params['page'] = page
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data
        except requests.exceptions.HTTPError as e:
            logger.error(f"An error occurred while fetching data: {e}")
            return None

    # Create a connection to SQLite database
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Create a new table named 'markets'
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS markets
        (
            id TEXT PRIMARY KEY,
            symbol TEXT,
            name TEXT,
            image TEXT,
            current_price REAL,
            market_cap INTEGER,
            market_cap_rank INTEGER,
            fully_diluted_valuation INTEGER,
            total_volume INTEGER,
            high_24h REAL,
            low_24h REAL,
            price_change_24h REAL,
            price_change_percentage_24h REAL,
            market_cap_change_24h REAL,
            market_cap_change_percentage_24h REAL,
            circulating_supply INTEGER,
            total_supply INTEGER,
            max_supply INTEGER,
            ath REAL,
            ath_change_percentage REAL,
            ath_date TEXT,
            atl REAL,
            atl_change_percentage REAL,
            atl_date TEXT,
            last_updated TEXT,
            price_change_percentage_14d_in_currency REAL,
            price_change_percentage_1h_in_currency REAL,
            price_change_percentage_1y_in_currency REAL,
            price_change_percentage_200d_in_currency REAL,
            price_change_percentage_24h_in_currency REAL,
            price_change_percentage_30d_in_currency REAL,
            price_change_percentage_7d_in_currency REAL

        )
    """)

    for page in range(1, 5):
        data = fetch_data(COINGECKO_API_URL, PARAMS, page)

        if data is not None:
            for item in data:
                # Insert data into 'markets' table
                values = (
                    item['id'],
                    item['symbol'],
                    item['name'],
                    item['image'],
                    item['current_price'],
                    item['market_cap'],
                    item['market_cap_rank'],
                    item['fully_diluted_valuation'],
                    item['total_volume'],
                    item['high_24h'],
                    item['low_24h'],
                    item['price_change_24h'],
                    item['price_change_percentage_24h'],
                    item['market_cap_change_24h'],
                    item['market_cap_change_percentage_24h'],
                    item['circulating_supply'],
                    item['total_supply'],
                    item['max_supply'],
                    item['ath'],
                    item['ath_change_percentage'],
                    item['ath_date'],
                    item['atl'],
                    item['atl_change_percentage'],
                    item['atl_date'],
                    item['last_updated'],
                    item['price_change_percentage_14d_in_currency'],
                    item['price_change_percentage_1h_in_currency'],
                    item['price_change_percentage_1y_in_currency'],
                    item['price_change_percentage_200d_in_currency'],
                    item['price_change_percentage_24h_in_currency'],
                    item['price_change_percentage_30d_in_currency'],
                    item['price_change_percentage_7d_in_currency']
                )

                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO markets
                        (
                            id,
                            symbol,
                            name,
                            image,
                            current_price,
                            market_cap,
                            market_cap_rank,
                            fully_diluted_valuation,
                            total_volume,
                            high_24h,
                            low_24h,
                            price_change_24h,
                            price_change_percentage_24h,
                            market_cap_change_24h,
                            market_cap_change_percentage_24h,
                            circulating_supply,
                            total_supply,
                            max_supply,
                            ath,
                            ath_change_percentage,
                            ath_date,
                            atl,
                            atl_change_percentage,
                            atl_date,
                            last_updated,
                            price_change_percentage_14d_in_currency,
                            price_change_percentage_1h_in_currency,
                            price_change_percentage_1y_in_currency,
                            price_change_percentage_200d_in_currency,
                            price_change_percentage_24h_in_currency,
                            price_change_percentage_30d_in_currency,
                            price_change_percentage_7d_in_currency
                        ) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?, ?, ?, ?, ?, ?, ?)
                    """, values)
                    logger.info(f"Data inserted successfully for {item['id']}")
                except Exception as e:
                    logger.error(f"An error occurred while inserting data: {e}")

            # Commit the transaction
            conn.commit()
        else:
            logger.warning("No data fetched to insert into the database")

        time.sleep(10)

    # Close the connection
    conn.close()