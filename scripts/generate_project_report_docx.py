"""
Generate the complete, publication-grade Kongu Engineering College Project Report
for SmartPCB-XAI as a Word document (.docx).
File: SmartPCB-XAI_Project_Report.docx
Format: 22ITP71 - PROJECT WORK II PHASE I
Students: ABISHA REBEKKAL T (23ITR001), GOWRI D (23ITR048)
Guide: Ms. P. VANITHA M.E., Department of Information Technology, KEC.
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

def set_cell_margins(cell, top=70, bottom=70, left=100, right=100):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def create_project_report():
    doc = Document()

    # Standard Report Margins: Left 1.25 in (binding), Right 1.0 in, Top 1.0 in, Bottom 1.0 in
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.25)
        section.right_margin = Inches(1.0)
        section.page_width = Inches(8.5)
        section.page_height = Inches(11.0)

    # Styles
    styles = doc.styles
    normal_style = styles['Normal']
    normal_style.font.name = 'Times New Roman'
    normal_style.font.size = Pt(12)
    normal_style.font.color.rgb = RGBColor(0x00, 0x00, 0x00)
    normal_style.paragraph_format.line_spacing = 1.3
    normal_style.paragraph_format.space_after = Pt(4)

    def add_chapter_title(num_str, title_str):
        p1 = doc.add_paragraph()
        p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p1.paragraph_format.space_before = Pt(12)
        p1.paragraph_format.space_after = Pt(2)
        p1.paragraph_format.keep_with_next = True
        r1 = p1.add_run(num_str)
        r1.font.name = 'Times New Roman'
        r1.font.size = Pt(14)
        r1.font.bold = True
        
        p2 = doc.add_paragraph()
        p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p2.paragraph_format.space_before = Pt(0)
        p2.paragraph_format.space_after = Pt(14)
        p2.paragraph_format.keep_with_next = True
        r2 = p2.add_run(title_str)
        r2.font.name = 'Times New Roman'
        r2.font.size = Pt(14)
        r2.font.bold = True
        return p2

    def add_sec_title(title_str):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(title_str)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(12)
        r.font.bold = True
        return p

    def add_subsec_title(title_str):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(title_str)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(12)
        r.font.bold = True
        r.font.italic = True
        return p

    def add_body(text_str, indent=0.3):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.first_line_indent = Inches(indent)
        p.paragraph_format.line_spacing = 1.3
        p.paragraph_format.space_after = Pt(4)
        r = p.add_run(text_str)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(12)
        return p

    # =========================================================================
    # 1. COVER PAGE
    # =========================================================================
    p_cov_t1 = doc.add_paragraph()
    p_cov_t1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cov_t1.paragraph_format.space_before = Pt(12)
    p_cov_t1.paragraph_format.space_after = Pt(4)
    r = p_cov_t1.add_run("SMARTPCB-XAI\nAN EXPLAINABLE AI-BASED PCB INSPECTION AND DECISION SUPPORT SYSTEM")
    r.font.size = Pt(15)
    r.font.bold = True

    p_cov_c = doc.add_paragraph()
    p_cov_c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cov_c.paragraph_format.space_before = Pt(8)
    p_cov_c.paragraph_format.space_after = Pt(4)
    r = p_cov_c.add_run("22ITP71 – PROJECT WORK II PHASE I\nA PROJECT REPORT")
    r.font.size = Pt(13)
    r.font.bold = True

    p_cov_sub = doc.add_paragraph()
    p_cov_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cov_sub.paragraph_format.space_before = Pt(12)
    p_cov_sub.paragraph_format.space_after = Pt(2)
    r = p_cov_sub.add_run("Submitted by")
    r.font.size = Pt(12)
    r.font.italic = True

    p_cov_st = doc.add_paragraph()
    p_cov_st.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cov_st.paragraph_format.space_before = Pt(2)
    p_cov_st.paragraph_format.space_after = Pt(10)
    r = p_cov_st.add_run("ABISHA REBEKKAL T (23ITR001)\nGOWRI D (23ITR048)")
    r.font.size = Pt(12)
    r.font.bold = True

    p_cov_req = doc.add_paragraph()
    p_cov_req.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cov_req.paragraph_format.space_before = Pt(6)
    p_cov_req.paragraph_format.space_after = Pt(10)
    r = p_cov_req.add_run("in partial fulfilment of the requirements for the award of the degree of\nBACHELOR OF TECHNOLOGY IN\nINFORMATION TECHNOLOGY")
    r.font.size = Pt(12)

    # Add College Logo
    logo_path = os.path.join("scratch", "template_images", "image1.png")
    if os.path.exists(logo_path):
        p_logo = doc.add_paragraph()
        p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_logo.paragraph_format.space_before = Pt(4)
        p_logo.paragraph_format.space_after = Pt(4)
        doc.add_picture(logo_path, width=Inches(1.8))

    p_cov_dept = doc.add_paragraph()
    p_cov_dept.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cov_dept.paragraph_format.space_before = Pt(8)
    p_cov_dept.paragraph_format.space_after = Pt(0)
    r = p_cov_dept.add_run("DEPARTMENT OF INFORMATION TECHNOLOGY\nKONGU ENGINEERING COLLEGE\n(AUTONOMOUS)\nPERUNDURAI, ERODE – 638 060\nOCTOBER 2025")
    r.font.size = Pt(12)
    r.font.bold = True

    doc.add_page_break()

    # =========================================================================
    # 2. BONAFIDE CERTIFICATE
    # =========================================================================
    p_bon_hdr = doc.add_paragraph()
    p_bon_hdr.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_bon_hdr.paragraph_format.space_before = Pt(12)
    p_bon_hdr.paragraph_format.space_after = Pt(2)
    r = p_bon_hdr.add_run("DEPARTMENT OF INFORMATION TECHNOLOGY\nKONGU ENGINEERING COLLEGE (AUTONOMOUS)\nPERUNDURAI, ERODE – 638 060\nOCTOBER 2025")
    r.font.size = Pt(12)
    r.font.bold = True

    p_bon_t = doc.add_paragraph()
    p_bon_t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_bon_t.paragraph_format.space_before = Pt(16)
    p_bon_t.paragraph_format.space_after = Pt(16)
    r = p_bon_t.add_run("BONAFIDE CERTIFICATE")
    r.font.size = Pt(14)
    r.font.bold = True

    p_bon_txt = doc.add_paragraph()
    p_bon_txt.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_bon_txt.paragraph_format.first_line_indent = Inches(0.5)
    p_bon_txt.paragraph_format.line_spacing = 1.4
    p_bon_txt.paragraph_format.space_after = Pt(20)
    r = p_bon_txt.add_run(
        "This is to certify that the project report titled SMARTPCB-XAI: AN EXPLAINABLE AI-BASED PCB "
        "INSPECTION AND DECISION SUPPORT SYSTEM is the bonafide record of project work done by "
        "ABISHA REBEKKAL T (23ITR001) and GOWRI D (23ITR048) in partial fulfilment of the requirements "
        "for the award of the Degree of Bachelor of Technology in INFORMATION TECHNOLOGY of Anna University, "
        "Chennai during the year 2025–2026."
    )
    r.font.size = Pt(12)

    # Signature Table
    sig_table = doc.add_table(rows=3, cols=2)
    sig_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    sig_table.autofit = False
    sig_table.columns[0].width = Inches(3.2)
    sig_table.columns[1].width = Inches(3.2)

    p00 = sig_table.cell(0, 0).paragraphs[0]
    p00.add_run("SUPERVISOR\nMs. P. VANITHA M.E.\nAssistant Professor\nDepartment of Information Technology")
    p01 = sig_table.cell(0, 1).paragraphs[0]
    p01.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p01.add_run("HEAD OF THE DEPARTMENT\nDr. S. VARADHAGANAPATHY M.E., Ph.D.\nProfessor and Head\nDepartment of Information Technology")

    p10 = sig_table.cell(1, 0).paragraphs[0]
    p10.paragraph_format.space_before = Pt(16)
    p10.add_run("Date:")

    p20 = sig_table.cell(2, 0).paragraphs[0]
    p20.paragraph_format.space_before = Pt(16)
    p20.add_run("Submitted for the end semester viva voce examination held on ___________________")

    p_ex = doc.add_paragraph()
    p_ex.paragraph_format.space_before = Pt(24)
    r_ex1 = p_ex.add_run("INTERNAL EXAMINER\t\t\t\tEXTERNAL EXAMINER")
    r_ex1.font.bold = True

    doc.add_page_break()

    # =========================================================================
    # 3. DECLARATION
    # =========================================================================
    p_dec_hdr = doc.add_paragraph()
    p_dec_hdr.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_dec_hdr.paragraph_format.space_before = Pt(12)
    p_dec_hdr.paragraph_format.space_after = Pt(2)
    r = p_dec_hdr.add_run("DEPARTMENT OF INFORMATION TECHNOLOGY\nKONGU ENGINEERING COLLEGE (AUTONOMOUS)\nPERUNDURAI, ERODE – 638 060\nOCTOBER 2025")
    r.font.size = Pt(12)
    r.font.bold = True

    p_dec_t = doc.add_paragraph()
    p_dec_t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_dec_t.paragraph_format.space_before = Pt(16)
    p_dec_t.paragraph_format.space_after = Pt(16)
    r = p_dec_t.add_run("DECLARATION")
    r.font.size = Pt(14)
    r.font.bold = True

    p_dec_txt = doc.add_paragraph()
    p_dec_txt.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_dec_txt.paragraph_format.first_line_indent = Inches(0.5)
    p_dec_txt.paragraph_format.line_spacing = 1.4
    p_dec_txt.paragraph_format.space_after = Pt(20)
    r = p_dec_txt.add_run(
        "We affirm that the Project Report titled SMARTPCB-XAI: AN EXPLAINABLE AI-BASED PCB "
        "INSPECTION AND DECISION SUPPORT SYSTEM being submitted in partial fulfillment of the requirements "
        "for the award of Bachelor of Technology is the original work carried out by us. It has not formed "
        "part of any other project report or dissertation based on which a degree or award was conferred on "
        "an earlier occasion on this or any other candidate."
    )
    r.font.size = Pt(12)

    p_sig_st = doc.add_paragraph()
    p_sig_st.paragraph_format.space_before = Pt(20)
    p_sig_st.add_run("Date:\n\n\nABISHA REBEKKAL T (23ITR001)\t\t\t\tGOWRI D (23ITR048)")

    p_cert = doc.add_paragraph()
    p_cert.paragraph_format.space_before = Pt(30)
    p_cert.add_run("I certify that the declaration made by the above candidates is true to the best of my knowledge.\n\n\nDate:\t\t\t\t\t\t\tName and Signature of Supervisor with Seal")

    doc.add_page_break()

    # =========================================================================
    # 4. ABSTRACT
    # =========================================================================
    p_abs_t = doc.add_paragraph()
    p_abs_t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_abs_t.paragraph_format.space_before = Pt(12)
    p_abs_t.paragraph_format.space_after = Pt(12)
    r = p_abs_t.add_run("ABSTRACT")
    r.font.size = Pt(14)
    r.font.bold = True

    add_body(
        "Printed Circuit Boards (PCBs) are essential components in modern electronic systems, and accurate "
        "inspection is necessary to identify manufacturing defects and component-related issues. Conventional PCB "
        "inspection methods largely depend on manual examination or automated detection systems that may provide "
        "limited explanation and decision support. Manual inspection is time-consuming, subjective, and susceptible to "
        "human error, while conventional deep learning systems often function as black-box models.", 0.5
    )
    add_body(
        "SmartPCB-XAI is proposed as an explainable artificial intelligence-based PCB inspection and decision support "
        "system that integrates computer vision, deep learning, explainable AI, severity analysis, and full-stack web "
        "technologies. The system processes PCB images through preprocessing and performs component and defect detection "
        "using YOLO-based object detection models. The defect detection model identifies PCB defects using bounding boxes "
        "and confidence scores.", 0.5
    )
    add_body(
        "To improve transparency, an activation-based heatmap approach is incorporated to visually indicate regions "
        "influencing the model prediction. The detected defect information is further processed by a decision layer to "
        "estimate defect severity and PCB quality using project-defined scoring rules. The system also provides possible "
        "causes and recommended corrective actions to assist users in interpreting inspection results.", 0.5
    )
    add_body(
        "The proposed system is implemented using Python, YOLO11, FastAPI, Express.js, React, and MongoDB. High-resolution "
        "tiled inference and Non-Maximum Suppression (NMS) are used to improve detection of small PCB defects and merge "
        "overlapping predictions. The verified defect detection model achieved 93.1% precision, 90.6% recall, 95.1% mAP@0.5, "
        "and 63.1% mAP@0.5:0.95 on the evaluated held-out test set. The complete system provides visual inspection results, "
        "explainable outputs, analytics, and PDF/Excel reporting.", 0.5
    )

    doc.add_page_break()

    # =========================================================================
    # 5. ACKNOWLEDGEMENT
    # =========================================================================
    p_ack_t = doc.add_paragraph()
    p_ack_t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_ack_t.paragraph_format.space_before = Pt(12)
    p_ack_t.paragraph_format.space_after = Pt(12)
    r = p_ack_t.add_run("ACKNOWLEDGEMENT")
    r.font.size = Pt(14)
    r.font.bold = True

    add_body("First and foremost, we acknowledge the abundant grace and presence of Almighty throughout different phases of the project and its successful completion.", 0.5)
    add_body("We wish to express our extreme gratefulness to our beloved Correspondent Thiru. E.R.K. KRISHNAN M.Com., and all the trust members of Kongu Vellalar Institute of Technology Trust for providing all the necessary facilities to complete the project successfully.", 0.5)
    add_body("We express our deep sense of gratitude to our beloved Principal Dr. R. PARAMESHWARAN M.E., Ph.D., for providing us an opportunity to complete the project.", 0.5)
    add_body("We express our gratitude to Dr. S. Varadhaganapathy M.E., Ph.D., Head of the Department, Department of Information Technology, for his valuable suggestions.", 0.5)
    add_body("We are thankful to our project coordinators Ms. K. SRUTHI M.E., and Ms. R. SANDHIYA M.E., for their valuable guidance and support to complete our project successfully.", 0.5)
    add_body("We are highly indebted to Ms. P. VANITHA M.E., Department of Information Technology, for her valuable supervision and advice for the fruitful completion of the project.", 0.5)
    add_body("We would like to express our sincere gratitude to the Centre of Excellence in Data Science and the Department of Information Technology for providing access to GPU computing resources, which were instrumental in the successful completion of this project. Their support in facilitating high-performance computing infrastructure significantly contributed to the efficiency and performance of our model development and experimentation.", 0.5)
    add_body("Finally, we extend our love and thanks to our parents and friends for their patience in teaching, love, encouragement and support.", 0.5)

    doc.add_page_break()

    # =========================================================================
    # 6. TABLE OF CONTENTS
    # =========================================================================
    p_toc_t = doc.add_paragraph()
    p_toc_t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_toc_t.paragraph_format.space_before = Pt(12)
    p_toc_t.paragraph_format.space_after = Pt(12)
    r = p_toc_t.add_run("TABLE OF CONTENTS")
    r.font.size = Pt(14)
    r.font.bold = True

    toc_table = doc.add_table(rows=17, cols=3)
    toc_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    toc_table.autofit = False
    toc_table.columns[0].width = Inches(1.2)
    toc_table.columns[1].width = Inches(4.3)
    toc_table.columns[2].width = Inches(0.9)

    toc_items = [
        ("", "ABSTRACT", "iv"),
        ("", "LIST OF ABBREVIATIONS", "viii"),
        ("", "LIST OF FIGURES", "ix"),
        ("1", "INTRODUCTION", "1"),
        ("", "1.1 INTRODUCTION", "1"),
        ("", "1.2 OBJECTIVE", "2"),
        ("", "1.3 SCOPE", "2"),
        ("2", "LITERATURE REVIEW", "3"),
        ("3", "PROBLEM DEFINITION", "7"),
        ("", "3.1 EXISTING SYSTEM", "7"),
        ("", "3.2 PROBLEM STATEMENT", "7"),
        ("4", "SYSTEM REQUIREMENTS", "8"),
        ("", "4.1 HARDWARE REQUIREMENTS", "8"),
        ("", "4.2 SOFTWARE REQUIREMENTS", "8"),
        ("", "4.3 SOFTWARE DESCRIPTION", "8"),
        ("5", "SYSTEM IMPLEMENTATION", "10"),
        ("", "5.1 PROPOSED SYSTEM", "10")
    ]

    for idx, (c1, c2, c3) in enumerate(toc_items):
        r_cells = toc_table.rows[idx].cells
        r_cells[0].paragraphs[0].text = c1
        r_cells[1].paragraphs[0].text = c2
        r_cells[2].paragraphs[0].text = c3
        r_cells[2].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
        if c1 != "":
            r_cells[0].paragraphs[0].runs[0].font.bold = True
            r_cells[1].paragraphs[0].runs[0].font.bold = True

    # Continue TOC rows
    toc_items_part2 = [
        ("", "5.2 SYSTEM ARCHITECTURE", "12"),
        ("6", "RESULTS AND DISCUSSION", "14"),
        ("7", "CONCLUSION AND FUTURE WORK", "19"),
        ("8", "APPENDICES", "20"),
        ("", "8.1 APPENDIX – 1 CODING", "20"),
        ("", "8.2 APPENDIX – 2 OUTPUT", "38"),
        ("", "REFERENCES", "40"),
        ("", "MAPPING TO SDG GOALS", "42")
    ]
    for c1, c2, c3 in toc_items_part2:
        row = toc_table.add_row()
        row.cells[0].paragraphs[0].text = c1
        row.cells[1].paragraphs[0].text = c2
        row.cells[2].paragraphs[0].text = c3
        row.cells[2].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
        if c1 != "":
            row.cells[0].paragraphs[0].runs[0].font.bold = True
            row.cells[1].paragraphs[0].runs[0].font.bold = True

    doc.add_page_break()

    # =========================================================================
    # 7. LIST OF ABBREVIATIONS & LIST OF FIGURES
    # =========================================================================
    p_abb_t = doc.add_paragraph()
    p_abb_t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_abb_t.paragraph_format.space_before = Pt(12)
    p_abb_t.paragraph_format.space_after = Pt(12)
    r = p_abb_t.add_run("LIST OF ABBREVIATIONS")
    r.font.size = Pt(14)
    r.font.bold = True

    abb_table = doc.add_table(rows=11, cols=2)
    abb_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    abb_table.columns[0].width = Inches(1.8)
    abb_table.columns[1].width = Inches(4.6)

    abbreviations = [
        ("AOI", "Automated Optical Inspection"),
        ("CAM", "Class Activation Mapping"),
        ("CLAHE", "Contrast Limited Adaptive Histogram Equalization"),
        ("CNN", "Convolutional Neural Network"),
        ("Grad-CAM++", "Generalized Gradient-Weighted Class Activation Mapping"),
        ("IPC", "Association Connecting Electronics Industries"),
        ("mAP", "mean Average Precision"),
        ("NMS", "Non-Maximum Suppression"),
        ("PCB", "Printed Circuit Board"),
        ("SMT", "Surface-Mount Technology"),
        ("XAI", "Explainable Artificial Intelligence")
    ]

    for idx, (abb, full) in enumerate(abbreviations):
        abb_table.rows[idx].cells[0].paragraphs[0].text = abb
        abb_table.rows[idx].cells[0].paragraphs[0].runs[0].font.bold = True
        abb_table.rows[idx].cells[1].paragraphs[0].text = full

    p_fig_t = doc.add_paragraph()
    p_fig_t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_fig_t.paragraph_format.space_before = Pt(16)
    p_fig_t.paragraph_format.space_after = Pt(10)
    r = p_fig_t.add_run("LIST OF FIGURES")
    r.font.size = Pt(14)
    r.font.bold = True

    fig_list = [
        ("Figure 5.1.1", "Proposed Methodology and Inspection Dataflow Pipeline"),
        ("Figure 5.2.1", "Layered System Architecture of SmartPCB-XAI"),
        ("Figure 6.1.1", "Precision-Recall Curve for Defect Detection"),
        ("Figure 6.1.2", "Normalized Confusion Matrix on Held-Out Test Set"),
        ("Figure 6.2.1", "Per-Class Defect mAP@50 Comparison"),
        ("Figure 6.8.2.1", "Test Board Defect Detection Visualization (00041200.jpg)"),
        ("Figure 6.8.2.2", "Test Board Defect Detection Visualization (00041204.jpg)")
    ]

    fig_table = doc.add_table(rows=len(fig_list), cols=2)
    fig_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    fig_table.columns[0].width = Inches(1.8)
    fig_table.columns[1].width = Inches(4.6)
    for idx, (f_num, f_title) in enumerate(fig_list):
        fig_table.rows[idx].cells[0].paragraphs[0].text = f_num
        fig_table.rows[idx].cells[0].paragraphs[0].runs[0].font.bold = True
        fig_table.rows[idx].cells[1].paragraphs[0].text = f_title

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 1: INTRODUCTION
    # =========================================================================
    add_chapter_title("CHAPTER 1", "INTRODUCTION")
    add_sec_title("1.1 INTRODUCTION")
    add_body(
        "Printed Circuit Boards (PCBs) are the core building blocks of contemporary electronics, supporting and electrically "
        "interconnecting critical passive and active components across automotive, aerospace, healthcare, and consumer computing "
        "domains. With continuous advancements in surface-mount technology (SMT), component packaging has shrunk to microscopic "
        "scales, leading to ultra-dense trace layouts. Consequently, minor manufacturing anomalies such as circuit shorts, etched "
        "breaks, mousebites, spur defects, spurious copper, or unetched pin-holes can result in disastrous functional device failures. "
        "In mission-critical sectors such as automotive avionics and medical instrumentation, undetected faults represent severe "
        "safety and reliability risks."
    )
    add_body(
        "Traditionally, electronics manufacturing relies on manual human visual inspection or commercial Automated Optical Inspection (AOI) "
        "machinery. Human inspection is inherently subjective, fatiguing, and slow, typically examining fewer than two boards per minute "
        "with declining accuracy over shifts. While conventional AOI machines use template subtraction algorithms, they are extremely "
        "cost-prohibitive ($50,000 to $300,000 per station) and susceptible to false-positive alarms triggered by minor illumination "
        "variations, board flexure, or solder-mask shade differences. Furthermore, traditional computer vision pipelines provide binary "
        "accept/reject flags without explaining the visual evidence behind their classifications."
    )
    add_body(
        "Recent computer vision research has turned toward deep-learning object detectors such as YOLO to automate PCB defect localization. "
        "However, existing deep-learning deployments function as opaque 'black-box' systems. When an AI model flags an anomaly, quality "
        "engineers receive no visual attribution confirming why the region was selected, nor do they receive standardized severity scores "
        "or rework guidance. To overcome these critical bottlenecks, SmartPCB-XAI introduces a four-tier inspection platform combining "
        "dual YOLOv11s object detectors, feature activation energy explainability, deterministic IPC-A-610-informed severity scoring, and an "
        "interactive 2D Digital Twin schematic."
    )

    add_sec_title("1.2 OBJECTIVE")
    add_body(
        "The primary objective of this project is to develop and deploy an explainable, dual-detector automated PCB inspection and decision "
        "support system. The specific technical goals encompass:\n"
        "1. Developing independent, high-speed YOLOv11s vision heads to decouple component identification from microscopic defect detection.\n"
        "2. Eliminating data leakage and provenance ambiguities by curating leak-free local training and testing datasets.\n"
        "3. Integrating visual explainability via multi-channel activation energy mapping to highlight discriminative receptive fields.\n"
        "4. Formulating a deterministic, IPC-A-610-compliant mathematical severity formula and four-tier quality scoring model.\n"
        "5. Constructing an interactive 2D Digital Twin schematic and full-stack web application delivering real-time inspection telemetry."
    )

    add_sec_title("1.3 SCOPE")
    add_body(
        "The scope of SmartPCB-XAI spans automated optical inspection of both bare PCBs and populated SMT electronic assemblies. The system "
        "evaluates bare board surface defects using the DeepPCB benchmark across six canonical classes: open circuit, short circuit, "
        "mouse-bite, spur, spurious copper, and missing hole. For component verification, the system inspects high-resolution scans across "
        "standard packages (ICs, capacitors, diodes, inductors, resistors, transistors). The operational boundary encompasses sliding-window "
        "high-resolution grid tiling, failure-safe outcome gating, prescriptive repair knowledge base retrieval, and automated PDF/Excel "
        "compliance reporting."
    )

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 2: LITERATURE REVIEW
    # =========================================================================
    add_chapter_title("CHAPTER 2", "LITERATURE REVIEW")
    add_body(
        "Automated optical inspection for printed circuit board defects has evolved through classical morphology, template subtraction, "
        "and deep learning architectures. This section reviews fifteen foundational and recent research studies informing this work."
    )

    lit_reviews = [
        ("Ling and Isa (2023) [1]", "surveyed machine learning and image processing methods for PCB defect detection, identifying template subtraction vulnerabilities to lighting noise and reviewing early CNN classifiers."),
        ("Redmon et al. (2016) [2]", "introduced the YOLO architecture, demonstrating real-time single-stage bounding-box regression that forms the algorithmic foundation of our dual inspection heads."),
        ("Ye et al. (2026) [3]", "proposed a lightweight PCB defect detection algorithm based on YOLOv11s incorporating EfficientViT backbones, FasterNet C3k2_Faster_EMA necks, and Wise-IoU loss, achieving 92.3% mAP@50 on DeepPCB."),
        ("Tang et al. (2019) [4]", "released the DeepPCB dataset comprising 1,500 paired template and defect images, formalizing the standard 6-class defect taxonomy adopted in this project."),
        ("Selvaraju et al. (2017) [5]", "formulated Grad-CAM, weighting convolutional feature maps by class gradients to produce 2D localization heatmaps for visual interpretability."),
        ("Chattopadhay et al. (2018) [6]", "introduced Grad-CAM++, utilizing higher-order partial derivatives to improve visual attribution when multiple defect instances co-exist on a single PCB."),
        ("Tao et al. (2019) [7]", "reviewed digital twin applications in manufacturing, providing the architectural foundation for our 2D interactive component and defect schematic."),
        ("Bhattacharya and Cloutier (2022) [8]", "analyzed explainable AI in safety-critical manufacturing, emphasizing the necessity of verifiable attribution for human-in-the-loop signoff."),
        ("Shakya et al. (2020) [9]", "curated the FICS-PCB benchmark, documenting microscopic scale challenges where 94% of components measure under 32x32 pixels."),
        ("IPC Association (2020) [10]", "codified IPC-A-610G acceptability standards, defining the workmanship criteria governing our deterministic severity formulas and repair procedures."),
        ("Jocher and Qiu (2024) [11]", "released Ultralytics YOLOv11, providing C3k2 convolutional blocks and spatial pyramid pooling utilized in our primary detectors."),
        ("Chen et al. (2021) [12]", "reviewed deep learning for industrial surface defects, noting that multi-task heads frequently experience negative transfer when mixing component and defect tasks."),
        ("Chen et al. (2023) [13]", "formulated FasterNet partial convolution (PConv), demonstrating memory-bandwidth efficiency for edge-deployed electronic quality inspection."),
        ("Ouyang et al. (2023) [14]", "introduced Efficient Multi-Scale Attention (EMA), improving cross-spatial feature representation for tiny solder bridge localization."),
        ("Tong et al. (2023) [15]", "introduced Wise-IoU dynamic loss, which balances gradient contributions to mitigate regression instability on tiny bounding boxes.")
    ]

    for author, desc in lit_reviews:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.first_line_indent = Inches(0.3)
        p.paragraph_format.space_after = Pt(3)
        r1 = p.add_run(author + " ")
        r1.bold = True
        p.add_run(desc)

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 3: PROBLEM DEFINITION
    # =========================================================================
    add_chapter_title("CHAPTER 3", "PROBLEM DEFINITION")
    add_sec_title("3.1 EXISTING SYSTEM")
    add_body(
        "Existing PCB inspection systems fall into three primary categories:\n"
        "1. Manual Visual Inspection: Human operators manually scan boards under magnification. This method is slow, inconsistent, and highly "
        "susceptible to visual fatigue, with error rates increasing noticeably during prolonged shifts.\n"
        "2. Optical Template Subtractors: Classical AOI systems compare test images against golden templates via pixel-wise XOR operations. "
        "These systems suffer from extreme false-positive rates due to minute variations in trace etching, board thickness, or camera angle.\n"
        "3. Single-Task Deep Learning Models: Commercial deep learning systems typically train a single neural network to predict both "
        "component designators and surface defects. This creates severe gradient conflict because components require macro-scale feature "
        "extraction while defects demand sub-pixel edge sensitivity. Furthermore, existing AI tools operate as black-box systems, offering "
        "no visual explanation, no standardized severity scoring, and no prescriptive rework recommendations."
    )

    add_sec_title("3.2 PROBLEM STATEMENT")
    add_body(
        "Current PCB manufacturing environments lack an integrated inspection framework that combines high-precision visual localization, "
        "verifiable explainability, and standardized quality auditing. Specifically:\n"
        "• Deep learning models fail to explain their visual predictions, preventing quality engineers from validating flagged anomalies.\n"
        "• Existing systems lack failure-safe outcome gating, often defaulting to false PASS outputs when inference timeouts occur.\n"
        "• Published models frequently suffer from training data leakage, resulting in benchmark accuracy figures that collapse in production.\n"
        "• Quality outputs lack mathematical alignment with electronics industry standards such as IPC-A-610.\n"
        "• Shop-floor operators lack centralized dashboards combining real-time digital twins, first-pass yield analytics, and feedback loops.\n"
        "SmartPCB-XAI resolves these limitations by introducing a decoupled, dual-detector architecture with deterministic quality evaluation."
    )

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 4: SYSTEM REQUIREMENTS
    # =========================================================================
    add_chapter_title("CHAPTER 4", "SYSTEM REQUIREMENTS")
    add_sec_title("4.1 HARDWARE REQUIREMENTS")
    add_body(
        "The minimal and recommended hardware specifications for running SmartPCB-XAI are as follows:\n"
        "• Processor: Intel Core i5 / Core i7 (2.4 GHz or higher, 12+ execution threads).\n"
        "• System Memory (RAM): 8 GB minimum (16 GB recommended for high-resolution grid tiling).\n"
        "• Storage: 50 GB available SSD storage (for DeepPCB benchmark datasets, weights, and MongoDB records).\n"
        "• Graphics Processing Unit (GPU): Dedicated NVIDIA GPU with 4GB+ VRAM (or Intel Iris Xe / CPU execution supported via PyTorch CPU)."
    )

    add_sec_title("4.2 SOFTWARE REQUIREMENTS")
    add_body(
        "• Operating System: Windows 11 / Windows 10 (64-bit) or Ubuntu Linux 22.04 LTS.\n"
        "• Programming Environments: Python 3.11+ and Node.js v20.19+ (with npm 10.8+).\n"
        "• Deep Learning Frameworks: PyTorch 2.13.0, Torchvision 0.18+, Ultralytics YOLO 8.4.98.\n"
        "• Backend & Storage: FastAPI, Express.js 4.19, MongoDB 7.0+.\n"
        "• Frontend Framework: React 18, TypeScript 5.5, Vite 6.4, TailwindCSS 3.4.\n"
        "• Document Generation: ReportLab 5.0 (PDF) and OpenPyXL 3.1 (Excel)."
    )

    add_sec_title("4.3 SOFTWARE DESCRIPTION")
    add_subsec_title("4.3.1 Python and PyTorch")
    add_body("Python serves as the primary programming language for AI microservice development, supported by PyTorch for dynamic tensor computation, forward activation hook registration, and model checkpoint management.")

    add_subsec_title("4.3.2 Ultralytics YOLOv11")
    add_body("Ultralytics YOLOv11 provides the core real-time object detection engine, featuring enhanced C3k2 convolutional feature extractors and anchor-free spatial prediction heads optimized for tiny bounding-box regression.")

    add_subsec_title("4.3.3 OpenCV and Image Preprocessing")
    add_body("OpenCV (cv2) handles image decoding, CLAHE trace contrast enhancement, spatial grid slicing, colormap jet rendering for XAI heatmaps, and annotated inspection canvas generation.")

    add_subsec_title("4.3.4 FastAPI and Express.js Web Gateway")
    add_body("FastAPI delivers an asynchronous REST microservice on port 8000 handling multi-part image ingestion and model execution. Express.js acts as the application gateway on port 5000, managing user authentication, feedback queues, and MongoDB persistence.")

    add_subsec_title("4.3.5 React 18, TypeScript, and Vite")
    add_body("The user dashboard is implemented in React 18 with TypeScript, offering five production views: Live Inspection, 2D Digital Twin, Analytics & Yield, Continuous Learning Feedback, and Model Benchmarks.")

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 5: SYSTEM IMPLEMENTATION
    # =========================================================================
    add_chapter_title("CHAPTER 5", "SYSTEM IMPLEMENTATION")
    add_sec_title("5.1 PROPOSED SYSTEM")
    add_body(
        "SmartPCB-XAI implements a decoupled dual-head deep learning inspection pipeline. Rather than forcing a single neural network "
        "to identify both large component packages and sub-millimeter copper defects, the system routes input imagery to specialized "
        "detection heads. Figure 5.1.1 illustrates the proposed methodology and inspection workflow."
    )

    wf_img = os.path.join("scratch", "pdf_images", "page_2_img_1_Image28.png")
    if os.path.exists(wf_img):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(2)
        doc.add_picture(wf_img, width=Inches(5.8))
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_after = Pt(6)
        r = p_cap.add_run("Figure 5.1.1. Proposed Methodology and Inspection Dataflow Pipeline")
        r.font.size = Pt(10)
        r.font.bold = True

    add_body(
        "Key operational stages of the proposed system include:\n"
        "1. Image Ingestion and Normalization: Images are uploaded via multi-part HTTP streams, validated for resolution and format, "
        "and normalized. Contrast Limited Adaptive Histogram Equalization (CLAHE) is applied to enhance microscopic trace borders.\n"
        "2. High-Resolution Grid Tiling: For large board scans, images are partitioned into 960x960 tiles with 33% overlap. Tile detections "
        "are mapped back into global canvas space via Non-Maximum Suppression (NMS).\n"
        "3. Decoupled Vision Heads: The defect head localizes six surface flaws (open, short, mousebite, spur, copper, pin-hole) while the "
        "component head identifies SMT devices.\n"
        "4. Visual Explainability: Activation energy maps are computed from the bottleneck layer, rendered via Jet colormaps at 40% opacity.\n"
        "5. Deterministic Severity Scoring: Defect severity (0-100) and board quality scores are calculated using project-defined formulas "
        "informed by IPC-A-610 workmanship guidance.\n"
        "6. Prescriptive Repair Guidance: Detected faults query an expert rule-based knowledge base to output root causes and rework procedures."
    )

    add_sec_title("5.2 SYSTEM ARCHITECTURE")
    add_body(
        "The architecture is organized into four interconnected tiers: Presentation Layer (React), Application Gateway (Express), "
        "AI Microservice (FastAPI), and Data Persistence (MongoDB). Figure 5.2.1 depicts the structural hierarchy."
    )

    arch_img = os.path.join("scratch", "pdf_images", "page_2_img_0_Image27.png")
    if os.path.exists(arch_img):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(2)
        doc.add_picture(arch_img, width=Inches(5.8))
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_after = Pt(6)
        r = p_cap.add_run("Figure 5.2.1. Layered System Architecture of SmartPCB-XAI")
        r.font.size = Pt(10)
        r.font.bold = True

    add_body(
        "Failure-Safe Outcome Gating: To prevent false PASS results caused by inference crashes, the system enforces a strict three-state "
        "evaluation logic: (i) Verified Clean: high component confidence and zero defect boxes confirm genuine board quality; (ii) Suspicious "
        "Zero Detection: signal anomalies trigger review_required=true; (iii) Explicit Error: exceptions return structured HTTP 500 responses."
    )

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 6: RESULTS AND DISCUSSION
    # =========================================================================
    add_chapter_title("CHAPTER 6", "RESULTS AND DISCUSSION")
    add_sec_title("6.1 DEFECT DETECTION PERFORMANCE")
    add_body(
        "The primary defect detection model (models/defect_best.pt, 19.18 MB) was trained from scratch with fixed random seed 42 exclusively "
        "on the local, leakage-free DeepPCB dataset (850 train, 150 val, 500 test images). Evaluation was executed using the official Ultralytics "
        "model.val() API on the 500 held-out test images comprising 3,140 ground-truth boxes. The model achieved 95.11% mAP@50 and 63.27% mAP@50-95, "
        "with 92.91% precision and 90.60% recall, exceeding the 95% accuracy target. Table 6.1 summarizes the benchmark findings."
    )

    # TABLE 6.1
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Table 6.1. Defect Detector Held-Out Test Set Performance (500 Images, 3,140 GT Boxes)")
    r.bold = True
    r.font.size = Pt(10)

    t_res1 = doc.add_table(rows=5, cols=5)
    t_res1.alignment = WD_TABLE_ALIGNMENT.CENTER
    h_res1 = ["Model Checkpoint", "Evaluation Protocol", "mAP@50", "mAP@50-95", "Micro-F1"]
    d_res1 = [
        ["Legacy Checkpoint (0.25)", "Default, fixed-threshold evaluator", "91.47%", "72.33%", "94.68%"],
        ["Legacy Checkpoint (0.70)", "Val-calibrated, fixed-threshold", "92.74%", "73.83%", "95.96%"],
        ["Legacy Checkpoint (Standard)", "Full PR-curve (unverified provenance)", "98.30%", "—", "—"],
        ["From-Scratch YOLOv11s (PRIMARY)", "Full PR-curve, seed 42, local data only", "95.11%", "63.27%", "91.84%"]
    ]
    w_res1 = [Inches(2.1), Inches(2.1), Inches(0.85), Inches(0.95), Inches(0.80)]
    for c_idx, text in enumerate(h_res1):
        cell = t_res1.cell(0, c_idx)
        cell.width = w_res1[c_idx]
        set_cell_background(cell, "1E293B")
        set_cell_margins(cell, 60, 60, 80, 80)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(text)
        r.font.size = Pt(9)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    for r_idx, row in enumerate(d_res1):
        bg = "EFF6FF" if r_idx == 3 else ("F8FAFC" if r_idx % 2 == 1 else "FFFFFF")
        for c_idx, val in enumerate(row):
            cell = t_res1.cell(r_idx + 1, c_idx)
            cell.width = w_res1[c_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, 50, 50, 80, 80)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if c_idx < 2 else WD_ALIGN_PARAGRAPH.RIGHT
            r = p.add_run(val)
            r.font.size = Pt(9)
            if r_idx == 3:
                r.font.bold = True

    add_sec_title("6.2 PER-CLASS DEFECT RESULTS")
    add_body(
        "Table 6.2 provides the class-level breakdown across all six defect categories. Pin-hole (98.3%), spurious copper (97.9%), "
        "mousebite (96.2%), and spur (95.8%) demonstrated outstanding accuracy, while open circuits achieved 94.1% and short circuits achieved 88.4%."
    )

    # TABLE 6.2
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Table 6.2. Per-Class Defect Detection Accuracy (Held-Out Test Set)")
    r.bold = True
    r.font.size = Pt(10)

    t_res2 = doc.add_table(rows=7, cols=6)
    t_res2.alignment = WD_TABLE_ALIGNMENT.CENTER
    h_res2 = ["Defect Category", "Canonical Label", "mAP@50", "Precision", "Recall", "GT Boxes"]
    d_res2 = [
        ["Pin-hole", "pin-hole", "98.3%", "95.2%", "94.8%", "470"],
        ["Spurious Copper", "copper", "97.9%", "96.4%", "93.1%", "464"],
        ["Mouse-bite", "mousebite", "96.2%", "94.8%", "91.5%", "586"],
        ["Spur", "spur", "95.8%", "93.7%", "92.4%", "483"],
        ["Open Circuit", "open", "94.1%", "91.6%", "89.3%", "659"],
        ["Short Circuit", "short", "88.4%", "85.8%", "82.5%", "478"]
    ]
    w_res2 = [Inches(1.8), Inches(1.3), Inches(0.9), Inches(1.0), Inches(1.0), Inches(1.0)]
    for c_idx, text in enumerate(h_res2):
        cell = t_res2.cell(0, c_idx)
        cell.width = w_res2[c_idx]
        set_cell_background(cell, "1E293B")
        set_cell_margins(cell, 60, 60, 80, 80)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(text)
        r.font.size = Pt(9)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    for r_idx, row in enumerate(d_res2):
        bg = "F8FAFC" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(row):
            cell = t_res2.cell(r_idx + 1, c_idx)
            cell.width = w_res2[c_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, 50, 50, 80, 80)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if c_idx < 2 else WD_ALIGN_PARAGRAPH.RIGHT
            p.add_run(val).font.size = Pt(9)

    # Precision-Recall & Confusion Matrix figures
    pr_img = os.path.join("runs", "detect", "reports", "eval", "defect_val_standard", "BoxPR_curve.png")
    cm_img = os.path.join("runs", "detect", "reports", "eval", "defect_val_standard", "confusion_matrix_normalized.png")
    if os.path.exists(pr_img) and os.path.exists(cm_img):
        p_f = doc.add_paragraph()
        p_f.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_f.paragraph_format.space_before = Pt(6)
        doc.add_picture(pr_img, width=Inches(3.1))
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p_cap.add_run("Figure 6.1.1. Precision-Recall Curve for Defect Detection")
        r.font.size = Pt(9.5)
        r.font.bold = True

        p_f2 = doc.add_paragraph()
        p_f2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_f2.paragraph_format.space_before = Pt(6)
        doc.add_picture(cm_img, width=Inches(3.1))
        p_cap2 = doc.add_paragraph()
        p_cap2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p_cap2.add_run("Figure 6.1.2. Normalized Confusion Matrix on Held-Out Test Set")
        r.font.size = Pt(9.5)
        r.font.bold = True

    add_sec_title("6.3 COMPONENT DETECTION PERFORMANCE & DISPARITY DIAGNOSIS")
    add_body(
        "In contrast to the defect model, the deployed component detector (models/component_best.pt, 5.78 MB) achieved an empirical mAP@50 "
        "of 9.33% at default 0.25 confidence. A thorough audit identified four root causes: (1) 10-vs-6 taxonomy mismatch (five classes "
        "such as battery, buzzer, led have zero ground truth in the test set); (2) 94.2% of target component boxes measure under 32x32 pixels; "
        "(3) systematic recall deficit (< 39.1% across all classes); and (4) severe physical board imbalance where 64% of test images originated "
        "from a single circuit board. To prevent silent false classifications, the system tags unmapped detections with class_mapped=false."
    )

    add_sec_title("6.4 20-IMAGE END-TO-END OPERATIONAL VALIDATION")
    add_body(
        "A full hardware-in-the-loop operational trial was executed on 20 unseen test images from the held-out DeepPCB test set. Every image "
        "was processed through dual YOLO inference, activation XAI rendering, deterministic severity scoring, and repair knowledge base lookup. "
        "Results: 20/20 SUCCESS, 123 defects localized (mean 6.15 defects/board), zero false zeros, and mean CPU latency of 2,388.3 ms."
    )

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 7: CONCLUSION AND FUTURE WORK
    # =========================================================================
    add_chapter_title("CHAPTER 7", "CONCLUSION AND FUTURE WORK")
    add_sec_title("7.1 CONCLUSION")
    add_body(
        "This project successfully developed and verified SmartPCB-XAI, an industrial-grade explainable artificial intelligence system for "
        "automated PCB defect detection and component placement verification. By decoupling defect localization and component identification "
        "into independent YOLOv11s vision heads, the platform resolved conflicting spatial scale objectives. The primary defect detector "
        "achieved 95.11% mAP@50 (63.27% mAP@50-95, 92.91% precision, 90.60% recall) on 500 held-out DeepPCB images without data leakage or "
        "unverified external training data. The component detector's empirical limitations were transparently documented and safely mitigated "
        "via an explicit class-mapping metadata flag. Integrated with activation energy XAI heatmaps, IPC-A-610-informed deterministic severity "
        "math, an interactive 2D Digital Twin schematic, and automated PDF/Excel compliance reporting, SmartPCB-XAI provides a robust, "
        "transparent foundation for next-generation Industry 4.0 electronics quality control."
    )

    add_sec_title("7.2 FUTURE WORK")
    add_body(
        "Future enhancements will focus on bridging the component detection performance gap and expanding deployment flexibility:\n"
        "1. Component Detector High-Resolution Retraining: Retraining the component head with balanced board-level splits and 960x960 tiled inputs.\n"
        "2. PKU-Market-PCB Integration: Incorporating multi-board datasets to expand training diversity across complex industrial SMT finishes.\n"
        "3. Advanced Neck and Loss Design: Integrating FasterNet partial convolutions (C3k2_Faster_EMA) and Wise-IoU v3 loss to boost tiny lead localization.\n"
        "4. Authentic Grad-CAM++ Hooks: Implementing automated PyTorch backward passes for true gradient-weighted spatial attribution.\n"
        "5. Edge TensorRT Quantization: Exporting FP16/INT8 ONNX engines for high-throughput deployment on NVIDIA Jetson embedded industrial nodes."
    )

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 8: APPENDICES
    # =========================================================================
    add_chapter_title("CHAPTER 8", "APPENDICES")
    add_sec_title("8.1 APPENDIX – 1 CODING")
    add_body("The core implementation modules of SmartPCB-XAI are presented below:")

    code_snippets = [
        ("AI Inference Engine (ai/inference/engine.py):",
"""# SmartPCB Inspection Engine - Dual YOLOv11 Inference Pipeline
import os, cv2, torch, numpy as np
from ultralytics import YOLO

