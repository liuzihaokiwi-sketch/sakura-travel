from __future__ import annotations

from app.domains.rendering.asset_manifest import build_manifest_from_material_pack


def test_asset_manifest_collects_metadata_only(tmp_path):
    root = tmp_path / "北海道"
    hotel_dir = root / "酒店素材"
    food_dir = root / "美食素材"
    hotel_dir.mkdir(parents=True)
    food_dir.mkdir(parents=True)

    (hotel_dir / "room.jpg").write_bytes(b"jpg-bytes")
    (food_dir / "soup.png").write_bytes(b"png-bytes")
    (food_dir / "clip.mp4").write_bytes(b"mp4-bytes")
    (food_dir / "ignore.txt").write_text("text", encoding="utf-8")

    manifest = build_manifest_from_material_pack(str(root), circle_id="hokkaido_city_circle")
    data = manifest.to_dict()

    assert data["manifest_version"] == "asset_manifest_v1"
    assert data["export_targets"] == ["h5", "pdf"]
    assert len(data["records"]) == 3

    categories = {r["category"] for r in data["records"]}
    media_types = {r["media_type"] for r in data["records"]}
    assert "hotel" in categories
    assert "food" in categories
    assert media_types == {"image", "video"}

    assert all("bytes_size" in r for r in data["records"])
    assert all("relative_path" in r for r in data["records"])
