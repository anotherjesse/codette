from jinja2 import Environment, FileSystemLoader
from flask import Flask, request, redirect, send_from_directory, render_template
import requests
import json
import threading
import os
import uuid
from claudette import *

app = Flask(__name__)


def get_schema(url):
    url += ".json"
    return requests.get(url).json()


def write_to_uuid_file(uuid, content, mode="html"):
    base = f"pages/{uuid}"
    if mode == "html":
        filename = f"{base}.html"
    elif mode == "json":
        filename = f"{base}.json"
    else:
        raise ValueError("Invalid mode. Use 'html' or 'json'.")

    with open(filename, "w") as f:
        if mode == "json":
            json.dump(content, f, indent=2)
        else:
            f.write(content)
    return filename


@app.route("/")
def hello_world():
    urls = [
        "https://datasette.simonwillison.net/",
        "https://global-power-plants.datasettes.com/global-power-plants/global-power-plants",
    ]
    # Get list of recent pages
    pages_dir = "pages"
    recent_uuids = []
    if os.path.exists(pages_dir):
        files = os.listdir(pages_dir)
        json_files = [f for f in files if f.endswith(".json")]
        json_files.sort(
            key=lambda x: os.path.getmtime(os.path.join(pages_dir, x)), reverse=True
        )
        recent_uuids = [f.replace(".json", "") for f in json_files[:10]]

    # Read queries from JSON files
    recent_queries = []
    for uuid in recent_uuids:
        with open(os.path.join(pages_dir, f"{uuid}.json"), "r") as f:
            data = json.load(f)
            recent_queries.append(data.get("query", "Unknown query"))

    return render_template(
        "index.html",
        urls=urls,
        recent=[
            {"uuid": uuid, "query": query}
            for uuid, query in zip(recent_uuids, recent_queries)
        ],
    )


@app.route("/", methods=["POST"])
def post():
    query = request.form["query"]
    url = request.form["url"]
    base = request.form.get("base")
    uuid_str = str(uuid.uuid4())
    generate(uuid_str, query, url, base)
    return redirect(f"/pages/{uuid_str}")


def generate(uuid_str, query, url, base=None):
    query_dir = f"pages/"
    os.makedirs(query_dir, exist_ok=True)

    write_to_uuid_file(
        uuid_str, {"query": query, "url": url, "base": base}, mode="json"
    )

    write_to_uuid_file(uuid_str, open("templates/generating.html").read())

    threading.Thread(target=generate_content, args=(query, uuid_str, url, base)).start()


def generate_content(query, uuid_str, url, base):
    try:
        schema = get_schema(url)
        docs = open("json.rst").read()
        model = "claude-3-5-sonnet-20240620"
        system_prompt = open("templates/system.md").read()
        prefill = """<html>"""

        previous = ""
        if base and os.path.exists(f"pages/{base}.html"):
            with open(f"pages/{base}.html", "r") as f:
                previous = f.read()

        env = Environment(loader=FileSystemLoader("templates"))
        template = env.get_template("context.jinja2")
        # Render the template
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
        print(html)

        write_to_uuid_file(uuid_str, html)

        json_blob = {
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

        write_to_uuid_file(uuid_str, json_blob, mode="json")
    except Exception as e:
        error_html = f"""
        <html>
        <body>
            <h1>An error occurred</h1>
            <p>{str(e)}</p>
        </body>
        </html>
        """
        write_to_uuid_file(uuid_str, error_html)
        print(f"Error occurred: {str(e)}")


@app.route("/pages/<path:uuid>")
def serve_page(uuid):
    if os.path.exists(f"pages/{uuid}"):
        return send_from_directory("pages", uuid)

    try:
        with open(os.path.join("pages", uuid + ".json"), "r") as f:
            metadata = json.load(f)

        return render_template("page.html", metadata=metadata, uuid=uuid)
    except FileNotFoundError:
        return "File not found", 404


@app.route("/pages/<path:uuid>", methods=["POST"])
def regenerate(uuid):
    query = request.form["query"]
    url = request.form["url"]
    generate(uuid, query, url)
    return redirect(f"/pages/{uuid}")


@app.route("/delete/<path:uuid>", methods=["POST"])
def delete(uuid):
    html_file = f"pages/{uuid}.html"
    json_file = f"pages/{uuid}.json"

    if os.path.exists(html_file):
        os.remove(html_file)
    if os.path.exists(json_file):
        os.remove(json_file)

    return redirect("/")


def parse(r):
    return r.content[0].text


if __name__ == "__main__":
    app.run(debug=True, port=8000, host="0.0.0.0")
