import os
import threading
from datetime import datetime
from uuid import uuid4

from flask import Flask, Response, abort, jsonify, redirect, render_template, request, send_file
from werkzeug.utils import secure_filename

import data
import generator
import prefix
import resources

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'  # Define the upload folder

@app.route("/")
def list_projects():
    projects = data.list_projects()
    return render_template("projects.html", projects=projects)

@app.route("/favicon.ico")
def favicon():
    abort(404)


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
    resources = data.project_resources(project)
    generations = data.project_generations(project)
    files = data.project_files(project)
    return render_template(
        "project.html",
        project=project,
        pages=pages,
        generations=generations,
        resources=resources,
        files=files
    )


@app.route("/<string:project>", methods=["POST"])
def project_post(project):
    kind = request.form["kind"]
    if kind == "page":
        page = request.form["page"]
        data.project_create_page(project, page)
        return redirect(f"/{project}/page/{page}")
    if kind == "datasette":
        url = request.form["url"]
        name = request.form["name"]
        info = resources.generate_datasette_doc(url)
        data.write(
            project,
            name,
            kind="resource",
            metadata=dict(
                url=url,
                name=name,
                created=datetime.now().isoformat(),
                kind="datasette",
                **info,
            ),
        )
        return redirect(f"/{project}")
    elif kind == "file":
        if 'file' not in request.files:
            abort(400, description="No file part")
        file = request.files['file']
        if file.filename == '':
            abort(400, description="No selected file")
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], project, filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            file.save(file_path)
            data.write(
                project,
                filename,
                kind="file",
                metadata=dict(
                    name=filename,
                    created=datetime.now().isoformat(),
                    kind="file",
                    path=file_path,
                ),
            )
            return redirect(f"/{project}")

    abort(400)


@app.route("/<string:project>/page/<string:page>", methods=["POST"])
def project_page_post(project, page):
    query = request.form["query"]
    if request.form.get("prefix"):
        query = prefix.get_prefix() + " " + query
    uuid = str(uuid4())
    base = request.form.get("base")

    data.write(
        project,
        uuid,
        kind="generation",
        html=open("templates/generating.html").read(),
        metadata=dict(
            query=query,
            page=page,
            base=base,
            uuid=uuid,
            created=datetime.now().isoformat(),
        ),
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
        return render_template(
            "page.html",
            metadata=metadata,
            page=page,
            selected_generation=metadata.get("generation"),
            project=project,
            generations=generations,
        )

    abort(404)


@app.route("/<string:project>/page/<string:page>/history")
def serve_history(project, page):
    metadata = data.read(project, page, kind="page", mode="metadata")
    generations = data.page_generations(project, page)
    if generations:
        return render_template(
            "history.html",
            generations=generations,
            project=project,
            metadata=metadata,
            page=page,
        )

    abort(404)


@app.route("/<string:project>/page/<string:page>/<string:generation>")
def serve_generation(project, page, generation):
    metadata = data.read(project, generation, kind="generation", mode="metadata")
    if metadata:
        generations = data.page_generations(project, page)
        return render_template(
            "page.html",
            metadata=metadata,
            page=page,
            selected_generation=generation,
            project=project,
            generations=generations,
        )

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


@app.route("/<string:project>/file/<string:filename>")
def serve_file(project, filename):
    metadata = data.read(project, filename, kind="file", mode="metadata")
    if metadata and 'path' in metadata:
        return send_file(metadata['path'])
    abort(404)


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
