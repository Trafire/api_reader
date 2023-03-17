"""Command-line interface."""
import json
from typing import Optional

import click
import pydantic

from api_reader.fetch_data import FetchData
from api_reader.fetch_data import FetchDRFPaginated


class ApiData(pydantic.BaseModel):
    """API data model."""

    url: str
    params: Optional[dict]
    results_key: str = "results"
    folder: str = "models"


@click.version_option()
@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option("--url", help="URL of API")
@click.option("--params", help="params", default=None)
@click.option(
    "--rk",
    help="Results Key, the key for the list of data in a list result",
    default="results",
)
@click.option(
    "--folder", help="Directory you want the models saved to", default="model"
)
def create_models(url, params, rk, folder):
    api_data = ApiData(
        url=url, params=json.loads(params), results_key=rk, folder=folder
    )
    FetchDRFPaginated(api_data.url, api_data.params, results_key=rk, folder_path=folder)
    
    
def main():
    pass


if __name__ == "__main__":
    cli(prog_name="API Reader")
