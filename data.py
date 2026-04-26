import ccxt
import pandas as pd

exchange = ccxt.mexc({
    "enableRateLimit": True
})

def get_symbols():
    tickers = exchange.fetch_tickers()
    symbols = []

    for s, t in tickers.items():
        if "/USDT" in s and t.get("last") and t["last"] <= 0.001:
            if t.get("quoteVolume", 0) > 10000:
                symbols.append(s)

    return symbols[:20]

def get_ohlcv(symbol):
    bars = exchange.fetch_ohlcv(symbol, timeframe="1m", limit=50)
    df = pd.DataFrame(bars, columns=['ts','o','h','l','c','v'])
    return df
