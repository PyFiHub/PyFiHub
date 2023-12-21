import requests
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import timedelta
from PIL import Image
from extras import logo_sidebar_lit
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
logo_path = os.path.join(parent_dir, 'extras', 'logo.png')
asset_thumbs_path = os.path.join(parent_dir, 'extras', 'assets_thumbs')
st.set_page_config(page_title='🌟 BTC Market Cycles', page_icon='🌐', layout='wide',initial_sidebar_state='expanded')
st.markdown(logo_sidebar_lit(logo_path, height=159), unsafe_allow_html=True)

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

col1, col2 = st.columns([1, 9])
col1.image(Image.open(f'{asset_thumbs_path}/BTC_32.png'))
col2.markdown(" ## BTC Market Cycles")
st.write(f"This chart highlights market cycles by looking at SMA crossover. (50 vs 200 Days) - In Yellow 200 Week SMA")
st.markdown("***", unsafe_allow_html=True)

## COINGECKO 100 & 200 Weekly Simple Moving Average
## COINGECKO PROVIDES A WIDER TIMEFRAME - USEFULL TO CALCULATE WEEKLY MA

@st.cache_data(ttl=float(timedelta(minutes=30).total_seconds()))
def get_figure():
    def get_weekly_sma(coin_id):    
        api_url = f'https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=max&interval=daily'
        data = requests.get(api_url).json()
        df = pd.DataFrame.from_records(list(data['prices']), columns =['Time', 'Price'])
        df['Time'] = df['Time'].apply(pd.to_datetime, unit='ms')
        window_100 = 50 * 7 # 100 weeks * 7 days per week
        window_200 = 200 * 7 # 200 weeks * 7 days per week
        df['SMA_W100'] = df['Price'].rolling(window=window_100).mean()
        df['SMA_W200'] = df['Price'].rolling(window=window_200).mean()
        df['Time'] = df['Time'].dt.date # extract the date part and store it in a new column "Date"
        df = df[:-1]
        return df
    def get_symbol_data(symbol, tick_interval, limit):
        api_url = 'https://api.binance.com/api/v3/klines?symbol='+symbol+'&interval='+tick_interval+'&limit='+limit
        data = requests.get(api_url).json()
        df = pd.DataFrame(data)
        df = df.iloc[:,:11]
        # Renaming columns
        df.columns = ['Time', 
                'open', 
                'high', 
                'low', 
                'close', 
                'volume',
                'close_time',
                'quote_asset_volume',
                'number_of_trades',
                'taker_buy_base_asset_volume',
                'taker_buy_quote_asset_volume']
        cols_to_convert = ['Time', 'close_time']
        df[cols_to_convert] = df[cols_to_convert].apply(pd.to_datetime, unit='ms')
        df['Time'] = df['Time'].dt.date
        return df
    def ta_funcs(df):
        df['sma_50'] = df.close.rolling(window=100).mean()
        df['sma_200'] = df.close.rolling(window=200).mean()
        return df
    coin_data = ta_funcs(get_symbol_data('BTCUSDT', '1d', '1000'))
    weekly_sma = get_weekly_sma('bitcoin')
    final = coin_data.merge(weekly_sma, on='Time', how='left')
    cols_to_convert = ['SMA_W100',
                    'SMA_W200',
                    'sma_50',
                    'sma_200',
                    'open',
                    'high',
                    'low',
                    'close',
                    'volume',
                    'quote_asset_volume',
                    'taker_buy_base_asset_volume',
                    'taker_buy_quote_asset_volume']
    final[cols_to_convert] = final[cols_to_convert].astype(float)
    final[cols_to_convert] = final[cols_to_convert].applymap('{:.0f}'.format)
    final = final.tail(800)
    # sample data
    df = final.copy()
    df.index = df.Time
    df = df[['close', 'sma_50', 'sma_200', 'SMA_W100', 'SMA_W200','open','high','low']]
    df = df.astype(float)
    df1 = df.copy()
    # split data into chunks where averages cross each other
    df['label'] = np.where(df['sma_50']>df['sma_200'], 1, 0)
    df['group'] = df['label'].ne(df['label'].shift()).cumsum()
    df = df.groupby('group')
    dfs = []
    for name, data in df:
        dfs.append(data)
    # custom function to set fill color
    def fillcol(label):
        if label >= 1:
            return 'rgba(0,250,0,0.4)'
        else:
            return 'rgba(250,0,0,0.4)'
    fig = go.Figure(data=go.Ohlc(x=df1.index,
                    open=df1.open,
                    high=df1.high,
                    low=df1.low,
                    close=df1.close, name='BTC'))
    for df in dfs:
        fig.add_traces(go.Scatter(x=df.index, y = df.sma_50, name='',showlegend = False,hoverinfo='skip',
                                line = dict(color='rgba(0,0,0,0)')))
        
        fig.add_traces(go.Scatter(x=df.index, y = df.sma_200, name='',showlegend = False,hoverinfo='skip',
                                line = dict(color='rgba(0,0,0,0)'),
                                fill='tonexty', 
                                fillcolor = fillcol(df['label'].iloc[0])))
        
    # include averages
    fig.add_traces(go.Scatter(x=df1.index, y = df1.sma_50, name='50D',
                            line = dict(color = 'teal', width=1)))
    fig.add_traces(go.Scatter(x=df1.index, y = df1.sma_200, name='200D',
                            line = dict(color = 'orange', width=1)))
    fig.add_trace(go.Scatter(x=final.Time, y=final.SMA_W200,
                        mode='lines',
                        name='200W SMA',
                        line = dict(color='yellow', width=2, dash='longdash')))
    fig.update_layout(hovermode="x unified", template='plotly_dark',width=1200, height=750, title=f'BTC SMA 50/200 Daily Cross - Last Daily Closed on the {final.Time.iloc[-2]}, @ ${final.close.iloc[-2]}')
    fig.update(layout_xaxis_rangeslider_visible=False)
    fig.update_layout(
        hoverlabel=dict(
            bgcolor="rgba(255,255,255,0.15)",
            font_size=14,
            font_family="Calibri",
            font_color="whitesmoke",
        )
    )
    fig.update_yaxes(type="log")
    return fig

fig = get_figure()
st.plotly_chart(fig, use_container_width=True)