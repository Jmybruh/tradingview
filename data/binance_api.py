import requests
import pandas as pd
from datetime import datetime

def get_ohlcv(symbol='BTCUSDT', interval='1h', limit=200):
    url = 'https://api.binance.com/api/v3/klines'
    params = {
        'symbol': symbol.upper(),
        'interval': interval,
        'limit': limit
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    df = pd.DataFrame(data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_volume', 'taker_buy_quote_volume', 'ignore'
    ])

    df['Date'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('Date', inplace=True)
    df = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
    df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    return df
