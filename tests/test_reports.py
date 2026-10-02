import os
import unittest
from ai.reports.report_generator import ReportGenerator

class TestReportGeneration(unittest.TestCase):
    def setUp(self):
        self.sample_data = {
            "inspection_id": "TEST-INSP-001",
            "pcb_id": "TEST-BOARD-XYZ",
            "timestamp": "2026-09-22T14:30:00",
            "inspector": "Quality Automated Test Suite",
            "model_version": "YOLOv11s-Test",
            "quality_score": {
                "overall_score": 92.5,
                "grade": "EXCELLENT",
                "status": "PASS",
                "defect_risk": "LOW",
                "component_integrity": 98.0,
                "defect_count": 1,
                "summary": "Sample test evaluation summary."
            },
            "components": [
                {"id": "C-1", "class": "ICs", "confidence": 0.98, "bbox": [100, 100, 200, 200]},
                {"id": "C-2", "class": "capacitors", "confidence": 0.95, "bbox": [220, 120, 250, 150]}
            ],
            "defects": [
                {
                    "id": "D-1",
                    "class": "mousebite",
                    "confidence": 0.88,
                    "bbox": [50, 50, 70, 70],
                    "near_component": "capacitors",
                    "severity": {
                        "score": 45.0,
                        "level": "MEDIUM",
                        "color": "#d97706",
                        "explanation": "Minor edge erosion."
                    }
                }
            ],
            "recommendations": [
                {
                    "title": "Mousebite Defect",
                    "probable_causes": ["Chemical etching unevenness."],
                    "repair_actions": ["Apply conformal coating."],
                    "ipc_standard": "IPC-A-610 Section 10.3"
                }
            ]
        }
        self.pdf_out = "tests/test_output.pdf"
        self.excel_out = "tests/test_output.xlsx"

    def tearDown(self):
        for p in [self.pdf_out, self.excel_out]:
            if os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass

    def test_pdf_generation(self):
        out = ReportGenerator.generate_pdf(self.sample_data, self.pdf_out)
        self.assertTrue(os.path.exists(out))
        self.assertGreater(os.path.getsize(out), 1000)

    def test_excel_generation(self):
        out = ReportGenerator.generate_excel(self.sample_data, self.excel_out)
        self.assertTrue(os.path.exists(out))
        self.assertGreater(os.path.getsize(out), 1000)

if __name__ == "__main__":
    unittest.main()
