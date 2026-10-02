"""
Final component-dataset audit (work order section 3).

Scans every component dataset variant, measures per-class statistics,
validates the Roboflow 4495-class -> 6-class remap, checks split leakage
by content hash, and writes a quarantine manifest for invalid annotations.

Outputs:
  reports/dataset/component_dataset_audit_final.json   (machine-readable)
  reports/dataset/component_quarantine_manifest.csv    (invalid annotations)
  stdout summary for COMPONENT_DATASET_AUDIT_FINAL.md

No labels are deleted or modified. Quarantine = manifest only.
"""
import os
import re
import csv
import json
import hashlib
import zipfile
from collections import defaultdict

from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
REPORTS_DIR = os.path.join(ROOT, "reports", "dataset")
os.makedirs(REPORTS_DIR, exist_ok=True)

CANONICAL = {0: "ICs", 1: "capacitors", 2: "diodes", 3: "inductors", 4: "resistors", 5: "transistors"}

VARIANTS = {
    "fics_tiled": (os.path.join(ROOT, "datasets", "fics_tiled"), "split"),
    "roboflow_remapped": (os.path.join(ROOT, "datasets", "roboflow_remapped"), "split"),
    "components_unified": (os.path.join(ROOT, "datasets", "components_unified"), "split"),
    "components_curated": (os.path.join(ROOT, "datasets", "components_curated"), "split"),
    "components_canonical": (os.path.join(ROOT, "datasets", "components_canonical"), "split"),
    "processed_fullres": (os.path.join(ROOT, "datasets", "processed"), "flat"),
    "processed_labels_v2": (os.path.join(ROOT, "datasets", "processed_labels_v2"), "flat"),
}

TINY_AREA_FRAC = (32.0 * 32.0) / (640.0 * 640.0)  # <32x32px equiv on a 640 tile


def md5_head(path, nbytes=65536):
    h = hashlib.md5()
    with open(path, "rb") as f:
        h.update(f.read(nbytes))
    return h.hexdigest()


