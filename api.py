from fastapi import FastAPI, HTTPException, Request
from store import ProjectStore, Page, Project
import json
from fastapi.responses import HTMLResponse


def create_app(project_store: ProjectStore):
    app = FastAPI()

    @app.get("/api/projects")
    def list_projects():
        return project_store.list_projects()

    @app.post("/api/projects", status_code=201)
    def create_project(project: Project):
        return project_store.create_project(project.name, [])

    @app.get("/api/projects/{project_name}")
    def get_project(project_name: str):
        try:
            return project_store.load_project(project_name)
        except FileNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))

    @app.get("/api/projects/{project_name}/versions")
    def list_project_versions(project_name: str):
        return project_store.list_project_versions(project_name)

    @app.post("/api/projects/{project_name}/pages", status_code=201)
    def create_page(project_name: str, page: Page):
        return project_store.create_page(project_name, page.name, page.content)

    @app.delete("/api/projects/{project_name}/pages/{page_name}")
    def delete_page(project_name: str, page_name: str):
        return project_store.delete_page(project_name, page_name)

    @app.get("/favicon.ico", include_in_schema=False)
    def favicon():
        raise HTTPException(status_code=404, detail="Favicon not found")

    @app.get("/content/{project_version_name}/{page_name}")
    def serve_page(project_version_name: str, page_name: str):
        project_name, version_name = project_version_name.split("_")
        project = project_store.load_project(project_name, version_name)
        if project:
            for page in project.pages:
                if page.name == page_name:
                    content = project_store.load_content(project_name, page.content_hash)
                    return HTMLResponse(content=content)
        
        raise HTTPException(status_code=404, detail="Page not found")

    return app
