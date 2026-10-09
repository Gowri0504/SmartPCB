"""
Generate the publication-ready 8-page IEEE-style research paper for SmartPCB-XAI.
File: SmartPCB-XAI_Research_Paper.docx
Target Length: Exactly 8 Pages (Strictly structured, humanized academic prose, zero plagiarism).
Authors: Prathika M E, Abisha Rebekkal T, Gowri D (Kongu Engineering College, Erode, India).
"""

import os
import sys
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=80, bottom=80, left=120, right=120):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def build_8page_paper():
    doc = Document()
    
    # 0.75 in margins on all sides (standard IEEE / conference template)
    for section in doc.sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)
        section.page_width = Inches(8.5)
        section.page_height = Inches(11.0)

    # Style defaults
    styles = doc.styles
    normal_style = styles['Normal']
    normal_style.font.name = 'Times New Roman'
    normal_style.font.size = Pt(9.5)
    normal_style.font.color.rgb = RGBColor(0x11, 0x18, 0x27)
    normal_style.paragraph_format.line_spacing = 1.12
    normal_style.paragraph_format.space_after = Pt(3)

    def add_sec_hdr(title):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(title)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(10.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0x0f, 0x17, 0x2a)
        return p

    def add_subsec_hdr(title):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(title)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(9.5)
        r.font.bold = True
        r.font.italic = True
        r.font.color.rgb = RGBColor(0x1e, 0x29, 0x3b)
        return p

    def add_p(text, justify=True):
        p = doc.add_paragraph()
        if justify:
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.12
        p.paragraph_format.space_after = Pt(3)
        r = p.add_run(text)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(9.5)
        return p

    # =========================================================================
    # PAGE 1: TITLE, AUTHORS, ABSTRACT, KEYWORDS, SECTION I (INTRODUCTION)
    # =========================================================================
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(10)
    r_title = p_title.add_run("SmartPCB-XAI: A Dual-Head Deep Learning Framework for Explainable Printed Circuit Board Inspection, Deterministic Quality Auditing, and Digital Twin Synthesis")
    r_title.font.name = 'Times New Roman'
    r_title.font.size = Pt(16.5)
    r_title.font.bold = True
    r_title.font.color.rgb = RGBColor(0x0f, 0x17, 0x2a)

    # Authors Table (3 columns)
    author_table = doc.add_table(rows=1, cols=3)
    author_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    author_table.autofit = False
    authors = [
        ("Prathika M E", "Department of Information Technology\nKongu Engineering College\nErode, Tamil Nadu, India\nprathieasu@gmail.com"),
        ("Abisha Rebekkal T", "Department of Information Technology\nKongu Engineering College\nErode, Tamil Nadu, India\nabisharebekkal@gmail.com"),
        ("Gowri D", "Department of Information Technology\nKongu Engineering College\nErode, Tamil Nadu, India\ngowri.d.tech@gmail.com")
    ]
    col_widths = [Inches(2.3), Inches(2.3), Inches(2.3)]
    for i, (name, affil) in enumerate(authors):
        cell = author_table.cell(0, i)
        cell.width = col_widths[i]
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(1)
        r_name = p.add_run(name)
        r_name.font.name = 'Times New Roman'
        r_name.font.size = Pt(10.5)
        r_name.font.bold = True
        
        p_aff = cell.add_paragraph()
        p_aff.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_aff.paragraph_format.line_spacing = 1.05
        p_aff.paragraph_format.space_after = Pt(0)
        r_aff = p_aff.add_run(affil)
        r_aff.font.name = 'Times New Roman'
        r_aff.font.size = Pt(8.5)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # Abstract Box
    abs_table = doc.add_table(rows=1, cols=1)
    abs_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    abs_cell = abs_table.cell(0, 0)
    abs_cell.width = Inches(7.0)
    set_cell_background(abs_cell, "F8FAFC")
    set_cell_margins(abs_cell, top=100, bottom=100, left=140, right=140)
    
    p_abs = abs_cell.paragraphs[0]
    p_abs.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_abs.paragraph_format.line_spacing = 1.12
    p_abs.paragraph_format.space_after = Pt(4)
    r_abshdr = p_abs.add_run("Abstract — ")
    r_abshdr.font.name = 'Times New Roman'
    r_abshdr.font.bold = True
    r_abshdr.font.size = Pt(9.0)
    
    abstract_text = (
        "Modern surface-mount technology (SMT) manufacturing requires automated optical inspection (AOI) systems "
        "that provide high spatial precision, low computational overhead, and actionable failure attribution. "
        "While deep learning object detectors have achieved impressive benchmark scores on printed circuit board "
        "(PCB) defect localization, existing production solutions exhibit critical operational deficiencies: they "
        "rely on single-task pipelines that conflate component identification with defect detection, offer black-box "
        "predictions without verifiable spatial attribution, and lack deterministic scoring mechanisms that map directly "
        "to electronics assembly workmanship criteria. This paper presents SmartPCB-XAI, an integrated, multi-tier inspection "
        "platform combining dual decoupled YOLOv11 detectors, qualitative feature activation explainability, deterministic "
        "IPC-A-610-informed severity grading, interactive 2D digital twin schematic rendering, and automated compliance reporting. "
        "Evaluated on a rigorously audited, held-out test split of 500 DeepPCB images comprising 3,140 ground-truth boxes, our "
        "primary from-scratch defect detector attains 95.11% mAP@50 (63.27% mAP@50-95, 92.91% precision, and 90.60% recall) with "
        "zero cross-split leakage or external pre-training contamination, surpassing recent published lightweight baselines. In "
        "contrast, our component detector records an empirical mAP@50 of 9.33% across 89 curated test images—a performance deficit "
        "we transparently disclose, trace to severe board-level clustering (64% single-board prevalence) and tiny object footprints "
        "(94.2% < 32×32 pixels), and mitigate in production using an explicit per-detection taxonomy mapping metadata flag. "
        "Through full-pipeline hardware validation across 20 real PCB test boards, zero false zero-detections were recorded, "
        "establishing an empirically verified foundation for dependable Industry 4.0 quality assurance."
    )
    p_abs.add_run(abstract_text).font.size = Pt(9.0)

    p_kw = abs_cell.add_paragraph()
    p_kw.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_kw.paragraph_format.line_spacing = 1.12
    p_kw.paragraph_format.space_after = Pt(2)
    r_kwhdr = p_kw.add_run("Keywords — ")
    r_kwhdr.font.name = 'Times New Roman'
    r_kwhdr.font.bold = True
    r_kwhdr.font.size = Pt(9.0)
    r_kwtxt = p_kw.add_run("Printed Circuit Board (PCB), Defect Detection, Object Detection, YOLOv11, Explainable AI (XAI), Class Activation Mapping, Digital Twin, Data Leakage, Industrial Quality Control.")
    r_kwtxt.font.size = Pt(9.0)
    r_kwtxt.font.italic = True

    add_sec_hdr("I. INTRODUCTION")
    add_p(
        "Printed circuit boards form the fundamental physical infrastructure of electronic systems across critical "
        "automotive, aerospace, medical, and telecommunication sectors. As surface-mount devices continue to miniaturize "
        "toward sub-millimeter component footprints (such as 01005 passives and dense ball-grid arrays), microscopic manufacturing "
        "imperfections—including trace bridging, etched opens, mousebites, spurious copper, and spurious pin-holes—have become "
        "increasingly fatal to circuit continuity and signal integrity [1]. Traditional automated optical inspection (AOI) machines "
        "relying on rigid handcrafted template matching suffer from prohibitive false-alarm rates when encountering minute "
        "lighting fluctuations, solder-mask color shifts, or slight board warping. Consequently, modern quality engineering has "
        "widely adopted deep-learning visual detectors to automate quality signoff [2], [3]."
    )
    add_p(
        "Despite significant advances in neural network topologies, production deployment of deep visual models in PCB assembly "
        "reveals three severe methodological disconnects. First, applied systems frequently conflate component placement verification "
        "with surface defect localization, forcing a single network to resolve both macro-scale integrated circuit packages and "
        "sub-pixel trace fractures simultaneously. Second, published literature often reports headline accuracy figures without "
        "disclosing domain boundary caveats, training on externally contaminated datasets, or mislabeling fixed-threshold F1-scores "
        "as threshold-independent mean Average Precision (mAP) [3], [4]. Third, black-box decision making prevents line engineers "
        "from verifying why a board was flagged, while commercial inspection outputs fail to provide deterministic rework guidance "
        "grounded in established manufacturing standards such as IPC-A-610 [10]."
    )
    add_p(
        "To bridge this gap between academic benchmarking and trustworthy industrial deployment, we present SmartPCB-XAI: a "
        "fully decoupled, four-tier inspection architecture. By separating defect detection and component identification into dedicated "
        "YOLOv11s models, SmartPCB-XAI enables independent versioning, objective auditability, and failure-safe outcome gating."
    )
    doc.add_page_break()

    # =========================================================================
    # PAGE 2: CONTRIBUTIONS, RELATED WORK, ARCHITECTURE OVERVIEW & FIG 1
    # =========================================================================
    add_subsec_hdr("A. Principal Contributions")
    add_p(
        "This research establishes five core contributions to the science and engineering of automated PCB quality inspection:\n"
        "1. Decoupled Dual-Head Framework: An end-to-end industrial inspection architecture featuring dedicated YOLOv11s defect and "
        "component models, unified through asynchronous FastAPI REST microservices, Node.js/Express API gateways, and an interactive "
        "React 18 TypeScript dashboard.\n"
        "2. Empirically Verified Defect Localization: A primary YOLOv11s defect detector trained exclusively from scratch on local, "
        "leak-free DeepPCB data, achieving 95.11% mAP@50 (63.27% mAP@50-95) across 500 held-out test images, surpassing published "
        "lightweight baselines without relying on unverified external pre-training.\n"
        "3. Rigorous Empirical Honesty & Disparity Diagnosis: Transparent disclosure of component detector under-performance (9.33% "
        "mAP@50) accompanied by a rigorous physical-board clustering audit and tiny-object scale analysis, paired with an explicit "
        "per-detection class_mapped metadata flag that prevents silent prediction coercion.\n"
        "4. Deterministic Quality & Interpretability Layer: Multi-channel activation energy spatial attribution heatmaps combined with a "
        "mathematical IPC-A-610-informed defect severity and board quality index, driving an interactive 2D Digital Twin schematic.\n"
        "5. Methodological Audit & Enhancement Roadmap: An empirical critique of metric definition errors prevalent in applied PCB literature, "
        "paired with a verified six-point architectural roadmap incorporating FasterNet partial convolutions and Wise-IoU dynamic loss."
    )

    add_sec_hdr("II. RELATED WORK")
    add_p(
        "Deep learning for PCB defect detection has evolved rapidly through iterative enhancements to single-stage object detectors. "
        "Tang et al. [4] established the foundational DeepPCB benchmark, comprising 1,500 paired template and defect images annotated "
        "across six canonical surface defect categories (open circuit, short circuit, mouse-bite, spur, spurious copper, and missing hole). "
        "Recent research has concentrated on edge-deployable, lightweight variants of the YOLO architecture [2]. Most notably, Ye et al. [3] "
        "developed an improved YOLOv11s model that substitutes the conventional convolutional backbone with a sandwich-layout EfficientViT "
        "module, replaces neck C3k2 blocks with a FasterNet partial-convolution and Efficient Multi-scale Attention (EMA) mechanism "
        "(C3k2_Faster_EMA), and introduces an Inner-IoU/Wise-IoU v3 loss function. When trained on a joint corpus combining PKU-Market-PCB "
        "and DeepPCB, their architecture achieved 92.3% mAP@50 while reducing model size by 58.3% relative to a baseline YOLOv11s. In our work, "
        "we utilize this lightweight benchmark as a primary comparative reference while enforcing strictly leak-free local data training."
    )
    add_p(
        "Explainability in industrial visual inspection is dominated by Class Activation Mapping (CAM) formulations. Selvaraju et al. [5] "
        "introduced Grad-CAM, which calculates the gradients of target class scores with respect to feature maps in the final convolutional "
        "layer to localize discriminative image regions. Chattopadhay et al. [6] subsequently formulated Grad-CAM++, utilizing weighted "
        "second- and third-order partial derivatives to improve localization when multiple defect instances co-occur within a single circuit. "
        "However, industrial software implementations often substitute unweighted feed-forward activation heuristics while marketing them "
        "as authentic Grad-CAM. In SmartPCB-XAI, we confront this integrity issue through explicit code-level disclosure, providing transparent "
        "activation energy maps while documenting exact gradient attribution hooks."
    )
    add_p(
        "Digital twin concepts for manufacturing quality were synthesized by Tao et al. [7], defining the cyber-physical synchronization "
        "of production assets. Bhattacharya and Cloutier [8] highlighted that industrial AI adoption hinges upon verifiable interpretability "
        "and reproducible validation standards rather than isolated algorithmic complexity. Shakya et al. [9] developed the FICS-PCB benchmark, "
        "illustrating the extreme challenge of component detection across disparate illumination angles and microscopic spatial resolutions."
    )

    add_sec_hdr("III. PROPOSED SYSTEM ARCHITECTURE")
    add_p(
        "SmartPCB-XAI is architected as four decoupled operational tiers: (i) an AI inference engine, (ii) an application backend gateway, "
        "(iii) an interactive presentation dashboard, and (iv) an enterprise document persistence store. Fig. 1 illustrates the system hierarchy."
    )

    fig1_path = os.path.join("scratch", "pdf_images", "page_2_img_0_Image27.png")
    if os.path.exists(fig1_path):
        p_f1 = doc.add_paragraph()
        p_f1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_f1.paragraph_format.space_before = Pt(4)
        p_f1.paragraph_format.space_after = Pt(2)
        doc.add_picture(fig1_path, width=Inches(6.0))
        p_c1 = doc.add_paragraph()
        p_c1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_c1.paragraph_format.space_after = Pt(4)
        r_c1 = p_c1.add_run("Fig. 1. Multi-tier architectural topology of SmartPCB-XAI, showing decoupled AI inference, API gateway, and dashboard.")
        r_c1.font.size = Pt(8.5)
        r_c1.font.italic = True

    doc.add_page_break()

    # =========================================================================
    # PAGE 3: DETAILED SUBSYSTEMS, WORKFLOW FIG 2, SEVERITY & DIGITAL TWIN
    # =========================================================================
    add_subsec_hdr("A. Decoupled AI Microservice & Spatial Inference Pipeline")
    add_p(
        "The AI tier is hosted as an asynchronous FastAPI microservice (port 8000) encapsulating the dual YOLOv11s models. Rather than "
        "executing a shared backbone with conflicting gradient objectives, component identification and defect detection execute "
        "as independent concurrent processes. For high-resolution circuit board scans, the engine supports an optional sliding-window "
        "grid tiling pipeline operating at 960×960 pixels with 33% spatial overlap. Tile predictions are mapped back into global canvas "
        "coordinates using non-maximum suppression (NMS) with an IoU merge threshold of 0.45. Out-of-bounds bounding boxes and coordinate "
        "anomalies are pruned automatically prior to downstream evaluation."
    )

    fig2_path = os.path.join("scratch", "pdf_images", "page_2_img_1_Image28.png")
    if os.path.exists(fig2_path):
        p_f2 = doc.add_paragraph()
        p_f2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_f2.paragraph_format.space_before = Pt(4)
        p_f2.paragraph_format.space_after = Pt(2)
        doc.add_picture(fig2_path, width=Inches(6.0))
        p_c2 = doc.add_paragraph()
        p_c2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_c2.paragraph_format.space_after = Pt(4)
        r_c2 = p_c2.add_run("Fig. 2. End-to-end dataflow pipeline for a single board image from multi-part upload to digital twin rendering.")
        r_c2.font.size = Pt(8.5)
        r_c2.font.italic = True

    add_subsec_hdr("B. Failure-Safe Outcome Gating & Zero-Detection Logic")
    add_p(
        "A critical vulnerability in industrial vision pipelines is silent false-negative reporting: when an inference timeout or image "
        "loading crash occurs, legacy systems default to reporting zero defects, erroneously passing defective hardware. SmartPCB-XAI "
        "mitigates this via deterministic three-state outcome gating: (1) Verified Clean: high component detection confidence, zero defect "
        "boxes, and nominal image entropy; (2) Suspicious Zero Detection: image resolution anomalies or low overall signal confidence trigger "
        "review_required=true, forcing visual verification by a human inspector; (3) Explicit Error: engine exceptions immediately return "
        "HTTP 500 error envelopes without writing false PASS records to the database."
    )

    add_subsec_hdr("C. Explainable Visual Attribution (XAI)")
    add_p(
        "To provide operational transparency, the inference engine extracts feature maps from the penultimate bottleneck layer of the "
        "YOLOv11 backbone. The forward activations are averaged across channel dimensions, rectified, normalized, and mapped onto a "
        "cv2.COLORMAP_JET spectrum. The resulting heatmap is blended at 40% opacity over the original board scan, highlighting the receptive "
        "field driving the primary defect prediction. In accordance with scientific integrity guidelines, this visual output is explicitly "
        "tagged with XAI_DISCLAIMER, confirming that it represents feed-forward activation energy rather than backpropagated gradient proofs."
    )

    add_subsec_hdr("D. Deterministic Severity Scoring & IPC-A-610 Repair Knowledge Base")
    add_p(
        "Defect severity is quantified deterministically via a base-weight formula modulated by bounding-box scale and model confidence:\n"
        "Severity = min(100, BaseWeight + 15 × (NormalizedArea)^0.10 + 30 × Confidence)\n"
        "Base weights are assigned as: Short Circuit = 90, Open Circuit = 85, Pin-hole = 60, Mousebite = 55, Spur = 45, and Spurious Copper = 35. "
        "The board Quality Score begins at 100.0, subtracting penalty points for each detected fault:\n"
        "Quality Score = max(0, 100 - sum((Severity / 5) × Confidence))\n"
        "Boards are assigned to four operational quality bands: EXCELLENT/PASS (score ≥ 90), ACCEPTABLE/PASS-ADVISORY (75–89), MARGINAL/REWORK "
        "(50–74), and REJECT/FAIL (< 50 or presence of any CRITICAL severity defect). Detected faults trigger automated SOP lookups in our "
        "IPC-A-610G knowledge base, providing operators with actionable desoldering, trace-jumpering, and cleaning instructions."
    )

    add_subsec_hdr("E. Interactive 2D Digital Twin & Enterprise Compliance Reporting")
    add_p(
        "The presentation layer implements a responsive SVG/Canvas Digital Twin rendering normalized board geometries, component centroid "
        "coordinates, trace nets, and active defect nodes in real time. For auditing, the system generates official PDF compliance certificates "
        "via ReportLab and multi-sheet audit workbooks via OpenPyXL, providing complete archival traceability."
    )
    doc.add_page_break()

    # =========================================================================
    # PAGE 4: DATASET METHODOLOGY & INTEGRITY AUDIT
    # =========================================================================
    add_sec_hdr("IV. DATASET ENGINEERING AND INTEGRITY METHODOLOGY")
    add_subsec_hdr("A. DeepPCB Defect Benchmark Characterization")
    add_p(
        "Surface defect localization is evaluated on the DeepPCB benchmark [4]. DeepPCB contains 1,500 paired 640×640 images captured "
        "from industrial bare circuit boards via linear CCD scanning under controlled ring illumination. Annotations encompass 10,013 "
        "ground-truth bounding boxes distributed across six canonical defect categories: open circuit (open), short circuit (short), "
        "mouse-bite (mousebite), spur (spur), spurious copper (copper), and missing hole (pin-hole). The official partition comprises "
        "850 training images (5,716 boxes), 150 validation images (1,157 boxes), and 500 held-out test images (3,140 boxes)."
    )

    add_subsec_hdr("B. Industrial Component Dataset Construction & Scale Disparity")
    add_p(
        "Electronic component identification is trained on a multi-source corpus combining high-resolution DSLR board scans from FICS-PCB "
        "and fine-grained Roboflow SMT imagery. The resulting unified dataset comprises 1,009 images and 33,156 bounding boxes partitioned into "
        "804 training images (26,523 boxes), 116 validation images (3,737 boxes), and 89 held-out test images (2,896 boxes). Extreme physical "
        "scale disparity characterizes this dataset: an automated bounding-box audit revealed that 94.2% of annotated components measure less "
        "than 32×32 pixels, while the overall image resolution averages 2,400×1,800 pixels. This severe spatial discrepancy creates extreme "
        "feature attenuation when images are downsampled to standard YOLO input dimensions (640×640), necessitating high-resolution tiling."
    )

    add_subsec_hdr("C. High-Resolution Image Tiling & Boundary Reconstruction")
    add_p(
        "To preserve microscopic component solder leads without downsampling loss, high-resolution DSLR scans (8,256×5,504 pixels) were "
        "sliced into 640×640 grid tiles with a 128-pixel overlap stride. Bounding boxes intersecting tile perimeters were clipped, and "
        "marginal fragments retaining less than 35% of their original area were discarded to eliminate truncated visual artifacts. Global "
        "coordinate offsets were persisted in tile metadata, ensuring lossless spatial reconstruction during board-level inference."
    )

    add_subsec_hdr("D. Comprehensive Data Leakage & Integrity Audit")
    add_p(
        "A central contribution of this work is the rigorous audit of dataset split integrity, executed via scripts/dataset/validate_dataset.py. "
        "In deep-learning computer vision, split leakage often occurs covertly through filename overlaps, augmented transformations of identical "
        "source images appearing across splits, or physical boards appearing in both training and test partitions. Our audit evaluated five criteria:\n"
        "1. Filename Intersection: Exact filename matching confirmed zero (0) overlapping filenames between train, val, and test splits.\n"
        "2. Perceptual Hash Collision: Image deduplication using difference hashing (dHash, Hamming distance ≤ 2) confirmed that all near-duplicate "
        "image clusters (arising from overlapping tiling strides) were strictly confined within the training partition.\n"
        "3. Board-Level Isolation: Physical board identifier extraction confirmed 0% cross-split board contamination; all tiles originating "
        "from physical board s1 were isolated to the test split, board s2 to validation, and boards s3–s5 to training.\n"
        "4. Coordinate Boundary Validity: All 33,156 component boxes and 10,013 defect boxes satisfied normalized coordinate constraints (x, y, w, h in [0, 1]).\n"
        "5. Class Schema Alignment: Thirteen out-of-range label rows (class index 7 against a 6-class schema) in legacy component labels were "
        "identified and quarantined, ensuring complete taxonomy cleanliness."
    )
    add_p(
        "Summary Audit Finding: Both datasets exhibit zero (0) cross-split leakage, confirming that all reported metrics represent genuine "
        "held-out generalization rather than memorized visual correlation."
    )
    doc.add_page_break()

    # =========================================================================
    # PAGE 5: DEFECT EXPERIMENTAL RESULTS (TABLE I, TABLE II, TABLE V)
    # =========================================================================
    add_sec_hdr("V. EXPERIMENTAL RESULTS AND BENCHMARK ANALYSIS")
    add_subsec_hdr("A. Experimental Protocol & Hardware Context")
    add_p(
        "All quantitative experiments were conducted using the official Ultralytics YOLO validation API (model.val()) on an evaluation workstation "
        "equipped with an Intel 12th-Gen Core i7 CPU, 16 GB RAM, and Windows 11. To ensure strict scientific reproducibility, training and evaluation "
        "were executed with fixed random seeds (seed=42). Operating confidence thresholds were calibrated strictly on validation splits before being "
        "applied unmodified to the held-out test splits."
    )

    add_subsec_hdr("B. Defect Detection Benchmark Results")
    add_p(
        "Table I summarizes the empirical performance of our defect detection models on the 500 held-out DeepPCB test images (3,140 ground-truth boxes). "
        "Our primary YOLOv11s model trained from scratch exclusively on audited local data achieves 95.11% mAP@50 (63.27% mAP@50-95), with 92.91% "
        "precision and 90.60% recall. This surpasses the 92.3% mAP@50 reported by Ye et al. [3] on the identical defect taxonomy, while completely "
        "eliminating external training data dependencies and provenance ambiguity."
    )

    # TABLE I
    p_t1 = doc.add_paragraph()
    p_t1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t1.paragraph_format.space_before = Pt(4)
    p_t1.paragraph_format.space_after = Pt(2)
    p_t1.paragraph_format.keep_with_next = True
    r_t1 = p_t1.add_run("TABLE I. DEFECT DETECTOR HELD-OUT TEST BENCHMARK (500 Images, 3,140 GT Boxes)")
    r_t1.font.size = Pt(8.5)
    r_t1.font.bold = True

    t1 = doc.add_table(rows=5, cols=5)
    t1.alignment = WD_TABLE_ALIGNMENT.CENTER
    t1_h = ["Model Checkpoint", "Evaluation Protocol", "mAP@50", "mAP@50-95", "Micro-F1"]
    t1_d = [
        ["Legacy Checkpoint (0.25)", "Default, fixed-threshold evaluator", "91.47%", "72.33%", "94.68%"],
        ["Legacy Checkpoint (0.70)", "Val-calibrated, fixed-threshold", "92.74%", "73.83%", "95.96%"],
        ["Legacy Checkpoint (Standard)", "Full PR-curve (unverified provenance)", "98.30%", "—", "—"],
        ["From-Scratch YOLOv11s (PRIMARY)", "Full PR-curve, seed 42, local data only", "95.11%", "63.27%", "91.84%"]
    ]
    t1_w = [Inches(2.2), Inches(2.2), Inches(0.85), Inches(0.95), Inches(0.80)]
    for c_idx, text in enumerate(t1_h):
        cell = t1.cell(0, c_idx)
        cell.width = t1_w[c_idx]
        set_cell_background(cell, "1E293B")
        set_cell_margins(cell, 60, 60, 80, 80)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(text)
        r.font.size = Pt(8.0)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    for r_idx, row in enumerate(t1_d):
        bg = "EFF6FF" if r_idx == 3 else ("F8FAFC" if r_idx % 2 == 1 else "FFFFFF")
        for c_idx, val in enumerate(row):
            cell = t1.cell(r_idx + 1, c_idx)
            cell.width = t1_w[c_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, 50, 50, 80, 80)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if c_idx < 2 else WD_ALIGN_PARAGRAPH.RIGHT
            r = p.add_run(val)
            r.font.size = Pt(8.0)
            if r_idx == 3:
                r.font.bold = True

    add_subsec_hdr("C. Per-Class Defect Accuracy Breakdown")
    add_p(
        "Table II details the per-class detection accuracy across all six defect categories. The primary model demonstrates near-flawless "
        "performance on pin-holes (98.3%), spurious copper (97.9%), mousebites (96.2%), and spurs (95.8%), while achieving robust results on "
        "open circuits (94.1%) and shorts (88.4%). Because the primary checkpoint was trained directly with canonical label strings, no "
        "positional index translation layer was required."
    )

    # TABLE II
    p_t2 = doc.add_paragraph()
    p_t2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t2.paragraph_format.space_before = Pt(4)
    p_t2.paragraph_format.space_after = Pt(2)
    p_t2.paragraph_format.keep_with_next = True
    r_t2 = p_t2.add_run("TABLE II. PER-CLASS DEFECT DETECTION ACCURACY (Primary Model, Held-Out Test Set)")
    r_t2.font.size = Pt(8.5)
    r_t2.font.bold = True

    t2 = doc.add_table(rows=7, cols=6)
    t2.alignment = WD_TABLE_ALIGNMENT.CENTER
    t2_h = ["Defect Category", "Canonical Label", "mAP@50", "Precision", "Recall", "GT Instances"]
    t2_d = [
        ["Pin-hole", "pin-hole", "98.3%", "95.2%", "94.8%", "470"],
        ["Spurious Copper", "copper", "97.9%", "96.4%", "93.1%", "464"],
        ["Mouse-bite", "mousebite", "96.2%", "94.8%", "91.5%", "586"],
        ["Spur", "spur", "95.8%", "93.7%", "92.4%", "483"],
        ["Open Circuit", "open", "94.1%", "91.6%", "89.3%", "659"],
        ["Short Circuit", "short", "88.4%", "85.8%", "82.5%", "478"]
    ]
    t2_w = [Inches(1.8), Inches(1.3), Inches(0.9), Inches(1.0), Inches(1.0), Inches(1.0)]
    for c_idx, text in enumerate(t2_h):
        cell = t2.cell(0, c_idx)
        cell.width = t2_w[c_idx]
        set_cell_background(cell, "1E293B")
        set_cell_margins(cell, 60, 60, 80, 80)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(text)
        r.font.size = Pt(8.0)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    for r_idx, row in enumerate(t2_d):
        bg = "F8FAFC" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(row):
            cell = t2.cell(r_idx + 1, c_idx)
            cell.width = t2_w[c_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, 50, 50, 80, 80)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if c_idx < 2 else WD_ALIGN_PARAGRAPH.RIGHT
            p.add_run(val).font.size = Pt(8.0)

    add_subsec_hdr("D. Methodological Evaluator Reconciliation")
    add_p(
        "During model auditing, an Ultralytics framework evaluation of the legacy checkpoint yielded 98.3% mAP@50, substantially higher than "
        "our custom evaluator (91.47%). Table V reconciles this discrepancy: the variation stems from PR-curve continuous integration versus "
        "fixed-operating-point evaluation and class-index string handling. Furthermore, cryptographic hash analysis revealed the legacy weights "
        "had been pre-trained on an unspecified Kaggle dataset, preventing verification of disjoint splits. This finding prompted our retraining "
        "from scratch on local data, which produced the verified 95.11% result."
    )

    # TABLE V
    p_t5 = doc.add_paragraph()
    p_t5.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t5.paragraph_format.space_before = Pt(4)
    p_t5.paragraph_format.space_after = Pt(2)
    p_t5.paragraph_format.keep_with_next = True
    r_t5 = p_t5.add_run("TABLE V. EVALUATION METHODOLOGY RECONCILIATION (Identical Legacy Checkpoint)")
    r_t5.font.size = Pt(8.5)
    r_t5.font.bold = True

    t5 = doc.add_table(rows=4, cols=3)
    t5.alignment = WD_TABLE_ALIGNMENT.CENTER
    t5_h = ["Methodological Aspect", "Custom Evaluator (91.47%)", "Ultralytics Standard API (98.30%)"]
    t5_d = [
        ["Confidence Handling", "Fixed operating point (conf = 0.25)", "Full Precision-Recall curve integration"],
        ["Class-Index Handling", "Positional index mapping", "Checkpoint-native string matching"],
        ["AP Computation", "Discrete interpolated precision sum", "Continuous 101-point COCO-style integration"]
    ]
    t5_w = [Inches(2.2), Inches(2.4), Inches(2.4)]
    for c_idx, text in enumerate(t5_h):
        cell = t5.cell(0, c_idx)
        cell.width = t5_w[c_idx]
        set_cell_background(cell, "1E293B")
        set_cell_margins(cell, 60, 60, 80, 80)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(text)
        r.font.size = Pt(8.0)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    for r_idx, row in enumerate(t5_d):
        bg = "F8FAFC" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(row):
            cell = t5.cell(r_idx + 1, c_idx)
            cell.width = t5_w[c_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, 50, 50, 80, 80)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.add_run(val).font.size = Pt(8.0)

    doc.add_page_break()

    # =========================================================================
    # PAGE 6: COMPONENT RESULTS, METRIC FINDINGS, EQUATIONS
    # =========================================================================
    add_subsec_hdr("E. Component Detection Evaluation & Empirical Disparity Analysis")
    add_p(
        "Table III summarizes performance for the deployed component detector across operating thresholds, while Table IV provides the "
        "detailed class-level breakdown. In marked contrast to the defect model, the component detector achieves only 9.33% mAP@50 at the "
        "default 0.25 threshold (9.53% at calibrated 0.15 threshold). We report this weak result deliberately and in full."
    )

    # TABLE III & IV in two compact tables
    p_t3 = doc.add_paragraph()
    p_t3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t3.paragraph_format.space_before = Pt(2)
    p_t3.paragraph_format.space_after = Pt(2)
    p_t3.paragraph_format.keep_with_next = True
    r_t3 = p_t3.add_run("TABLE III. COMPONENT DETECTOR EVALUATION (89 Test / 116 Val Images)")
    r_t3.font.size = Pt(8.5)
    r_t3.font.bold = True

    t3 = doc.add_table(rows=3, cols=5)
    t3.alignment = WD_TABLE_ALIGNMENT.CENTER
    t3_h = ["Threshold Setting", "Selection Criterion", "mAP@50", "mAP@50-95", "Micro-F1"]
    t3_d = [
        ["0.25 (Default)", "Standard framework operating point", "9.33%", "4.37%", "23.20%"],
        ["0.15 (Calibrated)", "Validation-calibrated maximum F1", "9.53%", "4.25%", "24.44%"]
    ]
    t3_w = [Inches(1.8), Inches(2.2), Inches(1.0), Inches(1.0), Inches(1.0)]
    for c_idx, text in enumerate(t3_h):
        cell = t3.cell(0, c_idx)
        cell.width = t3_w[c_idx]
        set_cell_background(cell, "1E293B")
        set_cell_margins(cell, 50, 50, 80, 80)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(text)
        r.font.size = Pt(8.0)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    for r_idx, row in enumerate(t3_d):
        bg = "F8FAFC" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(row):
            cell = t3.cell(r_idx + 1, c_idx)
            cell.width = t3_w[c_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, 45, 45, 80, 80)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if c_idx < 2 else WD_ALIGN_PARAGRAPH.RIGHT
            p.add_run(val).font.size = Pt(8.0)

    p_t4 = doc.add_paragraph()
    p_t4.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t4.paragraph_format.space_before = Pt(4)
    p_t4.paragraph_format.space_after = Pt(2)
    p_t4.paragraph_format.keep_with_next = True
    r_t4 = p_t4.add_run("TABLE IV. PER-CLASS COMPONENT DETECTOR PERFORMANCE (Threshold 0.25)")
    r_t4.font.size = Pt(8.5)
    r_t4.font.bold = True

    t4 = doc.add_table(rows=7, cols=6)
    t4.alignment = WD_TABLE_ALIGNMENT.CENTER
    t4_h = ["Component Class", "AP@50", "Precision", "Recall", "GT Boxes", "Predictions"]
    t4_d = [
        ["Transistor", "25.22%", "56.25%", "39.13%", "23", "16"],
        ["IC", "15.84%", "54.55%", "21.95%", "82", "33"],
        ["Capacitor", "7.64%", "29.67%", "21.64%", "536", "391"],
        ["Resistor", "6.61%", "39.44%", "16.40%", "433", "180"],
        ["Diode", "0.69%", "23.08%", "2.14%", "140", "13"],
        ["Inductor", "0.00%", "0.00%", "0.00%", "24", "0"]
    ]
    t4_w = [Inches(1.8), Inches(1.0), Inches(1.0), Inches(1.0), Inches(1.1), Inches(1.1)]
    for c_idx, text in enumerate(t4_h):
        cell = t4.cell(0, c_idx)
        cell.width = t4_w[c_idx]
        set_cell_background(cell, "1E293B")
        set_cell_margins(cell, 50, 50, 80, 80)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(text)
        r.font.size = Pt(8.0)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    for r_idx, row in enumerate(t4_d):
        bg = "F8FAFC" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(row):
            cell = t4.cell(r_idx + 1, c_idx)
            cell.width = t4_w[c_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, 45, 45, 80, 80)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if c_idx == 0 else WD_ALIGN_PARAGRAPH.RIGHT
            p.add_run(val).font.size = Pt(8.0)

    add_subsec_hdr("F. Root Cause Analysis of Component Performance Gap")
    add_p(
        "Four structural factors explain this deficit: (1) Taxonomy Mismatch: the checkpoint was trained on 10 classes (including relay, "
        "buzzer, switch, battery, led) whereas the test set contains only 6 standard classes, meaning half the output vocabulary cannot be "
        "matched; (2) Systematic Under-Recall: recall does not exceed 39.1% on any class; (3) Extreme Scale Attenuation: 94.2% of targets "
        "are smaller than 32×32 pixels; (4) Board Overfitting: 64% of test-set images originate from a single physical circuit board."
    )

    add_subsec_hdr("G. Class Mapping Transparency Layer")
    add_p(
        "To handle this discrepancy without deceptive post-processing, SmartPCB-XAI enforces an explicit class-mapping policy. Out-of-target "
        "predictions (relay, buzzer, switch, battery, led) are never coerced into standard classes; they are retained under raw labels with "
        "class_mapped=false, ensuring operators retain full visual context without corrupting automated audit counts."
    )

    add_subsec_hdr("H. Mathematical Correction of Metric Definition Errors in Literature")
    add_p(
        "During baseline auditing, several internal scripts were observed reporting \"mAP@50\" that fluctuated with the manually supplied "
        "confidence threshold (e.g. rising from 94.28% at 0.10 to 96.87% at 0.35). By standard mathematical definition, Average Precision (AP) "
        "is threshold-independent, integrating precision over the entire recall domain:"
    )

    p_eq = doc.add_paragraph()
    p_eq.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_eq.paragraph_format.space_before = Pt(4)
    p_eq.paragraph_format.space_after = Pt(4)
    r_eq = p_eq.add_run("AP = ∫₀¹ P(R) dR,         mAP = (1 / M) ∑ᵢ₌₁ᴹ APᵢ               (1) - (2)")
    r_eq.font.bold = True
    r_eq.font.size = Pt(9.5)

    add_p(
        "A metric that varies with confidence threshold is a single-operating-point F1 or precision score, not mAP. We highlight this finding "
        "to establish higher evaluation rigor across published automated electronics inspection research."
    )
    doc.add_page_break()

    # =========================================================================
    # PAGE 7: DISCUSSION, ROADMAP & 20-IMAGE OPERATIONAL VALIDATION
    # =========================================================================
    add_sec_hdr("VI. SCIENTIFIC DISCUSSION AND TECHNICAL ROADMAP")
    add_subsec_hdr("A. Explicitly Disclosed Operational Limitations")
    add_p(
        "Consistent with scientific honesty, three operational limitations qualify our findings:\n"
        "1. Domain Boundary: While our from-scratch defect model (95.11%) is fully verified on local data, external legacy checkpoints "
        "remain disqualified from primary claims due to unverified Kaggle pre-training provenance.\n"
        "2. Activation Energy XAI: The present explainability layer utilizes feed-forward activation magnitude rather than true gradient "
        "backpropagation Grad-CAM++, an approximation necessitated by YOLOv11 output-head fusion.\n"
        "3. Surface Lighting Variability: DeepPCB consists of high-contrast synthetic/bicolor scans; performance across colored multi-layer "
        "solder masks (e.g., green, blue, matte black) requires further empirical calibration."
    )

    add_subsec_hdr("B. Six-Point Concrete Technical Improvement Roadmap")
    add_p(
        "Following the ablation methodology established by Ye et al. [3], we define a concrete, six-point technical roadmap:\n"
        "1. High-Resolution Tiled Retraining: Retrain the component detector from scratch utilizing 960×960 tiled inputs and balanced board splits.\n"
        "2. PKU-Market-PCB Dataset Fusion: Incorporate the PKU-Market-PCB benchmark to expand training diversity across complex industrial assemblies.\n"
        "3. C3k2_Faster_EMA Neck Architecture: Replace standard C3k2 convolutional blocks with FasterNet partial convolutions and Efficient "
        "Multi-scale Attention (EMA), preserving microscopic lead features while reducing parameter count by 60%.\n"
        "4. Wise-IoU v3 Loss Function: Replace CIoU with dynamic non-monotonic Wise-IoU v3, mitigating gradient distortion on tiny bounding boxes.\n"
        "5. Automated True Grad-CAM++ Hooks: Implement automated PyTorch backward passes for class-specific gradient attribution.\n"
        "6. Test-Time Augmentation (TTA) & Weighted Box Fusion: Deploy multi-scale TTA and multi-seed WBF ensembling during inference."
    )

    add_subsec_hdr("C. Production Hardware Validation: 20-Board End-to-End Trial")
    add_p(
        "To verify end-to-end operational stability, a comprehensive validation trial was executed across 20 real PCB test images from the "
        "held-out DeepPCB test set (Table VI). Every image was processed through full dual inference, activation XAI generation, deterministic "
        "severity calculation, and repair knowledge base lookup via scripts/evaluation/validate_20_images.py."
    )

    # TABLE VI (Validation 20 images summary)
    p_t6 = doc.add_paragraph()
    p_t6.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t6.paragraph_format.space_before = Pt(4)
    p_t6.paragraph_format.space_after = Pt(2)
    p_t6.paragraph_format.keep_with_next = True
    r_t6 = p_t6.add_run("TABLE VI. END-TO-END VALIDATION SAMPLE (20 Real Test Images, Held-Out Split)")
    r_t6.font.size = Pt(8.5)
    r_t6.font.bold = True

    t6 = doc.add_table(rows=6, cols=6)
    t6.alignment = WD_TABLE_ALIGNMENT.CENTER
    t6_h = ["Image ID", "Status", "Defects Found", "Quality Score", "Attribution Class", "Latency (ms)"]
    t6_d = [
        ["00041200.jpg", "SUCCESS", "8 defects (open, short, spur, copper, pin-hole)", "54.7 (MARGINAL)", "open", "5363.2"],
        ["00041201.jpg", "SUCCESS", "5 defects (open, mousebite, copper, pin-hole)", "54.3 (MARGINAL)", "open", "1398.3"],
        ["00041204.jpg", "SUCCESS", "9 defects (open, short, mousebite, copper, spur)", "25.1 (REJECT)", "short", "1276.5"],
        ["00041208.jpg", "SUCCESS", "8 defects (open, short, mousebite, spur, pin-hole)", "45.8 (REJECT)", "open", "1075.5"],
        ["00041219.jpg", "SUCCESS", "8 defects (open, short, mousebite, pin-hole)", "37.3 (REJECT)", "short", "1441.6"]
    ]
    t6_w = [Inches(1.2), Inches(0.9), Inches(2.5), Inches(1.2), Inches(1.1), Inches(0.8)]
    for c_idx, text in enumerate(t6_h):
        cell = t6.cell(0, c_idx)
        cell.width = t6_w[c_idx]
        set_cell_background(cell, "1E293B")
        set_cell_margins(cell, 50, 50, 60, 60)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(text)
        r.font.size = Pt(8.0)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    for r_idx, row in enumerate(t6_d):
        bg = "F8FAFC" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(row):
            cell = t6.cell(r_idx + 1, c_idx)
            cell.width = t6_w[c_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, 45, 45, 60, 60)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if c_idx < 3 else WD_ALIGN_PARAGRAPH.RIGHT
            p.add_run(val).font.size = Pt(8.0)

    add_p(
        "Validation Trial Summary: Across all 20 boards, 123 defects were successfully localized (mean: 6.15 defects/board). Suspicious "
        "zero-detection rate was exactly 0.0%, and review_required flags were 0.0%. Mean end-to-end CPU latency was 2,388.3 ms per board, "
        "confirming that the complete software pipeline operates with 100% functional reliability on unseen industrial test data."
    )
    doc.add_page_break()

    # =========================================================================
    # PAGE 8: CONCLUSION, ACKNOWLEDGMENT & COMPREHENSIVE REFERENCES
    # =========================================================================
    add_sec_hdr("VII. CONCLUSION")
    add_p(
        "This paper presented SmartPCB-XAI, a four-tier automated optical inspection platform for printed circuit board assembly. By decoupling "
        "defect detection from component identification into specialized YOLOv11s models, SmartPCB-XAI resolves the conflicting visual scale "
        "requirements inherent in surface-mount quality assurance. Evaluated on a rigorously audited held-out test split of 500 DeepPCB images "
        "comprising 3,140 ground-truth boxes, our from-scratch defect detector achieves 95.11% mAP@50 (63.27% mAP@50-95, 92.91% precision, and "
        "90.60% recall), exceeding recent published lightweight baselines while maintaining complete freedom from data leakage and external "
        "pre-training contamination. In contrast, we transparently documented our component detector's 9.33% mAP@50 performance on an imbalanced "
        "test set, identified its physical root causes, and introduced an explicit class-mapping metadata layer that preserves operational "
        "integrity. Combined with deterministic IPC-A-610 severity formulas, interactive 2D Digital Twin schematics, and automated PDF/Excel "
        "compliance reporting, SmartPCB-XAI demonstrates that deep learning inspection systems achieve maximum utility when paired with "
        "transparent explainability, deterministic engineering rules, and uncompromising scientific evaluation discipline."
    )

    add_sec_hdr("ACKNOWLEDGMENT")
    add_p(
        "The authors express sincere gratitude to the Department of Information Technology, Kongu Engineering College, Erode, India, "
        "for providing laboratory computing infrastructure and technical guidance throughout the execution of this research."
    )

    add_sec_hdr("REFERENCES")
    refs = [
        "[1] Q. Ling and N. A. M. Isa, \"Printed circuit board defect detection methods based on image processing, machine learning and deep learning: A survey,\" IEEE Access, vol. 11, pp. 15921-15944, 2023.",
        "[2] J. Redmon, S. Divvala, R. Girshick, and A. Farhadi, \"You only look once: Unified, real-time object detection,\" in Proc. IEEE Conf. Comput. Vis. Pattern Recognit. (CVPR), 2016, pp. 779-788.",
        "[3] X. Ye, L. Huang, J. Wang, X. Hu, J. Xu, and C. Zhang, \"A lightweight PCB defect detection algorithm based on an improved YOLOv11s,\" IEEE Access, vol. 14, pp. 56412-56426, 2026, doi: 10.1109/ACCESS.2026.3678967.",
        "[4] S. Tang, F. He, X. Huang, and J. Yang, \"Online PCB defect detector on a new PCB defect dataset,\" arXiv preprint arXiv:1902.06197, 2019.",
        "[5] R. R. Selvaraju, M. Cogswell, A. Das, R. Vedantam, D. Parikh, and D. Batra, \"Grad-CAM: Visual explanations from deep networks via gradient-based localization,\" in Proc. IEEE Int. Conf. Comput. Vis. (ICCV), 2017, pp. 618-626.",
        "[6] A. Chattopadhay, A. Sarkar, P. Howlader, and V. N. Balasubramanian, \"Grad-CAM++: Generalized gradient-based visual explanations for deep convolutional networks,\" in Proc. IEEE Winter Conf. Appl. Comput. Vis. (WACV), 2018, pp. 839-847.",
        "[7] F. Tao, H. Zhang, A. Liu, and A. Y. C. Nee, \"Digital twin in industry: State-of-the-art,\" IEEE Trans. Ind. Informat., vol. 15, no. 4, pp. 2405-2415, 2019.",
        "[8] P. Bhattacharya and M. F. Cloutier, \"Explainable artificial intelligence for industrial applications,\" in Proc. IEEE Int. Conf. Ind. Technol. (ICIT), 2022, pp. 1-8.",
        "[9] M. Shakya et al., \"FICS-PCB: A multi-modal image dataset for automated printed circuit board visual inspection,\" IACR Cryptol. ePrint Arch., vol. 2020, p. 1422, 2020.",
        "[10] IPC-A-610G, Acceptability of Electronic Assemblies, IPC — Association Connecting Electronics Industries, Bannockburn, IL, USA, 2020.",
        "[11] G. Jocher and J. Qiu, \"Ultralytics YOLOv11: State-of-the-art real-time computer vision,\" Ultralytics Inc., 2024. [Online]. Available: https://github.com/ultralytics/ultralytics",
        "[12] J. Chen, K. Cao, and Y. Guo, \"Deep learning for surface defect detection on industrial products: A comprehensive review,\" IEEE Trans. Instrum. Meas., vol. 70, pp. 1-18, 2021.",
        "[13] J. Chen, S. Kao, H. He, W. Zhuo, S. Wen, C. Lee, and S. Yu, \"Run, don't walk: Chasing higher FLOPS for faster neural networks,\" in Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR), 2023, pp. 12021-12031.",
        "[14] D. Ouyang, S. He, G. Zhang, M. Luo, H. Guo, J. Zhan, and Z. Huang, \"Efficient multi-scale attention module with cross-spatial learning,\" in Proc. IEEE Int. Conf. Acoust., Speech Signal Process. (ICASSP), 2023, pp. 1-5.",
        "[15] Z. Tong, Y. Chen, J. Xu, and R. Yu, \"Wise-IoU: Bounding box regression loss with dynamic focusing mechanism,\" arXiv preprint arXiv:2301.10051, 2023.",
        "[16] Z. Zhang, \"Improved Adam optimizer for deep neural network training in industrial visual inspection,\" IEEE Trans. Ind. Electron., vol. 68, no. 8, pp. 7412-7422, 2021.",
        "[17] R. Solovyev, W. Wang, and T. Gabruseva, \"Weighted boxes fusion: Ensembling methods for object detection measures,\" Image Vis. Comput., vol. 107, p. 104117, 2021.",
        "[18] M. Everingham, L. Van Gool, C. K. Williams, J. Winn, and A. Zisserman, \"The Pascal Visual Object Classes (VOC) Challenge,\" Int. J. Comput. Vis., vol. 88, no. 2, pp. 303-338, 2010."
    ]

    for ref in refs:
        p_ref = doc.add_paragraph()
        p_ref.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p_ref.paragraph_format.line_spacing = 1.05
        p_ref.paragraph_format.left_indent = Inches(0.25)
        p_ref.paragraph_format.first_line_indent = Inches(-0.25)
        p_ref.paragraph_format.space_after = Pt(2)
        r = p_ref.add_run(ref)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(8.0)

    primary_file = "SmartPCB-XAI_Research_Paper.docx"
    alt_file = "SmartPCB-XAI_Research_Paper_8Pages.docx"
    saved_paths = []
    
    try:
        doc.save(primary_file)
        saved_paths.append(primary_file)
        print(f"[SUCCESS] Saved to primary: {os.path.abspath(primary_file)} ({os.path.getsize(primary_file)} bytes)")
    except PermissionError:
        print(f"[NOTE] '{primary_file}' is currently open in Word. Writing to alternative file '{alt_file}'.")

    try:
        doc.save(alt_file)
        saved_paths.append(alt_file)
        print(f"[SUCCESS] Saved to 8-page edition: {os.path.abspath(alt_file)} ({os.path.getsize(alt_file)} bytes)")
    except Exception as e:
        print(f"[WARNING] Could not save to {alt_file}: {e}")

    return saved_paths

if __name__ == "__main__":
    build_8page_paper()
