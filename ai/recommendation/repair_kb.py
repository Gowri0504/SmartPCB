"""
Rule-Based Root-Cause Recommendation Engine (SmartPCB-XAI project knowledge base).

Scientific honesty labeling — APPLIES TO THIS ENTIRE MODULE:
  1. This is a RULE-BASED knowledge base, NOT a trained AI/ML model.
     It uses static expert-entered mappings between defect classes and
     possible_causes / inspection_steps / repair_actions / verification_steps.
  2. Every probable_causes entry is framed as a POSSIBLE cause only.
     It is NOT a statement of proven causality.
  3. ipc_standard strings are reference guidance sections only. The numeric
     severity/quality scores in this project are project-defined — they are
     NOT mathematical scores published by IPC.
  4. safety_notes list ESD / thermal / chemical / high-voltage precautions.
"""


class RepairKnowledgeBase:
    """
    Industry 4.0 expert knowledge base for PCB defect root-cause analysis
    and prescriptive repair workflows.

    HONESTY LABEL (permanent):
        Rule-Based Root-Cause Recommendation Engine. All entries below are
        expert-curated static mappings; they are NOT produced by a trained
        machine learning classifier of SMT machine telemetry.
    """

    KNOWLEDGE_BASE = {
        "short": {
            "title": "Solder Bridge / Short Circuit",
            "probable_causes": [
                "Excessive solder paste volume deposited during stencil printing.",
                "Misaligned solder stencil aperture relative to PCB copper pads.",
                "Incorrect reflow thermal profile (excessive preheat soak or peak temperature).",
                "Component placement nozzle over-pressure causing solder paste squeeze-out."
            ],
            "inspection_steps": [
                "Examine adjacent copper traces using 20x-40x stereo microscope.",
                "Verify solder paste thickness using Solder Paste Inspection (SPI) system.",
                "Check for conductive debris or solder balls trapped beneath component body."
            ],
            "repair_actions": [
                "Apply mild rosin/no-clean liquid flux to bridged conductors.",
                "Use desoldering wick (braid) and temperature-controlled soldering iron (350°C) to absorb excess solder.",
                "Clean flux residue thoroughly using isopropyl alcohol (IPA) and ESD-safe brush."
            ],
            "verification_steps": [
                "Perform four-wire digital multimeter continuity test between bridged nets (ensure > 10 MΩ resistance).",
                "Re-run automated optical inspection to confirm zero residual bridging."
            ],
            "ipc_standard": "IPC-A-610G Section 10.2 (Bridging - Defect Class 1, 2, 3)",
            "safety_notes": [
                "ESD PRECAUTION: Ground the workstation, wear wrist strap, and use ESD-safe mat before touching bare PCB.",
                "THERMAL: Soldering iron tip reaches > 300°C; avoid skin contact and do not leave unattended.",
                "CHEMICAL: Isopropyl alcohol (IPA) is flammable; use in well-ventilated area, away from heat/spark sources.",
                "HIGH-VOLTAGE: After rework, discharge any high-voltage bulk capacitors before continuity testing."
            ],
        },
        "open": {
            "title": "Trace Disconnection / Open Circuit",
            "probable_causes": [
                "Etching over-exposure during inner/outer layer PCB chemical fabrication.",
                "Mechanical scratching or abrasion during manual handling / depaneling.",
                "Thermal expansion fatigue or copper trace fracture under thermal cycling.",
                "Insufficient solder volume on surface mount land (dry joint)."
            ],
            "inspection_steps": [
                "Conduct micro-continuity probe test along the signal net.",
                "Inspect trace under magnification for hairline cracks or copper delamination.",
                "Check via barrel integrity for barrel crack or knee separation."
            ],
            "repair_actions": [
                "Carefully scrape solder mask 2mm on either side of the open break using micro-chisel.",
                "Tin exposed copper trace using fine chisel soldering tip.",
                "Solder 30 AWG insulated polyurethane enameled copper jumper wire across the fracture.",
                "Encapsulate repair site with UV-curable solder mask resin and cure under 365nm UV lamp for 60 seconds."
            ],
            "verification_steps": [
                "Verify 0.0 Ω net continuity using digital multimeter.",
                "Perform IPC-7721 tape adhesion test on cured conformal resin."
            ],
            "ipc_standard": "IPC-7711/7721 Procedure 4.2.1 (Conductor Repair Using Wire Jumper)",
            "safety_notes": [
                "ESD PRECAUTION: Use ESD wrist strap and dissipative workbench during trace repair handling.",
                "UV RADIATION: 365nm UV lamps can damage unprotected eyes/skin; wear UV-blocking goggles and gloves during resin cure.",
                "MECHANICAL: Micro-chisel slips can cause lacerations — use tweezers to secure the board and cut AWAY from fingers.",
                "RESPIRATORY: Avoid inhaling rosin-core solder fumes; use local fume extraction."
            ],
        },
        "mousebite": {
            "title": "Mousebite / Trace Edge Erosion",
            "probable_causes": [
                "Uneven chemical etching or particulate contamination in acid bath.",
                "Defective photoresist film adhesion along high-density signal tracks.",
                "Air bubbles trapped beneath dry film photoresist during lamination."
            ],
            "inspection_steps": [
                "Measure minimum remaining conductor width with calibrated optical graticule.",
                "Check if trace width reduction exceeds 20% of nominal design rule."
            ],
            "repair_actions": [
                "If remaining trace width > 80% nominal: clean and apply conformal overcoat to prevent oxidation.",
                "If remaining trace width < 80%: reinforce by soldering tinned copper ribbon jumper per IPC-7721."
            ],
            "verification_steps": [
                "Ensure dielectric clearance to adjacent ground plane conforms to IPC-2221 spacing rules."
            ],
            "ipc_standard": "IPC-A-610G Section 10.3 (Conductor Width Reduction)",
            "safety_notes": [
                "ACID/CHEMICAL: If reprocessing an etched board, neutralize any residual acid with DI water before handling.",
                "ESD PRECAUTION: Apply conformal coating only on a grounded static-dissipative mat.",
                "OPTICAL: Calibrated optical graticule is fragile — do not touch objective lens with bare fingers."
            ],
        },
        "spur": {
            "title": "Copper Spur / Protrusion",
            "probable_causes": [
                "Incomplete chemical etching leaving residual copper spur.",
                "Micro-crack in photolithography master artwork (photomask).",
                "Defective copper electroplating adhesion."
            ],
            "inspection_steps": [
                "Measure clearance distance from spur tip to adjacent conductor.",
                "Verify whether minimum electrical clearance has been violated."
            ],
            "repair_actions": [
                "Use stereoscopic surgical micro-scalpel to excise unwanted copper protrusion.",
                "Clean debris with vacuum wand and apply insulating lacquer."
            ],
            "verification_steps": [
                "High-pot / dielectric withstand voltage test if spur occurs in high-voltage section."
            ],
            "ipc_standard": "IPC-A-610G Section 10.4 (Minimum Conductor Spacing)",
            "safety_notes": [
                "HIGH-VOLTAGE HIPOT: Always discharge DUT after high-pot test; lethal residual voltage can persist.",
                "SHARP TOOL: Surgical micro-scalpel is extremely sharp; use safety sheath when not in use.",
                "DEBRIS: Use closed-tip micro-vacuum for copper shavings; airborne conductive debris can short adjacent boards."
            ],
        },
        "copper": {
            "title": "Spurious Copper Residue",
            "probable_causes": [
                "Contaminated etching solution containing suspended copper particulate.",
                "Incomplete wash/rinse cycle post-etching.",
                "Solder splatter during wave soldering or hot air leveling (HASL)."
            ],
            "inspection_steps": [
                "Inspect board surface under 30x darkfield illumination for stray copper flecks.",
                "Determine if particle is encapsulated under solder mask or exposed on top."
            ],
            "repair_actions": [
                "Exposed copper flake: remove gently with fine precision tweezers or micro-vacuum.",
                "Embedded particle: route out non-conductive area and re-seal with UV resin."
            ],
            "verification_steps": [
                "Visual verification under UV illumination to ensure zero foreign material residues."
            ],
            "ipc_standard": "IPC-A-610G Section 10.5 (Extraneous Metallic Residue)",
            "safety_notes": [
                "UV INSPECTION: Darkfield UV can cause skin erythema with prolonged exposure — use timed exposure cycle.",
                "CHEMICAL: If post-etch rinse is incomplete, residual ammonium persulfate or FeCl3 is corrosive; wear nitrile gloves.",
                "HASL: Hot-air-leveled pads exceed 250°C shortly after processing; allow thermal equilibration before handling."
            ],
        },
        "pin-hole": {
            "title": "Pin-Hole / Via Void",
            "probable_causes": [
                "Air entrapment or outgassing during PTH (Plated Through Hole) copper plating.",
                "Moisture absorption in FR4 core before thermal lamination.",
                "Insufficient drill speed or dull drill bit causing rough hole wall topography."
            ],
            "inspection_steps": [
                "Perform X-ray micro-computed tomography or cross-sectional metallurgical mount.",
                "Measure pinhole depth relative to pad surface."
            ],
            "repair_actions": [
                "Fill surface pinhole with electronic-grade conductive silver epoxy or reflow solder.",
                "Smooth flush with pad surface using thermal flat blade."
            ],
            "verification_steps": [
                "Measure contact resistance across via barrel under 1 Amp load test."
            ],
            "ipc_standard": "IPC-A-610G Section 9.1 (Plated-Through Hole Voids)",
            "safety_notes": [
                "CURRENT LOAD: 1-Amp verification testing can cause localized thermal runaway if shorted; use current-limited supply.",
                "EPOXY: Silver epoxy is conductive until fully cured; avoid smearing onto adjacent dielectric spacing.",
                "X-RAY / CT: Micro-CT is ionizing radiation — only trained personnel should operate industrial X-ray sources.",
                "DRILL: Dull drill bits generate FR4 dust (fiberglass irritant); use local dust extraction and respirator mask."
            ],
        }
    }

    NORMALIZE_MAP = {
        "missing_hole": "pin-hole",
        "pinhole": "pin-hole",
        "mouse_bite": "mousebite",
        "open_circuit": "open",
        "spurious_copper": "copper",
    }

    # Permanent machine-readable provenance label attached to every returned entry.
    ENGINE_LABEL = "Rule-Based Root-Cause Knowledge Engine"
    ACTION_LABEL = "Suggested engineering action"

    @classmethod
    def _label(cls, entry: dict, matched_class: str, is_known: bool) -> dict:
        """Attach provenance so no consumer can mistake this for model output."""
        labelled = dict(entry)
        labelled["engine"] = cls.ENGINE_LABEL
        labelled["action_type"] = cls.ACTION_LABEL
        labelled["matched_class"] = matched_class
        labelled["known_class"] = is_known
        labelled["is_ml_predicted"] = False
        labelled["provenance_note"] = (
            "Static expert-curated mapping. Not a trained ML model output; "
            "probable causes are possible causes, not proven causality."
        )
        return labelled

    @classmethod
    def get_recommendation(cls, defect_class: str):
        raw_key = (defect_class or "").lower().strip()
        key = cls.NORMALIZE_MAP.get(raw_key, raw_key)
        if key in cls.KNOWLEDGE_BASE:
            return cls._label(cls.KNOWLEDGE_BASE[key], defect_class, True)

        # Default fallback for unlisted defect
        return cls._label({
            "title": f"Defect: {defect_class}",
            "probable_causes": [
                "Manufacturing process deviation during component mounting or board fabrication.",
                "Environmental contamination or thermal cycling stress."
            ],
            "inspection_steps": [
                "Inspect under optical microscope (20x-50x).",
                "Perform electrical net continuity check."
            ],
            "repair_actions": [
                "Clean area with isopropyl alcohol.",
                "Rework affected connection using calibrated soldering iron."
            ],
            "verification_steps": [
                "Re-scan on automated inspection platform."
            ],
            "ipc_standard": "IPC-A-610 General Quality Acceptance Criteria",
            "safety_notes": [
                "ESD PRECAUTION: Wear wrist strap and use dissipative mat before handling bare PCB.",
                "GENERAL: When repair type is unknown, follow the manufacturer's component handling and rework guidelines.",
                "THERMAL: Calibrate soldering iron tip temperature per IPC-7711/7721 Class 1/2/3 tables."
            ],
        }, defect_class, False)
