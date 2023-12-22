import streamlit as st
import requests
import pandas as pd
import json
import plotly.graph_objects as go
import numpy as np
import os
import re
import time
from extras import logo_sidebar_lit
import plotly.subplots as sp

script_dir = os.path.dirname(os.path.abspath(''))
#pd.set_option('display.float_format', '{:.9f}'.format)
ETHERSCAN_LOGO_URL = "https://etherscan.io/images/brandassets/etherscan-logo-light.svg"




# Read API key from a JSON configuration file.

def get_api_key():
    
    config_file_path = os.path.join(parent_dir, 'config', 'config.json')  
    with open(config_file_path) as config_file:
        config = json.load(config_file)
        api_key = config.get('api_key')
    return api_key



#Etherscan Functions

def get_balance(address, api_key):
    """
    Fetch balance for a given Ethereum address.
    """
    url = f"https://api.etherscan.io/api?module=account&action=balance&address={address}&tag=latest&apikey={api_key}"
    response = requests.get(url)
    balance = response.json()['result'] if response.status_code == 200 else '0'
    time.sleep(1)
    return float(balance) / 1e18  # convert from Wei to Ether

def get_transactions_eth(address, api_key):
    """
    Fetch transactions for a given Ethereum address.
    """
    startblock = 0
    all_transactions = []

    while True:
        url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock={startblock}&endblock=99999999&sort=asc&apikey={api_key}"
        response = requests.get(url)
        if response.status_code == 429:  # 429 is often used to indicate too many requests
            raise Exception("Rate limit exceeded.")
        
        if response.status_code == 200:
            result = response.json()['result']
            if not result:  # if no more transactions, break the loop
                break

            all_transactions.extend(result)

            # Check if the number of transactions equals to the limit of 10000 
            # which means we might have more transactions in the latest block.
            if len(result) == 10000:
                last_block = int(result[-1]['blockNumber'])
                # Filter transactions of the latest block
                latest_block_transactions = [t for t in result if int(t['blockNumber']) == last_block]
                if len(latest_block_transactions) == 10000:  # If we have 10000 transactions in the latest block
                    raise Exception(f"Block {last_block} has more transactions than fetched. Please adjust the function to handle this case.")
                # Otherwise, increment the startblock
                else:
                    startblock = last_block + 1
            # If we have less than 10000 transactions, increment the startblock
            else:
                startblock = int(result[-1]['blockNumber']) + 1
        else:
            break

        # sleep for 1 second to avoid hitting rate limits
        time.sleep(1)

    return all_transactions

def get_transactions_erc20(address, api_key):
    """
    Fetch ERC20 transactions for a given Ethereum address.
    """
    startblock = 0
    all_transactions = []

    while True:
        url = f"https://api.etherscan.io/api?module=account&action=tokentx&address={address}&startblock={startblock}&endblock=99999999&sort=asc&apikey={api_key}"
        response = requests.get(url)
        if response.status_code == 429:  # 429 is often used to indicate too many requests
            raise Exception("Rate limit exceeded.")
        
        if response.status_code == 200:
            result = response.json()['result']
            if not result:  # if no more transactions, break the loop
                break

            all_transactions.extend(result)

            # Check if the number of transactions equals to the limit of 10000 
            # which means we might have more transactions in the latest block.
            if len(result) == 10000:
                last_block = int(result[-1]['blockNumber'])
                # Filter transactions of the latest block
                latest_block_transactions = [t for t in result if int(t['blockNumber']) == last_block]
                if len(latest_block_transactions) == 10000:  # If we have 10000 transactions in the latest block
                    raise Exception(f"Block {last_block} has more transactions than fetched. Please adjust the function to handle this case.")
                # Otherwise, increment the startblock
                else:
                    startblock = last_block + 1
            # If we have less than 10000 transactions, increment the startblock
            else:
                startblock = int(result[-1]['blockNumber']) + 1
        else:
            break

        # sleep for 1 second to avoid hitting rate limits
        time.sleep(1)

    return all_transactions




#Dataframe Support Functions

def convert_timestamp(df):
    """
    Convert timestamp to HH:MM:SS mm/dd/yyyy
    """
    df['timeStamp'] = pd.to_datetime(df['timeStamp'], unit='s').dt.strftime('%H:%M:%S %m/%d/%Y')
    return df

