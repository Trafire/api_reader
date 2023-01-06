import abc
import asyncio
import types
from abc import ABC
from typing import Generator

import aiohttp

from api_reader.fetch_data import FetchData
from api_reader.fetch_data import FetchDRFPaginated


class AsyncFetchMixin(abc.ABC):
    """This Mixin is used to fetch data asynchronously.

    It is finetuned for DRF and will likely need some changes to be used more generally

    """

    def __init__(self, *args, search_size=100, **kwargs):
        self.data = []
        self.search_size = search_size
        self.failed_page = None
        self.datacls = None
        super().__init__(*args, **kwargs)
        assert self.datacls is not None

    @abc.abstractmethod
    async def populate_data(self):
        pass

    def get_async_data_units(self):
        for results in self.data:
            yield from results.get(self.results_key, [])

    def process(self) -> Generator:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.populate_data())
        return (self.datacls(**data) for data in self.get_async_data_units())


class AsyncFetchDRFPaginated(AsyncFetchMixin, FetchDRFPaginated):
    async def get_page(self, session, page):
        if self.failed_page is not None and page > self.failed_page:
            return None
        params = self.params
        params["page"] = page
        async with session.get(self.url, params=params) as response:
            if response.status == 200:
                return await response.json()
            else:
                if self.failed_page is None:
                    self.failed_page = page
                else:
                    self.failed_page = min(self.failed_page, page)
                return None

    async def populate_data(self) -> None:
        """Populates self.data"""
        async with aiohttp.ClientSession() as session:
            i = self.params.get("page", 1)
            while self.failed_page is None:
                tasks = []
                for page in range(i, i + self.search_size):
                    task = asyncio.ensure_future(self.get_page(session, page))
                    tasks.append(task)
                # Process the results as they are completed
                for completed in asyncio.as_completed(tasks):
                    result = await completed
                    if result is not None:
                        self.data.append(result)
                i += self.search_size


url = "https://c18c9qanx7.execute-api.ca-central-1.amazonaws.com/master/option/"
a = AsyncFetchDRFPaginated(url, params={"page": 1})
process = a.process()
for p in process:
    print(p)
