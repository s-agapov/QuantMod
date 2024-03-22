library(forecast)
market_path = '~/Robots/Data/Binance/BTC/ONT-BTC'
files = list.files(market_path, recursive = TRUE)


fn = 1
df = read.csv(paste0(market_path,'/', files[fn]))
print(files[fn])
prices = df[["C"]]
returns = diff(log(prices))
plot(prices)


plot(returns)
acf(returns, lag.max = 10)


rt.arima <- arima(returns, order=c(11,0,11))
Box.test(resid(rt.arima), lag=20, type="Ljung-Box")

timestamp()
rtfinal.aic <- Inf
rtfinal.order <- c(0,0,0)
for (p in 0:11) for (d in 0:2) for (q in 0:11) {
  rtcurrent.aic <- AIC(arima(returns, order=c(p, d, q)))
   if (rtcurrent.aic < rtfinal.aic) {
    rtfinal.aic <- rtcurrent.aic
    rtfinal.order <- c(p, d, q)
    }
}
rtfinal.arma <- arima(returns, order=rtfinal.order)
rtfinal.order
timestamp()


acf(resid(rtfinal.arma), na.action=na.omit)
Box.test(resid(rtfinal.arma), lag=20, type="Ljung-Box")

timestamp()
fit.arima <- auto.arima(returns, max.p = 12, max.q = 12, stepwise = FALSE, approximation = FALSE, parallel = TRUE, num.cores = 8)
#fit.arima <- auto.arima(returns, stepwise = FALSE, approximation = FALSE, parallel = TRUE)
Box.test(resid(fit.arima), lag=20, type="Ljung-Box")
