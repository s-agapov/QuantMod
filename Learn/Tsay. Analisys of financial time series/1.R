library(fBasics)

da=read.table("d-ibm3dx7008.txt",header=T) 
dim(da)
da[1,]
ibm = da[,2]
sibm = ibm*100
basicStats(sibm)

da=read.table("d-3stocks9908.txt",header=T) 
head(da)
da[,2:4] *100
dap = da
dap[,2:4] = dap[,2:4] * 100
dap
basicStats(da)
dalr = log(da[,2:4] + 1)
dalr
basicStats(dalr)
t.test(dalr[,1])


# Ex 2 --------------------------------------------------------------------

da=read.table("m-gm3dx7508.txt",header=T) 
head(da)
da[,2:4] * 100
dap = da
dap[,2:4] = dap[,2:4] * 100
basicStats(dap)
dalr = log(da[,2:4] + 1)
dalr
basicStats(dalr)

t.test(dalr[,3])


# Ex 3 --------------------------------------------------------------------

da=read.table("m-gm3dx7508.txt",header=T) 
sp = da[,4]
prod(sp+1)
sp = ts(da[,4], frequency = 12)
sp_year = aggregate(sp, nfrequency = 1, FUN =function(x) {prod(1+x)} )

exp(mean(log(1+sp_year)))-1


# Ex 4 ------------------------------------------------------------------


