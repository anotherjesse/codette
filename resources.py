import json
from jinja2 import Environment, FileSystemLoader
import requests


def generate_datasette_doc(url):
    docs = open("datasette_json.rst").read()

    schema = requests.get(url + ".json").json()
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("datasette.jinja2")

    return {
        "user": "What is the API documentation to use for this datasette?",
        "assistant": template.render(
            url=url,
            docs=docs,
            schema=json.dumps(schema, indent=2),
        ),
    }
