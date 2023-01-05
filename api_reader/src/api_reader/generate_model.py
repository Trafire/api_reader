import json
from pathlib import Path

import requests
from genson import SchemaBuilder
from datamodel_code_generator import InputFileType, generate


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
    return text.replace('_', ' ').title().replace(' ', '_').lower()


def generate_model(model_name, data):
    path = Path(f"models/{convert_to_snake_case(model_name)}.py")
    path.parents[0].mkdir(parents=True, exist_ok=True)
    class_name = convert_to_class_capitalization(model_name)
    if not path.exists():
        json_schema = json.dumps(generate_schema(data))

        generate(
            json_schema,
            class_name=class_name,
            input_file_type=InputFileType.JsonSchema,
            output=path)
    return path,convert_to_snake_case(model_name),class_name


def gen_from_url(url):
    name = requests.options(url).json()['name']
    generate_model(name, requests.get(url).json())
