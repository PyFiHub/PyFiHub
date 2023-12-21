import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from extras import logo_sidebar_lit
import os

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    logo_path = os.path.join(parent_dir, 'extras', 'logo.png')
    st.set_page_config(page_title='📊 Compare Crypto & Markets - PyFiHub', page_icon='🌐' , layout='wide',initial_sidebar_state='expanded')
    st.markdown(logo_sidebar_lit(logo_path, height=159), unsafe_allow_html=True)
    st.markdown(" ## Compare Crypto & Markets")
    st.write(f"Fetch data from Yahoo Finance, plot cumulative returns, and displays the latest percentage change with a visual trend indicator for the time-frame selected.")
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

    start = st.date_input('Start Date', value = pd.to_datetime('2023-01-01'))
    end = st.date_input('Start Date', value = pd.to_datetime('today'))

    tickers = ('^GSPC','^IXIC','^DJI','^STOXX','^FTSE','000001.SS','GC=F','SI=F','BTC-USD', 'ETH-USD', 'BNB-USD', 'XRP-USD', 'ADA-USD', 'DOGE-USD', 'MATIC-USD', 'SOL-USD', 'DOT-USD', 'SHIB-USD')
    # Create a dictionary mapping ticker symbols to names
    ticker_to_name = {
        '^GSPC': 'S&P 500',
        '^IXIC': 'NASDAQ',
        '^DJI':'Dow Jones Industrial',
        '^STOXX': 'Stoxx 600',
        '^FTSE': 'FTSE 100',
        '000001.SS':'Shanghai SE',
        'GC=F':'Gold',
        'SI=F':'Silver',
        'BTC-USD': 'Bitcoin',
        'ETH-USD': 'Ethereum',
        'BNB-USD': 'Binance Coin',
        'XRP-USD': 'Ripple',
        'ADA-USD': 'Cardano',
        'DOGE-USD': 'Dogecoin',
        'MATIC-USD': 'Polygon',
        'SOL-USD': 'Solana',
        'DOT-USD': 'Polkadot',
        'SHIB-USD': 'Shiba Inu',
    }

    # Create the reverse mapping
    name_to_ticker = {v: k for k, v in ticker_to_name.items()}

    # Use the names in the multiselect
    selected_names = st.multiselect("Select Ticker", list(ticker_to_name.values()))

    # Convert the selected names back to ticker symbols when processing
    assets = [name_to_ticker[name] for name in selected_names]

    def relativeret(df):
        rel = df.pct_change(1)
        cumret = (1+rel).cumprod() - 1
        cumret = cumret.fillna(0)
        cumret = (cumret*100).round(2)
        return cumret
    

    if len(assets) > 0:
        df = relativeret((yf.download(tickers,start,end)['Adj Close']))
        dfs = {}
        for asset in assets:
            df_ = df.loc[:, [asset]]
            dfs[asset] = df_

        fig = go.Figure()
        for asset in assets:
            asset_name = ticker_to_name[asset]  # Get the descriptive name
            df_ = df.loc[:, [asset]]
            fig = fig.add_trace(go.Scatter(x=df_.index, y=df_[asset], name=asset_name, hovertemplate = '%{y} %',))
        fig.update_layout(hovermode="x")
        fig.update_layout(
            title="Coin/Token Comparison - Cumulative Return",
            xaxis_title="Time",
            yaxis_title="%",
            legend_title="",
        )

        st.plotly_chart(fig, use_container_width=True)
        # Display latest percent changes
        start_str = start.strftime('%d/%m/%Y')
        end_str = end.strftime('%d/%m/%Y')

        # Display the updated message
        st.write(f"#### Percentage change from {start_str} to {end_str}")
        data = []
        for asset in assets:
            asset_name = ticker_to_name[asset]  # Get the descriptive name
            latest_pct_change = dfs[asset].iloc[-1][asset]  # Fetch the latest value
            direction = '🟩' if latest_pct_change >= 0 else '🟥'
            data.append([asset_name, latest_pct_change, direction])

        # Create a DataFrame with the data
        df_pct_changes = pd.DataFrame(data, columns=["Asset", "Latest Percent Change", "Trend"])

        # Display the DataFrame
        st.dataframe(df_pct_changes)

if __name__ == '__main__':
    main()


