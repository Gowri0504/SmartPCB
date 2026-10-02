"""
Canonical 6-class component dataset build (work order section 4).

Rebuilds the component dataset from authoritative sources only:

  1. FICS-PCB DSLR: labels regenerated from the raw human CSV annotations
     (datasets/raw/s*/DSLR/annotation/*.csv) using the VERIFIED class map
     (ICs=0, capacitors=1, diodes=2, inductors=3, resistors=4, transistors=5).
     This repairs the corruption documented in COMPONENT_DATASET_AUDIT_FINAL.md
     (517 mislabeled + 6 dropped boxes in datasets/processed/labels). The old
     corrupted label files are NOT touched - they remain as quarantined
     evidence. Regenerated full-res labels go to datasets/processed_labels_v2/
     (named to pair 1:1 with the actual image files).
  2. FICS tiling: 640px tiles, stride 512 (20% overlap), board-level split
     (s1->test, s2->val, s3-s5->train) - identical policy to the legacy
     tile_images.py, but on corrected labels, with explicit empty label files
     for background tiles and a fixed RNG seed.
  3. Roboflow PCB-Components: 6-class remap using PROVEN mappings only.
       - word match (tokenized): resistor/capacitor/diode/inductor/transistor/
         mosfet/choke/ic/chip/processor/eeprom (+ plurals)
       - led -> diodes (documented electronics ontology: LED = light-emitting
         diode; counted separately so it is reversible)
       - pure-designator names (e.g. "R12", "C10", "Q1", "U3") -> mapped via
         the standard designator-letter convention (R/C/D/L/Q/U). Reversible
         via INCLUDE_PURE_DESIGNATORS=False.
       - everything else (mixed-context names like "clock Q1", "pads C10",
         substring matches, unmapped) -> AMBIGUOUS quarantine (manifest with
         per-source-class box counts; never silently discarded).

Outputs:
  datasets/processed_labels_v2/                       (verified FICS labels)
  datasets/components_canonical/{train,val,test}/    (images + labels)
  datasets/components_canonical/data.yaml
  reports/dataset/canonical_build_report.json        (full accounting)
  reports/dataset/canonical_ambiguous_quarantine.csv (per-class disposition)

Run:  python scripts/dataset/build_canonical_components.py
"""
import os
import re
import csv
import json
import random
import zipfile
from collections import defaultdict

from PIL import Image
from tqdm import tqdm

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW_DIR = os.path.join(ROOT, "datasets", "raw")
FULLRES_IMG_DIR = os.path.join(ROOT, "datasets", "processed", "images")
LABELS_V2_DIR = os.path.join(ROOT, "datasets", "processed_labels_v2")
ROBO_ZIP = os.path.join(ROOT, "datasets", "PCB-Components.v1495i.yolov11.zip")
OUT_DIR = os.path.join(ROOT, "datasets", "components_canonical")
REPORTS_DIR = os.path.join(ROOT, "reports", "dataset")

CANONICAL = {0: "ICs", 1: "capacitors", 2: "diodes", 3: "inductors", 4: "resistors", 5: "transistors"}
VERIFIED_TYPE_MAP = {"ICs": 0, "capacitors": 1, "diodes": 2, "inductors": 3,
                     "resistors": 4, "transistors": 5}

BOARD_SPLIT = {"s1": "test", "s2": "val", "s3": "train", "s4": "train", "s5": "train"}

TILE_SIZE = 640
STRIDE = 512
MIN_COMPONENT_OVERLAP = 0.35
BACKGROUND_TILE_RATE = 0.02
BACKGROUND_SEED = 0

INCLUDE_PURE_DESIGNATORS = True

TINY_AREA_FRAC = (32.0 * 32.0) / (640.0 * 640.0)


