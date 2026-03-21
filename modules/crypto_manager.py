"""
Crypto manager for Jarvis X
Provides read-only market, mining, and wallet-watch features
"""

from typing import Dict, List
import requests
from utils.config_manager import get_config


config = get_config()


class CryptoManager:
    """Read-only crypto market and wallet monitoring."""

    def __init__(self):
        self.crypto_config = config.get('crypto', {})
        self.api_keys = config.get('advanced.api_keys', {})

    def _reload(self):
        self.crypto_config = config.get('crypto', {})
        self.api_keys = config.get('advanced.api_keys', {})

    def market_overview(self) -> Dict[str, object]:
        """Get a compact market snapshot for tracked coins."""
        tracked = self.crypto_config.get('tracked_coins', ['bitcoin', 'ethereum'])
        ids = ','.join([c.strip().lower() for c in tracked if c.strip()])
        if not ids:
            ids = 'bitcoin,ethereum'

        url = 'https://api.coingecko.com/api/v3/simple/price'
        params = {
            'ids': ids,
            'vs_currencies': 'usd',
            'include_24hr_change': 'true',
            'include_market_cap': 'true'
        }

        try:
            response = requests.get(url, params=params, timeout=20)
            response.raise_for_status()
            data = response.json()
            return {
                'success': True,
                'message': 'Market overview fetched',
                'data': data
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to fetch market overview: {e}'
            }

    def coin_price(self, coin: str) -> Dict[str, object]:
        """Get current USD price and daily change for one coin id/symbol alias."""
        aliases = {
            'btc': 'bitcoin',
            'eth': 'ethereum',
            'sol': 'solana',
            'bnb': 'binancecoin',
            'xrp': 'ripple',
            'ada': 'cardano',
            'doge': 'dogecoin'
        }

        query = (coin or '').strip().lower()
        if not query:
            return {'success': False, 'message': 'No coin provided'}

        coin_id = aliases.get(query, query)
        result = self.market_overview_for_ids([coin_id])
        if not result['success']:
            return result

        payload = result.get('data', {}).get(coin_id)
        if not payload:
            return {'success': False, 'message': f'No market data found for {coin}'}

        return {
            'success': True,
            'message': 'Coin price fetched',
            'coin': coin_id,
            'price_usd': payload.get('usd'),
            'change_24h': payload.get('usd_24h_change'),
            'market_cap': payload.get('usd_market_cap')
        }

    def market_overview_for_ids(self, coin_ids: List[str]) -> Dict[str, object]:
        """Internal helper for coingecko request by explicit ids."""
        ids = ','.join([c.strip().lower() for c in coin_ids if c.strip()])
        if not ids:
            return {'success': False, 'message': 'No coin ids provided'}

        url = 'https://api.coingecko.com/api/v3/simple/price'
        params = {
            'ids': ids,
            'vs_currencies': 'usd',
            'include_24hr_change': 'true',
            'include_market_cap': 'true'
        }

        try:
            response = requests.get(url, params=params, timeout=20)
            response.raise_for_status()
            return {
                'success': True,
                'data': response.json()
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Market request failed: {e}'
            }

    def mining_status(self) -> Dict[str, object]:
        """Get basic mining difficulty/sentiment indicators."""
        result = {
            'success': True,
            'message': 'Mining status fetched',
            'difficulty': {},
            'hashrate': {}
        }

        try:
            # Public BTC difficulty endpoint
            diff_resp = requests.get('https://blockchain.info/q/getdifficulty', timeout=20)
            if diff_resp.status_code == 200:
                result['difficulty']['bitcoin'] = float(diff_resp.text.strip())
        except Exception:
            result['difficulty']['bitcoin'] = None

        try:
            # Simple global market signal as mining profitability proxy
            global_resp = requests.get('https://api.coingecko.com/api/v3/global', timeout=20)
            if global_resp.status_code == 200:
                global_data = global_resp.json().get('data', {})
                result['hashrate']['market_cap_usd'] = global_data.get('total_market_cap', {}).get('usd')
                result['hashrate']['volume_usd'] = global_data.get('total_volume', {}).get('usd')
        except Exception:
            pass

        return result

    def hiveos_status(self) -> Dict[str, object]:
        """Fetch HiveOS farm info if token/farm id are configured."""
        token = self.api_keys.get('hiveos_token', '').strip()
        farm_id = str(self.crypto_config.get('hiveos_farm_id', '')).strip()

        if not token or not farm_id:
            return {
                'success': False,
                'message': 'HiveOS token or farm id is missing in config'
            }

        url = f'https://api2.hiveos.farm/api/v2/farms/{farm_id}'
        headers = {'Authorization': f'Bearer {token}'}

        try:
            response = requests.get(url, headers=headers, timeout=20)
            if response.status_code >= 400:
                return {
                    'success': False,
                    'message': f'HiveOS request failed: HTTP {response.status_code}',
                    'output': response.text[:500]
                }

            data = response.json()
            return {
                'success': True,
                'message': 'HiveOS status fetched',
                'data': data
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'HiveOS request error: {e}'
            }

    def wallet_overview(self) -> Dict[str, object]:
        """Return configured wallet watchlist (read-only, no private keys)."""
        wallets = self.crypto_config.get('wallet_watch', [])
        exchanges = self.crypto_config.get('exchange_watch', [])

        return {
            'success': True,
            'message': 'Wallet watchlist loaded',
            'wallets': wallets,
            'exchanges': exchanges,
            'read_only': not self.crypto_config.get('transaction_control_enabled', False)
        }

    def set_transaction_control(self, enabled: bool) -> Dict[str, object]:
        """Enable/disable transaction control flag in config."""
        ok = config.set('crypto.transaction_control_enabled', bool(enabled), save=True)
        self._reload()
        if not ok:
            return {
                'success': False,
                'message': 'Failed to update transaction control setting'
            }
        return {
            'success': True,
            'message': f"Transaction control {'enabled' if enabled else 'disabled'}",
            'enabled': bool(enabled)
        }

    def transaction_control_status(self) -> Dict[str, object]:
        """Get transaction mode and configured loss-prevention settings."""
        self._reload()
        lp = self.crypto_config.get('loss_prevention', {})
        return {
            'success': True,
            'enabled': bool(self.crypto_config.get('transaction_control_enabled', False)),
            'threshold_usd': float(lp.get('drop_threshold_usd', 5.0)),
            'trade_mode': self.crypto_config.get('trade_mode', 'advisory')
        }

    def evaluate_loss_prevention(self) -> Dict[str, object]:
        """Evaluate tracked positions and suggest action when drop threshold is breached."""
        self._reload()
        positions = self.crypto_config.get('positions', [])
        lp = self.crypto_config.get('loss_prevention', {})
        threshold_usd = float(lp.get('drop_threshold_usd', 5.0))
        threshold_pct = float(lp.get('drop_threshold_percent', 3.0))

        if not positions:
            return {
                'success': False,
                'message': 'No positions configured under crypto.positions'
            }

        alerts = []
        for pos in positions:
            coin = str(pos.get('coin', '')).strip().lower()
            buy_price = float(pos.get('buy_price_usd', 0) or 0)
            quantity = float(pos.get('quantity', 0) or 0)
            if not coin or buy_price <= 0 or quantity <= 0:
                continue

            live = self.coin_price(coin)
            if not live.get('success'):
                alerts.append({
                    'coin': coin,
                    'action': 'error',
                    'reason': live.get('message', 'price lookup failed')
                })
                continue

            current = float(live.get('price_usd') or 0)
            if current <= 0:
                continue

            drop_per_coin = buy_price - current
            drop_total = drop_per_coin * quantity
            drop_pct = (drop_per_coin / buy_price) * 100

            if drop_total >= threshold_usd or drop_pct >= threshold_pct:
                alerts.append({
                    'coin': coin,
                    'buy_price_usd': buy_price,
                    'current_price_usd': current,
                    'quantity': quantity,
                    'drop_total_usd': round(drop_total, 2),
                    'drop_percent': round(drop_pct, 2),
                    'action': 'reduce_or_exit'
                })

        return {
            'success': True,
            'message': 'Loss prevention evaluated',
            'threshold_usd': threshold_usd,
            'threshold_percent': threshold_pct,
            'alerts': alerts
        }

