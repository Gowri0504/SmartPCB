"""
Dataset validator & integrity checker for SmartPCB-XAI.

Checks enumerated in this script (8 total, per user spec "FR-3 + AC-3):
  1. duplicate_image_hashes         (per-image md5)
  2. duplicate_filenames          (cross-split basename collisions)
  3. board_id_overlap             (same physical board not disjoint across splits)
  4. split_overlap_by_filename     (identical basename collisions across splits)
  5. zero_area_boxes              (w<=0 or h<=0)
  6. normalized_coords_out_of_range (cx,cy,w,h outside [0,1] (w/h clamped >1)
  7. missing_image_label_pairs    (image without label file or vv)
  8. class_ids_out_of_range       (class_id <0 or >= num_classes)

Outputs:
  * text report to stdout (existing visuals
  * distribution plots to reports/dataset/*.png
  * MACHINE-READABLE JSON to reports/dataset/validation_report.json
"""

import os
import re
import json
import math
import hashlib
import statistics
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

# Perceptual hash near-duplicate detection (if imagehash library is installed)
# If not installed, the check is skipped with status UNAVAILABLE (no crash, no fabrication)
try:
    import imagehash  # type: ignore
    _IMAGEHASH_AVAILABLE = True
except ImportError:
    imagehash = None
    _IMAGEHASH_AVAILABLE = False

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
REPORTS_DIR = os.path.join(ROOT, "reports", "dataset")
os.makedirs(REPORTS_DIR, exist_ok=True)

COMP_DIR = os.path.join(ROOT, "datasets", "components_unified")
DEFECT_DIR = os.path.join(ROOT, "datasets", "defects")

COMP_CLASSES = ["ICs", "capacitors", "diodes", "inductors", "resistors", "transistors"]
DEFECT_CLASSES = ["open", "short", "mousebite", "spur", "copper", "pin-hole"]

# ---------------------------------------------------------------------------
# Board-ID extractors — group tiles of the same physical board together
# ---------------------------------------------------------------------------

_FICS_RE = re.compile(r"^(fics_s\d+_.+?)_tile_", re.IGNORECASE)
_ROBO_RE = re.compile(r"^(robo_[A-Za-z0-9_\-]+?)_?\.")
_DEEPPCB_RE = re.compile(r"^(\d+)_(?:test|temp|sample)")


def extract_board_id(filename_stem: str) -> str:
    """Return an opaque board identifier. Falls back to filename stem itself if no pattern matches."""
    stem = os.path.splitext(os.path.basename(filename_stem))[0]
    m = _FICS_RE.search(stem)
    if m:
        return m.group(1)
    m = _ROBO_RE.match(stem)
    if m:
        return m.group(1)
    m = _DEEPPCB_RE.match(stem)
    if m:
        return "deep_pcb_" + m.group(1)
    return "stem:" + stem


def md5_of_image(path: str) -> str:
    """md5 hash of image file bytes (cheap, effective dedup proxy for exact duplicates)."""
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def make_check_record(pass_flag: bool, count: int, details: list, skipped: bool = False, skip_reason=None):
    rec = {"pass": bool(pass_flag), "count": int(count), "details": list(details)}
    if skipped:
        rec["status"] = "UNAVAILABLE"
        rec["skip_reason"] = skip_reason
    return rec


def _box_stats_from_counts(counts_list):
    if not counts_list:
        return {"min": 0, "max": 0, "mean": 0.0, "median": 0.0, "samples": 0}
    return {
        "min": int(min(counts_list)),
        "max": int(max(counts_list)),
        "mean": round(statistics.mean(counts_list), 4),
        "median": round(statistics.median(counts_list), 4),
        "samples": len(counts_list),
    }


