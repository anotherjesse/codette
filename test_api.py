import pytest
import tempfile
import shutil
from pathlib import Path
from fastapi.testclient import TestClient
from api import create_app
from store import ProjectStore


@pytest.fixture
def test_client():
    temp_dir = tempfile.mkdtemp()
    project_store = ProjectStore(Path(temp_dir))
    app = create_app(project_store)
    client = TestClient(app)
    yield client
    shutil.rmtree(temp_dir)


def test_list_projects(test_client):
    response = test_client.get("/api/projects")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 0


def test_unknown_project_404s(test_client):
    response = test_client.get("/api/projects/unknown")
    assert response.status_code == 404


def test_create_project(test_client):
    project_data = {"name": "project-creation"}

    response = test_client.post("/api/projects", json=project_data)
    assert response.status_code == 201
    created_project = response.json()
    assert created_project["name"] == "project-creation"
    assert len(created_project["pages"]) == 0
    assert "version" in created_project

    response = test_client.get("/api/projects")
    assert response.status_code == 200
    projects = response.json()
    assert len(projects) == 1
    assert projects[0] == created_project


def test_adding_pages_to_empty_project(test_client):
    project_data = {
        "name": "pages-creation",
    }

    response = test_client.post("/api/projects", json=project_data)
    assert response.status_code == 201
    created_project = response.json()
    assert created_project["name"] == "pages-creation"
    assert len(created_project["pages"]) == 0

    page_data = {
        "name": "index",
        "content": "This is a new index page",
    }

    response = test_client.post(
        f"/api/projects/{created_project['name']}/pages", json=page_data
    )
    assert response.status_code == 201
    updated_project = response.json()
    assert len(updated_project["pages"]) == 1
    created_page = updated_project["pages"][0]
    assert created_page["name"] == "index"
    assert created_page["content_hash"]
    assert created_page["content"] == None

    response = test_client.get(
        f"/content/{updated_project['name']}_{updated_project['version']}/{created_page['name']}"
    )

    assert response.status_code == 200
    assert response.content.decode("utf-8") == page_data["content"]


def test_create_project_with_pages(test_client):
    project_data = {
        "name": "project-creation",
        "pages": [{"name": "index", "content": "This is a new index page"}],
    }

    response = test_client.post("/api/projects", json=project_data)
    assert response.status_code == 201
    created_project = response.json()
    assert created_project["name"] == "project-creation"
    assert len(created_project["pages"]) == 1
    assert "version" in created_project

    response = test_client.get(
        f"/content/{created_project['name']}_{created_project['version']}/{created_project['pages'][0]['name']}"
    )

    assert response.status_code == 200
    assert response.content.decode("utf-8") == project_data["pages"][0]["content"]


def test_updating_project_page(test_client):
    project_data = {
        "name": "project-creation",
        "pages": [{"name": "index", "content": "This is a new index page"}],
    }

    response = test_client.post("/api/projects", json=project_data)
    assert response.status_code == 201
    created_project = response.json()
    assert created_project["name"] == "project-creation"
    assert len(created_project["pages"]) == 1
    assert "version" in created_project

    response = test_client.get(
        f"/content/{created_project['name']}_{created_project['version']}/{created_project['pages'][0]['name']}"
    )

    assert response.status_code == 200
    assert response.content.decode("utf-8") == project_data["pages"][0]["content"]

    page_data = {
        "name": "index",
        "content": "This is an updated index page",
    }

    response = test_client.post(
        f"/api/projects/{created_project['name']}/pages", json=page_data
    )
    assert response.status_code == 201
    updated_project = response.json()
    assert len(updated_project["pages"]) == 1
    created_page = updated_project["pages"][0]
    assert created_page["name"] == "index"
    assert created_page["content_hash"]
    assert created_page["content"] == None

    response = test_client.get(
        f"/content/{updated_project['name']}_{updated_project['version']}/{created_page['name']}"
    )

    assert response.status_code == 200
    assert response.content.decode("utf-8") == page_data["content"]


def test_delete_page(test_client):
    project_data = {
        "name": "project-creation",
        "pages": [{"name": "index", "content": "This is a new index page"}],
    }

    # Create project
    response = test_client.post("/api/projects", json=project_data)
    assert response.status_code == 201
    created_project = response.json()

    # Verify initial page content
    initial_version = created_project["version"]
    response = test_client.get(
        f"/content/{created_project['name']}_{initial_version}/index"
    )
    assert response.status_code == 200
    assert response.content.decode("utf-8") == "This is a new index page"

    # Delete the page
    response = test_client.delete(
        f"/api/projects/{created_project['name']}/pages/index"
    )
    assert response.status_code == 200
    updated_project = response.json()
    assert len(updated_project["pages"]) == 0
    new_version = updated_project["version"]

    # Verify original version still accessible
    response = test_client.get(
        f"/content/{created_project['name']}_{initial_version}/index"
    )
    assert response.status_code == 200
    assert response.content.decode("utf-8") == "This is a new index page"

    # Verify new version returns 404
    response = test_client.get(
        f"/content/{created_project['name']}_{new_version}/index"
    )
    assert response.status_code == 404

    # Verify page is deleted in project details
    response = test_client.get(f"/api/projects/{created_project['name']}")
    assert response.status_code == 200
    project_details = response.json()
    assert len(project_details["pages"]) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
