import pytest
import tempfile
import shutil
from pathlib import Path
from fastapi.testclient import TestClient
from api import create_app
from store import ProjectStore


@pytest.fixture
def client_builder():
    temp_dir = tempfile.mkdtemp()
    project_store = ProjectStore(Path(temp_dir))
    app = create_app(project_store)

    def client_builder(subdomain='api'):
        return TestClient(app, base_url=f"http://{subdomain}.test")

    yield client_builder
    shutil.rmtree(temp_dir)


def test_list_projects(client_builder):
    api_client = client_builder()

    response = api_client.get("/v0/projects")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 0


def test_unknown_project_404s(client_builder):
    api_client = client_builder()

    response = api_client.get("/v0/projects/unknown")
    assert response.status_code == 404


def test_create_project(client_builder):
    api_client = client_builder()

    project_data = {"name": "project-creation"}

    response = api_client.post("/v0/projects", json=project_data)
    assert response.status_code == 201
    created_project = response.json()
    assert created_project["name"] == "project-creation"
    assert len(created_project["pages"]) == 0
    assert "version" in created_project

    response = api_client.get("/v0/projects")
    assert response.status_code == 200
    projects = response.json()
    assert len(projects) == 1
    assert projects[0] == created_project


def test_only_one_project(client_builder):
    api_client = client_builder()

    project_data = {"name": "only-one"}

    response = api_client.post("/v0/projects", json=project_data)
    assert response.status_code == 201
    created_project = response.json()
    assert created_project["name"] == "only-one"
    assert len(created_project["pages"]) == 0
    assert "version" in created_project

    response = api_client.post("/v0/projects", json=project_data)
    assert response.status_code == 409

    response = api_client.get("/v0/projects")
    assert response.status_code == 200
    projects = response.json()
    assert len(projects) == 1
    assert projects[0] == created_project


def test_adding_pages_to_empty_project(client_builder):
    api_client = client_builder()

    project_data = {
        "name": "pages-creation",
    }

    response = api_client.post("/v0/projects", json=project_data)
    assert response.status_code == 201
    created_project = response.json()
    assert created_project["name"] == "pages-creation"
    assert len(created_project["pages"]) == 0

    page_data = {
        "name": "index",
        "content": "This is a new index page",
    }

    response = api_client.post(
        f"/v0/projects/{created_project['name']}/pages", json=page_data
    )
    assert response.status_code == 201
    updated_project = response.json()
    assert len(updated_project["pages"]) == 1
    created_page = updated_project["pages"][0]
    assert created_page["name"] == "index"
    assert created_page["content_hash"]
    assert created_page["content"] == None

    content_client = client_builder(
        f"{updated_project['name']}_{updated_project['version']}"
    )

    response = content_client.get(f"/{created_page['name']}")

    assert response.status_code == 200
    assert response.content.decode("utf-8") == page_data["content"]


def test_create_project_with_pages(client_builder):
    api_client = client_builder()

    project_data = {
        "name": "project-creation",
        "pages": [{"name": "index", "content": "This is a new index page"}],
    }

    response = api_client.post("/v0/projects", json=project_data)
    assert response.status_code == 201
    created_project = response.json()
    assert created_project["name"] == "project-creation"
    assert len(created_project["pages"]) == 1
    assert "version" in created_project

    version_client = client_builder(
        f"{created_project['name']}_{created_project['version']}"
    )

    response = version_client.get(f"/{created_project['pages'][0]['name']}")

    assert response.status_code == 200
    assert response.content.decode("utf-8") == project_data["pages"][0]["content"]


def test_updating_project_page(client_builder):
    api_client = client_builder()

    project_data = {
        "name": "project-creation",
        "pages": [{"name": "index", "content": "This is a new index page"}],
    }

    response = api_client.post("/v0/projects", json=project_data)
    assert response.status_code == 201
    created_project = response.json()
    assert created_project["name"] == "project-creation"
    assert len(created_project["pages"]) == 1
    assert "version" in created_project

    version_client = client_builder(
        f"{created_project['name']}_{created_project['version']}"
    )
    response = version_client.get(f"/{created_project['pages'][0]['name']}")

    assert response.status_code == 200
    assert response.content.decode("utf-8") == project_data["pages"][0]["content"]

    page_data = {
        "name": "index",
        "content": "This is an updated index page",
    }

    response = api_client.post(
        f"/v0/projects/{created_project['name']}/pages", json=page_data
    )
    assert response.status_code == 201
    updated_project = response.json()
    assert len(updated_project["pages"]) == 1
    created_page = updated_project["pages"][0]
    assert created_page["name"] == "index"
    assert created_page["content_hash"]
    assert created_page["content"] == None

    version_client = client_builder(
        f"{updated_project['name']}_{updated_project['version']}"
    )

    response = version_client.get(f"/{created_page['name']}")

    assert response.status_code == 200
    assert response.content.decode("utf-8") == page_data["content"]


def test_delete_page(client_builder):
    api_client = client_builder()

    project_data = {
        "name": "project-creation",
        "pages": [{"name": "index", "content": "This is a new index page"}],
    }

    # Create project
    response = api_client.post("/v0/projects", json=project_data)
    assert response.status_code == 201
    created_project = response.json()

    # Verify initial page content
    initial_version = created_project["version"]
    version_client = client_builder(
        f"{created_project['name']}_{created_project['version']}"
    )
    response = version_client.get(f"/{created_project['pages'][0]['name']}")
    assert response.status_code == 200
    assert response.content.decode("utf-8") == "This is a new index page"

    # Delete the page
    response = api_client.delete(f"/v0/projects/{created_project['name']}/pages/index")
    assert response.status_code == 200
    updated_project = response.json()
    assert len(updated_project["pages"]) == 0
    new_version = updated_project["version"]

    # Verify original version still accessible
    version_client = client_builder(f"{created_project['name']}_{initial_version}")
    response = version_client.get(f"/{created_project['pages'][0]['name']}")
    assert response.status_code == 200
    assert response.content.decode("utf-8") == "This is a new index page"

    # Verify new version returns 404
    version_client = client_builder(f"{created_project['name']}_{new_version}")
    response = version_client.get(f"/{created_project['pages'][0]['name']}")
    assert response.status_code == 404

    # Verify page is deleted in project details
    response = api_client.get(f"/v0/projects/{created_project['name']}")
    assert response.status_code == 200
    project_details = response.json()
    assert len(project_details["pages"]) == 0


def test_index_served_at_index(client_builder):
    api_client = client_builder()

    project_data = {
        "name": "project-creation",
        "pages": [{"name": "index", "content": "This is a new index page"}],
    }

    # Create project
    response = api_client.post("/v0/projects", json=project_data)
    assert response.status_code == 201
    created_project = response.json()

    version_client = client_builder(
        f"{created_project['name']}_{created_project['version']}"
    )
    response = version_client.get("/")
    assert response.status_code == 200
    assert response.content.decode("utf-8") == project_data["pages"][0]["content"]


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
