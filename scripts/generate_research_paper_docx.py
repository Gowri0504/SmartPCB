"""
Generate the IEEE-style Research Paper Word document (SmartPCB-XAI_Research_Paper.docx)
matching the provided publication-grade PDF paper.
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

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def create_paper():
    doc = Document()
    
    # Page setup - 0.75 in margins (IEEE standard)
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)
        section.page_width = Inches(8.5)
        section.page_height = Inches(11.0)

    # Styles
    styles = doc.styles
    normal_style = styles['Normal']
    normal_style.font.name = 'Times New Roman'
    normal_style.font.size = Pt(10)
    normal_style.font.color.rgb = RGBColor(0x11, 0x18, 0x27)
    normal_style.paragraph_format.line_spacing = 1.15
    normal_style.paragraph_format.space_after = Pt(4)

    # Title
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(12)
    run_title = p_title.add_run("SmartPCB-XAI: Explainable Dual-Detector PCB Inspection System")
    run_title.font.name = 'Times New Roman'
    run_title.font.size = Pt(20)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(0x0f, 0x17, 0x2a)

    # Authors Table (3 columns)
    author_table = doc.add_table(rows=1, cols=3)
    author_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    author_table.autofit = False

    authors = [
        ("Prathika M E", "Department of Information Technology\nKongu Engineering College\nErode, India\nprathieasu@gmail.com"),
        ("Abisha Rebekkal T", "Department of Information Technology\nKongu Engineering College\nErode, India\nabisharebekkal@gmail.com"),
        ("Gowri D", "Department of Information Technology\nKongu Engineering College\nErode, India\ngowri.d.tech@gmail.com")
    ]

    col_widths = [Inches(2.3), Inches(2.3), Inches(2.3)]
    for i, (name, affil) in enumerate(authors):
        cell = author_table.cell(0, i)
        cell.width = col_widths[i]
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(2)
        r_name = p.add_run(name)
        r_name.font.name = 'Times New Roman'
        r_name.font.size = Pt(11)
        r_name.font.bold = True
        
        p_aff = cell.add_paragraph()
        p_aff.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_aff.paragraph_format.line_spacing = 1.1
        p_aff.paragraph_format.space_after = Pt(0)
        r_aff = p_aff.add_run(affil)
        r_aff.font.name = 'Times New Roman'
        r_aff.font.size = Pt(9)
        r_aff.font.italic = False

    # Add space after authors
    p_spacer = doc.add_paragraph()
    p_spacer.paragraph_format.space_after = Pt(8)

    # Abstract & Keywords Box
    abs_table = doc.add_table(rows=1, cols=1)
    abs_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    abs_cell = abs_table.cell(0, 0)
    abs_cell.width = Inches(7.0)
    set_cell_background(abs_cell, "F8FAFC")
    set_cell_margins(abs_cell, top=140, bottom=140, left=180, right=180)
    
    p_abs = abs_cell.paragraphs[0]
    p_abs.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_abs.paragraph_format.line_spacing = 1.15
    p_abs.paragraph_format.space_after = Pt(6)
    
    r_abshdr = p_abs.add_run("Abstract — ")
    r_abshdr.font.name = 'Times New Roman'
    r_abshdr.font.bold = True
    r_abshdr.font.size = Pt(9.5)
    
    abstract_text = (
        "Printed circuit board (PCB) inspection is increasingly relying on deep-learning object detectors, "
        "but published systems rarely disclose the gap between headline accuracy figures and what is actually "
        "measured on independently held-out data. This paper introduces SmartPCB-XAI, a two-stage solution "
        "distinguishing between PCB-defect (6 classes: open circuit, short, mouse-bite, spur, spurious copper, "
        "and missing hole) and component-identification (6 classes: IC, capacitor, diode, inductor, resistor, "
        "and transistor) with an explainability module, deterministic severity scoring, an interactive digital-twin "
        "visualization, and automated PDF/Excel reporting. On a rigorously audited, held-out test split of 500 DeepPCB "
        "images (3,140 ground-truth boxes), our defect detector attains 95.1% mAP@50 (93.1% precision, 90.6% recall) "
        "without external training data, exceeding a recent lightweight YOLOv11s baseline (92.3%) evaluated on the "
        "same benchmark. Conversely, our component detector achieves only 9.3% mAP@50 on a curated 89-image test set, "
        "an empirical deficit we trace to a 10-to-6 class taxonomy mismatch, tiny-object prevalence (94.2% under 32×32 "
        "pixels), and severe physical-board imbalance (64% of test images originating from a single board). To address "
        "this disparity in operational deployments, we implement an explicit per-detection class-mapping transparency "
        "flag rather than silently coercing or suppressing out-of-vocabulary detections. Finally, we establish a concrete, "
        "technique-level improvement roadmap—incorporating FasterNet partial convolution, Efficient Multi-scale Attention, "
        "and Wise-IoU loss—to bridge the component accuracy gap while preserving the system's end-to-end explainability "
        "and architectural integrity."
    )
    r_abstxt = p_abs.add_run(abstract_text)
    r_abstxt.font.name = 'Times New Roman'
    r_abstxt.font.size = Pt(9.5)

    p_kw = abs_cell.add_paragraph()
    p_kw.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_kw.paragraph_format.line_spacing = 1.15
    p_kw.paragraph_format.space_after = Pt(2)
    
    r_kwhdr = p_kw.add_run("Keywords — ")
    r_kwhdr.font.name = 'Times New Roman'
    r_kwhdr.font.bold = True
    r_kwhdr.font.size = Pt(9.5)
    
    keywords_text = "Printed Circuit Board (PCB), Defect Detection, Object Detection, YOLOv11, Explainable AI (XAI), Class Activation Mapping, Digital Twin, Data Leakage, Industrial Inspection."
    r_kwtxt = p_kw.add_run(keywords_text)
    r_kwtxt.font.name = 'Times New Roman'
    r_kwtxt.font.size = Pt(9.5)
    r_kwtxt.font.italic = True

    # Helper function for adding headings
    def add_sec_heading(title):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(title)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(11)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0x0f, 0x17, 0x2a)
        return p

    def add_subsec_heading(title):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(title)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(10)
        run.font.bold = True
        run.font.italic = True
        run.font.color.rgb = RGBColor(0x1e, 0x29, 0x3b)
        return p

    def add_body_p(text, justify=True):
        p = doc.add_paragraph()
        if justify:
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_after = Pt(4)
        run = p.add_run(text)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(10)
        return p

    # SECTION I
    add_sec_heading("I. INTRODUCTION")
    add_body_p(
        "Automated optical inspection (AOI) for printed circuit boards (PCBs) is an essential component of modern "
        "electronics manufacturing [1]. As electronic assemblies become denser and solder joints smaller, manual "
        "visual inspection becomes untenable, and deep-learning object detectors such as YOLO [2] have increasingly "
        "replaced traditional template-matching algorithms. Recent work has pushed detection accuracy to high headline "
        "figures while introducing architectural refinements to reduce inference cost [3], [4]."
    )
    add_body_p(
        "However, a significant gap often separates published accuracy metrics from what is reliably measured on "
        "independently held-out test data in real-world deployment. In production-grade PCB inspection systems, several "
        "methodological pitfalls recur: (1) training and evaluating on overlapping data splits, often obscured by external "
        "pre-training; (2) relying on opaque class-mapping layers that silently suppress or mislabel detections falling "
        "outside a target taxonomy; (3) confusing metric definitions, such as reporting single-threshold F1 or precision "
        "as \"mAP\"; and (4) marketing heuristic attribution maps as authentic gradient-based Grad-CAM without implementing "
        "the requisite backpropagation passes [5], [6]."
    )
    add_body_p(
        "This paper presents SmartPCB-XAI, an open and explainable dual-detector inspection system designed to confront "
        "these methodological challenges directly. SmartPCB-XAI decouples the inspection task into two specialized "
        "YOLOv11 detectors—one dedicated to surface defects (open circuit, short, mouse-bite, spur, spurious copper, "
        "missing hole) and one dedicated to electronic components (IC, capacitor, diode, inductor, resistor, transistor). "
        "The system pairs these detectors with an activation-energy explainability layer, deterministic IPC-A-610-informed "
        "severity scoring, an interactive digital-twin visualization [7], [8], and automated reporting."
    )
    add_body_p(
        "Crucially, we report our experimental results under strict evaluation discipline: our defect detector achieves "
        "95.1% mAP@50 (63.3% mAP@50-95, 93.1% precision, 90.6% recall) on a held-out 500-image test set, while our "
        "component detector achieves only 9.3% mAP@50 on an imbalanced test split. Rather than concealing the component "
        "disparity or claiming uniform perfection, we diagnose its root causes (severe board-level imbalance, tiny object "
        "scales, and taxonomy misalignment) and formulate an actionable, technique-level roadmap to resolve it."
    )
    add_body_p(
        "The primary contributions of this paper are fivefold:\n"
        "1. Architecture: An end-to-end, multi-tier inspection platform combining dual YOLOv11 inference, microservice API orchestration, full-stack reporting, and digital-twin visualization.\n"
        "2. Rigorous Evaluation: Genuinely held-out evaluation of both defect and component models, executed using official framework APIs and confirmed reproducible.\n"
        "3. Leakage & Domain Audit: A comprehensive data leakage audit showing zero filename or board-level split leakage, paired with full disclosure of domain-boundary caveats for external weights.\n"
        "4. Transparent Taxonomy: Implementation of an explicit per-detection class_mapped metadata flag preventing silent label coercion or suppression.\n"
        "5. Principled Roadmap: An empirical, ablation-backed enhancement roadmap incorporating FasterNet partial convolution, Efficient Multi-Scale Attention, and Wise-IoU loss to close the component accuracy gap."
    )

    # SECTION II
    add_sec_heading("II. RELATED WORK")
    add_body_p(
        "Deep learning for PCB defect detection has evolved substantially since the introduction of benchmark datasets. "
        "Tang et al. [4] released the DeepPCB dataset alongside an online defect detector, defining the canonical six-class "
        "defect taxonomy (open, short, mouse-bite, spur, copper, pin-hole) that remains the industrial and academic standard. "
        "Subsequent research has explored faster and more lightweight architectures for edge deployment. Most notably, "
        "Ye et al. [3] introduced an improved lightweight YOLOv11s model that incorporates an EfficientViT sandwich backbone, "
        "a C3k2_Faster_EMA neck incorporating FasterNet partial convolutions and Efficient Multi-scale Attention, and an "
        "Inner_Wise_IoU loss function. Evaluated on the joint PKU-Market-PCB and DeepPCB datasets, their model achieved "
        "92.3% mAP@50 while reducing model size by 58.3% and parameter count by 61.7% relative to a baseline YOLOv11s."
    )
    add_body_p(
        "Explainable AI (XAI) in visual quality inspection is predominantly based on Class Activation Mapping (CAM) methods. "
        "Selvaraju et al. [5] introduced Grad-CAM, which calculates the gradients of the score for class c with respect to "
        "feature activation maps in convolutional layers to produce coarse 2D localization heatmaps. Chattopadhay et al. [6] "
        "extended this with Grad-CAM++, using positive partial derivatives to capture multiple instances of the target class. "
        "In industrial software, however, computational constraints often lead developers to substitute feed-forward activation "
        "energy heuristics while erroneously presenting them as authentic Grad-CAM. In SmartPCB-XAI, we adopt an explicit "
        "disclosure policy, labeling our activation energy maps transparently while providing architectural hooks for full Grad-CAM++."
    )
    add_body_p(
        "Digital twins for manufacturing quality have been extensively reviewed by Tao et al. [7], defining the continuous "
        "virtual representation of physical assets across product lifecycles. Bhattacharya and Cloutier [8] highlighted the "
        "imperative of verifiable explainability in safety-critical automated manufacturing. Shakya et al. [9] developed the "
        "FICS-PCB multi-modal dataset for automated component visual inspection, highlighting the extreme variance in component "
        "appearance, tiny footprint scales, and dense arrangements encountered on physical circuit boards."
    )

    # SECTION III
    add_sec_heading("III. PROPOSED SYSTEM ARCHITECTURE")
    add_body_p(
        "SmartPCB-XAI is structured as a decoupled four-tier architecture separating high-performance AI inference, "
        "application orchestration, persistent enterprise storage, and interactive user visualization. Fig. 1 illustrates "
        "the system architecture, and Fig. 2 details the end-to-end inspection dataflow for a submitted board image."
    )

    add_subsec_heading("A. Layered Architecture and Responsibilities")
    add_body_p(
        "1. AI Inference Microservice (FastAPI / Python): Hosts the dual YOLOv11 detection engine, feature activation visualizer, "
        "deterministic severity scoring engine, and the IPC-A-610-aligned repair recommendation knowledge base. Exposes unified "
        "REST endpoints (/api/inspect, /api/health, /api/model-safety) operating asynchronously.\n"
        "2. Application Backend (Node.js / Express): Serves as the central API gateway and authentication manager. Handles file "
        "upload buffering, routes inspection payloads to FastAPI, persists records and technician feedback in MongoDB, and generates "
        "PDF/Excel inspection certificates.\n"
        "3. Presentation Layer (React / TypeScript / Vite): Implements five specialized operational views: Live Inspection, "
        "Interactive Digital Twin, Analytics & Yield Dashboard, Continuous Learning & Feedback, and Model Performance Analysis.\n"
        "4. Data Persistence Layer (MongoDB): Manages JSON inspection documents, defect bounding-box geometry, user reviews, "
        "and confidence thresholds for continuous quality auditing."
    )

    # Add Figure 1 if image exists
    fig1_path = os.path.join("scratch", "pdf_images", "page_2_img_0_Image27.png")
    if os.path.exists(fig1_path):
        p_fig1 = doc.add_paragraph()
        p_fig1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_fig1.paragraph_format.space_before = Pt(8)
        p_fig1.paragraph_format.space_after = Pt(2)
        doc.add_picture(fig1_path, width=Inches(6.2))
        p_cap1 = doc.add_paragraph()
        p_cap1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap1.paragraph_format.space_after = Pt(8)
        r_cap1 = p_cap1.add_run("Fig. 1. Layered architecture of SmartPCB-XAI showing decoupled AI microservice, Express gateway, and React interface.")
        r_cap1.font.name = 'Times New Roman'
        r_cap1.font.size = Pt(9)
        r_cap1.font.italic = True

    add_subsec_heading("B. End-to-End Inspection Workflow")
    add_body_p(
        "When an operator uploads a PCB image, Express passes the multipart stream to FastAPI. The image is preprocessed "
        "and normalized. For component detection on large boards, optional tiled inference partitions the surface into 960×960 "
        "windows with 33% stride overlap, merging predictions via non-maximum suppression (NMS). Both detectors run concurrently. "
        "Every component detection is matched against the canonical 6-class schema; unmapped classes (relay, buzzer, switch, "
        "battery, led) retain raw labels with class_mapped=false. Defect detections undergo confidence validation, spatial clustering, "
        "activation heat-map generation, and deterministic severity computation. If any CRITICAL defect is found, the board is "
        "immediately rejected; otherwise, a cumulative quality penalty is calculated. The complete response is persisted in MongoDB "
        "and visualized live on the operator's console."
    )

    # Add Figure 2 if image exists
    fig2_path = os.path.join("scratch", "pdf_images", "page_2_img_1_Image28.png")
    if os.path.exists(fig2_path):
        p_fig2 = doc.add_paragraph()
        p_fig2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_fig2.paragraph_format.space_before = Pt(8)
        p_fig2.paragraph_format.space_after = Pt(2)
        doc.add_picture(fig2_path, width=Inches(6.2))
        p_cap2 = doc.add_paragraph()
        p_cap2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap2.paragraph_format.space_after = Pt(8)
        r_cap2 = p_cap2.add_run("Fig. 2. End-to-end inspection workflow for a single board image from ingestion to report generation.")
        r_cap2.font.name = 'Times New Roman'
        r_cap2.font.size = Pt(9)
        r_cap2.font.italic = True

    add_subsec_heading("C. Failure-Safe Outcome Handling")
    add_body_p(
        "A critical vulnerability in automated inspection is silent failure, where inference crashes or corrupt images "
        "result in default \"0 defect\" PASS outputs. SmartPCB-XAI implements explicit failure-safe logic: (1) True Clean: "
        "high component confidence, zero defect boxes, valid image quality; (2) Suspicious Zero Detection: image resolution "
        "anomalies or low signal confidence flag review_required=true, preventing false PASS certificates; (3) Error State: "
        "exception handling wraps every inference branch, returning explicit HTTP 500 error envelopes without corrupting statistics."
    )

    add_subsec_heading("D. Explainability Module")
    add_body_p(
        "Visual interpretability is provided via multi-channel feature activation energy mapping. The penultimate convolutional "
        "feature maps are extracted during the forward pass, rectified, normalized, and mapped onto a jet colormap overlaid at "
        "40% opacity on the input image. This identifies the spatial receptive field driving the highest-confidence defect "
        "detection. Because this represents activation magnitude rather than true gradient backpropagation, the system attaches "
        "an explicit disclosure string (XAI_DISCLAIMER) ensuring transparency."
    )

    add_subsec_heading("E. Severity and Quality Estimation")
    add_body_p(
        "Defect severity is calculated deterministically via a base-weight lookup modulated by relative defect footprint and "
        "model confidence:\n"
        "Severity = BaseWeight(defect_type) + 15 × (NormalizedArea)^0.10 + 30 × Confidence\n"
        "The board Quality Score begins at 100.0, subtracting penalties proportional to defect severity and confidence. "
        "Boards are assigned one of four operational grades: EXCELLENT/PASS (score ≥ 90), ACCEPTABLE/PASS-ADVISORY (75–89), "
        "MARGINAL/REWORK-REQUIRED (50–74), or REJECT/FAIL (< 50 or presence of any CRITICAL severity defect). Defect types are "
        "mapped to standard IPC-A-610 repair procedures in the rule-based knowledge engine."
    )

    add_subsec_heading("F. Dashboard, Reporting, and Feedback")
    add_body_p(
        "The web interface displays high-resolution PCB zoom controls, bounding-box toggles, side-by-side XAI heatmaps, "
        "and an interactive Digital Twin rendering component placements and defect hotspots in SVG/WebGL coordinate space. "
        "Technicians can submit ground-truth corrections (false positive/negative feedback), which are stored in MongoDB to "
        "enable continuous model retraining. Inspection certificates can be exported on-demand in professional PDF or Excel format."
    )

    # SECTION IV
    add_sec_heading("IV. DATASET CONSTRUCTION AND METHODOLOGY")
    add_subsec_heading("A. Defect Dataset")
    add_body_p(
        "The defect detection model is trained and evaluated on the DeepPCB benchmark [4], consisting of 1,500 pairs of "
        "defect-free template and defective PCB images (size 640×640 pixels). Ground truth includes 10,013 annotations across "
        "six defect categories: open circuit (open), short circuit (short), mouse-bite (mousebite), spur (spur), spurious copper "
        "(copper), and missing hole (pin-hole). The official partition comprises 850 training images (5,716 boxes), 150 validation "
        "images (1,157 boxes), and 500 held-out test images (3,140 boxes)."
    )

    add_subsec_heading("B. Component Dataset")
    add_body_p(
        "The component dataset is derived from high-resolution industrial PCB scans (mean resolution 2,400×1,800 pixels) annotated "
        "for electronic components. The curated dataset contains 1,009 images and 33,156 bounding boxes across six target classes: "
        "ICs, capacitors, diodes, inductors, resistors, and transistors. The dataset is partitioned into 804 train, 116 val, and "
        "89 test images. Extreme scale disparity is present: 94.2% of annotated components measure less than 32×32 pixels, requiring "
        "high-resolution feature extraction or tiled inference."
    )

    add_subsec_heading("C. Data Leakage and Integrity Audit")
    add_body_p(
        "To establish genuine evaluation validity, an automated dataset integrity audit was executed across both corpora. "
        "The audit screened for: (1) exact filename overlaps; (2) perceptual hash collisions (pHash Hamming distance ≤ 2); "
        "(3) physical PCB board-ID duplication across splits; (4) out-of-bounds coordinates (x, y, w, h > 1.0); and (5) class "
        "index validity. Both datasets showed exactly 0 cross-split filename or board-level leakage. Zero bounding boxes exceeded "
        "image boundaries. In the component dataset, 13 residual rows containing out-of-range class indices (index 7 against 6 classes) "
        "were identified and quarantined."
    )

    # SECTION V
    add_sec_heading("V. EXPERIMENTAL RESULTS")
    add_body_p(
        "All quantitative evaluations were performed using the official Ultralytics YOLO validation API (model.val()) on the "
        "strictly held-out test partitions. All evaluations were executed on a dedicated benchmark workstation with fixed random "
        "seeds (seed=42) and verified against persisted prediction logs."
    )

    add_subsec_heading("A. Defect Detector Results")
    add_body_p(
        "Table I reports the performance of our defect detection models on the 500-image held-out DeepPCB test set. Our primary "
        "YOLOv11s model trained from scratch on audited local data achieves 95.1% mAP@50 (63.3% mAP@50-95), with 93.1% precision "
        "and 90.6% recall. This surpasses the 92.3% mAP@50 reported by Ye et al. [3] on the same defect taxonomy without requiring "
        "external pre-training data."
    )

    # TABLE I
    p_t1_cap = doc.add_paragraph()
    p_t1_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t1_cap.paragraph_format.space_before = Pt(8)
    p_t1_cap.paragraph_format.space_after = Pt(2)
    p_t1_cap.paragraph_format.keep_with_next = True
    r_t1_cap = p_t1_cap.add_run("TABLE I. DEFECT DETECTOR — HELD-OUT TEST SET (500 images, 3,140 GT boxes)")
    r_t1_cap.font.name = 'Times New Roman'
    r_t1_cap.font.size = Pt(9.5)
    r_t1_cap.font.bold = True

    t1 = doc.add_table(rows=5, cols=5)
    t1.alignment = WD_TABLE_ALIGNMENT.CENTER
    t1_headers = ["Model / Checkpoint", "Evaluation Protocol", "mAP@50", "mAP@50-95", "Micro-F1"]
    t1_data = [
        ["Legacy Checkpoint (0.25)", "Default, fixed-threshold evaluator", "91.47%", "72.33%", "94.68%"],
        ["Legacy Checkpoint (0.70)", "Val-calibrated, fixed-threshold evaluator", "92.74%", "73.83%", "95.96%"],
        ["Legacy Checkpoint (Standard)", "Full PR-curve evaluator (unverified data)", "98.30%", "—", "—"],
        ["From-Scratch YOLOv11s (PRIMARY)", "Full PR-curve evaluator, seed 42, local data", "95.11%", "63.27%", "91.84%"]
    ]
    t1_widths = [Inches(2.2), Inches(2.2), Inches(0.85), Inches(0.95), Inches(0.80)]
    
    for c_idx, h_text in enumerate(t1_headers):
        cell = t1.cell(0, c_idx)
        cell.width = t1_widths[c_idx]
        set_cell_background(cell, "1E293B")
        set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h_text)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(8.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    for r_idx, row in enumerate(t1_data):
        bg = "F1F5F9" if r_idx % 2 == 1 else "FFFFFF"
        if r_idx == 3:
            bg = "EFF6FF"  # Highlight primary model
        for c_idx, val in enumerate(row):
            cell = t1.cell(r_idx + 1, c_idx)
            cell.width = t1_widths[c_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=60, bottom=60, left=100, right=100)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if c_idx < 2 else WD_ALIGN_PARAGRAPH.RIGHT
            r = p.add_run(val)
            r.font.name = 'Times New Roman'
            r.font.size = Pt(8.5)
            if r_idx == 3:
                r.font.bold = True

    add_body_p(
        "Table II breaks down the per-class detection metrics across all six defect classes for our primary from-scratch model "
        "and the legacy checkpoint. The primary model achieves exceptional accuracy on pin-hole (98.3%), copper (97.9%), "
        "mousebite (96.2%), and spur (95.8%), while maintaining 94.1% on open circuit and 88.4% on short circuit."
    )

    # TABLE II
    p_t2_cap = doc.add_paragraph()
    p_t2_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t2_cap.paragraph_format.space_before = Pt(8)
    p_t2_cap.paragraph_format.space_after = Pt(2)
    p_t2_cap.paragraph_format.keep_with_next = True
    r_t2_cap = p_t2_cap.add_run("TABLE II. PER-CLASS DEFECT DETECTION RESULTS (500 Test Images, 3,140 Ground Truth Boxes)")
    r_t2_cap.font.name = 'Times New Roman'
    r_t2_cap.font.size = Pt(9.5)
    r_t2_cap.font.bold = True

    t2 = doc.add_table(rows=7, cols=6)
    t2.alignment = WD_TABLE_ALIGNMENT.CENTER
    t2_headers = ["Defect Class", "Canonical Label", "mAP@50", "Precision", "Recall", "GT Instances"]
    t2_data = [
        ["Pin-hole", "pin-hole", "98.3%", "95.2%", "94.8%", "470"],
        ["Spurious Copper", "copper", "97.9%", "96.4%", "93.1%", "464"],
        ["Mouse-bite", "mousebite", "96.2%", "94.8%", "91.5%", "586"],
        ["Spur", "spur", "95.8%", "93.7%", "92.4%", "483"],
        ["Open Circuit", "open", "94.1%", "91.6%", "89.3%", "659"],
        ["Short Circuit", "short", "88.4%", "85.8%", "82.5%", "478"],
    ]
    t2_widths = [Inches(1.8), Inches(1.3), Inches(0.9), Inches(1.0), Inches(1.0), Inches(1.0)]

    for c_idx, h_text in enumerate(t2_headers):
        cell = t2.cell(0, c_idx)
        cell.width = t2_widths[c_idx]
        set_cell_background(cell, "1E293B")
        set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h_text)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(8.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    for r_idx, row in enumerate(t2_data):
        bg = "F1F5F9" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(row):
            cell = t2.cell(r_idx + 1, c_idx)
            cell.width = t2_widths[c_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=60, bottom=60, left=100, right=100)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if c_idx < 2 else WD_ALIGN_PARAGRAPH.RIGHT
            r = p.add_run(val)
            r.font.name = 'Times New Roman'
            r.font.size = Pt(8.5)

    add_subsec_heading("B. Component Detector Results")
    add_body_p(
        "Table III summarizes performance for the deployed component detection model across confidence operating points, "
        "and Table IV provides the class-level breakdown. In contrast to the defect model, the component detector achieves "
        "only 9.33% mAP@50 at the default 0.25 threshold (9.53% at calibrated 0.15 threshold)."
    )

    # TABLE III
    p_t3_cap = doc.add_paragraph()
    p_t3_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t3_cap.paragraph_format.space_before = Pt(8)
    p_t3_cap.paragraph_format.space_after = Pt(2)
    p_t3_cap.paragraph_format.keep_with_next = True
    r_t3_cap = p_t3_cap.add_run("TABLE III. COMPONENT DETECTOR — CURATED EVALUATION SPLIT (89 test / 116 val images)")
    r_t3_cap.font.name = 'Times New Roman'
    r_t3_cap.font.size = Pt(9.5)
    r_t3_cap.font.bold = True

    t3 = doc.add_table(rows=3, cols=5)
    t3.alignment = WD_TABLE_ALIGNMENT.CENTER
    t3_headers = ["Threshold Setting", "Selection Criterion", "mAP@50", "mAP@50-95", "Micro-F1"]
    t3_data = [
        ["0.25 (Default)", "Standard framework operating point", "9.33%", "4.37%", "23.20%"],
        ["0.15 (Calibrated)", "Validation-calibrated maximum F1", "9.53%", "4.25%", "24.44%"]
    ]
    t3_widths = [Inches(1.8), Inches(2.2), Inches(1.0), Inches(1.0), Inches(1.0)]

    for c_idx, h_text in enumerate(t3_headers):
        cell = t3.cell(0, c_idx)
        cell.width = t3_widths[c_idx]
        set_cell_background(cell, "1E293B")
        set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h_text)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(8.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    for r_idx, row in enumerate(t3_data):
        bg = "F1F5F9" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(row):
            cell = t3.cell(r_idx + 1, c_idx)
            cell.width = t3_widths[c_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=60, bottom=60, left=100, right=100)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if c_idx < 2 else WD_ALIGN_PARAGRAPH.RIGHT
            r = p.add_run(val)
            r.font.name = 'Times New Roman'
            r.font.size = Pt(8.5)

    # TABLE IV
    p_t4_cap = doc.add_paragraph()
    p_t4_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t4_cap.paragraph_format.space_before = Pt(8)
    p_t4_cap.paragraph_format.space_after = Pt(2)
    p_t4_cap.paragraph_format.keep_with_next = True
    r_t4_cap = p_t4_cap.add_run("TABLE IV. PER-CLASS COMPONENT DETECTOR PERFORMANCE (Threshold 0.25)")
    r_t4_cap.font.name = 'Times New Roman'
    r_t4_cap.font.size = Pt(9.5)
    r_t4_cap.font.bold = True

    t4 = doc.add_table(rows=7, cols=6)
    t4.alignment = WD_TABLE_ALIGNMENT.CENTER
    t4_headers = ["Component Class", "AP@50", "Precision", "Recall", "GT Boxes", "Predictions"]
    t4_data = [
        ["Transistor", "25.22%", "56.25%", "39.13%", "23", "16"],
        ["IC", "15.84%", "54.55%", "21.95%", "82", "33"],
        ["Capacitor", "7.64%", "29.67%", "21.64%", "536", "391"],
        ["Resistor", "6.61%", "39.44%", "16.40%", "433", "180"],
        ["Diode", "0.69%", "23.08%", "2.14%", "140", "13"],
        ["Inductor", "0.00%", "0.00%", "0.00%", "24", "0"],
    ]
    t4_widths = [Inches(1.8), Inches(1.0), Inches(1.0), Inches(1.0), Inches(1.1), Inches(1.1)]

    for c_idx, h_text in enumerate(t4_headers):
        cell = t4.cell(0, c_idx)
        cell.width = t4_widths[c_idx]
        set_cell_background(cell, "1E293B")
        set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h_text)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(8.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    for r_idx, row in enumerate(t4_data):
        bg = "F1F5F9" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(row):
            cell = t4.cell(r_idx + 1, c_idx)
            cell.width = t4_widths[c_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=60, bottom=60, left=100, right=100)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if c_idx == 0 else WD_ALIGN_PARAGRAPH.RIGHT
            r = p.add_run(val)
            r.font.name = 'Times New Roman'
            r.font.size = Pt(8.5)

    add_body_p(
        "Four empirical factors explain this deficit: (1) Taxonomy Mismatch: the checkpoint was trained on 10 classes "
        "(including relay, buzzer, switch, battery, led) whereas the test set contains only 6 standard classes; "
        "(2) Systematic Under-Recall: recall does not exceed 39.1% on any class; (3) Extreme Scale: 94.2% of component "
        "targets are smaller than 32×32 pixels, suffering severe attenuation under global resizing; (4) Board Overfitting: "
        "a physical board-ID cluster analysis revealed that 64% of test-set images belong to a single physical board."
    )

    add_subsec_heading("C. Evaluation Methodology Reconciliation")
    add_body_p(
        "During verification, an Ultralytics framework evaluation of the legacy defect checkpoint returned 98.3% mAP@50, "
        "significantly higher than our custom evaluator (91.47%). Rather than adopting the higher number, we performed "
        "a methodological reconciliation (Table V). The discrepancy was traced to PR-curve trapezoidal integration versus "
        "fixed-operating-point evaluation and class-index string parsing. Furthermore, hash auditing revealed the legacy "
        "model had been pre-trained on an unspecified Kaggle dataset, preventing verification of disjoint splits. "
        "This prompted our retraining from scratch, which produced the verified 95.11% model."
    )

    # TABLE V
    p_t5_cap = doc.add_paragraph()
    p_t5_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t5_cap.paragraph_format.space_before = Pt(8)
    p_t5_cap.paragraph_format.space_after = Pt(2)
    p_t5_cap.paragraph_format.keep_with_next = True
    r_t5_cap = p_t5_cap.add_run("TABLE V. EVALUATION METHODOLOGY COMPARISON (Identical Legacy Checkpoint)")
    r_t5_cap.font.name = 'Times New Roman'
    r_t5_cap.font.size = Pt(9.5)
    r_t5_cap.font.bold = True

    t5 = doc.add_table(rows=4, cols=3)
    t5.alignment = WD_TABLE_ALIGNMENT.CENTER
    t5_headers = ["Evaluation Dimension", "Custom Script Evaluator (91.47%)", "Ultralytics Standard API (98.30%)"]
    t5_data = [
        ["Confidence Handling", "Fixed operating point threshold (0.25)", "Full Precision-Recall curve integration"],
        ["Class-Index Handling", "Positional index mapping", "Checkpoint-native string matching"],
        ["AP Computation", "Discrete interpolated precision sum", "Continuous 101-point COCO-style integration"]
    ]
    t5_widths = [Inches(2.2), Inches(2.4), Inches(2.4)]

    for c_idx, h_text in enumerate(t5_headers):
        cell = t5.cell(0, c_idx)
        cell.width = t5_widths[c_idx]
        set_cell_background(cell, "1E293B")
        set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h_text)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(8.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    for r_idx, row in enumerate(t5_data):
        bg = "F1F5F9" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(row):
            cell = t5.cell(r_idx + 1, c_idx)
            cell.width = t5_widths[c_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=60, bottom=60, left=100, right=100)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            r = p.add_run(val)
            r.font.name = 'Times New Roman'
            r.font.size = Pt(8.5)

    add_subsec_heading("D. Component-Class Mapping Transparency")
    add_body_p(
        "To resolve the tension between the 10-class model and the 6-class target taxonomy in production, SmartPCB-XAI rejects "
        "silent label coercion. Non-target detections (relay, buzzer, switch, battery, led) are retained under their true names "
        "and flagged with class_mapped=false. This provides downstream systems and human inspectors with unambiguous provenance."
    )

    add_subsec_heading("E. A Methodological Finding: Metric Definition Errors")
    add_body_p(
        "During development, several legacy scripts were found reporting \"mAP@50\" that varied when modifying the confidence "
        "threshold. By mathematical definition, Average Precision (AP) is threshold-independent, integrating precision over the "
        "entire recall domain:"
    )
    
    # Equation Paragraph
    p_eq = doc.add_paragraph()
    p_eq.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_eq.paragraph_format.space_before = Pt(6)
    p_eq.paragraph_format.space_after = Pt(6)
    r_eq = p_eq.add_run("AP = ∫₀¹ P(R) dR,         mAP = (1 / M) ∑ᵢ₌₁ᴹ APᵢ               (1) - (2)")
    r_eq.font.name = 'Times New Roman'
    r_eq.font.size = Pt(10.5)
    r_eq.font.bold = True

    add_body_p(
        "A metric that shifts with an arbitrary confidence threshold is a single-operating-point F1/precision score, not mAP. "
        "We highlight this finding to encourage higher rigor across applied PCB inspection publications."
    )

    # SECTION VI
    add_sec_heading("VI. DISCUSSION, LIMITATIONS, AND IMPROVEMENT PLAN")
    add_subsec_heading("A. Honest Limitations")
    add_body_p(
        "1. Domain Boundary: While our from-scratch defect model (95.1%) is completely clean, external legacy checkpoints retain "
        "unverifiable training provenance.\n"
        "2. Activation-Energy XAI: The present explainability layer utilizes feedforward activation magnitude rather than true "
        "gradient-weighted Grad-CAM++.\n"
        "3. Component Weakness: Component detection (9.3% mAP@50) remains inadequate for autonomous production signoff.\n"
        "4. Lighting & Board Diversity: The DeepPCB benchmark is restricted to synthetic/bicolor board surfaces, requiring further "
        "validation on complex multi-layer solder-mask finishes."
    )

    add_subsec_heading("B. Concrete Improvement Plan")
    add_body_p(
        "Following the ablation methodology of Ye et al. [3], we define a six-point improvement plan:\n"
        "1. Retrain Component Detector: Re-execute from-scratch YOLOv11 training using high-resolution tiled inputs (960×960) "
        "and balanced physical-board cross-validation splits.\n"
        "2. PKU-Market-PCB Integration: Incorporate the PKU-Market-PCB benchmark to expand training diversity to complex real-world boards.\n"
        "3. C3k2_Faster_EMA Neck: Replace standard C3k2 convolutional blocks with FasterNet partial convolution and Efficient Multi-scale "
        "Attention (EMA) to boost tiny-component feature preservation while reducing parameters by 60%.\n"
        "4. Wise-IoU Loss: Replace standard CIoU with dynamic non-monotonic Wise-IoU v3, mitigating gradient distortion on tiny bounding boxes.\n"
        "5. True Grad-CAM++ Integration: Implement automated backward hook passes for class-specific gradient computation.\n"
        "6. Test-Time Augmentation (TTA) & WBF: Deploy multi-scale test-time augmentation and Weighted Box Fusion across training checkpoints."
    )

    # SECTION VII
    add_sec_heading("VII. CONCLUSION")
    add_body_p(
        "This paper presented SmartPCB-XAI, an explainable, dual-detector automated PCB inspection platform built with an emphasis "
        "on evaluation honesty, failure-safe architectural design, and end-to-end integration. On a held-out 500-image test set, "
        "our from-scratch defect detector achieves 95.1% mAP@50 (93.1% precision, 90.6% recall), exceeding recent published baselines "
        "without data leakage or external pre-training dependencies. We transparently disclosed the 9.3% mAP@50 component detection "
        "deficit, dissected its root causes, and introduced an explicit class-mapping transparency flag alongside a concrete "
        "architectural roadmap for resolution. By bridging deep learning detection with deterministic severity rules, digital twins, "
        "and strict evaluation discipline, SmartPCB-XAI provides a robust foundation for trustworthy industrial PCB inspection."
    )

    # REFERENCES
    add_sec_heading("REFERENCES")
    refs = [
        "[1] Q. Ling and N. A. M. Isa, \"Printed circuit board defect detection methods based on image processing, machine learning and deep learning: A survey,\" IEEE Access, vol. 11, pp. 15921-15944, 2023.",
        "[2] J. Redmon, S. Divvala, R. Girshick, and A. Farhadi, \"You only look once: Unified, real-time object detection,\" in Proc. IEEE Conf. Comput. Vis. Pattern Recognit. (CVPR), 2016, pp. 779-788.",
        "[3] X. Ye, L. Huang, J. Wang, X. Hu, J. Xu, and C. Zhang, \"A lightweight PCB defect detection algorithm based on an improved YOLOv11s,\" IEEE Access, vol. 14, pp. 56412-56426, 2026, doi: 10.1109/ACCESS.2026.3678967.",
        "[4] S. Tang, F. He, X. Huang, and J. Yang, \"Online PCB defect detector on a new PCB defect dataset,\" arXiv:1902.06197, 2019.",
        "[5] R. R. Selvaraju, M. Cogswell, A. Das, R. Vedantam, D. Parikh, and D. Batra, \"Grad-CAM: Visual explanations from deep networks via gradient-based localization,\" in Proc. IEEE Int. Conf. Comput. Vis. (ICCV), 2017, pp. 618-626.",
        "[6] A. Chattopadhay, A. Sarkar, P. Howlader, and V. N. Balasubramanian, \"Grad-CAM++: Generalized gradient-based visual explanations for deep convolutional networks,\" in Proc. IEEE Winter Conf. Appl. Comput. Vis. (WACV), 2018, pp. 839-847.",
        "[7] F. Tao, H. Zhang, A. Liu, and A. Y. C. Nee, \"Digital twin in industry: State-of-the-art,\" IEEE Trans. Ind. Informat., vol. 15, no. 4, pp. 2405-2415, 2019.",
        "[8] P. Bhattacharya and M. F. Cloutier, \"Explainable artificial intelligence for industrial applications,\" in Proc. IEEE Int. Conf. Ind. Technol., 2022.",
        "[9] M. Shakya et al., \"FICS-PCB: A multi-modal image dataset for automated printed circuit board visual inspection,\" IACR Cryptol. ePrint Arch., 2020.",
        "[10] IPC-A-610G, Acceptability of Electronic Assemblies, IPC — Association Connecting Electronics Industries, 2020."
    ]

    for ref in refs:
        p_ref = doc.add_paragraph()
        p_ref.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p_ref.paragraph_format.line_spacing = 1.1
        p_ref.paragraph_format.left_indent = Inches(0.3)
        p_ref.paragraph_format.first_line_indent = Inches(-0.3)
        p_ref.paragraph_format.space_after = Pt(3)
        r = p_ref.add_run(ref)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(8.5)

    out_path = "SmartPCB-XAI_Research_Paper.docx"
    doc.save(out_path)
    print(f"[SUCCESS] Research paper written to: {os.path.abspath(out_path)}")
    print(f"[SUCCESS] File size: {os.path.getsize(out_path)} bytes")

if __name__ == "__main__":
    create_paper()
