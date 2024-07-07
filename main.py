import os
import threading
from datetime import datetime
from uuid import uuid4

from flask import (
    Flask,
    Response,
    abort,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
)
from werkzeug.utils import secure_filename

import data
import generator
import prefix
import resources

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"  # Define the upload folder

# Determine if we're in development or production
is_development = os.environ.get('FLASK_ENV') == 'development'

if is_development:
    app.config["SERVER_NAME"] = "localtest.me:8000"
    app.config["PREFERRED_URL_SCHEME"] = "http"
else:
    app.config["SERVER_NAME"] = "zomg.ai"
    app.config["PREFERRED_URL_SCHEME"] = "https"

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def catch_all(path):
    if is_development and request.host.startswith("localtest.me:"):
        return redirect(f"http://admin.localtest.me:8000/{path}", code=301)
    elif not is_development and request.host == "zomg.ai":
        return redirect(f"https://admin.zomg.ai/{path}", code=301)
    abort(404)


@app.route("/", subdomain="admin")
def list_projects():
    projects = data.list_projects()
    return render_template("projects.html", projects=projects)


@app.route("/favicon.ico", subdomain="<project>")
def favicon(project):
    abort(404)


@app.route("/", methods=["POST"], subdomain="admin")
def create_project():
    project = request.form["project"]
    data.create_project(project)
    return redirect(f"/{project}")


@app.route(
    "/<string:project>/page/<string:page>/delete", methods=["POST"], subdomain="admin"
)
def delete_page(project, page):
    data.delete_page(project, page)
    return redirect(f"/{project}")


@app.route("/<string:project>", subdomain="admin")
def serve_project(project):
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
        files=files,
    )


@app.route("/<string:project>", methods=["POST"], subdomain="admin")
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
        if "file" not in request.files:
            abort(400, description="No file part")
        file = request.files["file"]
        if file.filename == "":
            abort(400, description="No selected file")
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], project, filename)
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


@app.route("/<string:project>/page/<string:page>", methods=["POST"], subdomain="admin")
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


@app.route("/<string:project>/<string:kind>/<string:id>.json", subdomain="admin")
def serve_json(project, kind, id):
    metadata = data.read(project, id, kind=kind, mode="metadata")
    return jsonify(metadata)


@app.route("/<string:project>/<string:kind>/<string:id>.html", subdomain="admin")
def serve_html(project, kind, id):
    content = data.read(project, id, kind=kind, mode="html")
    if content:
        return Response(content, mimetype="text/html")

    abort(404)


@app.route("/<string:project>/page/<string:page>", subdomain="admin")
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


@app.route("/<string:project>/page/<string:page>/history", subdomain="admin")
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


@app.route(
    "/<string:project>/page/<string:page>/<string:generation>", subdomain="admin"
)
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


@app.route(
    "/<string:project>/page/<string:page>/<string:generation>.html", subdomain="admin"
)
def serve_generation_html(project, page, generation):
    html = data.read(project, generation, kind="generation", mode="html")
    if html:
        return Response(html, mimetype="text/html")

    abort(404)


@app.route(
    "/<string:project>/page/<string:page>/<string:generation>.json", subdomain="admin"
)
def serve_generation_json(project, page, generation):
    metadata = data.read(project, generation, kind="generation", mode="metadata")
    return jsonify(metadata)


@app.route("/<string:project>/file/<string:filename>", subdomain="admin")
def serve_file(project, filename):
    metadata = data.read(project, filename, kind="file", mode="metadata")
    if metadata and "path" in metadata:
        return send_file(metadata["path"])
    abort(404)


@app.route("/pages/<string:uuid>", methods=["POST"], subdomain="admin")
def regenerate(uuid):
    query = request.form["query"]
    url = request.form["url"]
    metadata = data.read(uuid, "metadata")
    generate(uuid, query, url, metadata.get("base"))
    return redirect(f"/pages/{uuid}")


@app.route("/delete/<string:uuid>", methods=["POST"], subdomain="admin")
def delete(uuid):
    data.delete(uuid)
    return redirect("/")


@app.route("/", subdomain="<project>")
def project_subdomain(project):
    pages = data.project_pages(project)
    return (
        "<ul>"
        + "".join([f'<li><a href="/{page}">{page}</a></li>' for page in pages])
        + "</ul>"
    )


@app.route("/<string:page_name>", subdomain="<project>")
def serve_page_subdomain(project, page_name):
    metadata = data.read(project, page_name, kind="page", mode="metadata")
    current_generation = metadata.get("generation")
    return serve_generation_html(project, page_name, current_generation)


@app.route("/<string:page>/<string:generation>", subdomain="<project>")
def serve_generation_subdomain(project, page, generation):
    return serve_generation(project, page, generation)


@app.route("/<string:page>/<string:generation>.html", subdomain="<project>")
def serve_generation_html_subdomain(project, page, generation):
    return serve_generation_html(project, page, generation)


@app.route("/<string:page>/<string:generation>.json", subdomain="<project>")
def serve_generation_json_subdomain(project, page, generation):
    return serve_generation_json(project, page, generation)


@app.route("/file/<string:filename>", subdomain="<project>")
def serve_file_subdomain(project, filename):
    return serve_file(project, filename)


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
    app.run(debug=is_development, port=8000, host="0.0.0.0")
