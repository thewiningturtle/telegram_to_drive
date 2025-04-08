
import yfinance as yf
import pandas as pd
import datetime as dt
from tqdm import tqdm
import matplotlib.pyplot as plt
import pytz
import warnings

warnings.filterwarnings("ignore")

# Define Top 10 Nifty 50 Stocks (Yahoo Tickers)
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

# Strategy Parameters
target_pct = 0.01
stop_loss_pct = 0.005

# Define date range for 5-min data (max ~60 days)
end_date = dt.datetime.now()
start_date = end_date - dt.timedelta(days=59)

# Store results
all_results = []

def apply_orb_strategy(df, stock_name):
    df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['RSI'] = df['Close'].rolling(14).apply(
        lambda x: 100 - (100 / (1 + (x.diff().clip(lower=0).mean() / abs(x.diff().clip(upper=0)).mean()))), raw=False)

    df = df.between_time("09:15", "15:15")

    for day in df.index.normalize().unique():
        day_df = df[df.index.normalize() == day]
        if len(day_df) == 0:
            continue

        or_range = day_df.between_time("09:15", "09:30")
        if or_range.empty:
            continue
        or_high = or_range['High'].max()
        or_low = or_range['Low'].min()

        for idx, row in day_df.iterrows():
            if idx.time() <= dt.time(9, 30):
                continue

            # Long entry condition
            if (row['Close'] > or_high and
                row['Volume'] > or_range['Volume'].mean() * 1.5 and
                row['EMA9'] > row['EMA20'] and
                row['RSI'] > 55):

                entry_price = row['Close']
                sl = entry_price * (1 - stop_loss_pct)
                target = entry_price * (1 + target_pct)
                outcome = "HOLD"
                exit_price = entry_price

                for _, future_row in day_df.loc[idx:].iterrows():
                    if future_row['Low'] <= sl:
                        exit_price = sl
                        outcome = "SL"
                        break
                    elif future_row['High'] >= target:
                        exit_price = target
                        outcome = "TARGET"
                        break
                else:
                    exit_price = day_df.iloc[-1]['Close']
                    outcome = "TIME_EXIT"

                pnl = exit_price - entry_price
                all_results.append({
                    'Date': day,
                    'Stock': stock_name,
                    'Entry Price': entry_price,
                    'Exit Price': exit_price,
                    'PnL': pnl,
                    'Outcome': outcome
                })
                break  # One trade per day

for stock, ticker in tqdm(nifty_top_10.items()):
    df = yf.download(ticker, start=start_date, end=end_date, interval='5m', progress=False)
    if not df.empty:
        df.index = df.index.tz_convert('Asia/Kolkata') if df.index.tzinfo else df.index.tz_localize('Asia/Kolkata')
        apply_orb_strategy(df, stock)

# Create final DataFrame
result_df = pd.DataFrame(all_results)
result_df.to_csv("ORB_Backtest_Results.csv", index=False)
print("Backtest completed. Results saved to ORB_Backtest_Results.csv.")
