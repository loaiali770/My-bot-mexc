import pandas as pd

def calculate_indicators(df):
    df['ema8'] = df['c'].ewm(span=8).mean()
    df['ema21'] = df['c'].ewm(span=21).mean()

    df['rsi'] = 100 - (100 / (1 + df['c'].pct_change().rolling(14).mean()))

    return df

def get_signal(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    score = 0

    # EMA crossover
    if last['ema8'] > last['ema21'] and prev['ema8'] <= prev['ema21']:
        score += 40

    # RSI
    if last['rsi'] < 30:
        score += 20

    # Momentum
    if last['c'] > prev['c']:
        score += 20

    # Volume spike
    if last['v'] > df['v'].rolling(10).mean().iloc[-1]:
        score += 20

    return score