def scan_variant(base, layout="split"):
    """Scan one dataset variant. Returns stats dict."""
    stats = {
        "splits": {},
        "issues": {"out_of_range_ids": 0, "malformed_lines": 0, "empty_label_files": 0,
                    "boxes_out_of_bounds": 0, "zero_size_boxes": 0, "missing_labels": 0},
        "quarantine": [],   # rows for manifest
        "image_hashes": {},  # hash -> [ {variant,split,file} ] (filled by caller)
    }
    hashes = {}
    if layout == "flat":
        iter_splits = [("fullres", os.path.join(base, "images"), os.path.join(base, "labels"))]
    else:
        iter_splits = [(sp, os.path.join(base, sp, "images"), os.path.join(base, sp, "labels"))
                       for sp in ["train", "val", "test"]]
    for split, img_dir, lbl_dir in iter_splits:
        if not os.path.isdir(img_dir):
            continue
        s = {"images": 0, "boxes": 0, "dims": defaultdict(int),
             "per_class": {c: {"images": 0, "boxes": 0, "areas": [], "tiny": 0} for c in CANONICAL}}
        img_files = sorted(f for f in os.listdir(img_dir) if f.lower().endswith((".jpg", ".jpeg", ".png")))
        for fname in img_files:
            img_path = os.path.join(img_dir, fname)
            stem = os.path.splitext(fname)[0]
            lbl_path = os.path.join(lbl_dir, stem + ".txt")
            s["images"] += 1
            try:
                with Image.open(img_path) as im:
                    w, h = im.size
            except Exception:
                w, h = 0, 0
            s["dims"][f"{w}x{h}"] += 1
            digest = md5_head(img_path)
            hashes.setdefault(digest, []).append({"split": split, "file": fname})

            if not os.path.exists(lbl_path):
                s["issues_row"] = True
                stats["issues"]["missing_labels"] += 1
                stats["quarantine"].append({"split": split, "file": fname, "reason": "missing_label_file"})
                continue
            lines = []
            try:
                with open(lbl_path, "r", encoding="utf-8") as f:
                    lines = [l for l in f.read().splitlines() if l.strip()]
            except Exception:
                stats["issues"]["malformed_lines"] += 1
                stats["quarantine"].append({"split": split, "file": fname, "reason": "unreadable_label_file"})
                continue
            if not lines:
                stats["issues"]["empty_label_files"] += 1
                continue
            classes_in_img = set()
            for line in lines:
                parts = line.split()
                if len(parts) < 5:
                    stats["issues"]["malformed_lines"] += 1
                    stats["quarantine"].append({"split": split, "file": fname, "reason": f"malformed_line:{line[:40]}"})
                    continue
                try:
                    cid = int(parts[0])
                    cx, cy, nw, nh = map(float, parts[1:5])
                except ValueError:
                    stats["issues"]["malformed_lines"] += 1
                    stats["quarantine"].append({"split": split, "file": fname, "reason": f"non_numeric:{line[:40]}"})
                    continue
                if cid not in CANONICAL:
                    stats["issues"]["out_of_range_ids"] += 1
                    stats["quarantine"].append({"split": split, "file": fname, "reason": f"out_of_range_class:{cid}"})
                    continue
                if nw <= 0 or nh <= 0:
                    stats["issues"]["zero_size_boxes"] += 1
                    stats["quarantine"].append({"split": split, "file": fname, "reason": f"zero_size_box"})
                    continue
                if cx < 0 or cy < 0 or cx > 1 or cy > 1 or nw > 1 or nh > 1:
                    stats["issues"]["boxes_out_of_bounds"] += 1
                    stats["quarantine"].append({"split": split, "file": fname, "reason": "box_out_of_[0,1]"})
                    continue
                area = nw * nh
                s["boxes"] += 1
                pc = s["per_class"][cid]
                pc["boxes"] += 1
                pc["areas"].append(area)
                classes_in_img.add(cid)
            for cid in classes_in_img:
                s["per_class"][cid]["images"] += 1
        # finalize per-class stats
        for cid, pc in s["per_class"].items():
            areas = pc["areas"]
            pc["avg_area_norm"] = round(sum(areas) / len(areas), 6) if areas else None
            pc["min_area_norm"] = round(min(areas), 6) if areas else None
            pc["max_area_norm"] = round(max(areas), 6) if areas else None
            pc["tiny_boxes"] = sum(1 for a in areas if a < TINY_AREA_FRAC)
            del pc["areas"]
        s["dims"] = dict(sorted(s["dims"].items(), key=lambda kv: -kv[1])[:8])
        stats["splits"][split] = s
    stats["image_hashes"] = hashes
    return stats


