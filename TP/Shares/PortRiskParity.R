library(dplyr)
data_path_crypto = 'G:/Datasets/BT/Binance/USDT'
tf = '6h'

assets = list.files(data_path_crypto, include.dirs = TRUE, recursive = TRUE, pattern = tf, full.names = TRUE)
asset_names = dir(data_path_crypto)


df_ret = data.frame(T = 0, C = 0)
asset_count = 1
for (asset in assets) {
  files = list.files(asset)
  df = read.csv(paste0(asset,'/',files))
  price = df[['C']]
  df$ret = c(0,  diff(price)/price[-length(price)])
  df_ret = full_join(df_ret,df[c('T', 'C')], by ='T')
  colnames(df_ret)[asset_count+2]=asset_names[asset_count]
  asset_count = asset_count + 1
}

df_ret = df_ret[asset_names[-13]]
df_ret = df_ret[-2]

xx <- NaRV.omit(as.matrix(df_ret))
Sigma <- cov(xx)
portfolio.parity <- riskParityPortfolio(Sigma)
portfolio.tangency <- tangencyPortfolio(as.timeSeries(xx), constraints = "LongOnly")
portfolio.weights <- rbind(portfolio.parity$w, getWeights(portfolio.tangency))

row.names(portfolio.weights)<-c("Parity Portfolio", "Tangency Portfolio")
rWindows<-rollingWindows(df_ret, period="12m", by="3m")

df_ret['T'] = as.POSIXct(df_ret[['T']]/1000,origin = '1970-01-01')

df_ret_zoo = read.zoo(df_ret)
as.xts(df_ret_zoo)

as.zoo(df_ret, df_ret$T)
