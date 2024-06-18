import streamlit as st
import pandas as pd
import json
from datetime import datetime
import plotly.graph_objs as go
from langchain_community.llms import Ollama

# List of cryptocurrency symbols and their corresponding JSON file names
symbols = {
    'avax': '../json_data/avax.json',
    'bnb': '../json_data/bnb.json',
    'btc': '../json_data/btc.json',
    'doge': '../json_data/doge.json',
    'eth': '../json_data/eth.json',
    'shib': '../json_data/shib.json',
    'sol': '../json_data/sol.json',
    'trx': '../json_data/trx.json',
    'usdt': '../json_data/usdt.json'
}

# Function to load historical data from JSON file
def load_data(symbol):
    file_name = symbols[symbol]
    with open(file_name, 'r') as f:
        data = json.load(f)
    for entry in data:
        if isinstance(entry['time'], int):
            entry['time'] = datetime.utcfromtimestamp(entry['time']).strftime('%Y-%m-%d %H:%M:%S')
        else:
            entry['time'] = datetime.strptime(entry['time'], '%Y-%m-%d %H:%M:%S')
    df = pd.DataFrame(data)
    df['time'] = pd.to_datetime(df['time'])
    df = df.sort_values(by='time', ascending=False)
    return df

# Function to resample data based on selected interval
def resample_data(df, interval):
    if interval == 'Daily':
        return df
    elif interval == 'Weekly':
        return df.resample('W', on='time').agg({
            'high': 'max',
            'low': 'min',
            'open': 'first',
            'close': 'last',
            'volumefrom': 'sum',
            'volumeto': 'sum'
        }).reset_index().sort_values(by='time', ascending=False)
    elif interval == 'Monthly':
        return df.resample('M', on='time').agg({
            'high': 'max',
            'low': 'min',
            'open': 'first',
            'close': 'last',
            'volumefrom': 'sum',
            'volumeto': 'sum'
        }).reset_index().sort_values(by='time', ascending=False)

# Function for Fundamental Analysis using Ollama
def evaluate_test_scenarios_by_llama3(symbol):
    llama3_llm = Ollama(model="llama3")
    evaluate_test_scenarios = f"""
    Give me information about {symbol.upper()} from 2021-01-01 to nowadays.
    """
    results = llama3_llm.invoke(evaluate_test_scenarios)
    return results

# Streamlit app
st.title('Cryptocurrency Historical Data')

# Combobox for selecting cryptocurrency
selected_symbol = st.selectbox('Select Cryptocurrency', list(symbols.keys()))

# Buttons for different sections
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    show_graphic = st.button('Show Graphic')
with col2:
    show_history = st.button('History')
with col3:
    show_fundamental = st.button('Fundamental Analysis')

# Load data based on selected symbol
df = load_data(selected_symbol)

# Combobox for selecting interval
interval = st.selectbox('Select Interval', ['Daily', 'Weekly', 'Monthly'])

# Resample data based on selected interval
resampled_data = resample_data(df, interval)

# Calculate percentage change for 'high' and 'low'
resampled_data['high_change'] = resampled_data['high'].pct_change() * 100
resampled_data['low_change'] = resampled_data['low'].pct_change() * 100

# Apply color formatting
def color_change(val):
    color = 'red' if val < 0 else 'green'
    return f'color: {color}'

# Display content based on button clicked
if show_graphic:
    st.write(f'Graph ({selected_symbol.upper()}, {interval}):')
    # Plot the candlestick chart
    fig = go.Figure(data=[go.Candlestick(
        x=resampled_data['time'],
        open=resampled_data['open'],
        high=resampled_data['high'],
        low=resampled_data['low'],
        close=resampled_data['close'],
        increasing_line_color='green',
        decreasing_line_color='red'
    )])
    fig.update_layout(xaxis_rangeslider_visible=False, title=f"{selected_symbol.upper()} Candlestick Chart")
    st.plotly_chart(fig)

elif show_history:
    st.write(f'Historical Data ({selected_symbol.upper()}, {interval}):')
    st.dataframe(resampled_data[['time', 'high', 'high_change', 'low', 'low_change']].style.applymap(color_change, subset=['high_change', 'low_change']))

elif show_fundamental:
    st.write("Fundamental Analysis:")
    results = evaluate_test_scenarios_by_llama3(selected_symbol)
    st.write(results)