def map_methodId(df):
    """
    Replace methodId with User Friendly Values.
    """
    methodId_dict = {'0x': 'Transfer',
                    '0x9fbf10fc': 'Swap',
                    '0x9fbf10fc':'Swap',
                    '0xeb672419': 'Request L2Trx',
                    '0xe2bbb158': 'Deposit',
                    '0x439370b1': 'Deposit Eth',
                    '0x29723511': 'Transfer',
                    '0x5ae401dc': 'Multicall',
                    '0x73e888fd':'Contribute',
                    '0x3593564c':'Execute',
                    '0xfb488204':'Multi Send ETH',
                    '0xb6f9de95':'Swap Exact ETH for Tokens Supporting Fee on Trx Tokens',
                    }
    df['methodId'] = df['methodId'].map(methodId_dict)
    df['methodId'] = df['methodId'].fillna('Unknown')
    return df

def major_tokens():
    major_token_list = [
      'Binance USD',
      'Dai Stablecoin',
      'Fei USD',
      'Tether USD',
      'TrueUSD',
      'USD Coin',    ]
    return major_token_list 

def holdings_erc20(address, df, major_token_filter = False):
    address = address.lower()
    df_out = df.loc[df['from'].isin([address])]
    df_out = df_out.groupby(['tokenName']).agg(amount_out=('value', 'sum')).reset_index()

    df_in = df.loc[df['to'].isin([address])]
    df_in = df_in.groupby(['tokenName']).agg(amount_in=('value', 'sum')).reset_index()

    df_holdings = pd.merge(df_in, df_out, on='tokenName', how='outer')
    # Fill NaN values with 0
    df_holdings.fillna(0, inplace=True)
    # Subtract the two columns
    df_holdings['current_holdings'] = df_holdings['amount_in'] - df_holdings['amount_out']
    
    if major_token_filter:
        df_holdings = df_holdings.loc[df_holdings['tokenName'].isin(major_tokens())]
    cols_to_convert = ['current_holdings','amount_in','amount_out']
    df_holdings[cols_to_convert] = df_holdings[cols_to_convert].round(2)
    
    
    # Compute sum for each column
    total_current_holdings = df_holdings['current_holdings'].sum()
    total_amount_in = df_holdings['amount_in'].sum()
    total_amount_out = df_holdings['amount_out'].sum()

    # Create a new DataFrame for the 'Total' row
    total_row = pd.DataFrame({
        'tokenName': ['Total'],
        'current_holdings': [total_current_holdings],
        'amount_in': [total_amount_in],
        'amount_out': [total_amount_out]
    })

    # Concatenate the original DataFrame and the 'Total' row DataFrame
    df_holdings = pd.concat([df_holdings, total_row], ignore_index=True)

    
    df_holdings.columns = ['Token Name','Amount In', 'Amount Out', 'Current Holdings']
    
    return df_holdings

def highlight_address(s, address, column):
    """
    Hightlight wallet searched by the User in Blue.
    """
    address = address.lower()  # Convert address to lower case
    return ['background-color: blue' if v==address else '' for v in s]

def convert_floats(df):
    for col in df.columns:
        if df[col].dtype == 'float64':
            df[col] = df[col].apply(lambda x: int(x) if x.is_integer() else x)
    return df




#Dataframe Main Functions

def dataframe_clearing(address, trxs):
    """
    Dataframe Clearing - required address and trxs dataframe
    """
    df = pd.DataFrame(trxs)
    df = df[df['value'] != '0']
    df['value'] = df['value'].astype(float)
    df['gasPrice'] = df['gasPrice'].astype(float) / 1e15  # convert from Kwei to Ether
    
    if 'tokenDecimal' in df.columns:
        df['tokenDecimal'] = df['tokenDecimal'].astype(float)
        df['value'] = df['value']/10**df['tokenDecimal'] # convert real value of erc20 token using provided decimal
        return df
    
    if 'methodId' in df.columns: # map eth trx with description (not avl for erc20)
        df['value'] = df['value'] / 1e18  # convert from wei to Ether
        return map_methodId(df)
    
    df = convert_timestamp(df)
    df.drop_duplicates(subset=['hash'], keep='first')
    df = pd.concat([df[df['to'] == address], df[df['to'] != address]])
    return df

