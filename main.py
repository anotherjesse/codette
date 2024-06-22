from flask import Flask, request, redirect, render_template
import threading
import os
import uuid
import data
import generator

app = Flask(__name__)


@app.route("/")
def hello_world():
    urls = [
        "https://datasette.simonwillison.net/",
        "https://global-power-plants.datasettes.com/global-power-plants/global-power-plants",
    ]

    return render_template(
        "index.html",
        urls=urls,
        recent=data.get_recent_pages(100),
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
    content = data.read(uuid, "raw")
    if content:
        if uuid.endswith('.json'):
            return content, {'Content-Type': 'application/json'}
        elif uuid.endswith('.html'):
            return content, {'Content-Type': 'text/html'}
        return content

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
    data.write(
        uuid_str,
        html=open("templates/generating.html").read(),
        metadata={"query": query, "url": url, "base": base},
    )

    threading.Thread(
        target=generator.generate_content, args=(query, uuid_str, url, base)
    ).start()


if __name__ == "__main__":
    app.run(debug=True, port=8000, host="0.0.0.0")
