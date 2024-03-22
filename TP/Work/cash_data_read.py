import ccxt
from data_provider import cash_data_read

binance = ccxt.binance()
cash_data_read(binance)