def group_transactions(df, address, transaction_type):
    if transaction_type == 'ETH':
        outgoing_df = df[df['from'] == address].groupby('to').agg({'hash': 'count', 'value': 'sum', 'gasPrice': 'sum'}).reset_index()
        incoming_df = df[df['to'] == address].groupby('from').agg({'hash': 'count', 'value': 'sum', 'gasPrice': 'sum'}).reset_index()
        outgoing_df.columns = ['address', 'num_outgoing_transactions', 'total_value_outgoing_trxs','total_gas_paid_outgoing']
        incoming_df.columns = ['address', 'num_incoming_transactions', 'total_value_incoming_trxs','total_gas_paid_incoming']
        df_grouped_columns = ['Address', '# Out Trx', 'ETH Out ','Gas Paid Out Trx', '# In Trx', 'ETH In','Gas Paid In Trx']
        
    elif transaction_type == 'ERC20':
        df = df.loc[df['tokenName'].isin(['Dai Stablecoin', 'USD Coin', 'Tether USD', 'TrueUSD'])]
        incoming_df = df[df['to'] == address.lower()].groupby(['from', 'tokenName']).agg({'hash': 'count', 'value': 'sum', 'gasPrice': 'sum'}).reset_index()
        outgoing_df = df[df['from'] == address.lower()].groupby(['to', 'tokenName']).agg({'hash': 'count', 'value': 'sum', 'gasPrice': 'sum'}).reset_index()
        outgoing_df.columns = ['address', 'erc20_token','num_outgoing_transactions', 'amount','total_gas_paid_outgoing']
        incoming_df.columns = ['address', 'erc20_token','num_incoming_transactions', 'amount','total_gas_paid_incoming']
        df_grouped_columns = ['Address','Outgoing ECR20-Token', '# Outgoing Trx', 'Amount Outgoing','ETH Gas Paid Outgoing Trx','Incoming ECR20-Token', '# Incoming Trx', 'Amount Incoming','ETH Gas Paid Incoming Trx']
    else:
        raise ValueError(f"Unsupported transaction type: {transaction_type}")

    if transaction_type == 'ETH':
        unique_addresses = pd.concat([df['from'], df['to']]).unique()
        outgoing_df = outgoing_df.set_index('address').reindex(unique_addresses).reset_index().fillna(0)
        incoming_df = incoming_df.set_index('address').reindex(unique_addresses).reset_index().fillna(0)

    df_grouped = pd.merge(outgoing_df, incoming_df, how='outer', on='address')
    df_grouped.columns = df_grouped_columns
    df_grouped = df_grouped.loc[~(df_grouped.iloc[:, 1:] == 0).all(axis=1)]

    if transaction_type == 'ERC20':
        if df_grouped['# Outgoing Trx'].sum() == 0:
                df_grouped['Address'] = df_grouped['ETH Gas Paid Outgoing Trx']
                df_grouped['ETH Gas Paid Outgoing Trx'] = np.nan


    df_grouped = df_grouped.fillna(0)

    sort_column = 'ETH In' if transaction_type == 'ETH' else 'Amount Incoming'
    df_grouped = df_grouped.sort_values(sort_column, ascending=False)

    if transaction_type == 'ETH':
        df_grouped['# Out Trx'] = pd.to_numeric(df_grouped['# Out Trx'], downcast='integer', errors='coerce')
        df_grouped['# In Trx'] = pd.to_numeric(df_grouped['# In Trx'], downcast='integer', errors='coerce')
        df_grouped['ETH In'] = pd.to_numeric(df_grouped['ETH In'], downcast='float', errors='coerce')
        df_grouped['ETH Out '] = pd.to_numeric(df_grouped['ETH Out '], downcast='float', errors='coerce')

    if transaction_type == 'ERC20':
        df_grouped['# Outgoing Trx'] = pd.to_numeric(df_grouped['# Outgoing Trx'], downcast='integer', errors='coerce')
        df_grouped['# Incoming Trx'] = pd.to_numeric(df_grouped['# Incoming Trx'], downcast='integer', errors='coerce')
        df_grouped['Amount Incoming'] = pd.to_numeric(df_grouped['Amount Incoming'], downcast='float', errors='coerce')
        df_grouped['Amount Outgoing'] = pd.to_numeric(df_grouped['Amount Outgoing'], downcast='float', errors='coerce')

    return df_grouped


#Plotly Figures

