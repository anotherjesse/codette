import json
from jinja2 import Environment, FileSystemLoader
import requests
from claudette import Chat
import data
import traceback


def get_datasette_schema(url):
    url += ".json"
    return requests.get(url).json()


def generate_content(project, uuid):
    try:
        metadata = data.read(project, uuid, kind="generation", mode="metadata")
        schema = get_datasette_schema(metadata["url"])
        docs = open("json.rst").read()
        model = "claude-3-5-sonnet-20240620"
        prefill = """<html>"""

        env = Environment(loader=FileSystemLoader("templates"))
        template = env.get_template("context.jinja2")

        system_prompt = template.render(
            url=metadata["url"],
            docs=docs,
            schema=json.dumps(schema, indent=2),
        )

        messages = list(load_previous(project, metadata.get("base"), count=4))
        messages.append(metadata.get("query"))

        chat = Chat(model, sp=system_prompt)
        r = chat(messages, prefill=prefill)

        html = parse(r)

        metadata = {
            "messages": messages,
            "schema": schema,
            "result": html,
            "model": model,
            "system_prompt": system_prompt,
            "prefill": prefill,
        }

        data.update(project, uuid, kind="generation", html=html, metadata=metadata)

    except Exception as e:
        error_html = (
            f"<title>error</title><p>{str(e)}</p><pre>{traceback.format_exc()}</pre>"
        )
        data.write(project, uuid, kind="generation", html=error_html)


def parse(r):
    return r.content[0].text


def load_previous(project, base, count=4):
    messages = []
    for i in range(count):
        if not base:
            break
        metadata = data.read(project, base, kind="generation", mode="metadata")
        if not metadata:
            break
        html = data.read(project, base, kind="generation", mode="html")
        messages.append({"user": metadata.get("query", ""), "assistant": html})
        base = metadata.get("base", "")

    messages.reverse()

    for m in messages:
        yield m["user"]
        yield m["assistant"]
