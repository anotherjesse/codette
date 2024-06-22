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


def write_to_uuid_file(uuid, content, mode='html'):
    base_filename = f"pages/{uuid}"
    if mode == 'html':
        filename = f"{base_filename}.html"
    elif mode == 'json':
        filename = f"{base_filename}.json"
    else:
        raise ValueError("Invalid mode. Use 'html' or 'json'.")

    with open(filename, "w") as f:
        if mode == 'json':
            json.dump(content, f, indent=2)
        else:
            f.write(content)
    return filename


@app.route("/")
def hello_world():
    # Get list of recent pages
    pages_dir = "pages"
    recent_pages = []
    if os.path.exists(pages_dir):
        files = os.listdir(pages_dir)
        json_files = [f for f in files if f.endswith('.json')]
        json_files.sort(key=lambda x: os.path.getmtime(os.path.join(pages_dir, x)), reverse=True)
        recent_pages = json_files[:5]  # Get 5 most recent pages

    # Read queries from JSON files
    recent_queries = []
    for json_file in recent_pages:
        with open(os.path.join(pages_dir, json_file), 'r') as f:
            data = json.load(f)
            recent_queries.append(data.get('query', 'Unknown query'))

    return f"""
    <html>
    <head>
        <title>Datasette Visualization</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
            textarea {{ width: 100%; height: 100px; margin-bottom: 10px; }}
            input[type="submit"] {{ padding: 10px; }}
            ul {{ list-style-type: none; padding: 0; }}
            li {{ margin-bottom: 5px; }}
        </style>
    </head>
    <body>
        <h1>Datasette Visualization Query</h1>
        <form method='post'>
            <textarea name='query' placeholder="Enter your query here...">visualize posts per month using the datasette api</textarea>
            <br>
            <input type='submit' value='Generate Visualization'>
        </form>
        <h2>Recent Visualizations</h2>
        <ul>
            {"".join(f"<li><a href='/pages/{page.replace('.json', '.html')}'>{query}</a></li>" for page, query in zip(recent_pages, recent_queries))}
        </ul>
    </body>
    </html>
    """


@app.route("/", methods=["POST"])
def post():
    query = request.form["query"]

    query_dir = f"pages/"
    os.makedirs(query_dir, exist_ok=True)
    uuid_str = str(uuid.uuid4())

    # Write initial JSON with query
    initial_json = {"query": query}
    write_to_uuid_file(uuid_str, initial_json, mode='json')

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

    filename = write_to_uuid_file(uuid_str, html)

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

    write_to_uuid_file(uuid_str, json_blob, mode='json')


@app.route("/pages/<path:filename>")
def serve_page(filename):
    if filename.endswith('.html'):
        json_filename = filename.replace('.html', '.json')
        try:
            with open(os.path.join('pages', json_filename), 'r') as f:
                metadata = json.load(f)
            
            with open(os.path.join('pages', filename), 'r') as f:
                content = f.read()
            
            return f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <title>Query Result</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                    pre {{ background-color: #f0f0f0; padding: 10px; overflow-x: auto; }}
                    iframe {{ width: 100%; height: 600px; border: 1px solid #ccc; }}
                </style>
            </head>
            <body>
                <h1><a href='/'>/</a> Query: {metadata['query']}</h1>
                <iframe srcdoc="{content.replace('"', '&quot;')}"></iframe>
            </body>
            </html>
            """
        except FileNotFoundError:
            return "File not found", 404
    else:
        return send_from_directory("pages", filename)


def parse(r):
    return r.content[0].text


if __name__ == "__main__":
    app.run(debug=True, port=8000, host="0.0.0.0")