def erc20_pies(df_holdings, address):
    df_holdings = df_holdings.drop(df_holdings.index[-1])
    df_holdings_filtered = df_holdings[df_holdings['Current Holdings'] != 0]

    fig = sp.make_subplots(rows=1, cols=3, subplot_titles=('Amount In', 'Amount Out', 'Current Holdings'), specs=[[{'type':'domain'}, {'type':'domain'}, {'type':'domain'}]])

    fig.add_trace(go.Pie(labels=df_holdings['Token Name'], values=df_holdings['Amount In'], textinfo='label+percent', hole=.3,
              hovertemplate="<b>%{label}: %{value:.2f} (%{percent:.2%}</b>)<extra></extra>"),
              1, 1)
    fig.add_trace(go.Pie(labels=df_holdings['Token Name'], values=df_holdings['Amount Out'], textinfo='label+percent', hole=.3,
              hovertemplate="<b>%{label}: %{value:.2f} (%{percent:.2%}</b>)<extra></extra>"),
              1, 2)
    fig.add_trace(go.Pie(labels=df_holdings['Token Name'], values=df_holdings_filtered['Current Holdings'], textinfo='label+percent', hole=.3,
              hovertemplate="<b>%{label}: %{value:.2f} (%{percent:.2%}</b>)<extra></extra>"),
              1, 3)

    fig.update_traces(textfont_size=12,
                  marker=dict(line=dict(color='#000000', width=2)))

    fig.update_layout(
    title_text=f"ERC20 Tokens Distribution - Pie Chart <b>{address[:6]}...{address[-4:]}</b>",
    showlegend=True,
    legend=dict(
        x=1,
        y=0.5,
        bgcolor='rgba(12,41,73, 1)',
        bordercolor='rgba(12,41,735, 1)'
    ),
    paper_bgcolor='rgba(14, 17, 23, 1)',
    plot_bgcolor='rgba(14, 17, 23, 1)',
    width=1200,
    height=600,
    font=dict(
        family="Courier New, monospace",
        size=12,
    ),
    hoverlabel=dict(
        font_size=15, 
        font_family="Courier New, monospace"
    )
)

    return fig

def erc20_sankey(df_holdings, address):
    df_holdings = df_holdings.drop(df_holdings.index[-1])
    labels = ["Amount In", "Amount Out", "Current Holdings"] + list(df_holdings['Token Name'])
    sources, targets, values, customdata = [], [], [], []
    
    for i, row in df_holdings.iterrows():
        if row['Amount In'] > 0:
            sources.append(0)
            targets.append(labels.index(row['Token Name']))
            values.append(row['Amount In'])
            customdata.append(row['Token Name'])
        if row['Amount Out'] > 0:
            sources.append(labels.index(row['Token Name']))
            targets.append(1)
            values.append(row['Amount Out'])
            customdata.append(row['Token Name'])
        if row['Current Holdings'] > 0:
            sources.append(labels.index(row['Token Name']))
            targets.append(2)
            values.append(row['Current Holdings'])
            customdata.append(row['Token Name'])
    
    fig = go.Figure(data=[go.Sankey(
        arrangement="snap",
        node=dict(
            pad=25,  # reduce padding between nodes
            thickness=25,
            line=dict(color = "rgba(182,190,200, 0.8)", width =1),
            label=labels,
            hoverlabel=dict(bgcolor="white", font_color="black"),
            hovertemplate='<b>Amount</b>: <br /><b>%{value:.2f} USD</b><extra></extra>'
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            customdata=customdata,
            hovertemplate='<b>Transaction Details</b>: <br />ERC20 Token: <b>%{customdata}</b><br />' +
                          'Amount: <b>%{value:.2f} USD</b><extra></extra>',
        ))])

    fig.update_layout(
        title_text=f"Wallet Transactions ERC20 Tokens - Sankey Chart <b>{address[:6]}...{address[-4:]}</b>",
        font=dict(
            family="Courier New, monospace",
            size=12,
        ),
        hoverlabel=dict(
            font_size=14,
            font_family="Courier New, monospace"
        ),
        paper_bgcolor='rgba(14, 17, 23, 1)',
        plot_bgcolor='rgba(14, 17, 23, 1)',
        width=1200,
        height=600,
    )
    return fig

