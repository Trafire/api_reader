import json
import os.path
from pathlib import Path

import requests
from datamodel_code_generator import InputFileType
from datamodel_code_generator import generate
from genson import SchemaBuilder


def generate_schema(data: dict) -> dict:
    """Generate schema from provided data."""
    schema_builder = SchemaBuilder()
    schema_builder.add_object(data)
    return schema_builder.to_schema()


def convert_to_class_capitalization(text):
    text = text.title()
    text = text.replace("_", "")
    text = text.replace(" ", "")
    return text


def convert_to_snake_case(text):
    return text.replace("_", " ").title().replace(" ", "_").lower()


def generate_model(model_name, data, folder="models/"):
    filename = os.path.join(folder, f"{convert_to_snake_case(model_name)}.py")
    path = Path(filename)
    path.parents[0].mkdir(parents=True, exist_ok=True)
    class_name = convert_to_class_capitalization(model_name)
    if not path.exists():
        json_schema = json.dumps(generate_schema(data))

        generate(
            json_schema,
            class_name=class_name,
            input_file_type=InputFileType.JsonSchema,
            output=path,
            force_optional_for_required_fields=True,
        )
    return path, convert_to_snake_case(model_name), class_name


def gen_from_url(url):
    name = requests.options(url).json()["name"]
    generate_model(name, requests.get(url).json())
