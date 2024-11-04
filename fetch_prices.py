import signal
from collections import deque
import aiohttp
import asyncio

class CryptoPrices:
    _CRYPTO_NAMES = ["BTC", "ETH"]
    interval_ = 10  # как часто отправляем запросы (сек)
    def __init__(self) -> None:
        self.crypt: dict[str, deque[float]] = {}
        for name in CryptoPrices._CRYPTO_NAMES:
            self.crypt[name] = deque(maxlen=(24 * 60 * 60 // CryptoPrices.interval_))
        self.update_task = None  # Task для периодического обновления

    async def _get_crypto_price(self, currency_from, currency_to):
        url = f'https://api.coinbase.com/v2/prices/{currency_from}-{currency_to}/spot'
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        price = float(data["data"]["amount"])
                        self.crypt[currency_from].append(price)
                    else:
                        print(f"Error fetching price for {currency_from}: HTTP {response.status}")
        except aiohttp.ClientError as e:
            print(f"Request error for {currency_from}: {e}")
        except (asyncio.TimeoutError, ValueError) as e:
            print(f"Error processing data for {currency_from}: {e}")

    async def update_exchange_rate(self):
        tasks = [self._get_crypto_price(currency, "USD") for currency in CryptoPrices._CRYPTO_NAMES]
        await asyncio.gather(*tasks) 

    async def start_periodic_update(self, interval: int): #Метод для периодического обновления курсов валют.
        try:
            while True:
                await self.update_exchange_rate()  # Обновляем курсы валют
                await asyncio.sleep(interval)      # Ждем заданный интервал
        except asyncio.CancelledError:
            print("Периодическое обновление остановлено")

    def start(self, interval: int = interval_):
        loop = asyncio.get_event_loop()
        self.update_task = loop.create_task(self.start_periodic_update(interval))

    def stop(self):
        if self.update_task:
            self.update_task.cancel()
