import pandas as pd
import tink_port as tink

from tinkoff.invest import CandleInterval, Client
from tinkoff.invest.utils import now

ETF = 't.6nHltT1dYSfrVTIV9zF72fxDlB2sXJbRD6iJNpZXTFAN61rmD7m71xPp9ko12ta1JxA06em4YdN36xicnBmjWg'


if __name__ == "__main__":
    token = ETF
    
    base = tink.get_id_base(token)
    dfx = base[base["type"] == "shares"]
    dfx = dfx[dfx["cur"] == "rub"]
    base_ru = dfx.copy()

    res = []
    for ind, pos in base_ru.iterrows():
        candles = tink.get_candles(token, pos.figi, CandleInterval.CANDLE_INTERVAL_DAY, now(),  50)
        df =  tink.get_open_price(candles)
        ticker = tink.figi_to_ticker(pos.figi, base)
        
        if ticker == None:
            ticker = pos.figi
        df.columns = [ticker]
        res.append(df)
        
    df_full = pd.concat(res, axis = 1)
