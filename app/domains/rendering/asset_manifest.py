from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.domains.rendering.page_view_model import PageViewModel

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".mov"}


@dataclass
class AssetRecord:
    asset_id: str
    category: str
    media_type: str
    relative_path: str
    bytes_size: int
    source: str = "material_pack"
    storage_uri: str | None = None
    tags: list[str] = field(default_factory=list)


@dataclass
class AssetManifest:
    manifest_version: str
    circle_id: str
    package_root: str
    generated_at: str
    records: list[AssetRecord] = field(default_factory=list)
    ui_assets: list[dict[str, Any]] = field(default_factory=list)
    export_targets: list[str] = field(default_factory=lambda: ["h5", "pdf"])

    def to_dict(self) -> dict[str, Any]:
        return {
            "manifest_version": self.manifest_version,
            "circle_id": self.circle_id,
            "package_root": self.package_root,
            "generated_at": self.generated_at,
            "records": [asdict(r) for r in self.records],
            "ui_assets": self.ui_assets,
            "export_targets": self.export_targets,
            "channels": list(self.export_targets),
        }


def _guess_category(path: Path) -> str:
    parent = path.parent.name.lower()
    if "酒店" in parent or "hotel" in parent:
        return "hotel"
    if "美食" in parent or "food" in parent:
        return "food"
    if "地标" in parent or "landmark" in parent:
        return "landmark"
    if "街景" in parent or "street" in parent:
        return "street"
    return "spot"


def _media_type(path: Path) -> str | None:
    ext = path.suffix.lower()
    if ext in IMAGE_EXTENSIONS:
        return "image"
    if ext in VIDEO_EXTENSIONS:
        return "video"
    return None


def build_manifest_from_material_pack(package_root: str, *, circle_id: str) -> AssetManifest:
    root = Path(package_root)
    records: list[AssetRecord] = []

    for file_path in sorted(root.rglob("*")):
        if not file_path.is_file():
            continue
        media_type = _media_type(file_path)
        if not media_type:
            continue

        rel = file_path.relative_to(root).as_posix()
        records.append(
            AssetRecord(
                asset_id=rel.replace("/", "_").replace(".", "_"),
                category=_guess_category(file_path),
                media_type=media_type,
                relative_path=rel,
                bytes_size=file_path.stat().st_size,
                tags=[circle_id],
            )
        )

    return AssetManifest(
        manifest_version="asset_manifest_v1",
        circle_id=circle_id,
        package_root=str(root),
        generated_at=datetime.now(timezone.utc).isoformat(),
        records=records,
        ui_assets=[],
    )


def hero_slot_id(page_id: str, page_type: str) -> str:
    return page_slot_id(page_id=page_id, page_type=page_type, slot_name="hero")


def page_slot_id(page_id: str, page_type: str, slot_name: str) -> str:
    return f"{page_type}.{slot_name}.{page_id}"


def resolve_slot_asset(manifest: dict[str, Any], slot_id: str) -> dict[str, Any] | None:
    slots = manifest.get("slots") if isinstance(manifest, dict) else {}
    assets = manifest.get("assets") if isinstance(manifest, dict) else {}
    slots = slots if isinstance(slots, dict) else {}
    assets = assets if isinstance(assets, dict) else {}

    slot_meta = slots.get(slot_id)
    if not isinstance(slot_meta, dict):
        return None

    asset_id = slot_meta.get("asset_id")
    if not isinstance(asset_id, str):
        return None

    asset = assets.get(asset_id)
    if not isinstance(asset, dict):
        return None

    merged = dict(asset)
    merged["asset_id"] = asset_id
    merged["slot_id"] = slot_id
    merged["channel"] = list(manifest.get("channels") or manifest.get("export_targets") or [])
    return merged


def attach_asset_metadata_to_pages(
    page_models: dict[str, PageViewModel],
    manifest: dict[str, Any],
) -> dict[str, PageViewModel]:
    """
    Resolve page asset slots from manifest and attach metadata to internal_state.
    Large binaries are NOT stored in repo; only manifest/metadata are resolved here.
    """
    updated = deepcopy(page_models)

    slots = manifest.get("slots") if isinstance(manifest, dict) else {}
    slots = slots if isinstance(slots, dict) else {}

    for vm in updated.values():
        vm.internal_state.setdefault("asset_slots", {})

        for slot_id in slots.keys():
            parsed = _parse_slot_for_page(slot_id=slot_id, page_id=vm.page_id, page_type=vm.page_type)
            if not parsed:
                continue
            slot_name = parsed["slot_name"]
            resolved = resolve_slot_asset(manifest, slot_id)

            vm.internal_state["asset_slots"][slot_name] = {
                "slot_id": slot_id,
                "asset_id": (resolved or {}).get("asset_id"),
                "resolved": resolved,
            }

            if slot_name == "hero" and vm.hero and resolved and isinstance(resolved.get("url"), str):
                vm.hero.image_url = resolved["url"]

    return updated


def _parse_slot_for_page(slot_id: str, *, page_id: str, page_type: str) -> dict[str, str] | None:
    # Expected format: <page_type>.<slot_name>.<page_id>
    if not isinstance(slot_id, str):
        return None
    prefix = f"{page_type}."
    suffix = f".{page_id}"
    if not slot_id.startswith(prefix) or not slot_id.endswith(suffix):
        return None
    slot_name = slot_id[len(prefix) : -len(suffix)]
    if not slot_name:
        return None
    return {"slot_name": slot_name}
