# Libraries
import os
import streamlit as st
from extras import logo_sidebar_lit, process_data_coingecko
from datetime import timedelta
from streamlit_autorefresh import st_autorefresh
from PIL import Image

COINGECKO_LOGO_URL = "https://static.coingecko.com/s/coingecko-branding-guide-8447de673439420efa0ab1e0e03a1f8b0137270fbc9c0b7c086ee284bd417fa1.png"
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
logo_path = os.path.join(parent_dir, 'extras', 'logo.png')
asset_thumbs_path = os.path.join(parent_dir, 'extras')
st.set_page_config(page_title='📌Cryptocurrency_Live_Prices', page_icon='🌐', layout='wide', initial_sidebar_state='expanded')
st.markdown(logo_sidebar_lit(logo_path, height=159), unsafe_allow_html=True)

# Autorefresh each 5 minute and cache data
st_autorefresh(interval=60*1000*5, key="autorefresh")
@st.cache_data(ttl=float(timedelta(minutes=5).total_seconds()))

def main():
    
    """
    Config Streamlit Template

    """
    hide_menu_style = """
    <style>
        #MainMenu {visibility: hidden;}
        button[title="View fullscreen"]{visibility: hidden;}
        .css-15zrgzn {display: none}
        section[data-testid="stSidebar"] .css-ng1t4o {width: 14rem;}
        footer {visibility: hidden;}
    </style>
    """
    
    st.markdown(hide_menu_style, unsafe_allow_html=True)
    # Functions after Config Streamlit Template.
    data, latest_timestamp = process_data_coingecko.process_data_gecko()
    header = f"""
    <div style="display: flex; justify-content: space-between; align-items: left;">
        <div style="display: flex; align-items: left;">
            <span style="font-weight: bold; margin-left: 1; white-space: nowrap;">Powered by</span>
            <img src="{COINGECKO_LOGO_URL}" alt="CoinGecko Logo" style="height: 40px; margin-left: 8px;" />
        </div>
    </div>
    """
    st.markdown(header, unsafe_allow_html=True)
    st.divider()
    col1, col2, col3 = st.columns([3, 1, 1])
    col1.markdown(" #### Cryptocurrencies Live Prices (Top 1000) by Market Cap")
    col2.write(f' Last Update: {latest_timestamp}')
    # Streamlit Dataframe
    st.dataframe(
        data,
        column_config={
            "Image": st.column_config.ImageColumn(
                "Image"),
            "Percentage In Circulation": st.column_config.ProgressColumn(
                "Percentage In Circulation",
                help='Circulating Supply / Max Supply',
                format="%.2f",
                min_value=0,
                max_value=100,
                width=None),
            "Fully Diluted Valuation": st.column_config.Column(
                "Fully Diluted Valuation",
                help="Fully Diluted Valuation - Hypothetical market value if maximum supply is reached.",
                width="small"),
            "Circulating Supply": st.column_config.Column(
                "Circulating Supply",
                help="Circulating Supply - Total coins in circulation, excluding locked/reserved tokens.",
                width="small"),
            "Total Supply": st.column_config.Column(
                "Total Supply",
                help="Total Supply - Maximum coins that can exist, including future releases.",
                width="small"),
            "Max Supply": st.column_config.Column(
                "Max Supply",
                help="Max Supply - Absolute maximum coins that can ever be created.",
                width="small"),
        },

        height = 1000, column_order=(
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
                                    'Percentage In Circulation',
                                    '1h %',
                                    '24h %',
                                    '7d %',
                                    '30d %',
                                    '1y %',), hide_index=True,
    )

if __name__ == "__main__":
    main()