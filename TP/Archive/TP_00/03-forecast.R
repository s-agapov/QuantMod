library(forecast)
library(quantmod)

data_path = "G:/Code/Projects/Quant Mod/Robots/Data/USD/BTC-USDT/1h"
files = list.files(data_path)

fn = paste0(data_path,'/',files[length(files)])

df = read.csv(fn)
prices = df$C

fh = 3
train = prices[1:(length(prices)-fh)]
market_position = 0

fit2 = rwf(train[1:ind], h = fh, drift=TRUE)
accuracy(fit1)
lambda <- BoxCox.lambda(prices) 
plot(BoxCox(prices,lambda))
plot(prices)

fit1 = rwf(prices[1:8], h = fh, drift = TRUE)
fit1
pred = fit1$fitted #[1:length(prices)]
pred
lp = Lag(prices)
lp[1:7]
pred[1:7]
signals = as.numeric(pred > lp)
signals
lp[1:10]
pred[1:10]
rwf(prices, drift = TRUE)