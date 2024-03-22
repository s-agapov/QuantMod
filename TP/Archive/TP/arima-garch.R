
# ARIMA-GARCH -------------------------------------------------------------
library(timeSeries)
library(rugarch)
library(zoo)

data_path = '~/Robots/Data/Binance/BTC'
market = 'EOS-BTC'
market_path = paste0(data_path, '/', market)
files = list.files(market_path, recursive = TRUE)
df = read.csv(paste0(market_path,'/', files[1]))
prices = df[["C"]]
all_returns = diff(log(prices))
returns = all_returns[1:600]
returns[as.character(head(index(prices),1))] = 0

windowLength = 500
foreLength = length(returns) - windowLength
forecasts <- vector(mode="character", length=foreLength)
for (d in 0:foreLength) {
  timestamp()
  returnsOffset = returns[(1+d):(windowLength+d)]
  final.aic <- Inf
  final.order <- c(0,0,0)
  for (p in 0:5) for (q in 0:5) {
    if ( p == 0 && q == 0) {
      next
    }
    arimaFit = tryCatch( arima(returnsOffset, order=c(p, 0, q)),
                         error=function( err ) FALSE,
                         warning=function( err ) FALSE )
    if( !is.logical( arimaFit ) ) {
      current.aic <- AIC(arimaFit)
      if (current.aic < final.aic) {
        final.aic <- current.aic
        final.order <- c(p, 0, q)
        final.arima <- arima(returnsOffset, order=final.order)
      }
    } else {
      next
    }
  }
  
  # Specify and fit the GARCH model
  spec = ugarchspec(
    variance.model=list(garchOrder=c(1,1)),
    mean.model=list(armaOrder=c(
      final.order[1], final.order[3]
    ), include.mean=T),
    distribution.model="sged"
  )
  fit = tryCatch(
    ugarchfit(
      spec, returnsOffset, solver = 'hybrid'
    ), error=function(e) e, warning=function(w) w
  )
  
  # If the GARCH model does not converge, set the direction to "long" else
  # choose the correct forecast direction based on the returns prediction
  # Output the results to the screen and the forecasts vector
  if(is(fit, "warning")) {
    forecasts[d+1] = paste(
      index(returnsOffset[windowLength]), 1, sep=","
    )
    print(paste(d, index(returnsOffset[windowLength]), 1, sep=","))
    
  } else {
    fore = ugarchforecast(fit, n.ahead=1)
    ind = fore@forecast$seriesFor
    forecasts[d+1] = paste(
      colnames(ind), ifelse(ind[1] < 0, -1, 1), sep=","
    )
    print(paste(colnames(ind), ifelse(ind[1] < 0, -1, 1), sep=","))
  }
}

# Output the CSV file to "forecasts.csv"
write.csv(forecasts, file="forecasts.csv", row.names=FALSE)
# Input the Python-refined CSV file AFTER CONVERSION
spArimaGarch = as.xts(
  read.zoo(
    file="forecasts_new.csv", format="%Y-%m-%d", header=F, sep=","
  )
)
# Create the ARIMA+GARCH returns
spIntersect = merge(  spArimaGarch[,1], returns, all=F )
spArimaGarchReturns = spIntersect[,1] * spIntersect[,2]
# Create the backtests for ARIMA+GARCH and Buy & Hold
spArimaGarchCurve = log( cumprod( 1 + spArimaGarchReturns ) )
spBuyHoldCurve = log( cumprod( 1 + spIntersect[,2] ) )
spCombinedCurve = merge( spArimaGarchCurve, spBuyHoldCurve, all=F )
# Plot the equity curves
xyplot(
  spCombinedCurve,
  superpose=T,
  col=c("darkred", "darkblue"),
  lwd=2,
  key=list(
    text=list(
      c("ARIMA+GARCH", "Buy & Hold")
    ),
    lines=list(
      lwd=2, col=c("darkred", "darkblue")
    )
  )
)