class SmartPCBInspectionEngine:
    def __init__(self, defect_weights, component_weights, device='cpu'):
        self.device = device
        self.defect_model = YOLO(defect_weights)
        self.component_model = YOLO(component_weights)
        self.defect_model.to(device)
        self.component_model.to(device)
        print(f"[Engine] Ready on device={device}")

    def inspect_image(self, image_path, conf_thresh=0.25):
        img_bgr = cv2.imread(image_path)
        h, w = img_bgr.shape[:2]
        # Defect Detection Head
        def_results = self.defect_model.predict(img_bgr, conf=conf_thresh, verbose=False)[0]
        defects = []
        for box in def_results.boxes:
            cls_id = int(box.cls[0].item())
            conf = float(box.conf[0].item())
            coords = box.xyxy[0].tolist()
            defects.append({"class_id": cls_id, "confidence": conf, "bbox": coords})
        # Component Identification Head
        comp_results = self.component_model.predict(img_bgr, conf=0.18, verbose=False)[0]
        components = []
        for box in comp_results.boxes:
            cls_id = int(box.cls[0].item())
            conf = float(box.conf[0].item())
            components.append({"class_id": cls_id, "confidence": conf, "bbox": box.xyxy[0].tolist()})
        return {"image_size": [w, h], "defects": defects, "components": components}"""),

        ("Deterministic Defect Severity & Quality Engine (ai/severity/severity_engine.py):",
"""# Deterministic Severity Scoring informed by IPC-A-610 Workmanship Guidance
BASE_WEIGHTS = {'short': 90, 'open': 85, 'pin-hole': 60, 'mousebite': 55, 'spur': 45, 'copper': 35}

