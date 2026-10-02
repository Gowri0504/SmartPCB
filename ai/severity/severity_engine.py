class SeverityEngine:
    """
    SmartPCB-XAI project-defined severity score & quality scoring engine.

    NOTE: The numeric 0–100 formulas in this module are a project-defined
    deterministic construction — they are NOT the official numeric score of
    the IPC-A-610 standard. IPC-A-610 is cited here only as a reference for
    workmanship acceptability guidance and defect category naming.

    Fully documented for research auditability.
    (SmartPCB-XAI project-defined severity score)
    """

    DEFECT_BASE_WEIGHTS = {
        "short": 90.0,            # Solder/trace bridging causing catastrophic short circuits
        "open": 85.0,             # Trace disconnection causing circuit functional failure
        "open_circuit": 85.0,     # Trace disconnection (model alias)
        "pin-hole": 60.0,         # Via/pad pinhole causing long-term reliability issues
        "missing_hole": 60.0,     # Missing hole / pinhole (model alias)
        "mousebite": 55.0,        # Edge erosion reducing dielectric withstand voltage
        "mouse_bite": 55.0,       # Edge erosion (model alias)
        "spur": 45.0,             # Trace spur with potential to bridge under vibration
        "copper": 35.0,           # Spurious copper flakes/etching residue
        "spurious_copper": 35.0,  # Spurious copper (model alias)
    }

    COMPONENT_CRITICALITY = {
        "ics": 1.5,
        "ic": 1.5,
        "transistors": 1.3,
        "transistor": 1.3,
        "diodes": 1.2,
        "diode": 1.2,
        "inductors": 1.1,
        "inductor": 1.1,
        "capacitors": 1.0,
        "capacitor": 1.0,
        "resistors": 1.0,
        "resistor": 1.0,
        "relay": 1.2,
        "switch": 1.1,
        "battery": 1.4,
        "led": 1.0,
        "buzzer": 1.0
    }

    @classmethod
    def calculate_defect_severity(cls, defect_class: str, confidence: float, bbox_area_norm: float = 0.01, near_component: str = None):
        """
        Calculates individual defect severity score (0 to 100).
        """
        base = cls.DEFECT_BASE_WEIGHTS.get(defect_class.lower(), 50.0)
        crit_mult = cls.COMPONENT_CRITICALITY.get(near_component.lower(), 1.0) if near_component else 1.0
        
        # Scale with defect area (larger defects have higher impact)
        size_mult = 1.0 + min(1.0, bbox_area_norm * 10.0)
        
        raw_score = base * crit_mult * size_mult * (0.7 + 0.3 * confidence)
        score = round(min(100.0, max(5.0, raw_score)), 1)

        if score >= 75.0:
            level = "CRITICAL"
            color = "#dc2626"
        elif score >= 50.0:
            level = "HIGH"
            color = "#ea580c"
        elif score >= 25.0:
            level = "MEDIUM"
            color = "#d97706"
        else:
            level = "LOW"
            color = "#16a34a"

        explanation = (
            f"Defect '{defect_class}' has base weight {base}. "
            f"{f'Proximity to critical component {near_component} (x{crit_mult}). ' if near_component else ''}"
            f"Confidence {confidence*100:.1f}%. Resulting score: {score}/100 ({level})."
        )

        return {
            "score": score,
            "level": level,
            "color": color,
            "base_weight": base,
            "criticality_multiplier": crit_mult,
            "explanation": explanation
        }

    @classmethod
    def calculate_pcb_quality_score(cls, defects: list, total_components: int = 0):
        """
        Calculates overall PCB quality score (0 to 100) and assembly rating.

        NOTE: This is a SmartPCB-XAI project-defined severity score.
        IPC-A-610 is referenced for workmanship guidance, not numeric scoring.

        Formula (deterministic):
          penalty_sum = SUM( defect_severity_score / 5.0 * detection_confidence )
                        over all detected defects
          overall_score = clamp(100.0 - penalty_sum, 0, 100)
          component_integrity = clamp(100.0 - 4.5 * num_defects, 0, 100)
          Pass / Rework / Fail thresholds are: overall >= 90 / 75-90 / <75 or any CRITICAL.
        """
        component_count = int(total_components)
        defect_count = len(defects) if defects else 0

        if not defects:
            return {
                "overall_score": 100.0,
                "grade": "EXCELLENT",
                "status": "PASS",
                "defect_risk": "MINIMAL",
                "component_integrity": 100.0,
                "defect_count": 0,
                "component_count": component_count,
                "formula": "score = 100 - Σ(severity/5 * confidence)  →  no defect penalty applied. (SmartPCB-XAI project-defined severity score)",
                "summary": f"Zero defects detected. {component_count} components verified. No defects found by detectors; refer to IPC-A-610 for formal workmanship acceptability guidance."
            }

        total_penalty = 0.0
        has_critical = False

        for d in defects:
            sev = d.get("severity", {})
            score = sev.get("score", 50.0)
            conf = d.get("confidence", 0.8)
            if sev.get("level") == "CRITICAL":
                has_critical = True

            total_penalty += (score / 5.0) * conf

        overall = round(max(0.0, 100.0 - total_penalty), 1)

        if has_critical or overall < 50.0:
            grade = "REJECT"
            status = "FAIL"
            risk = "CRITICAL"
        elif overall < 75.0:
            grade = "MARGINAL"
            status = "REWORK REQUIRED"
            risk = "HIGH"
        elif overall < 90.0:
            grade = "ACCEPTABLE"
            status = "PASS (ADVISORY)"
            risk = "MODERATE"
        else:
            grade = "EXCELLENT"
            status = "PASS"
            risk = "LOW"

        comp_integrity = round(max(0.0, 100.0 - (len(defects) * 4.5)), 1)

        summary = (
            f"AI-assisted PCB Quality Score: {overall}/100 ({grade}). "
            f"{defect_count} total defects, {component_count} components verified. "
            f"Manufacturing Status: {status}."
        )

        return {
            "overall_score": overall,
            "grade": grade,
            "status": status,
            "defect_risk": risk,
            "component_integrity": comp_integrity,
            "defect_count": defect_count,
            "component_count": component_count,
            "formula": "overall = clamp(100 - Σ(severity/5 * conf), 0, 100). component_integrity = clamp(100 - 4.5 * n_defects, 0, 100).",
            "summary": summary
        }
