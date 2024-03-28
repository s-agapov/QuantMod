from pybit.unified_trading import HTTP

def get_all_assets_main(session : HTTP):
    """
    Получаю остатки на аккаунте по всем монетам
    :param cl:
    :return: dict
    """
    r = session.get_wallet_balance(accountType="UNIFIED")
    assets = {
        asset.get('coin') : float(asset.get('availableToWithdraw', '0.0'))
        for asset in r.get('result', {}).get('list', [])[0].get('coin', [])
    }
    return assets

def get_all_assets_sub(session, subaccount : str):
    
    memberId = subaccounts[subaccount]
    res = session.get_coins_balance(
        memberId = memberId,
        accountType="UNIFIED")
    
    assets = {asset['coin']:asset['walletBalance']
              for asset in res['result']['balance'] if float(asset['walletBalance'])}
    return assets

def get_all_assets(session, subaccount = None):
    if subaccount is None:
        assets = get_all_assets_main(session)  
    else:
        assets = get_all_assets_sub(session, subaccount)
        
    return assets
        
def get_assets(cl : HTTP, memberId,  coin):
    """
    Получаю остатки на аккаунте по конкретной монете
    :param cl:
    :param coin:
    :return:
    """
    assets = get_all_assets(cl)
    return assets.get(coin, 0.0)

def get_subaccounts_id():
    res = session.get_sub_uid()
    return res['result']['subMemberIds']