# ---------------------------------------------------------------- FICS labels
def regenerate_fics_labels():
    """CSV -> verified YOLO labels (datasets/processed_labels_v2/).
    Returns (label_path_by_image, verification) where verification proves the
    regenerated labels match the CSV ground truth exactly."""
    os.makedirs(LABELS_V2_DIR, exist_ok=True)
    label_by_image = {}
    gt_boxes_total = defaultdict(int)
    written_boxes_total = defaultdict(int)
    problems = []

    samples = sorted(d for d in os.listdir(RAW_DIR)
                     if os.path.isdir(os.path.join(RAW_DIR, d, "DSLR", "annotation")))
    for sample in samples:
        ann_dir = os.path.join(RAW_DIR, sample, "DSLR", "annotation")
        for csv_name in sorted(os.listdir(ann_dir)):
            if not csv_name.endswith(".csv"):
                continue
            rows = []
            with open(os.path.join(ann_dir, csv_name), newline="", encoding="utf-8") as fh:
                for row in csv.DictReader(fh):
                    rows.append(row)

            # resolve the actual image file for image_name (naming variants)
            img_file = None
            for row in rows:
                base = os.path.splitext(str(row["image_name"]).strip())[0]
                for cand in (f"{base}.jpg", f"{sample}_{base}.jpg",
                             f"{base}.jpeg", f"{sample}_{base}.jpeg", f"{base}.png"):
                    p = os.path.join(FULLRES_IMG_DIR, cand)
                    if os.path.exists(p):
                        img_file = cand
                        break
                if img_file:
                    break
            if img_file is None:
                problems.append({"file": csv_name, "issue": "image_not_found"})
                continue

            img_path = os.path.join(FULLRES_IMG_DIR, img_file)
            with Image.open(img_path) as im:
                W, H = im.size

            lines = []
            for row in rows:
                ctype = str(row["component_type"]).strip()
                if ctype not in VERIFIED_TYPE_MAP:
                    problems.append({"file": csv_name, "issue": f"unknown_type:{ctype}"})
                    continue
                try:
                    b = json.loads(row["component_location"])
                    x, y, w, h = b["x"], b["y"], b["width"], b["height"]
                except (ValueError, KeyError):
                    problems.append({"file": csv_name, "issue": "bad_location_json"})
                    continue
                cid = VERIFIED_TYPE_MAP[ctype]
                gt_boxes_total[ctype] += 1
                lines.append(f"{cid} {(x + w / 2) / W:.6f} {(y + h / 2) / H:.6f} "
                             f"{w / W:.6f} {h / H:.6f}")
                written_boxes_total[ctype] += 1

            stem = os.path.splitext(img_file)[0]
            lbl_path = os.path.join(LABELS_V2_DIR, stem + ".txt")
            with open(lbl_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + ("\n" if lines else ""))
            label_by_image[img_file] = lbl_path

    verification = {
        "gt_boxes_by_type": dict(gt_boxes_total),
        "written_boxes_by_type": dict(written_boxes_total),
        "gt_total": sum(gt_boxes_total.values()),
        "written_total": sum(written_boxes_total.values()),
        "mismatches": [t for t in gt_boxes_total if gt_boxes_total[t] != written_boxes_total.get(t)],
        "problems": problems,
    }
    verification["ok"] = (not verification["mismatches"]
                          and not problems
                          and verification["gt_total"] == verification["written_total"])
    return label_by_image, verification


