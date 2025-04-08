
import yfinance as yf
import pandas as pd
import datetime as dt
import requests
from tqdm import tqdm
import warnings

warnings.filterwarnings("ignore")

# Telegram Bot Settings
TELEGRAM_TOKEN = "7798265911:AAHsOWJGVkjsMRAFPi9rRCuIBHZq0URU_uM"
CHAT_ID = "1193294280"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=data)

# Strategy Settings
target_pct = 0.01
sl_pct = 0.005
trail_start = 0.005  # start trailing after 0.5% move
trail_step = 0.002   # move SL up by 0.2% with each gain
max_trades_per_day = 2

# Top 10 Nifty 50 Stocks
nifty_top_10 = {
    "RELIANCE": "RELIANCE.NS",
    "HDFCBANK": "HDFCBANK.NS",
    "ICICIBANK": "ICICIBANK.NS",
    "INFY": "INFY.NS",
    "TCS": "TCS.NS",
    "HINDUNILVR": "HINDUNILVR.NS",
    "ITC": "ITC.NS",
    "BHARTIARTL": "BHARTIARTL.NS",
    "KOTAKBANK": "KOTAKBANK.NS",
    "SBIN": "SBIN.NS"
}

# Date Range
end_date = dt.datetime.now()
start_date = end_date - dt.timedelta(days=59)

results = []

def apply_strategy(df_5m, df_15m, stock):
    df_5m['EMA9'] = df_5m['Close'].ewm(span=9).mean()
    df_5m['EMA20'] = df_5m['Close'].ewm(span=20).mean()
    df_5m['RSI'] = df_5m['Close'].rolling(14).apply(
        lambda x: 100 - (100 / (1 + (x.diff().clip(lower=0).mean() / abs(x.diff().clip(upper=0)).mean()))), raw=False)

    df_5m = df_5m.between_time("09:15", "15:15")
    trades = 0

    for day in df_5m.index.normalize().unique():
        if trades >= max_trades_per_day:
            break

        day_df = df_5m[df_5m.index.normalize() == day]
        or_range = day_df.between_time("09:15", "09:30")
        if or_range.empty: continue
        or_high = or_range['High'].max()
        or_low = or_range['Low'].min()

        day_15m = df_15m[df_15m.index.normalize() == day]
        trend_15m = day_15m['EMA9'].iloc[-1] > day_15m['EMA20'].iloc[-1] if not day_15m.empty else True

        for idx in day_df.index:
            row = day_df.loc[idx]

            if idx.time() <= dt.time(9, 30):
                continue

            if (row['Close'] > or_high and
                row['Volume'] > or_range['Volume'].mean() * 1.5 and
                row['EMA9'] > row['EMA20'] and
                row['RSI'] > 55 and
                trend_15m):

                entry_price = row['Close']
                sl = entry_price * (1 - sl_pct)
                target = entry_price * (1 + target_pct)
                trail_price = entry_price * (1 + trail_start)
                exit_price = entry_price
                outcome = "HOLD"

                send_telegram_message(f"📈 Entry: {stock} at ₹{entry_price:.2f} on {idx.date()}")

                for fut_idx in day_df.loc[idx:].index:
                    fut = day_df.loc[fut_idx]
                    if fut['Low'] <= sl:
                        exit_price = sl
                        outcome = "SL"
                        send_telegram_message(f"❌ SL Hit: {stock} at ₹{sl:.2f}")
                        break
                    elif fut['High'] >= target:
                        exit_price = target
                        outcome = "TARGET"
                        send_telegram_message(f"✅ Target Hit: {stock} at ₹{target:.2f}")
                        break
                    elif fut['High'] >= trail_price:
                        sl = trail_price - (trail_step * entry_price)
                        trail_price += trail_step * entry_price

                pnl = exit_price - entry_price
                results.append({
                    "Date": idx.date(),
                    "Stock": stock,
                    "Entry": entry_price,
                    "Exit": exit_price,
                    "PnL": pnl,
                    "Outcome": outcome
                })
                trades += 1
                if trades >= max_trades_per_day:
                    break

for stock, ticker in tqdm(nifty_top_10.items()):
    df_5m = yf.download(ticker, start=start_date, end=end_date, interval="5m", progress=False)
    df_15m = yf.download(ticker, start=start_date, end=end_date, interval="15m", progress=False)

    if not df_5m.empty and not df_15m.empty:
        df_5m.index = df_5m.index.tz_localize(None)
        df_15m['EMA9'] = df_15m['Close'].ewm(span=9).mean()
        df_15m['EMA20'] = df_15m['Close'].ewm(span=20).mean()
        apply_strategy(df_5m, df_15m, stock)

df = pd.DataFrame(results)
df.to_csv("ORB_Strategy_Advanced_Results.csv", index=False)
print("✅ Strategy backtest completed. Results saved.")
