import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

ticker = 'AAPL'
start = '2015-01-01'
end = '2023-08-01'

data = yf.download(ticker, start, end)

data['SMA50'] = data["Close"].rolling(50).mean()
data['SMA200'] = data["Close"].rolling(200).mean()

data["Prev SMA50"] = data["SMA50"].shift(1)

data.dropna(inplace=True)

def find_crossovers(fast_sma, prev_fast_sma, slow_sma):
    if fast_sma > slow_sma and prev_fast_sma < slow_sma:
        return 'Bullish Crossover'
    elif fast_sma < slow_sma and prev_fast_sma > slow_sma:
        return 'Bearish Crossover'
    return None

data["crossover"] = np.vectorize(find_crossovers)(data["SMA50"], data["Prev SMA50"], data["SMA200"])

signal = data[data["crossover"] == 'Bullish Crossover'].copy()

# This is mainly boilerplate code to create a Position class and a Strategy class.
# The Strategy class is where the main logic of the strategy is implemented. (i.e. the run method)

class Position:
    def __init__(self, open_datetime, open_price, order_type, volume, sl, tp):
        self.open_datetime = open_datetime
        self.open_price = open_price
        self.order_type = order_type
        self.volume = volume
        self.sl = sl
        self.tp = tp
        self.close_datetime = None
        self.close_price = None
        self.profit = None
        self.status = 'open'
        
    def close_position(self, close_datetime, close_price):
        self.close_datetime = close_datetime
        self.close_price = close_price
        self.profit = (self.close_price - self.open_price) * self.volume if self.order_type == 'buy' \
                                                                        else (self.open_price - self.close_price) * self.volume
        self.status = 'closed'
        
    def _asdict(self):
        return {
            'open_datetime': self.open_datetime,
            'open_price': self.open_price,
            'order_type': self.order_type,
            'volume': self.volume,
            'sl': self.sl,
            'tp': self.tp,
            'close_datetime': self.close_datetime,
            'close_price': self.close_price,
            'profit': self.profit,
            'status': self.status,
        }
        
        
class Strategy:
    def __init__(self, df, starting_balance, volume):
        self.starting_balance = starting_balance
        self.volume = volume
        self.positions = []
        self.data = df
        
    def get_positions_df(self):
        df = pd.DataFrame([position._asdict() for position in self.positions])
        df['pnl'] = df['profit'].cumsum() + self.starting_balance
        return df
        
    def add_position(self, position):
        self.positions.append(position)
        
        return True
        
# This is the main strategy logic.
    def run(self):
        for i, data in self.data.iterrows():
            if data.crossover == 'Bearish Crossover':
                for position in self.positions:
                    if position.status == 'open':
                        position.close_position(data.name, data.Close)
            
            if data.crossover == 'Bullish Crossover':
                self.add_position(Position(data.name, data.Close, 'buy', self.volume, 0, 0))
        
        return self.get_positions_df()
    
sma_crossover_strategy = Strategy(data, 10000, 1)
result = sma_crossover_strategy.run()

# Plotting the PnL
fig, ax1 = plt.subplots(figsize=(10, 6))


ax1.plot(result["close_datetime"], result["pnl"], label="PnL")
ax1.set_xlabel("Date")
ax1.set_ylabel("Value")
ax1.legend()

plt.title("PnL")
plt.grid(True)
plt.show()

# Plotting the SMAs and stock price
fig, ax1 = plt.subplots(figsize=(10, 6))

# Plot the stock price and SMAs
ax1.plot(data.index, data["Close"], label="Stock Price")
ax1.plot(data.index, data["SMA50"], label="SMA50", color="purple")
ax1.plot(data.index, data["SMA200"], label="SMA200", color="orange")
ax1.set_xlabel("Date")
ax1.set_ylabel("Value")
ax1.legend()

# Plot vertical lines for bullish signals
for signal_date in signal.index:
    ax1.axvline(x=signal_date, color='red', linestyle='--', label="Bullish Crossover")

for i, row in result[result['status'] == 'closed'].iterrows():
    if row.profit > 0:
        ax1.plot([row.open_datetime, row.close_datetime], [row.open_price, row.close_price], color="Green", linewidth=3)
    elif row.profit < 0:
        ax1.plot([row.open_datetime, row.close_datetime], [row.open_price, row.close_price], color="Red", linewidth=3)

plt.title("SMAs, Stock Price and Signal")
plt.grid(True)
plt.show()