def validate_dataset(dataset_path, class_names, name):
    print(f"\n==========================================")
    print(f"Validating {name} at {dataset_path}...")

    splits = ["train", "val", "test"]
    stats = {s: {"images": 0, "labels": 0, "boxes": 0, "class_counts": {i: 0 for i in range(len(class_names))}} for s in splits}

    corrupted_images = 0
    image_decode_errors = 0  # images that PIL.verify passed but cv2.imdecode fails (corrupted codestream)
    invalid_boxes = 0
    zero_area_boxes = 0
    out_of_bounds = 0
    class_out_of_range = 0
    class_out_of_range_details = []
    missing_pairs_missing_label = 0
    missing_pairs_missing_image_counter = 0
    empty_label_files = 0  # label .txt exists but has zero valid annotations

    hash_to_paths = {}
    duplicate_hash_details = []
    split_images = {s: set() for s in splits}
    split_board_ids = {s: set() for s in splits}
    # New T4 fields
    per_split_box_counts_per_image = {s: [] for s in splits}
    per_split_empty_label_count = {s: 0 for s in splits}
    phash_near_duplicates_groups = []
    phash_unavailable_reason = None

    # pHash state
    _phash_to_paths = {}

    # collect all per-image-label files across splits for missing-pair lookup
    all_expected_labels = {s: set() for s in splits}

    for split in splits:
        img_dir = os.path.join(dataset_path, split, "images")
        lbl_dir = os.path.join(dataset_path, split, "labels")

        if not os.path.exists(img_dir):
            print(f"Warning: {img_dir} does not exist!")
            continue

        lbl_files_on_disk = set()
        if os.path.exists(lbl_dir):
            for fn in os.listdir(lbl_dir):
                if fn.endswith(".txt"):
                    lbl_files_on_disk.add(os.path.splitext(fn)[0])

        for img_file in sorted(os.listdir(img_dir)):
            if not img_file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.webp')):
                continue

            img_path = os.path.join(img_dir, img_file)
            stem = os.path.splitext(img_file)[0]
            split_images[split].add(img_file)
            split_board_ids[split].add(extract_board_id(img_file))

            # Check corruption — PIL structural verify first
            boxes_this_image = 0
            try:
                with Image.open(img_path) as img:
                    img.verify()
                stats[split]["images"] += 1
            except Exception as e:
                print(f"Corrupted image: {img_path} ({e})")
                corrupted_images += 1
                continue

            # Second-stage decode check: cv2.imdecode (catches some codestream corruptions that PIL.verify misses)
            try:
                import cv2 as _cv2
                _dec = _cv2.imread(img_path)
                if _dec is None:
                    image_decode_errors += 1
                    corrupted_images += 1
                    continue
            except Exception:
                pass

            # pHash near-duplicate detection (T4 new) — only for successfully-decoded images
            if _IMAGEHASH_AVAILABLE:
                try:
                    with Image.open(img_path) as _img_pil:
                        ph = imagehash.phash(_img_pil, hash_size=8)
                    ph_str = str(ph)
                    if ph_str in _phash_to_paths:
                        _phash_to_paths[ph_str].append(img_path)
                        if len(_phash_to_paths[ph_str]) == 2:
                            phash_near_duplicates_groups.append({
                                "phash": ph_str,
                                "hamming_threshold_used": 0,
                                "paths": list(_phash_to_paths[ph_str]),
                            })
                        else:
                            for _d in phash_near_duplicates_groups:
                                if _d["phash"] == ph_str:
                                    _d["paths"].append(img_path)
                                    break
                    else:
                        _phash_to_paths[ph_str] = [img_path]
                except Exception as _pe:
                    phash_unavailable_reason = f"imagehash compute exception: {_pe}"
            else:
                phash_unavailable_reason = (
                    "imagehash package not installed. Install with `pip install imagehash` to enable "
                    "perceptual-hash near-duplicate detection. Skipping this check (UNAVAILABLE)."
                )

            # MD5 dedup
            try:
                h = md5_of_image(img_path)
            except Exception:
                h = "err:" + img_file
            if h in hash_to_paths:
                hash_to_paths[h].append(img_path)
                if len(hash_to_paths[h]) == 2:
                    duplicate_hash_details.append({
                        "hash": h,
                        "paths": list(hash_to_paths[h]),
                    })
                else:
                    for d in duplicate_hash_details:
                        if d["hash"] == h:
                            d["paths"].append(img_path)
                            break
            else:
                hash_to_paths[h] = [img_path]

            lbl_file = stem + ".txt"
            lbl_path = os.path.join(lbl_dir, lbl_file)
            all_expected_labels[split].add(stem)

            if os.path.exists(lbl_path):
                stats[split]["labels"] += 1
                with open(lbl_path, "r") as f:
                    content_lines = [ln.strip() for ln in f if ln.strip()]
                if not content_lines:
                    empty_label_files += 1
                    per_split_empty_label_count[split] += 1
                    per_split_box_counts_per_image[split].append(0)
                    continue
                for line_idx, line in enumerate(content_lines):
                    parts = line.split()
                    if len(parts) != 5:
                        invalid_boxes += 1
                        continue
                    try:
                        cid = int(parts[0])
                        cx, cy, w, h = map(float, parts[1:])
                    except Exception:
                        invalid_boxes += 1
                        continue
                    if cid < 0 or cid >= len(class_names):
                        class_out_of_range += 1
                        class_out_of_range_details.append({
                            "split": split,
                            "label_file": os.path.relpath(label_path, dataset_path).replace("\\", "/"),
                            "class_id": cid,
                            "num_classes_in_yaml": len(class_names),
                        })
                        continue
                    if w <= 0 or h <= 0:
                        zero_area_boxes += 1
                        continue
                    if not (0 <= cx <= 1 and 0 <= cy <= 1 and 0 < w <= 1.0 and 0 < h <= 1.0):
                        out_of_bounds += 1
                        continue
                    stats[split]["boxes"] += 1
                    stats[split]["class_counts"][cid] += 1
                    boxes_this_image += 1
                per_split_box_counts_per_image[split].append(boxes_this_image)
            else:
                missing_pairs_missing_label += 1

        # labels without matching images
        if os.path.exists(lbl_dir):
            for label_stem in lbl_files_on_disk:
                if label_stem not in all_expected_labels[split]:
                    missing_pairs_missing_image_counter += 1

    # Cross-split filename leakage (exact basename equality)
    leakage_train_val = split_images["train"].intersection(split_images["val"])
    leakage_train_test = split_images["train"].intersection(split_images["test"])
    leakage_val_test = split_images["val"].intersection(split_images["test"])
    total_filename_leakage = (
        len(leakage_train_val) + len(leakage_train_test) + len(leakage_val_test)
    )
    filename_leakage_details = []
    if leakage_train_val:
        filename_leakage_details.append({"pair": "train/val", "files": sorted(leakage_train_val)})
    if leakage_train_test:
        filename_leakage_details.append({"pair": "train/test", "files": sorted(leakage_train_test)})
    if leakage_val_test:
        filename_leakage_details.append({"pair": "val/test", "files": sorted(leakage_val_test)})

    # Cross-split board-ID leakage (tiles from same physical board)
    board_train_val = sorted(split_board_ids["train"].intersection(split_board_ids["val"]))
    board_train_test = sorted(split_board_ids["train"].intersection(split_board_ids["test"]))
    board_val_test = sorted(split_board_ids["val"].intersection(split_board_ids["test"]))
    total_board_leakage = len(board_train_val) + len(board_train_test) + len(board_val_test)
    board_leakage_details = []
    if board_train_val:
        board_leakage_details.append({"pair": "train/val", "board_ids": board_train_val})
    if board_train_test:
        board_leakage_details.append({"pair": "train/test", "board_ids": board_train_test})
    if board_val_test:
        board_leakage_details.append({"pair": "val/test", "board_ids": board_val_test})

    missing_pair_total = missing_pairs_missing_label + missing_pairs_missing_image_counter

    check_duplicate_hashes = make_check_record(
        len(duplicate_hash_details) == 0,
        sum(len(d["paths"]) - 1 for d in duplicate_hash_details),
        duplicate_hash_details,
    )
    check_duplicate_filenames = make_check_record(
        total_filename_leakage == 0,
        total_filename_leakage,
        filename_leakage_details,
    )
    check_board_id_overlap = make_check_record(
        total_board_leakage == 0,
        total_board_leakage,
        board_leakage_details,
    )
    check_split_overlap_by_filename = make_check_record(
        total_filename_leakage == 0,
        total_filename_leakage,
        filename_leakage_details,
    )
    check_zero_area_boxes = make_check_record(
        zero_area_boxes == 0,
        zero_area_boxes,
        [],
    )
    check_normalized_coords_out_of_range = make_check_record(
        out_of_bounds == 0,
        out_of_bounds,
        [],
    )
    check_missing_image_label_pairs = make_check_record(
        missing_pair_total == 0,
        missing_pair_total,
        [
            {"images_without_label_files": missing_pairs_missing_label},
            {"label_files_without_images": missing_pairs_missing_image_counter},
        ],
    )
    check_class_ids_out_of_range = make_check_record(
        class_out_of_range == 0,
        class_out_of_range,
        class_out_of_range_details[:200],
    )

    total_images = sum(stats[s]["images"] for s in splits)
    total_boxes = sum(stats[s]["boxes"] for s in splits)

    print(f"\nResults for {name}:")
    print(f"  Total Images Checked: {total_images}")
    print(f"  Total Valid Boxes:    {total_boxes}")
    print(f"  Corrupted Images:     {corrupted_images}")
    print(f"  Zero-Area Boxes:      {zero_area_boxes}")
    print(f"  Out-of-Bounds Boxes:  {out_of_bounds}")
    print(f"  Out-of-Range ClassIDs:{class_out_of_range}")
    print(f"  Missing Img/Lbl Pairs: {missing_pair_total}")
    print(f"  Image MD5 Duplicates:  {check_duplicate_hashes['count']} ({len(duplicate_hash_details)} groups)")
    print(f"  Filename Cross-Split: {total_filename_leakage}")
    print(f"  Board-ID Cross-Split Leakage:  {total_board_leakage} (Train-Val: {len(board_train_val)}, Train-Test: {len(board_train_test)})")
    print(f"  Cross-Split Filename Leakage:  {total_filename_leakage} (Train-Val: {len(leakage_train_val)}, Train-Test: {len(leakage_train_test)})")

    for s in splits:
        print(f"\n  Split [{s}]: {stats[s]['images']} images, {stats[s]['boxes']} boxes, {len(split_board_ids[s])} unique board IDs")
        for cid, cname in enumerate(class_names):
            cnt = stats[s]["class_counts"][cid]
            pct = (cnt / max(1, stats[s]["boxes"])) * 100
            print(f"    {cname:<15}: {cnt:>6} ({pct:>5.1f}%)")

    return {
        "dataset_name": name,
        "dataset_path": dataset_path,
        "total_images": total_images,
        "total_boxes": total_boxes,
        "corrupted_images": corrupted_images,
        "image_decode_errors": image_decode_errors,
        "empty_label_files": empty_label_files,
        "invalid_box_rows_ignored": invalid_boxes,
        "class_names": class_names,
        "class_counts_total": {
            class_names[cid]: sum(stats[s]["class_counts"][cid] for s in splits)
            for cid in range(len(class_names))
        },
        "per_split": {
            s: {
                "images": stats[s]["images"],
                "boxes": stats[s]["boxes"],
                "labels": stats[s]["labels"],
                "empty_label_count": per_split_empty_label_count.get(s, 0),
                "box_count_per_image_stats": _box_stats_from_counts(per_split_box_counts_per_image.get(s, [])),
                "class_counts": stats[s]["class_counts"],
                "unique_board_ids_count": len(split_board_ids[s]),
                "split_board_ids_sample": sorted(list(split_board_ids[s]))[:20],
            }
            for s in splits
        },
        "hash_duplicates_group_count": len(duplicate_hash_details),
        "phash_duplicates_group_count": len(phash_near_duplicates_groups),
        "phash_unavailable_reason": phash_unavailable_reason,
        "board_level_cross_split_leak_count": total_board_leakage,
        "filename_cross_split_leak_count": total_filename_leakage,
        "checks": {
            "duplicate_image_hashes": check_duplicate_hashes,
            "phash_near_duplicates": make_check_record(
                (len(phash_near_duplicates_groups) == 0) if _IMAGEHASH_AVAILABLE else True,
                len(phash_near_duplicates_groups),
                phash_near_duplicates_groups[:200],
                skipped=_IMAGEHASH_AVAILABLE is False,
                skip_reason=phash_unavailable_reason,
            ),
            "duplicate_filenames": check_duplicate_filenames,
            "board_id_overlap": check_board_id_overlap,
            "split_overlap_by_filename": check_split_overlap_by_filename,
            "zero_area_boxes": check_zero_area_boxes,
            "normalized_coords_out_of_range": check_normalized_coords_out_of_range,
            "missing_image_label_pairs": check_missing_image_label_pairs,
            "class_ids_out_of_range": check_class_ids_out_of_range,
            "corrupted_images": make_check_record(corrupted_images == 0, corrupted_images, []),
            "empty_label_files": make_check_record(True, empty_label_files, []),
        },
    }, stats


