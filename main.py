from flask import Flask, request, redirect, render_template, jsonify, Response, abort
from datetime import datetime
import threading
from uuid import uuid4
import data
import generator

app = Flask(__name__)


@app.route("/")
def list_projects():
    projects = data.list_projects()
    return render_template("projects.html", projects=projects)


@app.route("/", methods=["POST"])
def create_project():
    project = request.form["project"]
    data.create_project(project)
    return redirect(f"/{project}")


@app.route("/<string:project>/page/<string:page>/delete", methods=["POST"])
def delete_page(project, page):
    data.delete_page(project, page)
    return redirect(f"/{project}")


@app.route("/<string:project>")
def project(project):
    pages = data.project_pages(project)
    artifacts = data.project_artifacts(project)
    generations = data.project_generations(project)
    return render_template(
        "project.html",
        project=project,
        pages=pages,
        artifacts=artifacts,
        generations=generations,
    )


@app.route("/<string:project>", methods=["POST"])
def project_post(project):
    kind = request.form["kind"]
    if kind == "page":
        page = request.form["page"]
        data.project_create_page(project, page)
        return redirect(f"/{project}/page/{page}")

    abort(4000)


@app.route("/<string:project>/page/<string:page>", methods=["POST"])
def project_page_post(project, page):
    query = request.form["query"]
    uuid = str(uuid4())
    url = "https://datasette.simonwillison.net/"
    base = request.form.get("base")

    data.write(
        project,
        uuid,
        kind="generation",
        html=open("templates/generating.html").read(),
        metadata=dict(query=query, page=page, base=base, url=url, uuid=uuid, created=datetime.now().isoformat()),
    )

    data.update(project, page, kind="page", metadata={"generation": uuid})

    threading.Thread(target=generator.generate_content, args=(project, uuid)).start()

    return redirect(f"/{project}/page/{page}")


@app.route("/<string:project>/<string:kind>/<string:id>.json")
def serve_json(project, kind, id):
    metadata = data.read(project, id, kind=kind, mode="metadata")
    return jsonify(metadata)


@app.route("/<string:project>/<string:kind>/<string:id>.html")
def serve_html(project, kind, id):
    content = data.read(project, id, kind=kind, mode="html")
    if content:
        return Response(content, mimetype="text/html")

    abort(404)


@app.route("/<string:project>/page/<string:page>")
def serve_page(project, page):
    metadata = data.read(project, page, kind="page", mode="metadata")
    if metadata:
        generations = data.page_generations(project, page)
        return render_template("page.html", metadata=metadata, page=page, selected_generation=metadata.get("generation"), project=project, generations=generations)

    abort(404)


@app.route("/<string:project>/page/<string:page>/history")
def serve_history(project, page):
    metadata = data.read(project, page, kind="page", mode="metadata")
    generations = data.page_generations(project, page)
    if generations:
        return render_template("history.html", generations=generations, project=project, metadata=metadata, page=page)

    abort(404)


@app.route("/<string:project>/page/<string:page>/<string:generation>")
def serve_generation(project, page, generation):
    metadata = data.read(project, generation, kind="generation", mode="metadata")
    if metadata:
        generations = data.page_generations(project, page)
        return render_template("page.html", metadata=metadata, page=page, selected_generation=generation, project=project, generations=generations)

    abort(404)

@app.route("/<string:project>/page/<string:page>/<string:generation>.html")
def serve_generation_html(project, page, generation):
    html = data.read(project, generation, kind="generation", mode="html")
    if html:
        return Response(html, mimetype="text/html")

    abort(404)

@app.route("/<string:project>/page/<string:page>/<string:generation>.json")
def serve_generation_json(project, page, generation):
    metadata = data.read(project, generation, kind="generation", mode="metadata")
    return jsonify(metadata)

@app.route("/pages/<string:uuid>", methods=["POST"])
def regenerate(uuid):
    query = request.form["query"]
    url = request.form["url"]
    metadata = data.read(uuid, "metadata")
    generate(uuid, query, url, metadata.get("base"))
    return redirect(f"/pages/{uuid}")


@app.route("/delete/<string:uuid>", methods=["POST"])
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
