"""Named and default picture storage for student scripts."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

from .exceptions import NoImageError, PictureNameError, PictureNotFoundError


_VALID_NAME = re.compile(r"^[A-Za-z0-9_-]+$")


class ImageStore:
    def __init__(self, workspace: Path):
        self.workspace = Path(workspace).expanduser().resolve()
        self.images_dir = self.workspace / "images"
        self.results_dir = self.images_dir / "results"
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def normalize_name(name: str | None) -> str:
        if name is None or str(name).strip() == "":
            return "current"
        value = str(name).strip()
        if value.lower().endswith(".jpg"):
            value = value[:-4]
        if not _VALID_NAME.fullmatch(value):
            raise PictureNameError(
                "Picture names may contain only letters, numbers, underscores, "
                "and hyphens. Do not include a folder path."
            )
        return value

    def path_for(self, name: str | None = None, *, must_exist: bool = False) -> Path:
        normalized = self.normalize_name(name)
        path = self.images_dir / f"{normalized}.jpg"
        if must_exist and not path.is_file():
            available = ", ".join(self.list_pictures()) or "none"
            raise PictureNotFoundError(
                f"No saved picture named '{normalized}'. "
                f"Available pictures: {available}"
            )
        return path

    def save_current_as(self, name: str) -> Path:
        source = self.path_for("current")
        if not source.is_file():
            raise NoImageError(
                "No current picture exists. Call ai.take_picture() first."
            )
        destination = self.path_for(name)
        if destination != source:
            shutil.copy2(source, destination)
        return destination

    def list_pictures(self) -> list[str]:
        return sorted(path.stem for path in self.images_dir.glob("*.jpg"))

    def picture_exists(self, name: str | None = None) -> bool:
        return self.path_for(name).is_file()

    def delete_picture(self, name: str) -> None:
        path = self.path_for(name, must_exist=True)
        path.unlink()
