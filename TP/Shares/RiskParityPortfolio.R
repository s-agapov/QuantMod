library(IDPmisc)
library(riskParityPortfolio)
library(fPortfolio)
library(xts)

# load FAANG returns
# data available at https://github.com/souzatharsis/open-quant-live-book
fr.zoo = read.zoo('FAANG.csv', header=TRUE, index.column=1, sep=",")
faang.returns<-as.xts(fr.zoo)

# consider returns from 2018
# omit days with missing data (INF/NA returns)
faang.returns.filtered <- NaRV.omit(as.matrix(faang.returns["2018"]))

# calculate covariance matrix
Sigma <- cov(faang.returns.filtered)


data_path_shares = 'G:/Datasets/Shares'





# compute risk parity portfolio
portfolio.parity <- riskParityPortfolio(Sigma)

# compute tangency portfolio
portfolio.tangency <- tangencyPortfolio(as.timeSeries(faang.returns.filtered), 
                                        constraints = "LongOnly")
portfolio.weights <- rbind(portfolio.parity$w, getWeights(portfolio.tangency))
row.names(portfolio.weights)<-c("Parity Portfolio", "Tangency Portfolio")


faang.returns.xts<-faang.returns["2014-01-01/2019-09-01"]
rWindows<-rollingWindows(faang.returns.xts, period="12m",
                         by="3m")

# Apply FUN to time-series R in the subset [from, to].
ApplyFilter <- function(from, to, R, FUN){
  return(FUN(R[paste0(from, "/", to)]))
}
# For each pair (from, to) ApplyFilter to time-series R using FUN
ApplyRolling <- function(from, to, R, FUN){
  library(purrr)
  return(map2(from, to, ApplyFilter, R=R, FUN=FUN))
}
# Returns weights of a risk parity portfolio from covariance matrix of matrix of returns r
CalculateRiskParity <- function(r){
  library(riskParityPortfolio)
  return(riskParityPortfolio(cov(r))$w)
}
# Given a matrix of returns `r`,
# calculates risk parity weights for each date in `to` considering a time window from `from` and `to` 
RollingRiskParity <- function(from, to, r){
  library(rlist)
  p<-ApplyRolling(from, to, r, CalculateRiskParity)
  names(p)<-to
  return(list.rbind(p))
}

parity.weights<-RollingRiskParity(rWindows$from@Data, rWindows$to@Data, faang.returns.xts)



faang.returns.ts<-as.timeSeries(faang.returns.xts)
Spec = portfolioSpec()

rolling.portfolio.tangency <- rollingTangencyPortfolio(faang.returns.ts,
                                                       constraints = "LongOnly",
                                                       from=rWindows$from,
                                                       to=rWindows$to,
                                                       spec=Spec)

names(rolling.portfolio.tangency)<-rWindows$to
tan.weights <- sapply(rolling.portfolio.tangency,getWeights)
rownames(tan.weights) <- colnames(faang.returns.ts)
tan.weights<-t(tan.weights)

library(PerformanceAnalytics)
tan.returns <- Return.portfolio(faang.returns.xts, weights=tan.weights,verbose=TRUE)
parity.returns <- Return.portfolio(faang.returns.xts, weights=parity.weights,verbose=TRUE)
p.returns<-merge(tan.returns$returns, parity.returns$returns)
names(p.returns)<-c("FAANG Tangency Index", "FAANG Parity Index")

plot(cumsum(p.returns))