def eth_sankey(df, address):
    
    df['abs_value'] = df['value'].abs()

    # Compute the total absolute value of transactions for each address
    address_values = df.groupby('from')['abs_value'].sum().add(df.groupby('to')['abs_value'].sum(), fill_value=0)
    top_addresses = address_values.nlargest(25).index
    other_addresses = address_values.index.difference(top_addresses)

    # Replace addresses not in top_addresses with 'Other'
    df['from'] = df['from'].where(df['from'].isin(top_addresses), 'Other')
    df['to'] = df['to'].where(df['to'].isin(top_addresses), 'Other')
    
    unique_addresses = pd.concat([df['from'], df['to']]).unique()
    
    incoming_counts = df['to'].value_counts().reindex(unique_addresses).fillna(0).astype(int)
    outgoing_counts = df['from'].value_counts().reindex(unique_addresses).fillna(0).astype(int)
    labels = [(address[:6]+'...'+address[-4:] if address not in ['Other'] else address) + ' - Incoming: ' + str(incoming_counts[address]) + ', Outgoing: ' + str(outgoing_counts[address]) for address in unique_addresses]
    

    fig = go.Figure(data=[go.Sankey(
        arrangement = "snap",
        node = 
        dict(
        pad = 25,
        thickness = 25,
        line = 
        dict(color = "rgba(182,190,200, 0.8)", width =1),
        label = labels,
        hoverlabel=dict(bgcolor="white",font_color="black"),
        hovertemplate='<b>Wallet Details</b>: <br />Address: %{label}<br />Total Trx Amount: <b>%{value:.8f} ETH</b><extra></extra>',
    ),
    link = dict(
        line = dict(color = "rgba(182,190,200, 0.8)", width =1),
        #arrowlen=50,
        source = df['from'].apply(lambda x: np.where(unique_addresses == x)[0][0]).values, 
        target = df['to'].apply(lambda x: np.where(unique_addresses == x)[0][0]).values,
        value = df['value'],
        customdata = df[['hash', 'timeStamp', 'methodId']].values,
        hovertemplate='<b>Transaction Details</b>: <br />Transaction Hash: %{customdata[0]}<br />'+
        'Timestamp: %{customdata[1]}<br />Amount: <b>%{value:.9f} ETH</b><br />Type: <b>%{customdata[2]}</b><extra></extra>',
    ))])

    fig.update_layout(
    title_text=f"Wallet Transactions ETH - Sankey Chart <b>{address[:6]}...{address[-4:]}</b>",
    font=dict(
        family="Courier New, monospace",
        size=12,
    ),
    hoverlabel=dict(
        font_size=14, 
        font_family="Courier New, monospace"
    ),
    paper_bgcolor='rgba(14, 17, 23, 1)',
    plot_bgcolor='rgba(14, 17, 23, 1)',
    width=1200,
    height=600,
)

    return fig



# Streamlit Page - Stage Before user Sumbits ETH Address

def main(address):
    address = address.lower()
    api_key = get_api_key()
    balance = get_balance(address, api_key)
    trx_eth = get_transactions_eth(address, api_key)
    trx_erc20 = get_transactions_erc20(address, api_key)

    if not trx_eth:
        st.error("Warning: No transactions found for this address.")
    if not trx_erc20:
        st.error("Warning: No ERC20 transactions found for this address.")

