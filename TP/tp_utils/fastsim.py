
def fastsim_00(prices, signals, init_data):
    """ Trade simulation on full capital
    """
    commission      = init_data['exchange_commission']
    start_capital   = init_data['start_capital']
    buy_correction  = init_data['buy_correction']
    sell_correction = init_data['sell_correction']

    s1 = signals[signals!=0]

    if len(s1) == 0:
        profit = 0
        trades = 0
        profit_to_bnh = 0
    else:
        inds = np.where(signals!=0)
        s2 = s1 + 1
        s3 = np.roll(s2,1)
        s3[0] = 0
        s4 = np.logical_xor(s2,s3)
        inds1  = inds[0][s4]
        trades = int(len(inds1)/2)
        inds2 = inds1[:trades*2]
        correction = np.tile([buy_correction,sell_correction], trades)
        start   = len(prices) - len(signals) 
        prices1 = prices[start:]
        prices2 = prices1[inds2]
        prices3 = prices2 * correction
        powers = np.tile([-1, 1], trades)
        cum_trades  = np.cumprod(np.power(prices3, powers)*(1-commission)) * start_capital

        profit = cum_trades[-1] - start_capital  if len(cum_trades) != 0 else 0
        bnh = prices[-1] / prices[0] * start_capital - start_capital
        profit_to_bnh = round(profit/bnh, 2)
   # return correction
    return [profit,trades,profit_to_bnh]