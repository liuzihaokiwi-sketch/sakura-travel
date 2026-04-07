"""Apply pre-computed editorial judgments to hotels and spots phase2b ledgers."""

import json

HOTEL_FILE = "data/kansai_spots/phase2_ledger/hotels_ledger_phase2b.json"
SPOT_FILE = "data/kansai_spots/phase2_ledger/spots_ledger_phase2b.json"
HOTEL_ED_FILE = "scripts/hotel_editorials.json"
SPOT_ED_FILE = "scripts/spot_editorials.json"


def apply_hotels():
    with open(HOTEL_FILE, encoding="utf-8") as f:
        hotels = json.load(f)
    with open(HOTEL_ED_FILE, encoding="utf-8") as f:
        editorials = json.load(f)

    updated = 0
    skipped = 0
    for h in hotels:
        if h["selection_status"] not in ("selected", "borderline"):
            continue
        name = h.get("name_ja", "")
        if name in editorials:
            ed = editorials[name]
            h["grade"] = ed["grade"]
            h["one_line_editorial_note"] = ed["one_line_editorial_note"]
            h["selection_tags"] = ed["selection_tags"]
            h["opus_reviewed"] = True
            updated += 1
        else:
            print(f"  [HOTEL] No editorial for: {repr(name)}")
            skipped += 1

    with open(HOTEL_FILE, "w", encoding="utf-8") as f:
        json.dump(hotels, f, ensure_ascii=False, indent=2)
    print(f"Hotels: updated={updated}, skipped={skipped}, saved to {HOTEL_FILE}")


def apply_spots():
    with open(SPOT_FILE, encoding="utf-8") as f:
        spots = json.load(f)
    with open(SPOT_ED_FILE, encoding="utf-8") as f:
        editorials = json.load(f)

    updated = 0
    skipped = 0
    for s in spots:
        if s["selection_status"] not in ("selected", "borderline"):
            continue
        name = s.get("name_ja", "")
        if name in editorials:
            ed = editorials[name]
            s["grade"] = ed["grade"]
            s["one_line_editorial_note"] = ed["one_line_editorial_note"]
            s["selection_tags"] = ed["selection_tags"]
            s["opus_reviewed"] = True
            updated += 1
        else:
            print(f"  [SPOT] No editorial for: {repr(name)}")
            skipped += 1

    with open(SPOT_FILE, "w", encoding="utf-8") as f:
        json.dump(spots, f, ensure_ascii=False, indent=2)
    print(f"Spots: updated={updated}, skipped={skipped}, saved to {SPOT_FILE}")


def main():
    print("Applying hotel editorials...")
    apply_hotels()
    print("\nApplying spot editorials...")
    apply_spots()
    print("\nDone.")


if __name__ == "__main__":
    main()
