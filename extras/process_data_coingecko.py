import sqlite3
import pandas as pd
from pathlib import Path
import base64
import os
from PIL import Image
import requests
import io
from datetime import datetime

dir_path = Path(__file__).parent.resolve()
db_path = dir_path / '..' / 'dbs' / 'coingecko.db'

def fetch_data(db_path):
    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    # Fetch data from the database
    try:
        df = pd.read_sql_query("SELECT * FROM markets", conn)
        return df
    except Exception as e:
        print(f"An error occurred while fetching data: {e}")
        return None
            
def thumbnail_assets(image_url, symbol, size=(32, 32)):
    # Use the provided symbol to create a unique filename.
    filename = f"{symbol}_{size[0]}.png"
    # Define the path where you'll save the images.
    folder_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "assets_thumbs")
    local_image_path = os.path.join(folder_path, filename)

    # Ensure the directory exists
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    try:
        # Check if the image already exists locally.
        if os.path.exists(local_image_path):
            # If it does, open the image from the local file.
            img = Image.open(local_image_path)
            #print('Found ', symbol)
        else:
            # If it doesn't, download and save the image.
            response = requests.get(image_url)
            img = Image.open(io.BytesIO(response.content))
            img = img.resize(size)
            img.save(local_image_path, format="PNG")
            #print('New Saved ', symbol)
        # Create a BytesIO object
        buffer = io.BytesIO()
        # Save the resized image into the buffer
        img.save(buffer, format="PNG")
        # Get the content of the image in the buffer
        img_str = buffer.getvalue()
        # Base64 encode.
        img_base64 = base64.b64encode(img_str)

        # Return as data URL.
        return f"data:image/png;base64,{img_base64.decode()}"
    except Exception as e:
        print(f"Could not resize image {image_url}. Error: {e}")
        return None
    
def abbreviate_number(num):
    if pd.isnull(num) or num == 0:
        return 'None'
    elif num >= 10**12:  # Trillion
        return str(round(num / 10**12, 2)) + 'T'
    elif num >= 10**9:  # Billion
        return str(round(num / 10**9, 2)) + 'B'
    elif num >= 10**6:  # Million
        return str(round(num / 10**6, 2)) + 'M'
    elif num >= 10**3:  # Thousand
        return str(round(num / 10**3, 2)) + 'K'
    else:
        return str(num)

def color_positive_negative(val):
    if pd.isnull(val):
        return ''
    if isinstance(val, str):
        val = float(val.replace(",", ""))
    else:
        val = float(val)
    color = 'green' if val > 0 else ('red' if val < 0 else 'grey')
    return 'background-color: %s' % color
    
def process_data_gecko():
    df = fetch_data(db_path)
    latest_timestamp = max(df['last_updated'])
    latest_timestamp = datetime.strptime(latest_timestamp, '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%Y/%m/%d - %H:%M:%S UTC')

    selected_columns = [
        'id',
        'image', 
        'market_cap_rank', 
        'symbol', 
        'name', 
        'current_price', 
        'total_volume', 
        'market_cap',
        'fully_diluted_valuation',
        'circulating_supply',
        'total_supply',
        'max_supply',
        'price_change_percentage_1h_in_currency',
        'price_change_percentage_24h_in_currency',
        'price_change_percentage_7d_in_currency',
        'price_change_percentage_30d_in_currency', 
        'price_change_percentage_1y_in_currency'
    ]
    column_names = ['id',
                    'Image', 
                    'Rank', 
                    'Symbol', 
                    'Name', 
                    'Current Price', 
                    '24h Volume',
                    'Market Cap',
                    'Fully Diluted Valuation',
                    'Circulating Supply',
                    'Total Supply',
                    'Max Supply',
                    '1h %',
                    '24h %',
                    '7d %',
                    '30d %',
                    '1y %',
                    ]


    df = df[selected_columns]
    df.columns = column_names

    df['Symbol'] = df['Symbol'].str.upper()
    df['Percentage In Circulation'] = (df['Circulating Supply']/df['Max Supply'])*100
    df['Current Price'] = df['Current Price'].apply(lambda x: '{:,.12f}'.format(x).rstrip('0').rstrip('.'))
    info_columns = ['Market Cap','24h Volume','Fully Diluted Valuation', 'Circulating Supply', 'Total Supply', 'Max Supply']
    df[info_columns] = df[info_columns].apply(pd.to_numeric, errors='coerce')
    df[info_columns] = df[info_columns].fillna(0)
    df[info_columns] = df[info_columns].applymap(abbreviate_number)
    df['Image'] = df.apply(lambda row: thumbnail_assets(row['Image'], row['Symbol']), axis=1)
    percentage_columns = ['1h %', '24h %', '7d %', '30d %', '1y %']
    df[percentage_columns] = df[percentage_columns].applymap(lambda x: '{:,.2f}'.format(x))
    df = df.drop(['id'], axis=1)
    print(len(df))
    df = df.sort_values('Rank')
    df = df.style.applymap(color_positive_negative, subset=percentage_columns)
    return df, latest_timestamp