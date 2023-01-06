import abc
import types
from importlib.machinery import SourceFileLoader
from typing import Tuple, Generator

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
                yield from resp.get(self.results_key, [resp])
                if self.is_instance:
                    break
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
    def __init__(self, url, results_key, params=None, folder_path="models", name_model=None):
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


class FetchMeals(UnPaginatedMixin, FetchData):
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

    def is_instance(self) -> bool:
        return self.name_model.endswith("Instance")


class FetchDRFPaginated(FetchDRF):
    def __init__(self, url, params, *args, **kwargs):
        results_key = "results"
        if 'results_key' in kwargs:
            del kwargs['results_key']
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


if __name__ == "__main__":
    # url = "https://www.themealdb.com/api/json/v1/1/search.php"
    url = "https://c18c9qanx7.execute-api.ca-central-1.amazonaws.com/master/category/"
    params = {"page": 1}
    c = FetchDRFPaginated(url, params=params)
    for i in c.process():
        print(i)