def compute_defect_severity(defect_type, norm_area, confidence):
    base = BASE_WEIGHTS.get(defect_type, 40)
    # Area scale factor and confidence modulation
    area_factor = 15.0 * (norm_area ** 0.10)
    conf_factor = 30.0 * confidence
    severity = min(100.0, base + area_factor + conf_factor)
    return round(severity, 2)

def compute_board_quality_score(defects):
    score = 100.0
    for d in defects:
        penalty = (d['severity'] / 5.0) * d['confidence']
        score -= penalty
        if d['severity'] >= 85.0: # Auto-reject on CRITICAL defect
            return max(0.0, round(score, 1)), "REJECT/FAIL"
    score = max(0.0, round(score, 1))
    if score >= 90.0: grade = "EXCELLENT/PASS"
    elif score >= 75.0: grade = "ACCEPTABLE/PASS-ADVISORY"
    elif score >= 50.0: grade = "MARGINAL/REWORK-REQUIRED"
    else: grade = "REJECT/FAIL"
    return score, grade""")
    ]

    for title, code in code_snippets:
        p_c = doc.add_paragraph()
        p_c.paragraph_format.space_before = Pt(6)
        p_c.paragraph_format.space_after = Pt(2)
        r = p_c.add_run(title)
        r.bold = True
        r.font.size = Pt(11)

        p_box = doc.add_paragraph()
        p_box.paragraph_format.space_after = Pt(6)
        p_box.paragraph_format.line_spacing = 1.05
        r_box = p_box.add_run(code)
        r_box.font.name = 'Courier New'
        r_box.font.size = Pt(9.0)

    doc.add_page_break()

    # APPENDIX 2 OUTPUT
    add_sec_title("8.2 APPENDIX – 2 OUTPUT")
    add_body("Figure 6.8.2.1 and Figure 6.8.2.2 depict actual visual inspection outputs generated by the deployed SmartPCB-XAI inference engine on unseen test boards.")

    out1 = os.path.join("results", "annotated", "00041200_annotated.jpg")
    out2 = os.path.join("results", "annotated", "00041204_annotated.jpg")
    if os.path.exists(out1):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(4)
        doc.add_picture(out1, width=Inches(4.5))
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p_cap.add_run("Figure 6.8.2.1. Test Board Defect Detection Visualization (00041200.jpg, 8 defects)")
        r.font.size = Pt(9.5)
        r.font.bold = True

    if os.path.exists(out2):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(4)
        doc.add_picture(out2, width=Inches(4.5))
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p_cap.add_run("Figure 6.8.2.2. Test Board Defect Detection Visualization (00041204.jpg, 9 defects, Quality: 25.1 REJECT)")
        r.font.size = Pt(9.5)
        r.font.bold = True

    doc.add_page_break()

    # =========================================================================
    # REFERENCES & SDG GOALS
    # =========================================================================
    p_ref_t = doc.add_paragraph()
    p_ref_t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_ref_t.paragraph_format.space_before = Pt(12)
    p_ref_t.paragraph_format.space_after = Pt(12)
    r = p_ref_t.add_run("REFERENCES")
    r.font.size = Pt(14)
    r.font.bold = True

    references_list = [
        "[1] Q. Ling and N. A. M. Isa, \"Printed circuit board defect detection methods based on image processing, machine learning and deep learning: A survey,\" IEEE Access, vol. 11, pp. 15921–15944, Dec. 2023.",
        "[2] J. Redmon, S. Divvala, R. Girshick, and A. Farhadi, \"You only look once: Unified, real-time object detection,\" in Proc. IEEE Conf. Comput. Vis. Pattern Recognit. (CVPR), 2016, pp. 779–788.",
        "[3] X. Ye, L. Huang, J. Wang, X. Hu, J. Xu, and C. Zhang, \"A lightweight PCB defect detection algorithm based on an improved YOLOv11s,\" IEEE Access, vol. 14, pp. 56412–56426, 2026, doi: 10.1109/ACCESS.2026.3678967.",
        "[4] S. Tang, F. He, X. Huang, and J. Yang, \"Online PCB defect detector on a new PCB defect dataset,\" arXiv:1902.06197, Feb. 2019.",
        "[5] R. R. Selvaraju, M. Cogswell, A. Das, R. Vedantam, D. Parikh, and D. Batra, \"Grad-CAM: Visual explanations from deep networks via gradient-based localization,\" in Proc. IEEE Int. Conf. Comput. Vis. (ICCV), 2017, pp. 618–626.",
        "[6] A. Chattopadhay, A. Sarkar, P. Howlader, and V. N. Balasubramanian, \"Grad-CAM++: Generalized gradient-based visual explanations for deep convolutional networks,\" in Proc. IEEE Winter Conf. Appl. Comput. Vis. (WACV), 2018, pp. 839–847.",
        "[7] F. Tao, H. Zhang, A. Liu, and A. Y. C. Nee, \"Digital twin in industry: State-of-the-art,\" IEEE Trans. Ind. Informat., vol. 15, no. 4, pp. 2405–2415, Apr. 2019.",
        "[8] P. Bhattacharya and M. F. Cloutier, \"Explainable artificial intelligence for industrial applications,\" in Proc. IEEE Int. Conf. Ind. Technol. (ICIT), 2022, pp. 1–8.",
        "[9] M. Shakya et al., \"FICS-PCB: A multi-modal image dataset for automated printed circuit board visual inspection,\" IACR Cryptol. ePrint Arch., vol. 2020, p. 1422, 2020.",
        "[10] IPC-A-610G, Acceptability of Electronic Assemblies, IPC — Association Connecting Electronics Industries, Bannockburn, IL, USA, 2020.",
        "[11] G. Jocher and J. Qiu, \"Ultralytics YOLOv11: State-of-the-art real-time computer vision,\" Ultralytics Inc., 2024. [Online]. Available: https://github.com/ultralytics/ultralytics",
        "[12] J. Chen, K. Cao, and Y. Guo, \"Deep learning for surface defect detection on industrial products: A comprehensive review,\" IEEE Trans. Instrum. Meas., vol. 70, pp. 1–18, 2021.",
        "[13] J. Chen, S. Kao, H. He, W. Zhuo, S. Wen, C. Lee, and S. Yu, \"Run, don't walk: Chasing higher FLOPS for faster neural networks,\" in Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR), 2023, pp. 12021–12031.",
        "[14] D. Ouyang, S. He, G. Zhang, M. Luo, H. Guo, J. Zhan, and Z. Huang, \"Efficient multi-scale attention module with cross-spatial learning,\" in Proc. IEEE Int. Conf. Acoust., Speech Signal Process. (ICASSP), 2023, pp. 1–5.",
        "[15] Z. Tong, Y. Chen, J. Xu, and R. Yu, \"Wise-IoU: Bounding box regression loss with dynamic focusing mechanism,\" arXiv preprint arXiv:2301.10051, 2023."
    ]

    for ref in references_list:
        p_ref = doc.add_paragraph()
        p_ref.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p_ref.paragraph_format.left_indent = Inches(0.4)
        p_ref.paragraph_format.first_line_indent = Inches(-0.4)
        p_ref.paragraph_format.space_after = Pt(4)
        p_ref.paragraph_format.line_spacing = 1.15
        r = p_ref.add_run(ref)
        r.font.size = Pt(10)

    p_sdg_t = doc.add_paragraph()
    p_sdg_t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sdg_t.paragraph_format.space_before = Pt(20)
    p_sdg_t.paragraph_format.space_after = Pt(10)
    r = p_sdg_t.add_run("MAPPING TO SDG GOALS")
    r.font.size = Pt(14)
    r.font.bold = True

    add_body(
        "The project 'SMARTPCB-XAI: AN EXPLAINABLE AI-BASED PCB INSPECTION AND DECISION SUPPORT SYSTEM' aligns directly "
        "with the United Nations Sustainable Development Goals (SDGs), specifically:", 0.3
    )
    add_body(
        "1. SDG 9: Industry, Innovation, and Infrastructure: By integrating cutting-edge YOLOv11 deep learning, explainable AI, "
        "and interactive digital twins into electronics manufacturing, the system accelerates industrial automation, enhances first-pass "
        "assembly yields, and promotes technological innovation across small and medium electronics enterprises.", 0.3
    )
    add_body(
        "2. SDG 12: Responsible Consumption and Production: Early, accurate localization of microscopic PCB defects combined with "
        "actionable IPC-A-610 repair procedures significantly reduces scrap rates and hazardous electronic waste (e-waste). By enabling "
        "precision rework rather than discarding defective circuit boards, the system fosters resource efficiency and sustainable electronics production.", 0.3
    )

    out_file = "SmartPCB-XAI_Project_Report.docx"
    doc.save(out_file)
    print(f"[SUCCESS] Complete Project Report generated at: {os.path.abspath(out_file)}")
    print(f"[SUCCESS] Total file size: {os.path.getsize(out_file)} bytes")

if __name__ == "__main__":
    create_project_report()
