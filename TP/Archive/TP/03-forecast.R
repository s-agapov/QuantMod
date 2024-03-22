library(fpp2)
library(prophet)
library(forecast)

data_path = '~/Robots/Data/Binance/BTC'
market_path = paste0(data_path, '/','BNB-BTC')
files = list.files(market_path, recursive = TRUE)

{fn = 4
print(files[fn])
df = read.csv(paste0(market_path,'/', files[fn]))

prices = df[["C"]]
returns = c(0,diff(log(prices)))
t_data = ts(returns, frequency = 1)

train_part = 0.8
train = round(train_part * length(t_data))
train_ts = window(t_data, 1, train)
test_ts =  window(t_data, train + 1)
}



ggAcf(train_ts)

# benchmarks --------------------------------------------------------------
fit1 <- meanf(train_ts, h=1)
fit2 <- rwf(train_ts,   h=1)
fit3 <- rwf(train_ts,   h=1, drift = TRUE)
accuracy(fit1, test_ts)
accuracy(fit2, test_ts)
accuracy(fit3, test_ts)

#cross-validation----------------------------------------------------------
tsx = ts(1:1000, frequency = 1)
tsx = test_ts
{timestamp()
e0 = tsCV(tsx, forecast, h = 1)
rmse0 = sqrt(mean(e0^2, na.rm=TRUE))
timestamp()}

e1 <- tsCV(tsx, meanf, h=1)
rmse1 = sqrt(mean(e1^2, na.rm=TRUE))

e2 <- tsCV(tsx, rwf, h=1)
rmse2 = sqrt(mean(e2^2, na.rm=TRUE))

e3 <- tsCV(tsx, rwf, drift=TRUE, h=1)
rmse3 = sqrt(mean(e3^2, na.rm=TRUE))

# prophet------------------------------------------------------------------
xx = cbind(as.POSIXct(df[,1]/1000, origin="1970-01-01"), df["C"])
names(xx) = c("ds", "y")
m = prophet(xx)
future <- make_future_dataframe(m, periods = 10)
forecast <- predict(m, future)
tail(forecast[c('ds', 'yhat', 'yhat_lower', 'yhat_upper')],15)

# robot -------------------------------------------------------------------
win = 2
pred_signals = function(ind) {
  pred = rwf(train_ts[1:ind],1)
  signal = sign(pred$mean)
  return(signal)
}

start = win
signals = sapply(start:length(prices), pred_signals)

# backtest ----------------------------------------------------------------
{
market_position = 0         
commission      = 0.0005
start_capital   = 0.1
buy_correction  = 1.004
sell_correction = 0.996

cur_capital   = start_capital 
shares_amount = 0
trade_profit  = 0
cum_profit    = 0

xx = length(prices) - length(signals)
signals = c(rep(0,xx), signals)
trade_statistics = data.frame()}

for (i in seq_along(signals)){
  if (market_position == 0 & signals[i] == 1) {
        price = prices[i] * buy_correction   
        shares_amount = cur_capital * (1-commission)/price  
        trade_profit  = -cur_capital
        cur_capital  = 0
        market_position = 1 
    } else if (market_position == 1 & signals[i] == -1) { 
        price = prices[i] * sell_correction
        cur_capital  = (shares_amount * price)*(1-commission)
        trade_profit = trade_profit + cur_capital
        cum_profit  =  cum_profit + trade_profit
        shares_amount   = 0
        market_position = 0
    } else {
        signals[i] = 0
    }
  trade_statistics = rbind(trade_statistics,c(prices[i], signals[i], market_position, cur_capital, shares_amount, trade_profit, cum_profit))                
}
names(trade_statistics) = c("price", "signal","market_position","cur_capital", "shares_amount", "trade_profit", "cum_profit")

# trade statistics --------------------------------------------------------
tail(trade_statistics,1)



