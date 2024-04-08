import json
import os

from tinkoff.invest import  Client
from tinkoff.invest import OrderDirection, OrderType
from tinkoff.invest.sandbox.client import SandboxClient


import tink_port as tink


BASE = 't.UFRJ8SC9hafVOhFxEUY7yf1wZ1gGhwJp-WCp9o4rnEChHWns0c3jQ21eQwoOW_RurFqeZpss2scJkmMQnomJ9g'
MOMENTUM = 't.24WV5_MMG1bQArK1WPp1_DYWD52f-VfGjpR1ci5Pqf0PJ948zWhDstoO_6d4wXIhFTMVsVJSgOzPElUIPEO4Mw'
SANDBOX = 't.qTfMeDk8iM5GLjIGj5Q5DVSnGdvOmSOzG4r3jQqdkdE2YUJMtFvBNb4v-Tyr50-4rxPBqia2jT-kBsE4NtoiKw'

token = SANDBOX
account_id = "ebed5b2d-8ff8-4ea7-be10-295f78939cf0"

base = tink.get_id_base(token)
dfx = base[base["type"] == "shares"]
dfx = dfx[dfx["cur"] == "rub"]
base_ru = dfx.copy()

##---------------------------------------------------------------------Продаем-----------------------------
print("Продаем:")
with open('rebalance_sell.json') as f:
    rebalance_sell = json.load(f)

with SandboxClient(token) as client:

    for asset in rebalance_sell:
        qty = rebalance_sell[asset]
        print(asset, qty)
        if asset is None:
            continue
            
        figi = tink.ticker_to_figi(asset, base_ru)
        trading_status = client.market_data.get_trading_status(
            figi=figi
        )
        
        if trading_status.market_order_available_flag and trading_status.api_trade_available_flag:
            if qty < 0:
                resp = client.orders.post_order(figi=figi,
                            quantity= -qty,
                            direction=OrderDirection.ORDER_DIRECTION_SELL,
                            account_id=account_id,
                            order_type=OrderType.ORDER_TYPE_MARKET,)

os.remove('rebalance_sell.json')

with open('rebalance_buy.json') as f:
    rebalance_buy = json.load(f)
    
##----------------------------------- Покупаем------------------------------------------------------------
print()
print("Покупаем")
with SandboxClient(token) as client:

    for asset in rebalance_buy:
        qty = rebalance_buy[asset]
        if asset is None:
            continue
            
        figi = tink.ticker_to_figi(asset, base_ru)
        trading_status = client.market_data.get_trading_status(
            figi=figi
        )
        
        if trading_status.market_order_available_flag and trading_status.api_trade_available_flag:
            if qty > 0:
                print(asset, qty)
                resp = client.orders.post_order(figi=figi,
                            quantity= qty,
                            direction=OrderDirection.ORDER_DIRECTION_BUY,
                            account_id=account_id,
                            order_type=OrderType.ORDER_TYPE_MARKET,)

os.remove('rebalance_buy.json')