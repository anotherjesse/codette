import json
import os


def write(uuid, html=None, metadata=None):
    base = f"pages/{uuid}"
    if html:
        filename = f"{base}.html"
        with open(filename, "w") as f:
            f.write(html)
    if metadata:
        filename = f"{base}.json"
        with open(filename, "w") as f:
            json.dump(metadata, f, indent=2)

def read(uuid, mode="html"):
    base = f"pages/{uuid}"
    if mode == "raw":
        filename = base
    elif mode == "html":
        filename = f"{base}.html"
    elif mode == "metadata":
        filename = f"{base}.json"
    else:
        raise ValueError("Invalid mode. Use 'html' or 'json'.")

    if not os.path.exists(filename):
        return None
    
    with open(filename, "r") as f:
        return f.read()


def delete(uuid):
    html_file = f"pages/{uuid}.html"
    json_file = f"pages/{uuid}.json"

    if os.path.exists(html_file):
        os.remove(html_file)
    if os.path.exists(json_file):
        os.remove(json_file)


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