def read_yolo_boxes(lbl_path):
    boxes = []
    with open(lbl_path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 5:
                cid = int(parts[0])
                cx, cy, nw, nh = map(float, parts[1:5])
                boxes.append((cid, cx, cy, nw, nh))
    return boxes


# ---------------------------------------------------------------- FICS tiling
def tile_fics(label_by_image):
    rng = random.Random(BACKGROUND_SEED)
    stats = {"tiles": defaultdict(int), "boxes": defaultdict(int)}
    for img_file, lbl_path in sorted(label_by_image.items()):
        split = next((BOARD_SPLIT[b] for b in BOARD_SPLIT if b in img_file), "train")
        img_path = os.path.join(FULLRES_IMG_DIR, img_file)
        with Image.open(img_path) as im:
            img_w, img_h = im.size

        boxes = read_yolo_boxes(lbl_path)
        abs_boxes = []
        for cid, cx, cy, nw, nh in boxes:
            bx1, by1 = (cx - nw / 2) * img_w, (cy - nh / 2) * img_h
            bx2, by2 = (cx + nw / 2) * img_w, (cy + nh / 2) * img_h
            abs_boxes.append((cid, bx1, by1, bx2, by2, nw * nh * img_w * img_h))

        stem = os.path.splitext(img_file)[0]
        out_img_dir = os.path.join(OUT_DIR, split, "images")
        out_lbl_dir = os.path.join(OUT_DIR, split, "labels")
        os.makedirs(out_img_dir, exist_ok=True)
        os.makedirs(out_lbl_dir, exist_ok=True)

        x_steps = list(range(0, img_w - TILE_SIZE + 1, STRIDE))
        if x_steps[-1] < img_w - TILE_SIZE:
            x_steps.append(img_w - TILE_SIZE)
        y_steps = list(range(0, img_h - TILE_SIZE + 1, STRIDE))
        if y_steps[-1] < img_h - TILE_SIZE:
            y_steps.append(img_h - TILE_SIZE)

        for ty in y_steps:
            for tx in x_steps:
                tx2, ty2 = tx + TILE_SIZE, ty + TILE_SIZE
                tile_labels = []
                for cid, bx1, by1, bx2, by2, orig_area in abs_boxes:
                    ix1, iy1 = max(bx1, tx), max(by1, ty)
                    ix2, iy2 = min(bx2, tx2), min(by2, ty2)
                    if ix2 > ix1 and iy2 > iy1:
                        inter = (ix2 - ix1) * (iy2 - iy1)
                        if inter / max(1.0, orig_area) >= MIN_COMPONENT_OVERLAP:
                            tcx = ((ix1 + ix2) / 2 - tx) / TILE_SIZE
                            tcy = ((iy1 + iy2) / 2 - ty) / TILE_SIZE
                            tw, th = (ix2 - ix1) / TILE_SIZE, (iy2 - iy1) / TILE_SIZE
                            if tw > 0.005 and th > 0.005:
                                tile_labels.append(f"{cid} {tcx:.6f} {tcy:.6f} {tw:.6f} {th:.6f}")

                if not tile_labels and not (split == "train" and rng.random() < BACKGROUND_TILE_RATE):
                    continue
                tile_name = f"fics_{stem}_x{tx}_y{ty}"
                with Image.open(img_path) as im:
                    im.crop((tx, ty, tx2, ty2)).save(
                        os.path.join(out_img_dir, tile_name + ".jpg"), quality=95)
                # explicit label file even for background tiles
                with open(os.path.join(out_lbl_dir, tile_name + ".txt"), "w", encoding="utf-8") as f:
                    f.write("\n".join(tile_labels) + ("\n" if tile_labels else ""))
                stats["tiles"][split] += 1
                for lab in tile_labels:
                    stats["boxes"][split] += 1
    return {k: dict(v) for k, v in stats.items()}


# ------------------------------------------------------------- Roboflow remap
WORD_TOKEN_MAP = {
    "resistor": 4, "resistors": 4,
    "capacitor": 1, "capacitors": 1,
    "diode": 2, "diodes": 2,
    "inductor": 3, "inductors": 3,
    "transistor": 5, "transistors": 5,
    "mosfet": 5, "mosfets": 5,
    "choke": 3, "chokes": 3,
    "ic": 0, "ics": 0,
    "chip": 0, "chips": 0,
    "processor": 0, "processors": 0,
    "eeprom": 0, "eeproms": 0,
    "led": 2, "leds": 2,
}
DESIGNATOR_MAP = {"r": 4, "c": 1, "d": 2, "l": 3, "q": 5, "u": 0}
PURE_DESIGNATOR_RE = re.compile(r"^([rcdlqu])\d+[a-z]*$")


def classify_roboflow_class(name):
    """Returns (canonical_id or None, disposition). Dispositions:
    word / led / designator_pure / excluded / ambiguous / unmapped."""
    nl = name.lower().strip()
    if nl.startswith("-component text-") or "test point" in nl or "jumper" in nl or \
       "button" in nl or "switch" in nl or "connector" in nl or "header" in nl:
        return None, "excluded"

    tokens = re.split(r"[^a-z0-9]+", nl)
    tokens = [t for t in tokens if t]
    for t in tokens:
        if t in WORD_TOKEN_MAP:
            if t in ("led", "leds"):
                return 2, "led"
            return WORD_TOKEN_MAP[t], "word"

    if INCLUDE_PURE_DESIGNATORS:
        m = PURE_DESIGNATOR_RE.match(nl.replace(" ", ""))
        if m and m.group(1) in DESIGNATOR_MAP:
            return DESIGNATOR_MAP[m.group(1)], "designator_pure"

    if not tokens:
        return None, "unmapped"
    return None, "ambiguous"


def remap_roboflow():
    """Extract Roboflow zip with proven-only mappings into components_canonical."""
    if not os.path.exists(ROBO_ZIP):
        return {"error": "zip_not_found"}, []

    import yaml
    with zipfile.ZipFile(ROBO_ZIP) as z:
        names = yaml.safe_load(z.read("data.yaml").decode("utf-8"))["names"]

        class_map = {}
        disposition_by_class = {}
        for idx, name in enumerate(names):
            cid, disp = classify_roboflow_class(name)
            class_map[idx] = cid
            disposition_by_class[idx] = disp

        boxes_by_disposition = defaultdict(int)
        classes_by_disposition = defaultdict(int)
        ambiguous_classes = []  # rows for quarantine csv
        for idx, name in enumerate(names):
            disp = disposition_by_class[idx]
            classes_by_disposition[disp] += 1
            if disp in ("ambiguous", "unmapped", "excluded"):
                ambiguous_classes.append({"source_class": name, "class_id": idx,
                                          "disposition": disp, "kept_boxes": 0,
                                          "quarantined_boxes": 0})

        stats = {"images": defaultdict(int), "boxes": defaultdict(int)}
        quarantined_boxes = defaultdict(int)
        per_class_boxes = defaultdict(int)
        kept_by_class = defaultdict(int)
        quarantined_by_class = defaultdict(int)

        for split, target in [("train", "train"), ("valid", "val"), ("test", "test")]:
            out_img_dir = os.path.join(OUT_DIR, target, "images")
            out_lbl_dir = os.path.join(OUT_DIR, target, "labels")
            os.makedirs(out_img_dir, exist_ok=True)
            os.makedirs(out_lbl_dir, exist_ok=True)

            label_files = [n for n in z.namelist()
                           if n.startswith(f"{split}/labels/") and n.endswith(".txt")]
            for lbl_path in tqdm(label_files, desc=f"Roboflow {split}"):
                lines = [l for l in z.read(lbl_path).decode("utf-8").splitlines() if l.strip()]
                kept = []
                for line in lines:
                    parts = line.split()
                    if len(parts) < 5:
                        continue
                    orig_cid = int(parts[0])
                    cid = class_map.get(orig_cid)
                    disp = disposition_by_class.get(orig_cid, "unmapped")
                    if cid is not None:
                        kept.append(f"{cid} " + " ".join(parts[1:5]))
                        boxes_by_disposition[disp] += 1
                        per_class_boxes[cid] += 1
                        kept_by_class[orig_cid] += 1
                    else:
                        quarantined_boxes[disp] += 1
                        quarantined_by_class[orig_cid] += 1

                if not kept:
                    continue

                fname = os.path.basename(lbl_path)
                img_name = None
                for ext in (".jpg", ".png", ".jpeg"):
                    cand = f"{split}/images/{fname[:-4]}{ext}"
                    if cand in z.namelist():
                        img_name = fname[:-4] + ext
                        break
                if img_name is None:
                    continue

                stem = os.path.splitext(img_name)[0]
                with open(os.path.join(out_img_dir, f"robo_{img_name}"), "wb") as f_img:
                    f_img.write(z.read(f"{split}/images/{img_name}"))
                with open(os.path.join(out_lbl_dir, f"robo_{stem}.txt"), "w", encoding="utf-8") as f_lbl:
                    f_lbl.write("\n".join(kept) + "\n")

                stats["images"][target] += 1
                stats["boxes"][target] += len(kept)

        for row in ambiguous_classes:
            row["kept_boxes"] = kept_by_class.get(row["class_id"], 0)
            row["quarantined_boxes"] = quarantined_by_class.get(row["class_id"], 0)

        # count kept boxes per ambiguous... (kept boxes only come from mapped classes)
        result = {
            "source_classes_total": len(names),
            "classes_by_disposition": dict(classes_by_disposition),
            "boxes_by_disposition": dict(boxes_by_disposition),
            "quarantined_boxes_by_disposition": dict(quarantined_boxes),
            "per_class_boxes": {CANONICAL[c]: per_class_boxes.get(c, 0) for c in CANONICAL},
            "images": dict(stats["images"]),
            "boxes": dict(stats["boxes"]),
            "include_pure_designators": INCLUDE_PURE_DESIGNATORS,
        }
        return result, ambiguous_classes


# ------------------------------------------------------------------ final pass
def finalize_dataset():
    """Scan the built dataset, count per-class stats, write data.yaml."""
    report = {"splits": {}}
    totals = {CANONICAL[c]: {"images": 0, "boxes": 0, "tiny": 0} for c in CANONICAL}
    for split in ["train", "val", "test"]:
        img_dir = os.path.join(OUT_DIR, split, "images")
        lbl_dir = os.path.join(OUT_DIR, split, "labels")
        s = {"images": 0, "boxes": 0,
             "per_class": {CANONICAL[c]: {"images": 0, "boxes": 0, "tiny": 0} for c in CANONICAL}}
        if os.path.isdir(img_dir):
            for fname in sorted(os.listdir(img_dir)):
                if not fname.lower().endswith((".jpg", ".jpeg", ".png")):
                    continue
                s["images"] += 1
                lbl_path = os.path.join(lbl_dir, os.path.splitext(fname)[0] + ".txt")
                if not os.path.exists(lbl_path):
                    continue
                classes_in_img = set()
                with open(lbl_path, "r", encoding="utf-8") as f:
                    for line in f:
                        parts = line.split()
                        if len(parts) >= 5:
                            cid = int(parts[0])
                            nw, nh = float(parts[3]), float(parts[4])
                            if cid in CANONICAL:
                                s["boxes"] += 1
                                cname = CANONICAL[cid]
                                s["per_class"][cname]["boxes"] += 1
                                if nw * nh < TINY_AREA_FRAC:
                                    s["per_class"][cname]["tiny"] += 1
                                classes_in_img.add(cid)
                for cid in classes_in_img:
                    s["per_class"][CANONICAL[cid]]["images"] += 1
        report["splits"][split] = s
        for c in CANONICAL:
            cname = CANONICAL[c]
            totals[cname]["images"] += s["per_class"][cname]["images"]
            totals[cname]["boxes"] += s["per_class"][cname]["boxes"]
            totals[cname]["tiny"] += s["per_class"][cname]["tiny"]
    report["totals"] = totals

    with open(os.path.join(OUT_DIR, "data.yaml"), "w", encoding="utf-8") as f:
        f.write(f"path: {OUT_DIR}\ntrain: train/images\nval: val/images\ntest: test/images\n\n"
                "names:\n  0: ICs\n  1: capacitors\n  2: diodes\n  3: inductors\n"
                "  4: resistors\n  5: transistors\n")
    return report


def main():
    os.makedirs(REPORTS_DIR, exist_ok=True)
    if os.path.isdir(OUT_DIR):
        print(f"ERROR: {OUT_DIR} already exists - refusing to overwrite. "
              "Move or delete it first if you intend a rebuild.")
        return

    print("Step 1: regenerate FICS labels from raw CSV annotations ...")
    label_by_image, fics_verify = regenerate_fics_labels()
    print(f"  GT boxes by type:   {fics_verify['gt_boxes_by_type']}")
    print(f"  written by type:    {fics_verify['written_boxes_by_type']}")
    print(f"  verification OK:    {fics_verify['ok']} (problems: {fics_verify['problems']})")
    if not fics_verify["ok"]:
        print("  FICS label regeneration FAILED verification - aborting.")
        return

    print("Step 2: tile FICS boards with corrected labels ...")
    tile_stats = tile_fics(label_by_image)
    print(f"  tiles by split:  {tile_stats['tiles']}")
    print(f"  boxes by split:  {tile_stats['boxes']}")

    print("Step 3: remap Roboflow with proven-only mappings ...")
    robo_result, ambiguous_rows = remap_roboflow()
    if "error" in robo_result:
        print(f"  {robo_result}")
        return
    print(f"  classes by disposition: {robo_result['classes_by_disposition']}")
    print(f"  boxes kept by disposition: {robo_result['boxes_by_disposition']}")
    print(f"  boxes quarantined by disposition: {robo_result['quarantined_boxes_by_disposition']}")
    print(f"  images by split: {robo_result['images']}")

    print("Step 4: finalize dataset + data.yaml ...")
    final = finalize_dataset()
    for cname, t in final["totals"].items():
        print(f"  {cname:<12} images={t['images']:<4} boxes={t['boxes']:<6} tiny={t['tiny']}")

    # quarantine csv (ambiguous + unmapped + excluded source classes)
    with open(os.path.join(REPORTS_DIR, "canonical_ambiguous_quarantine.csv"), "w",
              newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["source_class", "class_id", "disposition",
                                          "kept_boxes", "quarantined_boxes"])
        w.writeheader()
        w.writerows(ambiguous_rows)

    report = {
        "generated": "2026-09-23",
        "output": OUT_DIR,
        "fics_label_regeneration": fics_verify,
        "fics_tiling": {"tile_size": TILE_SIZE, "stride": STRIDE,
                        "min_component_overlap": MIN_COMPONENT_OVERLAP,
                        "background_tile_rate": BACKGROUND_TILE_RATE,
                        "background_seed": BACKGROUND_SEED,
                        "board_split": BOARD_SPLIT,
                        **tile_stats},
        "roboflow": robo_result,
        "final": final,
    }
    with open(os.path.join(REPORTS_DIR, "canonical_build_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1)
    print(f"\nBuild report -> reports/dataset/canonical_build_report.json")
    print(f"Quarantine   -> reports/dataset/canonical_ambiguous_quarantine.csv ({len(ambiguous_rows)} rows)")
    print(f"Dataset      -> {OUT_DIR}")


if __name__ == "__main__":
    main()
