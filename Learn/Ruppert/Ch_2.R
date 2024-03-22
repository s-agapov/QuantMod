data_path = "G:/Datasets/Ruppert"
data_file = "Stock_Bond.csv"
df = read.csv(paste0(data_path,"/",data_file), header = TRUE)
head(df)

n = dim(df)[1]
df["GM_AC"]
attach(df)
GMReturn = GM_AC[-1]/GM_AC[-n] - 1
FReturn = F_AC[-1]/F_AC[-n] - 1
par(mfrow = c(1, 1))
plot(GMReturn,FReturn)
logGM = log(GMReturn + 1)
logF = log(FReturn + 1)

plot(logGM, GMReturn)
cor(logGM, GMReturn)

MSFT_ret = MSFT_AC[-1]/MSFT_AC[-n] - 1
MRK_ret = MRK_AC[-1]/MRK_AC[-n] - 1

plot(MSFT_ret, MRK_ret)
cor(MSFT_ret, MRK_ret)
cor(GMReturn, FReturn)

niter = 1e5
below = rep(0, niter)
above = rep(0, niter)
sells = rep(0, niter)
set.seed(2009)

mu = 0.05
s = 0.23

for (i in 1:niter) {
  r = rnorm(100, mean = mu/253, sd = s/sqrt(253))
  logPrice = log(1e6) + cumsum(r)

  maxlogP = max(logPrice)
  maxDay = which.min(logPrice)
  minlogP = min(logPrice)
  minDay = which.min(logPrice)

  rule1 = minlogP > log(950000)
  rule2 = minlogP < log(950000) & maxlogP > log(1100000)
  
  rule3 = maxDay < minDay
  rule = rule1 | rule2 & rule3
  above[i] = as.numeric((maxlogP > log(1100000)) & rule)
  if (above[i]) {
    sells[i] = maxDay
  }
    
  rule1 = maxlogP < log(1100000)
  rule2 = minlogP < log(950000) & maxlogP > log(1100000)
  rule3 = maxDay > minDay
  rule = rule1 | rule2 & rule3
  
  below[i] = as.numeric((minlogP < log(950000)) & rule)
  if (below[i]) {
    sells[i] = maxDay
  }
  
}

m_s = mean(sells)
m_a = mean(above)
m_b = mean(below)
E = m_a * 100000 + m_b * (-50000)

