import re
from pydantic import BaseModel, Field, field_validator, ValidationInfo
from typing import List, Dict, Union, Optional, Any
import json
import hashlib
from pathlib import Path
import uuid
from datetime import datetime


def validate_name(name: str) -> str:
    if not re.match(r"^[a-z0-9-]+$", name):
        raise ValueError(
            "Name must be lowercase alphanumeric with dashes only, no spaces"
        )
    return name


class Page(BaseModel):
    name: str
    title: str = ""
    content: Optional[str] = None
    content_hash: Optional[str] = None

    @field_validator("name")
    @classmethod
    def must_be_valid_name(cls, v: str) -> str:
        return validate_name(v)

    @field_validator("title")
    @classmethod
    def set_title_if_empty(cls, v: str, info: ValidationInfo) -> str:
        if not v and "name" in info.data:
            return info.data["name"]
        return v


class Project(BaseModel):
    name: str
    version: str = Field(
        default_factory=lambda: f"{int(datetime.now().timestamp())}-{uuid.uuid4().hex[:6]}"
    )
    pages: List[Page] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def must_be_valid_name(cls, v: str) -> str:
        return validate_name(v)


class ProjectStore:
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.content_path = base_path / "content"
        self.content_path.mkdir(parents=True, exist_ok=True)

    def _hash_content(self, content: Union[str, bytes]) -> str:
        if isinstance(content, str):
            content = content.encode()
        return hashlib.sha256(content).hexdigest()

    def _store_content(self, content: Union[str, bytes]) -> str:
        content_hash = self._hash_content(content)
        file_path = self.content_path / content_hash
        if not file_path.exists():
            mode = "w" if isinstance(content, str) else "wb"
            with file_path.open(mode) as f:
                f.write(content)
        return content_hash

    def save_project(self, project: Project):
        project_path = self.base_path / f"{project.name}_{project.version}.json"
        with project_path.open("w") as f:
            json.dump(project.model_dump(), f, indent=2)

    # FIXME(ja) - this whole "latest version" is the current version
    # is kinda broken!
    # Load the latest version if no specific version is provided
    def load_project(self, project_name: str, version: str = None) -> Project:
        if version:
            project_path = self.base_path / f"{project_name}_{version}.json"
        else:
            project_files = list(self.base_path.glob(f"{project_name}_*.json"))
            if not project_files:
                raise FileNotFoundError(f"Project {project_name} not found")
            project_path = max(project_files, key=lambda p: p.stat().st_mtime)

        with project_path.open("r") as f:
            data = json.load(f)
        return Project.model_validate(data)

    def load_page(self, project_name: str, page_name: str, version: str = None) -> Page:
        project = self.load_project(project_name, version)
        for page in project.pages:
            if page.name == page_name:
                return page
        return None

    # this is ugly because of the version issue
    def list_projects(self, include_versions=True) -> List[Project]:
        projects = {}
        for f in self.base_path.glob("*.json"):
            name, version = f.stem.rsplit("_", 1)
            if name not in projects:
                projects[name] = [self.load_project(name, version)]
            elif include_versions:
                projects[name].append(self.load_project(name, version))
            elif version > projects[name][0]["version"]:
                projects[name] = [self.load_project(name, version)]
        for name, versions in projects.items():
            projects[name] = sorted(versions, key=lambda v: v.version, reverse=True)

        response = []
        for versions in projects.values():
            for v in versions:
                response.append(v)
        return response

    def exists(self, name: str) -> bool:
        return len(list(self.base_path.glob(f"{name}_*.json"))) > 0

    def create_project(self, name: str, pages: List[Dict]) -> Project:
        if self.exists(name):
            raise FileExistsError(f"A project named '{name}' already exists")

        processed_pages = []
        for page in pages:
            content_hash = self._store_content(page["content"])
            processed_pages.append(
                Page(
                    name=page["name"],
                    title=page["title"],
                    content_hash=content_hash,
                )
            )

        project = Project(name=name, pages=processed_pages)
        self.save_project(project)
        return project

    # def get_project_pages(self, project_name: str) -> List[str]:
    #     project = self.load_project(project_name)
    #     return [page.name for page in project.pages]

    def load_content(self, project_name: str, content_hash: str) -> str:
        file_path = self.content_path / content_hash
        with file_path.open("r") as f:
            return f.read()

    def create_or_update_page(
        self, project_name: str, page_name: str, content: str
    ) -> Project:
        project = self.load_project(project_name)
        content_hash = self._store_content(content)
        new_page = Page(
            name=page_name,
            title=page_name,
            content_hash=content_hash,
        )
        updated_project = Project(
            name=project.name,
            pages=[p for p in project.pages if p.name != page_name] + [new_page],
        )
        self.save_project(updated_project)
        return updated_project

    def delete_page(self, project_name: str, page_name: str) -> Project:
        project = self.load_project(project_name)
        updated_pages = [page for page in project.pages if page.name != page_name]
        updated_project = Project(name=project.name, pages=updated_pages)
        self.save_project(updated_project)
        return updated_project

    def list_project_versions(self, project_name: str) -> List[str]:
        versions = [
            f.stem.split("_")[-1] for f in self.base_path.glob(f"{project_name}_*.json")
        ]
        return sorted(versions, reverse=True)