def audit_roboflow_mapping():
    """Re-run the deployed remap logic over the 4495 original class names and
    categorize risky mappings."""
    zpath = os.path.join(ROOT, "datasets", "PCB-Components.v1495i.yolov11.zip")
    if not os.path.exists(zpath):
        return {"error": "zip not found"}
    import yaml
    with zipfile.ZipFile(zpath) as z:
        names = yaml.safe_load(z.read("data.yaml").decode())["names"]

    def get_canonical_class(nl):
        nl = nl.lower().strip()
        if nl.startswith("-component text-") or "test point" in nl or "jumper" in nl or \
           "button" in nl or "switch" in nl or "connector" in nl or "header" in nl:
            return None, "excluded"
        if "resistor" in nl or re.search(r'\br\d+\b', nl):
            return 4, "word" if "resistor" in nl else "designator_only"
        if "capacitor" in nl or re.search(r'\bc\d+\b', nl):
            return 1, "word" if "capacitor" in nl else "designator_only"
        if "diode" in nl or "led" in nl or re.search(r'\bd\d+\b', nl):
            if "led" in nl and "diode" not in nl:
                return 2, "led_to_diode"
            return 2, "word" if "diode" in nl else "designator_only"
        if "inductor" in nl or "choke" in nl or re.search(r'\bl\d+\b', nl):
            return 3, "word" if ("inductor" in nl or "choke" in nl) else "designator_only"
        if "transistor" in nl or "mosfet" in nl or re.search(r'\bq\d+\b', nl):
            return 5, "word" if ("transistor" in nl or "mosfet" in nl) else "designator_only"
        if "ic" in nl or "chip" in nl or "processor" in nl or "eeprom" in nl or re.search(r'\bu\d+\b', nl):
            return 0, "substring_ic" if ("ic" in nl and not ("chip" in nl or "processor" in nl or "eeprom" in nl)) else "word"
        return None, "unmapped"

    cat_counts = defaultdict(int)
    examples = defaultdict(list)
    for name in names:
        cid, cat = get_canonical_class(name)
        cat_counts[cat] += 1
        if cat in ("designator_only", "substring_ic", "led_to_diode") and len(examples[cat]) < 12:
            examples[cat].append(name)
    return {"total_classes": len(names), "category_counts": dict(cat_counts),
            "risky_examples": {k: v for k, v in examples.items()}}


def verify_fics_label_mapping(lbl_dir=None):
    """Join the raw FICS-PCB DSLR CSV annotations (human component_type labels) to
    YOLO label files (default: legacy datasets/processed/labels) and recover, by box-coordinate matching, the
    type -> class-id mapping that was ACTUALLY used when the labels were written.
    Detects silent class corruption and silently dropped ground-truth boxes.

    Canonical mapping (per COMPONENT_CLASS_SCHEMA.md): ICs=0, capacitors=1,
    diodes=2, inductors=3, resistors=4, transistors=5.
    """
    CANON = {"ICs": 0, "capacitors": 1, "diodes": 2, "inductors": 3,
             "resistors": 4, "transistors": 5}
    raw = os.path.join(ROOT, "datasets", "raw")
    if lbl_dir is None:
        lbl_dir = os.path.join(ROOT, "datasets", "processed", "labels")
    W, H = 8256, 5504  # verified identical for all 9 DSLR board images

    result = {"files_checked": 0, "type_to_label_id": {}, "per_type_gt_boxes": {},
              "mislabeled_boxes": 0, "correct_boxes": 0, "dropped_gt_boxes": 0,
              "dropped_by_type": {}, "out_of_schema_label_ids": {}, "corrupted_files": []}

    for sample in sorted(os.listdir(raw)):
        ann = os.path.join(raw, sample, "DSLR", "annotation")
        if not os.path.isdir(ann):
            continue
        for f in sorted(os.listdir(ann)):
            if not f.endswith(".csv"):
                continue
            # GT boxes grouped by (image_name, type)
            gt = []
            with open(os.path.join(ann, f), newline="", encoding="utf-8") as fh:
                for row in csv.DictReader(fh):
                    t = str(row.get("component_type", "")).strip()
                    img_name = str(row.get("image_name", "")).strip()
                    try:
                        b = json.loads(row["component_location"])
                    except (ValueError, KeyError):
                        continue
                    gt.append((img_name, t, b["x"], b["y"], b["width"], b["height"]))
            if not gt:
                continue
            result["files_checked"] += 1
            for _, t, *_ in gt:
                result["per_type_gt_boxes"][t] = result["per_type_gt_boxes"].get(t, 0) + 1

            # label file for this CSV (image_name .tif -> .txt, with naming variants)
            img_names = {g[0] for g in gt}
            lbl_path = None
            for iname in img_names:
                base = os.path.splitext(iname)[0]
                for cand in (base + ".txt", f"{sample}_{base}.txt"):
                    p = os.path.join(lbl_dir, cand)
                    if os.path.exists(p):
                        lbl_path = p
                        break
                if lbl_path:
                    break
            if lbl_path is None:
                result["corrupted_files"].append({"file": f, "issue": "label_file_not_found"})
                result["dropped_gt_boxes"] += len(gt)
                continue

            labels = []
            with open(lbl_path, "r", encoding="utf-8") as fh:
                for line in fh:
                    parts = line.split()
                    if len(parts) >= 5:
                        try:
                            labels.append((int(parts[0]), *map(float, parts[1:5])))
                        except ValueError:
                            pass
            used = [False] * len(labels)
            votes = defaultdict(int)  # (type, cid) -> count
            for iname, t, x, y, w, h in gt:
                exp = ((x + w / 2) / W, (y + h / 2) / H, w / W, h / H)
                best, best_d = -1, 1e9
                for i, (cid, cx, cy, nw, nh) in enumerate(labels):
                    if used[i]:
                        continue
                    d = sum((a - b) ** 2 for a, b in zip(exp, (cx, cy, nw, nh)))
                    if d < best_d:
                        best, best_d = i, d
                if best >= 0 and best_d < 1e-6:
                    used[best] = True
                    votes[(t, labels[best][0])] += 1
                else:
                    result["dropped_gt_boxes"] += 1
                    result["dropped_by_type"][t] = result["dropped_by_type"].get(t, 0) + 1
            for (t, cid), n in votes.items():
                result["type_to_label_id"][t] = cid
                if cid == CANON.get(t):
                    result["correct_boxes"] += n
                else:
                    result["mislabeled_boxes"] += n
                    result["out_of_schema_label_ids"][str(cid)] = result["out_of_schema_label_ids"].get(str(cid), 0) + n
            # label lines never matched to GT = phantom/extra annotations
            result["extra_label_boxes"] = result.get("extra_label_boxes", 0) + sum(1 for u in used if not u)

    result["verdict"] = "CORRUPTED" if result["mislabeled_boxes"] > 0 or result["dropped_gt_boxes"] > 0 else "OK"
    return result


