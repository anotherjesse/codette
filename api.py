from fastapi import FastAPI, HTTPException, Request, Body
from pydantic import BaseModel
from generator import generate_content
from store import ProjectStore, Page, Project
from fastapi.responses import HTMLResponse
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.requests import Request as StarletteRequest
from fastapi.middleware.cors import CORSMiddleware


def create_app(project_store: ProjectStore):
    api = FastAPI(
        title="Codette API",
        description="API for managing projects and pages",
        version="0.0.1",
    )
    content = FastAPI()

    # Add CORS middleware to api
    api.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],  # Allows all methods
        allow_headers=["*"],  # Allows all headers
    )

    @api.get("/", include_in_schema=False)
    async def root():
        return api.openapi()

    @api.get("/v0/projects")
    def list_projects():
        return project_store.list_projects()

    @api.post("/v0/projects", status_code=201)
    def create_project(project: Project):
        try:
            return project_store.create_project(
                project.name, [p.model_dump() for p in project.pages]
            )
        except FileExistsError as e:
            raise HTTPException(status_code=409, detail=str(e))

    @api.get("/v0/projects/{project_name}")
    def get_project(project_name: str):
        try:
            return project_store.load_project(project_name)
        except FileNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))

    @api.get("/v0/projects/{project_name}/versions")
    def list_project_versions(project_name: str):
        return project_store.list_project_versions(project_name)

    @api.post("/v0/projects/{project_name}/pages", status_code=201)
    def create_or_update_page(project_name: str, page: Page):
        return project_store.create_or_update_page(
            project_name, page.name, page.content
        )

    # FIXME(ja): we should be able to send more context here (not just the prompt, but other resources
    # to include in the context (api docs, other pages, list of static files, ...)
    class GeneratePageRequest(BaseModel):
        prompt: str

    @api.post("/v0/projects/{project_name}/pages/{page_name}/generate", status_code=201)
    def generate_page(
        project_name: str, page_name: str, request: GeneratePageRequest = Body(...)
    ):
        messages = []

        page = project_store.load_page(project_name, page_name)
        if page:
            existing_content = project_store.load_content(
                project_name, page.content_hash
            )
            if existing_content:
                messages.append(f"What is the current page content?")
                messages.append(existing_content)

        messages.append(request.prompt)
        content = generate_content(messages)

        # FIXME(ja): we should save more context here ... like the parent or ...
        return project_store.create_or_update_page(project_name, page_name, content)

    @api.delete("/v0/projects/{project_name}/pages/{page_name}")
    def delete_page(project_name: str, page_name: str):
        # FIXME(ja): we should support mutating versions other than the latest
        return project_store.delete_page(project_name, page_name)

    @api.get("/v0/projects/{project_name}/raw/{page_name}")
    def get_page_raw(project_name: str, page_name: str):
        # FIXME(ja): we should support loading raw content for older versions
        content = project_store.load_content(project_name, page_name)
        return HTMLResponse(content=content)

    @content.get("/{page_name}")
    @content.get("/")
    def serve_page(request: Request, page_name: str = None):
        subdomain = request.scope.get("subdomain")
        if "_" in subdomain:
            project_name, version_name = subdomain.split("_")
        else:
            project_name = subdomain
            version_name = None

        if not page_name:
            page_name = "index"

        page = project_store.load_page(project_name, page_name, version=version_name)
        if page:
            content = project_store.load_content(project_name, page.content_hash)
            return HTMLResponse(content=content)

        raise HTTPException(status_code=404, detail="Page not found")

    async def router(scope, receive, send):
        if scope["type"] == "http":
            request = StarletteRequest(scope, receive)
            host = request.headers.get("host", "")

            if host.startswith("api."):
                await api(scope, receive, send)
            else:
                subdomain = host.split(".")[0] if "." in host else None
                scope["subdomain"] = subdomain

                await content(scope, receive, send)
        else:
            # Handle other types of requests (e.g., WebSocket)
            raise NotImplementedError(f"Unsupported scope type: {scope['type']}")

    app = Starlette(routes=[Mount("/", app=router)])

    return app
