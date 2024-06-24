import json
import os
from utils import rm

urls = [
    "https://datasette.simonwillison.net/",
    "https://global-power-plants.datasettes.com/global-power-plants/global-power-plants",
]


def list_projects():
    return os.listdir("projects")


def delete_page(project, page):
    rm(f"projects/{project}/pages/{page}.json", no_error=False)
    rm(f"projects/{project}/pages/{page}.html")
    for generation in project_generations(project):
        metadata = read(project, generation, kind="generation", mode="metadata")
        if metadata.get("page") == page:
            rm(f"projects/{project}/generations/{generation}.html")
            rm(f"projects/{project}/generations/{generation}.json")


def project_pages(project):
    return [
        f.replace(".json", "")
        for f in os.listdir(f"projects/{project}/pages")
        if f.endswith(".json")
    ]


def project_artifacts(project):
    return [
        f.replace(".json", "")
        for f in os.listdir(f"projects/{project}/artifacts")
        if f.endswith(".json")
    ]


def project_generations(project):
    return [
        load_generation(project, f.replace(".json", ""))
        for f in os.listdir(f"projects/{project}/generations")
        if f.endswith(".json")
    ]

def page_generations(project, page):
    return [
        g for g in project_generations(project)
        if g.get("page") == page
    ]

def load_generation(project, uuid):
    metadata = json.load(open(f"projects/{project}/generations/{uuid}.json"))
    if metadata.get("uuid") != uuid:
        metadata["uuid"] = uuid
        update(project, uuid, kind="generation", metadata=metadata)
    return metadata



def project_create_page(project, page):
    write(project, page, kind="page", metadata={"page": page, "generation": None})


def update(project, id, kind="page", html=None, metadata=None):
    existing = read(project, id, kind=kind, mode="metadata")
    existing.update(metadata)
    write(project, id, kind=kind, html=html, metadata=existing)


def write(project, id, kind="page", html=None, metadata=None):
    base = f"projects/{project}/{kind}s/{id}"
    if html:
        filename = f"{base}.html"
        with open(filename, "w") as f:
            f.write(html)
    if metadata:
        filename = f"{base}.json"
        with open(filename, "w") as f:
            json.dump(metadata, f, indent=2)


def read(project, id, kind="page", mode="html"):
    base = f"projects/{project}/{kind}s/{id}"
    if mode == "raw":
        filename = base
    elif mode == "html":
        filename = f"{base}.html"
    elif mode == "metadata":
        filename = f"{base}.json"
    else:
        raise ValueError("Invalid mode. Use 'html', 'metadata', or 'raw'.")

    if not os.path.exists(filename):
        return None

    with open(filename, "r") as f:
        content = f.read()

    if mode == "metadata":
        return json.loads(content)
    return content


def delete(uuid):
    rm(f"pages/{uuid}.html")
    rm(f"pages/{uuid}.json")


def get_recent_pages(count=10):
    recent_uuids = []
    if os.path.exists("pages"):
        files = os.listdir("pages")
        json_files = [f for f in files if f.endswith(".json")]
        json_files.sort(
            key=lambda x: os.path.getmtime(os.path.join("pages", x)), reverse=True
        )
        recent_uuids = [f.replace(".json", "") for f in json_files[:count]]

    # Read queries from JSON files
    recent_queries = []
    for uuid in recent_uuids:
        filename = os.path.join("pages", f"{uuid}.json")
        print(filename)
        if os.path.exists(filename):
            with open(filename, "r") as f:
                data = json.load(f)
            recent_queries.append(data.get("query", "Unknown query"))

    return [
        {"uuid": uuid, "query": query}
        for uuid, query in zip(recent_uuids, recent_queries)
    ]