def cross_split_leakage(stats):
    """Content-hash duplicates that appear in MORE THAN ONE split of the same variant."""
    leaks = []
    for digest, occ in stats["image_hashes"].items():
        splits = {o["split"] for o in occ}
        if len(splits) > 1:
            leaks.append({"hash": digest, "splits": sorted(splits), "files": [o["file"] for o in occ][:6]})
    return leaks


def cross_variant_overlap(all_stats):
    """Same content hash appearing in different VARIANTS (expected by construction
    for fics_tiled -> components_unified and roboflow_remapped -> components_unified)."""
    variant_hash_split = {}
    for vname, st in all_stats.items():
        for digest, occ in st["image_hashes"].items():
            for o in occ:
                variant_hash_split.setdefault(digest, set()).add(f"{vname}/{o['split']}")
    suspicious = []
    for digest, vs in variant_hash_split.items():
        # same variant, multiple splits already caught; flag unified-split conflicts:
        splits_in_unified = {v.split("/")[1] for v in vs if v.startswith("components_unified/")}
        if len(splits_in_unified) > 1:
            suspicious.append({"hash": digest, "locations": sorted(vs)})
    return suspicious


def main():
    all_stats = {}
    for vname, (vpath, layout) in VARIANTS.items():
        if not os.path.isdir(vpath):
            continue
        print(f"Scanning {vname} ...")
        st = scan_variant(vpath, layout)
        st["cross_split_leaks"] = cross_split_leakage(st)
        all_stats[vname] = st

    print("Verifying FICS label class mapping against raw CSV annotations ...")
    fics_map = verify_fics_label_mapping()

    print("Auditing Roboflow mapping ...")
    robo_map = audit_roboflow_mapping()

    print("Cross-variant overlap ...")
    overlap = cross_variant_overlap(all_stats)

    # ---- console summary ----
    for vname, st in all_stats.items():
        print(f"\n=== {vname} ===")
        tot = {"images": 0, "boxes": 0}
        agg = {c: {"images": 0, "boxes": 0, "tiny": 0} for c in CANONICAL}
        for split, s in st["splits"].items():
            tot["images"] += s["images"]; tot["boxes"] += s["boxes"]
            for c in CANONICAL:
                agg[c]["images"] += s["per_class"][c]["images"]
                agg[c]["boxes"] += s["per_class"][c]["boxes"]
                agg[c]["tiny"] += s["per_class"][c]["tiny_boxes"]
        print(f"  totals: {tot['images']} images / {tot['boxes']} boxes")
        for c, cname in CANONICAL.items():
            a = agg[c]
            print(f"  {cname:<12} imgs={a['images']:<5} boxes={a['boxes']:<6} tiny={a['tiny']}")
        print(f"  issues: {st['issues']}")
        print(f"  cross-split hash leaks: {len(st['cross_split_leaks'])}")
        for sp, s in st["splits"].items():
            print(f"    {sp}: {s['images']} imgs / {s['boxes']} boxes / dims {list(s['dims'].items())[:3]}")

    print("\n=== Roboflow mapping categories ===")
    print(json.dumps(robo_map.get("category_counts", {}), indent=1))
    for cat, exs in robo_map.get("risky_examples", {}).items():
        print(f"  {cat}: {exs[:4]}")

    print("\n=== FICS label class-mapping verification (raw CSV vs processed labels) ===")
    print(f"  files checked:        {fics_map['files_checked']}")
    print(f"  GT boxes by type:     {fics_map['per_type_gt_boxes']}")
    print(f"  actual type->label id: {fics_map['type_to_label_id']}")
    print(f"  correct boxes:        {fics_map['correct_boxes']}")
    print(f"  MISLABELED boxes:     {fics_map['mislabeled_boxes']}")
    print(f"  dropped GT boxes:     {fics_map['dropped_gt_boxes']} (by type: {fics_map['dropped_by_type']})")
    print(f"  extra label boxes:    {fics_map.get('extra_label_boxes', 0)}")
    print(f"  VERDICT:              {fics_map['verdict']}")

    print(f"\n=== unified split conflicts by hash: {len(overlap)} ===")
    for o in overlap[:5]:
        print(" ", o)

    # ---- persist ----
    out = {
        "generated": "2026-09-23",
        "variants": {v: {k: val for k, val in st.items() if k != "image_hashes"} for v, st in all_stats.items()},
        "roboflow_mapping_audit": robo_map,
        "fics_label_mapping_verification": fics_map,
        "components_unified_split_conflicts": overlap,
    }
    with open(os.path.join(REPORTS_DIR, "component_dataset_audit_final.json"), "w") as f:
        json.dump(out, f, indent=1)

    qrows = []
    for vname, st in all_stats.items():
        for q in st["quarantine"]:
            qrows.append({"variant": vname, **q})
    # FICS full-res label corruption: one manifest row per affected label file
    if fics_map.get("verdict") == "CORRUPTED":
        for sample in sorted(os.listdir(os.path.join(ROOT, "datasets", "raw"))):
            ann = os.path.join(ROOT, "datasets", "raw", sample, "DSLR", "annotation")
            if not os.path.isdir(ann):
                continue
            for f in sorted(os.listdir(ann)):
                if f.endswith(".csv"):
                    qrows.append({"variant": "processed_fullres", "split": "fullres",
                                  "file": f.replace(".csv", ".txt"),
                                  "reason": "fics_class_map_corruption:mislabeled_or_dropped_boxes"})
    with open(os.path.join(REPORTS_DIR, "component_quarantine_manifest.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["variant", "split", "file", "reason"])
        w.writeheader()
        w.writerows(qrows)
    print(f"\nQuarantine manifest rows: {len(qrows)} -> reports/dataset/component_quarantine_manifest.csv")
    print("Audit JSON -> reports/dataset/component_dataset_audit_final.json")


if __name__ == "__main__":
    main()
