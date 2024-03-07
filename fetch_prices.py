from collections import deque
import aiohttp
import asyncio


class CryptoPrices():
    _CRYPTO_NAMES = ["BTC", "ETH" ]

    def __init__(self) -> None:
        self.crypt: dict[str: deque[float]] = {}
        for name in CryptoPrices._CRYPTO_NAMES:
            self.crypt[name] = deque(maxlen = 5760)


    def update_exchange_rate(self):
        loop = asyncio.get_event_loop()
        tasks = [self._get_crypto_price(currency, "USD") for currency in CryptoPrices._CRYPTO_NAMES]
        loop.run_until_complete(asyncio.wait(tasks))
    

    async def _get_crypto_price(self, currency_from, currency_to):
        url = f'https://api.coinbase.com/v2/prices/{currency_from}-{currency_to}/spot'
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
                price = float(data["data"]["amount"])
                self.crypt[currency_from].append(price)
