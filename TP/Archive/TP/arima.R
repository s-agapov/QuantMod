
# ARIMA -------------------------------------------------------------
library(forecast)
library(microbenchmark)

data_path = '~/Robots/Data/Binance/BTC'
market = 'EOS-BTC'
market_path = paste0(data_path, '/', market)
files = list.files(market_path, recursive = TRUE)
windowLength = 500

for (cur_file in files) {
  timestamp()
  df = read.csv(paste0(market_path,'/', cur_file))
  prices = df[["C"]]
  all_returns = diff(log(prices))
  returns = all_returns
  foreLength = length(returns) - windowLength
  ff <- vector("numeric", length=foreLength+1)
  signals <- vector("numeric", length=foreLength+1)
  pv_all = 0
  for (d in 0:foreLength) {
    returns_offset = returns[(1+d):(windowLength+d)]
    fit_arima = auto.arima(returns_offset)
    xx = Box.test(resid(fit_arima), lag = 20, type="Ljung-Box")
    pv_all = pv_all + xx$p.value
  }
  timestamp()
  print(cur_file)
  print(pv_all / foreLength)
}

 # robot -------------------------------------------------------------------


{ mp = 1
  ns = 100
  capital = 0
  timestamp()
  foreLength = length(returns) - windowLength
  ff <- vector("numeric", length=foreLength+1)
  signals <- vector("numeric", length=foreLength+1)
#  pv_all = 0
  for (d in 0:foreLength) {
    returns_offset = returns[(1+d):(windowLength+d)]
    fit_arima = auto.arima(returns_offset)
#    xx = Box.test(resid(fit_arima), lag = 20, type="Ljung-Box")
#    pv_all = pv_all + xx$p.value
    xx = forecast(fit_arima, h=1)
    ff[d+1]  = xx$mean  
    if (mp == 0 & xx$mean > 0) {
      mp = 1
    }
    if (mp == 1 & xx$mean < 0){ 
      capital = ns * 
      mp = 0
    }
  }
  timestamp()
 # pv_all / foreLength
}

prices[500:510]


