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
    base_filename = f"pages/{uuid}"
    if mode == "html":
        filename = f"{base_filename}.html"
    elif mode == "json":
        filename = f"{base_filename}.json"
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
        "https://global-power-plants.datasettes.com/global-power-plants/global-power-plants",
        "https://datasette.simonwillison.net/",
    ]
    # Get list of recent pages
    pages_dir = "pages"
    recent_pages = []
    if os.path.exists(pages_dir):
        files = os.listdir(pages_dir)
        json_files = [f for f in files if f.endswith(".json")]
        json_files.sort(
            key=lambda x: os.path.getmtime(os.path.join(pages_dir, x)), reverse=True
        )
        recent_pages = json_files[:5]  # Get 5 most recent pages

    # Read queries from JSON files
    recent_queries = []
    for json_file in recent_pages:
        with open(os.path.join(pages_dir, json_file), "r") as f:
            data = json.load(f)
            recent_queries.append(data.get("query", "Unknown query"))

    return render_template('index.html', urls=urls, recent_pages=recent_pages, recent_queries=recent_queries)


@app.route("/", methods=["POST"])
def post():
    query = request.form["query"]
    url = request.form["url"]
    uuid_str = str(uuid.uuid4())
    generate(uuid_str, query, url)
    return redirect(f"/pages/{uuid_str}")


def generate(uuid_str, query, url):
    query_dir = f"pages/"
    os.makedirs(query_dir, exist_ok=True)

    write_to_uuid_file(uuid_str, {"query": query, "url": url}, mode="json")

    write_to_uuid_file(
        uuid_str,
        """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="1">
    <title>Generating...</title>
</head>
<body>
    <h1>Generating...</h1>
</body>
</html>
""",
    )

    threading.Thread(target=generate_content, args=(query, uuid_str, url)).start()


def generate_content(query, uuid_str, url):
    try:
        schema = get_schema(url)
        docs = open("json.rst").read()
        model = "claude-3-5-sonnet-20240620"
        system_prompt = open('templates/system.md').read()
        prefill = """<html>"""
        
        env = Environment(loader=FileSystemLoader('templates'))
        template = env.get_template('context.jinja2')
        
        # Render the template
        ctx = template.render(
            url=url,
            docs=docs,
            schema=json.dumps(schema, indent=2),
            query=query
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


@app.route("/pages/<path:filename>")
def serve_page(filename):
    if os.path.exists(f"pages/{filename}"):
        return send_from_directory("pages", filename)

    try:
        with open(os.path.join("pages", filename + ".json"), "r") as f:
            metadata = json.load(f)

        return render_template('page.html', metadata=metadata, filename=filename)
    except FileNotFoundError:
        return "File not found", 404


@app.route("/pages/<path:uuid>", methods=["POST"])
def regenerate(uuid):
    query = request.form["query"]
    url = request.form["url"]
    generate(uuid, query, url)
    return redirect(f"/pages/{uuid}")


def parse(r):
    return r.content[0].text


if __name__ == "__main__":
    app.run(debug=True, port=8000, host="0.0.0.0")
