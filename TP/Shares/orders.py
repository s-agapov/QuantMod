import json
import os
import argparse
from pathlib import Path
import yaml

from tinkoff.invest import  Client
from tinkoff.invest import OrderDirection, OrderType
from tinkoff.invest.sandbox.client import SandboxClient


import tink_port as tink

with open('settings.yaml') as f:
    # Load YAML data from the file
    config = yaml.load(f, Loader=yaml.FullLoader)

sandbox_account_id = config["sandbox_account"]


parser = argparse.ArgumentParser(
                    prog='Portfolio Rebalance',
                    description='Rebalance Portfolio On Thinkoff API',
                    epilog='')

parser.add_argument('portfolio', choices=['sandbox', 'momentum', 'base']) 



args = parser.parse_args()
if args.portfolio == 'base':
    token = config["base"]
    WorkClient = Client
elif args.portfolio == 'momentum':
    token = config["momentum"]
    WorkClient = Client
elif args.portfolio == 'sandbox':
    token = config["sandbox"]
    WorkClient = SandboxClient

sess = tink.TinkSession(WorkClient, token)
    
accs = sess.get_accounts()
print("Количество аккаунтов:", len(accs.accounts))

print(accs.accounts[0].name)
account_id = accs.accounts[0].id

print("Account id:", account_id)


base = sess.get_id_base()
dfx = base[base["type"] == "shares"]
dfx = dfx[dfx["cur"] == "rub"]
base_ru = dfx.copy()

##---------------------------------------------------------------------Продаем-----------------------------
print("Продаем:")
sell_file = 'rebalance_sell.json'
my_file = Path(sell_file)
if my_file.is_file():
    with open(sell_file) as f:
        rebalance_sell = json.load(f)

    with WorkClient(token) as client:

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

    os.remove(sell_file)

else:
    print("Нет файла с позициями для продажи")

    


    
##----------------------------------- Покупаем------------------------------------------------------------

print()
print("Покупаем")

buy_file = 'rebalance_buy.json'
my_file = Path(buy_file)
if my_file.is_file():
    with open(buy_file) as f:
        rebalance_buy = json.load(f)

    with WorkClient(token) as client:

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

    os.remove(buy_file)
else:
    print("Нет файла с позициями для покупки")    