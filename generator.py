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
        system_prompt = open("templates/system.md").read()
        prefill = """<html>"""

        previous = data.read(base, "html") or ""

        env = Environment(loader=FileSystemLoader("templates"))
        template = env.get_template("context.jinja2")

        ctx = template.render(
            url=url,
            docs=docs,
            schema=json.dumps(schema, indent=2),
            query=query,
            previous=previous,
        )

        chat = Chat(model, sp=system_prompt)
        r = chat(ctx, prefill=prefill)

        html = parse(r)

        metadata = {
            "query": query,
            "context": ctx,
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
