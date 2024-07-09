import requests
from typing import List, Optional
from store import Project, Page


class CodetteClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def list_projects(self) -> List[Project]:
        response = requests.get(f"{self.base_url}/v0/projects")
        response.raise_for_status()
        return [Project(**project) for project in response.json()]

    def create_project(self, project: Project) -> Project:
        response = requests.post(
            f"{self.base_url}/v0/projects", json=project.model_dump()
        )
        response.raise_for_status()
        return Project(**response.json())

    def get_project(self, project_name: str) -> Project:
        response = requests.get(f"{self.base_url}/v0/projects/{project_name}")
        response.raise_for_status()
        return Project(**response.json())

    def list_project_versions(self, project_name: str) -> List[str]:
        response = requests.get(f"{self.base_url}/v0/projects/{project_name}/versions")
        response.raise_for_status()
        return response.json()

    def create_or_update_page(self, project_name: str, page: Page) -> Page:
        response = requests.post(
            f"{self.base_url}/v0/projects/{project_name}/pages", json=page.model_dump()
        )
        response.raise_for_status()
        return Page(**response.json())

    def delete_page(self, project_name: str, page_name: str) -> None:
        response = requests.delete(
            f"{self.base_url}/v0/projects/{project_name}/pages/{page_name}"
        )
        response.raise_for_status()


def import_directory(import_path):
    import os, glob

    client = CodetteClient("http://api.localtest.me:8000")

    project_name = os.path.basename(import_path)
    def page_name(fp):
        return os.path.splitext(os.path.basename(fp))[0]

    pages = [
        Page(
            name=page_name(fp), content=open(fp).read()
        )
        for fp in glob.glob(os.path.join(import_path, "*"))
    ]
    new_project = Project(name=project_name, pages=pages)
    client.create_project(new_project)


# Example usage
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python client.py <path1> <path2> ...")
        sys.exit(1)
    for path in sys.argv[1:]:
        import_directory(path)