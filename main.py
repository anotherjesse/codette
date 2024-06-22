from jinja2 import Environment, FileSystemLoader
from flask import Flask, request, redirect, send_from_directory, render_template
import requests
import json
import threading
import os
import uuid
from claudette import *
import traceback

app = Flask(__name__)

import data


def get_schema(url):
    url += ".json"
    return requests.get(url).json()


@app.route("/")
def hello_world():
    urls = [
        "https://datasette.simonwillison.net/",
        "https://global-power-plants.datasettes.com/global-power-plants/global-power-plants",
    ]

    recent = data.get_recent_pages(10)
    return render_template(
        "index.html",
        urls=urls,
        recent=recent,
    )


@app.route("/", methods=["POST"])
def post():
    query = request.form["query"]
    url = request.form["url"]
    base = request.form.get("base")
    uuid_str = str(uuid.uuid4())
    generate(uuid_str, query, url, base)
    return redirect(f"/pages/{uuid_str}")


@app.route("/pages/<path:uuid>")
def serve_page(uuid):
    # serve requests to .json or .html files directly
    content = data.read(uuid, "raw")
    if content:
        return content

    # if the request is actually for the uuid, do the page iframe thing
    metadata = data.read(uuid, "metadata")
    if metadata:
        return render_template("page.html", metadata=metadata, uuid=uuid)

    return "File not found", 404


@app.route("/pages/<path:uuid>", methods=["POST"])
def regenerate(uuid):
    query = request.form["query"]
    url = request.form["url"]
    generate(uuid, query, url)
    return redirect(f"/pages/{uuid}")


@app.route("/delete/<path:uuid>", methods=["POST"])
def delete(uuid):
    data.delete(uuid)
    return redirect("/")


def generate(uuid_str, query, url, base=None):
    query_dir = f"pages/"
    os.makedirs(query_dir, exist_ok=True)

    data.write(
        uuid_str,
        html=open("templates/generating.html").read(),
        metadata={"query": query, "url": url, "base": base},
    )

    threading.Thread(target=generate_content, args=(query, uuid_str, url, base)).start()


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


if __name__ == "__main__":
    app.run(debug=True, port=8000, host="0.0.0.0")
