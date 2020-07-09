from ..interact import CurationNavigator


class PyppeteerNavigator(CurationNavigator):
    def __init__(self, page):
        self.page = page

    async def navigate(self, url, auxiliary):
        await self.page.goto(url)
