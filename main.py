from flask import Flask, request
import requests
import json
from claudette import *

app = Flask(__name__)

def get_schema(url):
    url += ".json"
    return requests.get(url).json()

@app.route('/')
def hello_world():
    # datasette_url = "https://datasette.simonwillison.net/"
    # schema = get_schema(datasette_url)
    # return "<pre>" + json.dumps(schema, indent=2) + "</pre>"
    return """<form method='post'>
    <textarea name='query'>visualize posts per month using the datasette api</textarea>
    <input type='submit'>
    </form>"""

@app.route('/', methods=['POST'])
def post():
    query = request.form['query']
    ctx = build_context(query)
    chat = Chat("claude-3-5-sonnet-20240620", sp="""You are an expert web developer, you are tasked with producing a single file that will be used to display data from a datasette api.  All of your code should be inline in the html file, but you can use CDNs to import packages if needed.""")
    r = chat(ctx, prefill='<html>')
    print(r)
    return parse(r)


def parse(r):
    return r.content[0].text


def build_context(query):
    url = "https://datasette.simonwillison.net/"
    schema = get_schema(url)
    docs = open('json.rst').read()
    return f"""Attached is documentation and schema for the datasette api: {url}

<Documentation>
{docs}
</Documentation>

<Schema>
{json.dumps(schema, indent=2)}
</Schema>

produce a single single html file with inline <script> to fetch from said api and display data that user requests
{query}
"""


if __name__ == '__main__':
    app.run(debug=True, port=8000, host='0.0.0.0')
