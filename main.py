from flask import Flask, request, redirect, send_from_directory
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


def write_to_uuid_file(uuid, content):
    filename = f"pages/{uuid}.html"
    with open(filename, "w") as f:
        f.write(content)
    return filename


@app.route("/")
def hello_world():
    return """<form method='post'>
    <textarea name='query'>visualize posts per month using the datasette api</textarea>
    <input type='submit'>
    </form>"""


@app.route("/", methods=["POST"])
def post():
    query = request.form["query"]

    # Create a directory for the query
    query_dir = f"pages/"
    os.makedirs(query_dir, exist_ok=True)
    uuid_str = str(uuid.uuid4())

    # Create initial "generating" HTML file
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

    threading.Thread(target=generate_content, args=(query, uuid_str)).start()

    return redirect(f"/pages/{uuid_str}.html")


def generate_content(query, uuid_str):
    url = "https://datasette.simonwillison.net/"
    schema = get_schema(url)
    docs = open("json.rst").read()
    model = "claude-3-5-sonnet-20240620"
    system_prompt = """You are an expert web developer, you are tasked with producing a single file that will be used to display data from a datasette api.  All of your code should be inline in the html file, but you can use CDNs to import packages if needed."""
    prefill = """<html>"""
    ctx = f"""Attached is documentation and schema for the datasette api: {url}

<Documentation>
{docs}
</Documentation>

<Schema>
{json.dumps(schema, indent=2)}
</Schema>

produce a single single html file with inline <script> to fetch from said api and display data that user requests
{query}
"""

    chat = Chat(model, sp=system_prompt)
    r = chat(ctx, prefill=prefill)

    html = parse(r)
    print(html)

    # Save the result using the helper function
    filename = write_to_uuid_file(uuid_str, html)

    # Store all relevant information as a JSON blob
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

    json_filename = filename.replace(".html", ".json")
    with open(json_filename, "w") as f:
        json.dump(json_blob, f, indent=2)


@app.route("/pages/<path:filename>")
def serve_page(filename):
    return send_from_directory("pages", filename)


def parse(r):
    return r.content[0].text


if __name__ == "__main__":
    app.run(debug=True, port=8000, host="0.0.0.0")
