from bs4 import BeautifulSoup
import aiohttp
import asyncio


class Scraper:
    def __init__(self, _link_to_watch, pause=0):
        self.url = _link_to_watch
        self.pause = pause

    async def check_status(self):
        return False


class Action:
    async def take_action(self, url):
        successful = True
        return successful


class OzoneScraper(Scraper):
    async def check_status(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url) as r:
                html = await r.text(encoding='ISO-8859-1')
                soup = BeautifulSoup(html, "html.parser")
                availability = "out-of-stock" not in soup.find_all("p", class_="availability")[0]['class']
        await asyncio.sleep(self.pause)
        return availability


class ConsoleNotification(Action):
    def __init__(self):
        self.notified = {"product_url": False}

    async def take_action(self, url):
        if not self.notified.get(url):
            print(f'Product now available @ {url}')
            self.notified[url] = True


class ScraperRunner:
    # TODO: add dynamic module (both scrapers and notifications) loading from a json file
    def __init__(self):
        self.__loop = asyncio.get_event_loop()
        self.__scrapers = []
        self.__actions = []

    def mount_scraper(self, s: Scraper):
        self.__scrapers.append(s)

    def mount_action(self, a: Action):
        self.__actions.append(a)

    def check_scrapers(self):
        coroutines = asyncio.gather(*[scraper.check_status() for scraper in self.__scrapers])
        results = self.__loop.run_until_complete(coroutines)
        return [i for (i, successful) in enumerate(results) if successful]

    def take_actions(self, successful_scrapers):
        coro_groups = []
        for scraper_idx in successful_scrapers:
            scraper = self.__scrapers[scraper_idx]
            coro_group = asyncio.gather(*[action.take_action(scraper.url) for action in self.__actions])
            coro_groups.append(coro_group)
        self.__loop.run_until_complete(asyncio.gather(*coro_groups))

    def run(self):
        while True:
            scr_res = self.check_scrapers()
            if scr_res:
                self.take_actions(scr_res)

    def __del__(self):
        self.__loop.close()


if __name__ == "__main__":
    ozs = OzoneScraper("https://www.ozone.bg/product/geyming-slushalki-razer-kraken-x/", pause=5)
    sr = ScraperRunner()
    console_notifier = ConsoleNotification()
    sr.mount_scraper(ozs)
    sr.mount_action(console_notifier)
    sr.run()
