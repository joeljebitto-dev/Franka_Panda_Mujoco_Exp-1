from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import AppSettings, get_settings


@dataclass(frozen=True)
class ScenePaths:
    project_root: Path
    panda_dir: Path
    scene_xml: Path


def get_scene_paths(settings: AppSettings | None = None) -> ScenePaths:
    settings = settings or get_settings()
    project_root = settings.paths.project_root
    panda_dir = settings.paths.panda_dir
    scene_xml = settings.paths.scene_xml
    return ScenePaths(project_root=project_root, panda_dir=panda_dir, scene_xml=scene_xml)


def validate_scene_assets(settings: AppSettings | None = None) -> Path:
    settings = settings or get_settings()
    paths = get_scene_paths(settings)
    missing = [
        path
        for path in (paths.panda_dir, settings.paths.mjx_scene_xml, paths.scene_xml)
        if not path.exists()
    ]
    if missing:
        formatted = "\n".join(f"- {path}" for path in missing)
        raise FileNotFoundError(f"Required MuJoCo scene assets are missing:\n{formatted}")
    return paths.scene_xml
