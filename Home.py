# Libraries
import streamlit as st
from streamlit_extras.switch_page_button import switch_page
import os
from PIL import Image
from extras import logo_sidebar_lit

script_dir = os.path.dirname(os.path.abspath(__file__))
image_dir = 'extras'
asset_thumbs_path = os.path.join(script_dir, image_dir, 'assets_thumbs')
logo_path = os.path.join(script_dir, image_dir, 'logo.png')
st.set_page_config(page_title='PyFiHub - Home', page_icon='🌐', layout='wide', initial_sidebar_state='expanded')
st.markdown(logo_sidebar_lit(logo_path, height=159), unsafe_allow_html=True)

def main():
    # Content
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

    st.markdown(" ## PyFi Hub")
    st.divider()

    col1, col2, col3, col4, col5 = st.columns([1,1,1,1,1])

    with col1:
        searched = st.button("🌟 BTC Market Cycles")
        if searched:
            switch_page('btc market cycles') 

    with col2:
        historical = st.button("📋 Binance Historical Data")
        if historical:
            switch_page('binance historical data')  

    with col3:
        compare = st.button("📊 Compare Crypto & Markets")
        if compare:
            switch_page('compare crypto & markets')

    with col4:
        live_prices = st.button("📌 Cryptocurrency Live Prices (Top 1000)")
        if live_prices:
            switch_page('cryptocurrency live prices')
        
    with col5:
        live_prices = st.button("🔎 Ethereum Wallet Explorer")
        if live_prices:
            switch_page('ethereum wallet explorer')

    col6, col7, col8, col9, col10 = st.columns([1,1,1,1,1])

    with col6:
        live_prices = st.button("📓 Markdown To PDF Converter")
        if live_prices:
            switch_page('markdown to pdf converter')

    st.text("")
    st.markdown("**Disclaimer:** ⚠️ This website uses data from third-party APIs. We do not guarantee or warrant the accuracy, completeness, or timeliness of the data. We are not responsible for any errors or omissions in the data, or for any losses or damages that may arise from the use of the data. We do not own or control the API that we use to obtain the data, and we are not affiliated with by the owning company. By using this website, you acknowledge and agree to these terms and conditions. This is not financial advice. ⚠️", unsafe_allow_html=True)
    st.text("")
    st.divider()
    col1, col2 = st.columns([2,1])

    with col1:
        expander = st.expander("About")
        expander.markdown('''
        ##### Welcome to PyFiHub 
        Your gateway to the intersection of programming, cryptocurrencies, and financial analysis.

        This website serves as a dynamic, evolving showcase of **Python programming, financial data manipulation, and blockchain technology**, aimed at demonstrating the capabilities of these technologies for real-world applications.

        ###### Here's what you'll find on the website:
        - **BTC Market Cycles**: Dive into the fluctuations and trends of Bitcoin's market, dynamically pulled from CoinGecko and Binance APIs.
        - **Binance Historical Data SQL Database**: A comprehensive database that leverages the Binance API to provide historical data about various cryptocurrencies.
        - **Compare Crypto & Market ROI**: Utilize the power of Yfinance to compare the return on investment (ROI) of different cryptocurrencies and financial markets.
        - **Crypto Live Prices**: Get real-time price updates of various cryptocurrencies, powered by CoinGecko API.
        - **Ethereum Wallet Explorer**: An interactive tool that uses Etherscan API to allow exploration of Ethereum wallets, providing detailed insights and analytics.

        This website is built using **Python, Streamlit**, and hosted on a **Linux EC2 AWS server with Nginx**. 

        Remember, this website is a playground for testing and implementing innovative ideas. 
        The data and information you find here are part of this testing environment, always evolving and improving. Enjoy exploring!
        
        If you find this work interesting, feel free to get in touch!
        ''')
        expander.info('**E-Mail: [pyfihub@outlook.com]**', icon="✉️")
        expander.info('**GitHub: [@PyFiHub](https://github.com/PyFiHub)**', icon="ℹ️")
        expander.write("")
        
if __name__ == "__main__":
    main()