import unittest
from portfolio_tools import load_data_for_portfolio

class TestLoadDataForPortfolio(unittest.TestCase):

    def test_load_data_for_portfolio(self):
        tickers = ['AAPL', 'MSFT']
        tf = '1d'
        df = load_data_for_portfolio(tickers, tf)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df.columns), len(tickers))
    
    def test_load_data_for_portfolio_empty(self):
        tickers = ['INVALID']
        tf = '1d'
        df = load_data_for_portfolio(tickers, tf)
        self.assertTrue(df.empty)

    def test_load_data_for_portfolio_verbose(self):
        tickers = ['AAPL', 'MSFT']
        tf = '1d'
        df = load_data_for_portfolio(tickers, tf, verbose=True)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df.columns), len(tickers))

import unittest
from unittest.mock import patch

from portfolio_tools import sell_portfolio

class TestSellPortfolio(unittest.TestCase):

    @patch('portfolio_tools.create_market_sell_order') 
    def test_sell_portfolio_calculate_balance(self, mock_sell_order):
        mock_sell_order.return_value = 10
        portfolio = {'BTC-USD': 2, 'ETH-USD': 3}
        expected_balance = 40

        balance = sell_portfolio({}, portfolio)

        self.assertEqual(expected_balance, balance)

    def test_sell_portfolio_calls_sell_order(self):
        portfolio = {'BTC-USD': 2, 'ETH-USD': 3}
        
        with patch('portfolio_tools.create_market_sell_order') as mock_sell_order:
            sell_portfolio({}, portfolio)
            
            mock_sell_order.assert_any_call({}, 'BTC-USD', 2)
            mock_sell_order.assert_any_call({}, 'ETH-USD', 3)

if __name__ == '__main__':
    unittest.main()
