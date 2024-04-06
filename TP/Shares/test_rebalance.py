from unittest import TestCase


class Test(TestCase):
    def test_calculate_portfolio_difference(self):
        self.fail()
class TestCalculatePortfolioDifference(TestCase):

    def test_empty_portfolios(self):
        old_portfolio = {}
        new_portfolio = {}
        expected = {}
        actual = calculate_portfolio_difference(old_portfolio, new_portfolio)
        self.assertEqual(expected, actual)

    def test_no_overlap(self):
        old_portfolio = {'AAPL': 100, 'MSFT': 50}
        new_portfolio = {'TSLA': 75, 'GOOG': 25}
        expected = {'AAPL': -100, 'MSFT': -50, 'TSLA': 75, 'GOOG': 25}
        actual = calculate_portfolio_difference(old_portfolio, new_portfolio)
        self.assertEqual(expected, actual)
    
    def test_partial_overlap(self):
        old_portfolio = {'AAPL': 100, 'MSFT': 50, 'TSLA': 20}
        new_portfolio = {'AAPL': 80, 'GOOG': 30, 'TSLA': 40}
        expected = {'AAPL': -20, 'MSFT': -50, 'GOOG': 30, 'TSLA': 20}
        actual = calculate_portfolio_difference(old_portfolio, new_portfolio)
        self.assertEqual(expected, actual)

    def test_same_tickers(self):
        old_portfolio = {'AAPL': 100, 'MSFT': 50}
        new_portfolio = {'AAPL': 80, 'MSFT': 70}
        expected = {'AAPL': -20, 'MSFT': 20}
        actual = calculate_portfolio_difference(old_portfolio, new_portfolio)
        self.assertEqual(expected, actual)

    def test_sorting(self):
        old_portfolio = {'AAPL': 100, 'MSFT': 50}
        new_portfolio = {'AAPL': 80, 'MSFT': 70, 'GOOG': 20}
        expected = [('MSFT', 20), ('GOOG', 20), ('AAPL', -20)]
        actual = calculate_portfolio_difference(old_portfolio, new_portfolio)
        self.assertEqual(expected, actual)

