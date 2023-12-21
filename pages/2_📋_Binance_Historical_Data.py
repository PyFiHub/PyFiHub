import streamlit as st
from streamlit_autorefresh import st_autorefresh
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import io
from extras import logo_sidebar_lit
from pathlib import Path
import os

dir_path = Path(__file__).parent.resolve()
db_path = dir_path / '..' / 'dbs' / 'trading_data.db'

# Function to get data from the SQLite database
def get_data(query, params=()):
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute(query, params)
        data = c.fetchall()

    return data

# Query the total number of tables
num_tables = get_data("SELECT count(name) FROM sqlite_master WHERE type='table'")[0][0]

# Query the first and latest date from "pair_BTCUSDT"
min_date, max_date = get_data("SELECT MIN(close_time), MAX(close_time) FROM pair_BTCUSDT")[0]

min_date = pd.to_datetime(min_date)
max_date = pd.to_datetime(max_date)

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    logo_path = os.path.join(parent_dir, 'extras', 'logo.png')
    st.set_page_config(page_title='📋 Binance Historical Data - PyFiHub', page_icon='🌐' , layout='wide',initial_sidebar_state='expanded')
    st.markdown(logo_sidebar_lit(logo_path, height=159), unsafe_allow_html=True)
    st_autorefresh(interval=60 * 60 * 1000 * 24, limit=None, key='refresh') #1days

    hide_menu_style = """
        <style>
            #MainMenu {visibility: hidden;}
            button[title="View fullscreen"]{visibility: hidden;}
            .css-15zrgzn {display: none}
            section[data-testid="stSidebar"] .css-ng1t4o {{width: 14rem;}}
            footer {visibility: hidden;}
        </style>
        """
    st.markdown(hide_menu_style, unsafe_allow_html=True)

    st.markdown(" ## Binance Historical Data - Daily Window")

    # Add a markdown description
    st.markdown(
        """
        This application allows you to explore historical price data for various cryptocurrencies listed on Binance Global Exchange.
        You can select an asset, choose a date range, and visualize the OHLC (Open, High, Low, Close) data in a candlestick chart. 
        Additionally, you can download the data as a CSV or Excel file.
        Only showing USDT pairs. New rows are imported daily.
        """
    )

    # Add a box to display the minimum date and the number of total assets
    st.markdown(
        f"""
        **Database Information:**
        - Earliest available date: `{min_date.strftime('%Y-%m-%d')}`
        - Number of assets available: `{num_tables}`
        """
    )

    # Create a drop-down box with all available assets
    tables = get_data("SELECT name FROM sqlite_master WHERE type='table'")
    assets = [table[0].replace("pair_", "") for table in tables]
    sorted_assets = sorted(assets)

    default_asset = 'BTCUSDT'
    default_asset_index = sorted_assets.index(default_asset) if default_asset in sorted_assets else 0
    selected_asset = st.selectbox("Select an asset", sorted_assets, index=default_asset_index)


    st.write("Start Date")
    start_date = st.date_input("Start Date", value=min_date, label_visibility="collapsed")

    st.write("End Date")
    end_date = st.date_input("End Date", value=max_date, label_visibility="collapsed")

    # Add a note about the available date range
    st.markdown(
        f"""
        **Note:** The date range for the asset must be within the available dates: `{min_date.strftime('%Y-%m-%d')}` to `{max_date.strftime('%Y-%m-%d')}`.
        """
    )

    # Fetch the data for the selected asset
    table_name = f"pair_{selected_asset}"
    data = get_data(f"SELECT * FROM {table_name} WHERE close_time BETWEEN ? AND ?", (start_date, end_date))
    data = pd.DataFrame(data, columns=["open_time", "open", "high", "low", "close", "volume", "close_time", "num_trades"])
    data["open_time"] = pd.to_datetime(data["open_time"])
    data["close_time"] = pd.to_datetime(data["close_time"])

    if data.empty:
        st.warning("No data available for the selected timeframe.")
    else:
        def display_summary_and_charts(data, selected_asset):
            # Rest of the code for plotting, summary tables, and download buttons

            # Plot the OHLC graph and price summary table side by side
            col1, col2 = st.columns([1, 5])

            # Display the price summary table in col1
            summary_data = {
                selected_asset: [
                    data["open"].iloc[0],
                    data["close"].iloc[-1],
                    data["high"].max(),
                    data["low"].min(),
                ]
            }

            # Calculate additional summary values
            percentage_change = round(((data["close"].iloc[-1] - data["open"].iloc[0]) / data["open"].iloc[0]) * 100, 2)
            sma_50 = data["close"].rolling(window=50).mean().iloc[-1]
            sma_200 = data["close"].rolling(window=200).mean().iloc[-1]

            if pd.isna(sma_200):
                crossover_status = float('nan')
            else:
                crossover_status = "Bullish" if sma_50 > sma_200 else "Bearish"

            # Calculate RSI and StochRSI values

            def rsi(close_prices, window=14):
                delta = close_prices.diff()
                gain = delta.where(delta > 0, 0)
                loss = -delta.where(delta < 0, 0)
                avg_gain = gain.rolling(window=window).mean()
                avg_loss = loss.rolling(window=window).mean()
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
                return rsi

            def stochrsi(rsi_values, window=14):
                min_rsi = rsi_values.rolling(window=window).min()
                max_rsi = rsi_values.rolling(window=window).max()
                stochrsi = (rsi_values - min_rsi) / (max_rsi - min_rsi)
                return stochrsi

            rsi_values = rsi(data["close"])
            stochrsi_values = stochrsi(rsi_values)

            # Get the latest RSI and StochRSI values
            latest_rsi = rsi_values.iloc[-1]
            latest_stochrsi = stochrsi_values.iloc[-1]

            # Add the additional summary values to the summary_data dictionary
            summary_data[selected_asset].extend([percentage_change, sma_50, sma_200, crossover_status, latest_rsi, latest_stochrsi])

            # Update the index to include the additional summary values
            summary_df = pd.DataFrame(summary_data, index=["Opening Price", "Closing Price", "Highest Price", "Lowest Price", "Percentage Change", "SMA 50", "SMA 200", "Crossover Status", "RSI", "StochRSI"]).astype(str)

            # Function to format numbers and remove unnecessary trailing zeros
            def format_number(val, idx):
                if isinstance(val, (int, float)):
                    if idx in ('RSI', 'StochRSI'):
                        return f"{val:.2f}"
                    return f"{val:.10g}"
                return val

            # Apply the format_number function to the summary_data dictionary
            formatted_summary_data = {
                key: [format_number(val, idx) for val, idx in zip(values, summary_df.index)]
                for key, values in summary_data.items()
            }

            # Create the summary_df DataFrame with the formatted values
            summary_df = pd.DataFrame(formatted_summary_data, index=["Opening Price", "Closing Price", "Highest Price", "Lowest Price", "Percentage Change", "SMA 50", "SMA 200", "Crossover Status", "RSI", "StochRSI"])


            # Color code the percentage change and crossover status
            def color_values(val):
                if val == "Bullish":
                    return "background-color: green"
                elif val == "Bearish":
                    return "background-color: red"
                return ""

            # Apply the color coding to the summary_df
            colored_df = summary_df.style.applymap(color_values, subset=('Crossover Status',))

            # Display the price summary table in col1
            col1.write("Price Summary")
            col1.write(colored_df)

            # Plot the OHLC graph in col2
            fig = go.Figure(data=[go.Candlestick(x=data['close_time'],
                            open=data['open'],
                            high=data['high'],
                            low=data['low'],
                            close=data['close'])])
            fig.update_layout(title='OHLC Candlestick Chart', xaxis_title='Date', yaxis_title='Price', xaxis_rangeslider_visible=False, margin=dict(l=0, r=0, t=30, b=0))
            col2.plotly_chart(fig, use_container_width=True)

            # Add the Download CSV button
            csv = data.to_csv(index=False)
            st.download_button(label="Download CSV (UTF-8 encoding)", data=csv, file_name=f"{selected_asset}_price_data.csv", mime="text/csv")

            # Add the Download Excel button
            excel_file = io.BytesIO()  # Create an in-memory binary stream
            data.to_excel(excel_file, index=False, engine='openpyxl')
            excel_file.seek(0)  # Reset the file pointer to the beginning of the stream
            st.download_button(label="Download Excel", data=excel_file.getvalue(), file_name=f"{selected_asset}_price_data.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        display_summary_and_charts(data, selected_asset)
    
if __name__ == '__main__':
    main()