# Streamlit Page - Stage After user Sumbits ETH Wallet Address

    if not trx_eth and not trx_erc20:
        return
    

    balance_container = st.container()
    with balance_container:
        st.markdown(f"#### Balance: **{balance:.9f} ETH**" )
    if trx_erc20:
        st.markdown(f"#### ECR 20 Balance (Stables Only):" )
        st.dataframe(holdings_erc20(address, dataframe_clearing(address, trx_erc20), major_token_filter = True),
    column_config={
        "Amount In": st.column_config.NumberColumn(
            "Amount In",
            help="Total Stable Received (USD)",
            min_value=None,
            max_value=None,
            step=None,
            format="$ %.2f"),
        "Amount Out": st.column_config.NumberColumn(
            "Amount Out",
            help="Total Stable Sent (USD)",
            min_value=None,
            max_value=None,
            step=None,
            format="$ %.2f"),
        "Current Holdings": st.column_config.NumberColumn(
            "Current Holdings",
            help="Current Holdings on Wallet (USD)",
            min_value=None,
            max_value=None,
            step=None,
            format="$ %.2f"),
    }, use_container_width=False, hide_index=True)
    
    
    tab1, tab2 = st.tabs([f"ETH Transactions Overview", "ERC20 Transactions Overview"])
    with tab1:
        if trx_eth:
            st.dataframe(group_transactions(dataframe_clearing(address, trx_eth), address, 'ETH').style.apply(highlight_address, address=user_input, column=['to']), use_container_width=True, hide_index=True)
            
        if not trx_eth:
            st.write('No ETH transactions found for this address')
    with tab2:
        if trx_erc20:
            st.dataframe(group_transactions(dataframe_clearing(address, trx_erc20), address, 'ERC20').style.apply(highlight_address, address=user_input, column=['to']), use_container_width=True, hide_index=True)
            
        if not trx_erc20:
            st.write('No ERC-20 transactions found for this address')

    st.divider()
    st.caption('''
    **Wallet Transactions ETH - Sankey Chart:** This function creates a Sankey diagram to visualize the flow of Ether between different Ethereum addresses. The 'from' and 'to' addresses are grouped into 'Top 25' and 'Other', based on the total absolute value of transactions associated with each address. This visualization provides an overview of the transaction activities for a given Ethereum address.

    ''')
    st.plotly_chart(eth_sankey(dataframe_clearing(address, trx_eth), address), theme=None, use_container_width=True)
    st.divider()
    if trx_erc20:
        st.caption('''
        **Wallet Transactions ERC20 Tokens - Sankey Chart:** This function generates a Sankey diagram to visualize the flow of ERC20 tokens from "Amount In" to the specific token and then to "Amount Out" or "Current Holdings".

        ''')
        st.plotly_chart(erc20_sankey(holdings_erc20(address, dataframe_clearing(address, trx_erc20), major_token_filter = True), address), theme=None, use_container_width=True)
        st.caption('''
        **ERC20 Tokens Distribution - Pie Chart:** This function generates a 1-row, 3-column subplot with pie charts illustrating the amount in, amount out, and current holdings of ERC20 tokens for a given Ethereum address.

        ''')
        st.plotly_chart(erc20_pies(holdings_erc20(address, dataframe_clearing(address, trx_erc20), major_token_filter = True), address), theme=None, use_container_width=True)
    st.divider()

# Streamlit Settings - Before calling main

script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
logo_path = os.path.join(parent_dir, 'extras', 'logo.png')
st.set_page_config(page_title='🔎 Ethereum Wallet Explorer - PyFi Hub', page_icon='🌐', layout='wide',initial_sidebar_state='expanded')
st.markdown(logo_sidebar_lit(logo_path, height=159), unsafe_allow_html=True)

hide_menu_style = """
            <style>
                #MainMenu {visibility: hidden;}
                .css-15zrgzn {display: none}
                section[data-testid="stSidebar"] .css-ng1t4o {{width: 14rem;}}
                footer {visibility: hidden;}
            </style>
            """

st.markdown(hide_menu_style, unsafe_allow_html=True)
header = f"""
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div style="flex-grow: 1;">
            <h2 style="margin: 0; white-space: nowrap;">Ethereum Wallet Explorer</h2>
        </div>
        <div style="display: flex; align-items: center;">
            <span style="font-weight: bold; margin-left: 16px; white-space: nowrap;">Powered by</span>
            <img src="{ETHERSCAN_LOGO_URL}" alt="Etherscan Logo" style="height: 40px; margin-left: 8px;" />
        </div>
    </div>
    """
st.markdown(header, unsafe_allow_html=True)

st.markdown('''
    This application provides an easy-to-use interface to explore transactions 
    and balances of Ethereum addresses. Powered by Etherscan.

    **Non-zero values transaction are removed.**
    The application focus on transactions where ETH is actually being transferred between addresses. 
    This helps to reduce the noise from contract calls that don't involve a direct ETH transfer.

    Transactions are fetched for both ETH and ERC20 (Stables Only).
    
    1. **Enter an Ethereum address**: Start by entering a valid Ethereum address 
       in the input field and clicking "Submit".
    ''')

user_input = st.text_input("", "", help="Please enter a valid Ethereum address.")

if st.button('Submit'):
    if user_input and re.match("^0x[a-fA-F0-9]{40}$", user_input):
        try:
            # Initialize the progress bar
            progress_bar = st.progress(0)
            for i in range(100):
                # Update progress
                time.sleep(0.01)  # adjust this to match real progress
                progress_bar.progress(i + 1)  # increment progress

            main(user_input)
        except Exception as e:
            if str(e) == "Rate limit exceeded.":
                st.error("Too many requests. Please try again later.")
            else:
                st.write("An error occurred:", e)
    else:
        st.write("Please enter a valid Ethereum address.")