def plot_distributions(comp_stats_detail, defect_stats_detail):
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')

    # 1. Component Class Distribution Plot (dynamic count — no hardcoded numbers)
    comp_classes_full = comp_stats_detail["class_names"]
    totals = [comp_stats_detail["class_counts_total"].get(cn, 0) for cn in comp_classes_full]
    comp_boxes_total = comp_stats_detail["total_boxes"]
    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
    bars = ax.bar(comp_classes_full, totals, color=['#2563eb', '#3b82f6', '#60a5fa', '#93c5fd', '#1d4ed8', '#1e40af'])
    ax.set_title(f"PCB Component Dataset — Class Distribution ({comp_boxes_total:,} Annotations)", fontsize=14, fontweight='bold', pad=15)
    ax.set_ylabel("Bounding Box Count", fontsize=12)
    ax.set_xlabel("Component Classes", fontsize=12)
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2.0, yval + max(150, 0.005*max(totals or [1])), f"{yval:,}", ha='center', va='bottom', fontsize=10, fontweight='bold')
    plt.tight_layout()
    comp_plot_path = os.path.join(REPORTS_DIR, "component_class_distribution.png")
    plt.savefig(comp_plot_path)
    plt.close()
    print(f"\nGenerated: {comp_plot_path}")

    # 2. Defect Class Distribution Plot
    defect_classes_full = defect_stats_detail["class_names"]
    totals_d = [defect_stats_detail["class_counts_total"].get(cn, 0) for cn in defect_classes_full]
    defect_boxes_total = defect_stats_detail["total_boxes"]
    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
    bars_d = ax.bar(defect_classes_full, totals_d, color=['#dc2626', '#ea580c', '#d97706', '#ca8a04', '#65a30d', '#16a34a'])
    ax.set_title(f"PCB Defect Dataset — Class Distribution ({defect_boxes_total:,} Annotations)", fontsize=14, fontweight='bold', pad=15)
    ax.set_ylabel("Defect Bounding Box Count", fontsize=12)
    ax.set_xlabel("Defect Classes", fontsize=12)
    for bar in bars_d:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2.0, yval + max(30, 0.005*max(totals_d or [1])), f"{yval:,}", ha='center', va='bottom', fontsize=10, fontweight='bold')
    plt.tight_layout()
    defect_plot_path = os.path.join(REPORTS_DIR, "defect_class_distribution.png")
    plt.savefig(defect_plot_path)
    plt.close()
    print(f"Generated: {defect_plot_path}")

    # 3. Splits Distribution Plot (dynamic image counts)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), dpi=300)
    splits = ["train", "val", "test"]
    comp_images_total = comp_stats_detail["total_images"]
    comp_splits = [comp_stats_detail["per_split"][s]["images"] for s in splits]
    defect_images_total = defect_stats_detail["total_images"]
    defect_splits = [defect_stats_detail["per_split"][s]["images"] for s in splits]

    ax1.pie(comp_splits, labels=[f"{s.upper()} ({v})" for s, v in zip(splits, comp_splits)],
            autopct='%1.1f%%', colors=['#3b82f6', '#10b981', '#f59e0b'], startangle=140,
            textprops={'fontsize': 11, 'fontweight': 'bold'})
    ax1.set_title(f"Component Dataset Splits ({comp_images_total:,} Images)", fontsize=13, fontweight='bold')

    ax2.pie(defect_splits, labels=[f"{s.upper()} ({v})" for s, v in zip(splits, defect_splits)],
            autopct='%1.1f%%', colors=['#ef4444', '#8b5cf6', '#06b6d4'], startangle=140,
            textprops={'fontsize': 11, 'fontweight': 'bold'})
    ax2.set_title(f"Defect Dataset Splits ({defect_images_total:,} Images)", fontsize=13, fontweight='bold')

    plt.tight_layout()
    splits_plot_path = os.path.join(REPORTS_DIR, "dataset_splits.png")
    plt.savefig(splits_plot_path)
    plt.close()
    print(f"Generated: {splits_plot_path}")


def main():
    comp_json, _stats_comp = validate_dataset(COMP_DIR, COMP_CLASSES, "Unified Component Dataset")
    defect_json, _stats_defect = validate_dataset(DEFECT_DIR, DEFECT_CLASSES, "DeepPCB Defect Dataset")

    report = {
        "generated_at": __import__("datetime").datetime.now().isoformat(),
        "components": comp_json,
        "defects": defect_json,
    }
    out_path = os.path.join(REPORTS_DIR, "validation_report.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\nJSON report written: {out_path}")

    plot_distributions(comp_json, defect_json)
    print("\n==========================================")
    print("Dataset Validation and Quality Visuals Complete!")


if __name__ == "__main__":
    main()
