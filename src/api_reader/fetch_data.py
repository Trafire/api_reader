import abc
import asyncio
import concurrent.futures
import math
import sys
import types
from importlib.machinery import SourceFileLoader
from typing import Generator
from typing import Tuple

import aiohttp
import pydantic
import requests

from api_reader.generate_model import generate_model


class FetchData(abc.ABC):
    def __init__(self, url, results_key, params=None, folder_path="models"):
        self.folder_path = folder_path
        if params is None:
            params = {}
        self.url = url
        self.params = params
        self.results_key = results_key
        self._name_model = None
        try:
            self.datacls = self._load_data_class()
        except TypeError:
            raise Exception("No Data Found")

    @abc.abstractmethod
    def next_page(self):
        pass

    @abc.abstractmethod
    def next_url(self):
        pass

    def fetch_data(self) -> Tuple[int, dict]:
        resp = requests.get(self.url, params=self.params)
        return resp.status_code, resp.json()

    @property
    @abc.abstractmethod
    def name_model(self) -> str:
        pass

    @property
    def is_instance(self) -> bool:
        pass

    def get_data_units(self) -> Generator:
        status_code, resp = self.fetch_data()
        while True:
            if status_code == 200:
                if self.is_instance:
                    yield resp
                    break
                yield from resp.get(self.results_key, [resp])

                status_code, resp = self.next_page()
            else:
                break
            if self.is_instance:
                break

    def process(self):
        for data in self.get_data_units():
            yield self.datacls(**data)

    def _load_data_class(self):
        # get data
        data = next(self.get_data_units())
        name = self.name_model
        path, module_name, class_name = generate_model(name, data, self.folder_path)
        module = SourceFileLoader(module_name, str(path.absolute())).load_module()
        return getattr(module, class_name)


class GenericCreateModel(FetchData):
    def __init__(
            self, url, results_key, params=None, folder_path="models", name_model=None
    ):
        assert isinstance(name_model, str)
        self.folder_path = folder_path
        if params is None:
            params = {}
        self.url = url
        self.params = params
        self.results_key = results_key
        self._name_model = name_model
        try:
            self.datacls = self._load_data_class()
        except TypeError:
            raise Exception("No Data Found")

    @property
    def name_model(self) -> str:
        return self._name_model


class UnPaginatedMixin:
    def next_url(self):
        pass

    def next_page(self) -> Tuple[int, dict]:
        return 404, {}


class GenericUnpaginated(UnPaginatedMixin, FetchData):
    def __init__(self, url, params, *args, **kwargs):
        results_key = "meals"
        super().__init__(url, results_key, params, *args, **kwargs)

    @property
    def name_model(self):
        if self._name_model is None:
            self._name_model = "Meal"


class FetchDRF(FetchData, abc.ABC):
    @property
    def name_model(self):
        if self._name_model is None:
            self._name_model = requests.options(self.url).json()["name"]
        return self._name_model

    @property
    def is_instance(self) -> bool:
        return self.name_model.endswith("Instance")


class FetchDRFPaginated(FetchDRF):
    def __init__(self, url, params, *args, **kwargs):
        results_key = "results"
        if "results_key" in kwargs:
            del kwargs["results_key"]
        super().__init__(url, results_key, params, *args, **kwargs)

    def next_url(self):
        if not self.name_model.endswith("Instance"):
            current_page = int(self.params.get("page", 0)) + 1
            self.params["page"] = current_page

    def next_page(self) -> Tuple[int, dict]:
        # update page url
        self.next_url()
        # fetch data
        return self.fetch_data()

    @property
    def total_num_pages(self):
        return math.ceil(self.fetch_data()[1]["count"] / 10)

    async def async_process_data_unit(self, data_unit):
        return self.datacls(**data_unit)

    async def async_fetch_data(self, params) -> Tuple[int, dict]:
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url, params=params) as resp:
                return resp.status, await resp.json()

    async def async_get_data_units(self):
        urls = [{"page": page_num} for page_num in range(1, self.total_num_pages + 1)]
        tasks = [asyncio.create_task(self.async_fetch_data(url)) for url in urls]
        results = await asyncio.gather(*tasks)
        for status, resp in results:
            data_units = resp.get(self.results_key, [resp])
            for row in (self.async_process_data_unit(data) for data in data_units):
                yield await row

    #     status_code, resp = self.fetch_data()
    #     tasks = []
    #     while True:

    # while True:
    #     if status_code == 200:
    #         data_units = resp.get(self.results_key, [resp])
    #         tasks.extend([asyncio.create_task(self.async_process_data_unit(data)) for data in data_units])
    #         if self.is_instance:
    #             break
    #         status_code, resp = self.next_page()
    #     else:
    #         break
    #     if self.is_instance:
    #         break
    # data = await asyncio.gather(*tasks)
    # for d in data:
    #     yield d

    async def async_process(self):
        async for data in self.async_get_data_units():
            yield data


class BuilderJson(FetchDRF):
    def next_page(self):
        pass

    def next_url(self):
        pass

    def __init__(self, url, params, *args, **kwargs):
        super().__init__(url, None, params, *args, **kwargs)

    @property
    def name_model(self):
        return "BuilderJson"

    def get_data_units(self) -> Generator:
        status_code, resp = self.fetch_data()

        if status_code == 200:
            to_process = [resp]
            processed = []
            while to_process:
                data = to_process.pop()
                if isinstance(data, list):
                    nodes = data
                else:
                    nodes = [data]
                for node in nodes:
                    if node not in processed:
                        if "values" in node:
                            for r in node["values"]:
                                to_process.append(r)

                        if "children" in node:
                            for r in node["children"]:
                                to_process.append(r)
                        print(node)
                        yield node

                # yield row
                # if "values" in row:
                #     for r in row['values']:
                #         print(123, r)
                #         yield r
                # if "children" in row:
                #     for r in row['children']:
                #         print(123, r)
                #         yield r
