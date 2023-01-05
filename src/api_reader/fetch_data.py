import abc
import types
from typing import Tuple

import pydantic
import requests
from importlib.machinery import SourceFileLoader

from api_reader.generate_model import generate_model


class FetchData(abc.ABC):
    def __init__(self, url, results_key, params=None):
        if params is None:
            params = {}
        self.url = url
        self.params = params
        self.results_key = results_key
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

    @abc.abstractmethod
    def name_model(self) -> str:
        pass

    def get_data_units(self):
        status_code, resp = self.fetch_data()
        while True:
            if status_code == 200:
                try:
                    for item in resp.get(self.results_key, []):
                        yield item
                except KeyError:
                    yield resp
                    break
                status_code, resp = self.next_page()
            else:
                break

    def process(self):
        for data in self.get_data_units():
            yield self.datacls(**data)

    def _load_data_class(self):
        # get data
        data = next(self.get_data_units())
        name = self.name_model()
        path, module_name, class_name = generate_model(name, data)
        module = SourceFileLoader(module_name, str(path.absolute())).load_module()
        return getattr(module, class_name)


class UnPaginatedMixin:
    def next_url(self):
        pass

    def next_page(self) -> Tuple[int, dict]:
        return 404, {}


class FetchMeals(UnPaginatedMixin, FetchData):
    def __init__(self, url, params):
        results_key = "meals"
        super(FetchMeals, self).__init__(url, results_key, params)

    def name_model(self):
        return "meal_db"


class FetchDRF(FetchData, abc.ABC):
    def name_model(self):
        return requests.options(self.url).json()['name']


class FetchDRFPaginated(FetchDRF):
    def __init__(self, url, params):
        results_key = "results"
        super(FetchDRFPaginated, self).__init__(url, results_key, params)

    def next_url(self):
        current_page = int(self.params.get("page", 0)) + 1
        self.params["page"] = current_page

    def next_page(self) -> Tuple[int, dict]:
        # update page url
        self.next_url()
        # fetch data
        return self.fetch_data()

