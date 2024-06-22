import json
from jinja2 import Environment, FileSystemLoader
import requests
from claudette import Chat
import data
import traceback


def get_schema(url):
    url += ".json"
    return requests.get(url).json()


def generate_content(query, uuid_str, url, base):
    try:
        schema = get_schema(url)
        docs = open("json.rst").read()
        model = "claude-3-5-sonnet-20240620"
        prefill = """<html>"""


        env = Environment(loader=FileSystemLoader("templates"))
        template = env.get_template("context.jinja2")

        system_prompt = template.render(
            url=url,
            docs=docs,
            schema=json.dumps(schema, indent=2),
        )

        messages = list(load_previous(base, count=4))
        messages.append(query)

        chat = Chat(model, sp=system_prompt)
        r = chat(messages, prefill=prefill)

        html = parse(r)

        metadata = {
            "query": query,
            "messages": messages,
            "url": url,
            "schema": schema,
            "result": html,
            "model": model,
            "system_prompt": system_prompt,
            "prefill": prefill,
            "base": base,
        }

        data.write(uuid_str, html=html, metadata=metadata)
    except Exception as e:
        error_html = f"<p>{str(e)}</p><pre>{traceback.format_exc()}</pre>"
        data.write(uuid_str, html=error_html)


def parse(r):
    return r.content[0].text


def load_previous(base, count=4):
    messages = []
    for i in range(count):
        if not base:
            break
        metadata = data.read(base, "metadata")
        html = data.read(base, "html")
        messages.append({"user": metadata.get("query", ""), "assistant": html})
        base = metadata.get("base", "")

    messages.reverse()

    for m in messages:
        yield m["user"]
        yield m["assistant"]