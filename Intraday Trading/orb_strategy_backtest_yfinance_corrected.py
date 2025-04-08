
import yfinance as yf
import pandas as pd
import datetime as dt
from tqdm import tqdm
import matplotlib.pyplot as plt
import seaborn as sns
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

        for idx in day_df.index:
            row = day_df.loc[idx]

            if idx.time() <= dt.time(9, 30):
                continue

            if (
                float(row['Close']) > or_high and
                float(row['Volume']) > or_range['Volume'].mean() * 1.5 and
                float(row['EMA9']) > float(row['EMA20']) and
                float(row['RSI']) > 55
            ):
                entry_price = row['Close']
                sl = entry_price * (1 - stop_loss_pct)
                target = entry_price * (1 + target_pct)
                outcome = "HOLD"
                exit_price = entry_price

                for future_idx in day_df.loc[idx:].index:
                    future_row = day_df.loc[future_idx]
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

# --- Metrics & Charts ---
if not result_df.empty:
    result_df['Date'] = pd.to_datetime(result_df['Date'])
    result_df.sort_values('Date', inplace=True)
    result_df['Cumulative PnL'] = result_df['PnL'].cumsum()

    # Metrics Summary
    wins = result_df[result_df['PnL'] > 0]
    losses = result_df[result_df['PnL'] <= 0]
    total_trades = len(result_df)

    print("\nPerformance Summary:")
    print("Total Trades:", total_trades)
    print("Winning Trades:", len(wins))
    print("Losing Trades:", len(losses))
    print("Win Rate (%):", round(len(wins) / total_trades * 100, 2) if total_trades > 0 else 0)
    print("Average PnL:", round(result_df['PnL'].mean(), 2))
    print("Total PnL:", round(result_df['PnL'].sum(), 2))
    print("Profit Factor:", round(wins['PnL'].sum() / abs(losses['PnL'].sum()), 2) if not losses.empty else "inf")

    # Save Charts
    result_df.plot(x='Date', y='Cumulative PnL', title='Cumulative PnL Over Time', figsize=(10, 5), grid=True)
    plt.tight_layout()
    plt.savefig("cumulative_pnl_chart.png")

    sns.histplot(result_df['PnL'], bins=30, kde=True)
    plt.title("PnL Distribution")
    plt.tight_layout()
    plt.savefig("pnl_distribution_chart.png")
