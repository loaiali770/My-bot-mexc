from storage import *

def handle_trade(symbol, price, score, config):
    balance = get_balance()
    positions = get_positions()

    # خروج
    if symbol in positions:
        entry = positions[symbol]["entry"]
        max_price = positions[symbol]["max"]

        if price > max_price:
            update_max(symbol, price)
            return

        drop = (max_price - price) / max_price

        if drop >= config.TRAILING_STOP:
            profit = (price - entry) / entry
            balance += balance * config.RISK_PER_TRADE * (1 + profit)
            update_balance(balance)
            remove_position(symbol)
            print(f"SELL {symbol} {profit*100:.2f}%")

    # دخول
    else:
        if score >= 75 and balance > 1:
            amount = balance * config.RISK_PER_TRADE
            balance -= amount
            update_balance(balance)
            save_position(symbol, price)
            print(f"BUY {symbol}")
