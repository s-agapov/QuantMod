import unittest

from bybit import get_all_assets_main

class TestGetAllAssetsMain(unittest.TestCase):

    def test_get_all_assets_main_returns_dict(self):
        session = MockSession()
        assets = get_all_assets_main(session)
        self.assertIsInstance(assets, dict)

    def test_get_all_assets_main_returns_correct_keys(self):
        session = MockSession()
        assets = get_all_assets_main(session)
        self.assertIn('BTC', assets)
        self.assertIn('ETH', assets)

    def test_get_all_assets_main_returns_float_values(self):
        session = MockSession()
        assets = get_all_assets_main(session)
        for value in assets.values():
            self.assertIsInstance(value, float)

class MockSession:
    def get_wallet_balance(self, accountType):
        return {'result': {'list': [{'coin': [{'availableToWithdraw': '1.5', 'coin': 'BTC'}, {'availableToWithdraw': '2.5', 'coin': 'ETH'}]}]}}
