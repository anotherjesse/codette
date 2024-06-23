from flask import Flask, request, redirect, render_template, jsonify, Response, abort
import threading
from uuid import uuid4
import data
import generator

app = Flask(__name__)


@app.route("/")
def index():
    count = int(request.args.get("count", 25))
    params = {
        "urls": data.urls,
        "recent": data.get_recent_pages(count),
    }

    return render_template("index.html", **params)


@app.route("/", methods=["POST"])
def post():
    query = request.form["query"]
    url = request.form["url"]
    base = request.form.get("base")
    uuid = str(uuid4())
    generate(uuid, query, url, base)
    return redirect(f"/pages/{uuid}")


@app.route("/pages/<path:uuid>.json")
def serve_json(uuid):
    metadata = data.read(uuid, "metadata")
    return jsonify(metadata)


@app.route("/pages/<path:uuid>.html")
def serve_html(uuid):
    content = data.read(uuid, "html")
    if content:
        return Response(content, mimetype="text/html")

    abort(404)


@app.route("/pages/<path:uuid>")
def serve_page(uuid):
    metadata = data.read(uuid, "metadata")
    if metadata:
        return render_template("page.html", metadata=metadata, uuid=uuid)

    abort(404)


@app.route("/pages/<path:uuid>", methods=["POST"])
def regenerate(uuid):
    query = request.form["query"]
    url = request.form["url"]
    metadata = data.read(uuid, "metadata")
    generate(uuid, query, url, metadata.get("base"))
    return redirect(f"/pages/{uuid}")


@app.route("/delete/<path:uuid>", methods=["POST"])
def delete(uuid):
    data.delete(uuid)
    return redirect("/")


def generate(uuid, query, url, base=None):
    data.write(
        uuid,
        html=open("templates/generating.html").read(),
        metadata={"query": query, "url": url, "base": base},
    )

    threading.Thread(
        target=generator.generate_content, args=(query, uuid, url, base)
    ).start()


if __name__ == "__main__":
    app.run(debug=True, port=8000, host="0.0.0.0")
