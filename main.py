import time
import config
from data import get_symbols, get_ohlcv
from strategy import calculate_indicators, get_signal
from execution import handle_trade

def run():
    print("BOT STARTED")

    while True:
        try:
            symbols = get_symbols()

            for symbol in symbols:
                df = get_ohlcv(symbol)
                df = calculate_indicators(df)
                score = get_signal(df)

                price = df.iloc[-1]['c']

                handle_trade(symbol, price, score, config)

        except Exception as e:
            print("ERROR:", e)

        time.sleep(config.LOOP_INTERVAL)

if __name__ == "__main__":
    run()
