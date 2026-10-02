# CHANGELOG_AI.md

**Purpose:** Track all AI-related changes to datasets, models, and configurations.

---

## 2026-09-26 - Defect Model From-Scratch Deployment

### Action: Deployed defect_best_scratch.pt
- **New model:** `models/defect_best_scratch.pt` (YOLO11s, from-scratch, local data only)
- **Training:** Kaggle GPU, seed 42, 50 epochs, datasets/defects (train 850 / val 150 / test 500)
- **Verified metrics:** mAP50 0.951, mAP50-95 0.631, precision 0.931, recall 0.906
- **Class names:** {0: 'open', 1: 'short', 2: 'mousebite', 3: 'spur', 4: 'copper', 5: 'pin-hole'}
- **Contamination risk:** NONE (local data only, verifiable training pipeline)

### Configuration Changes
- **Updated `ai/config.py`:**
  - `DEPLOYED_DEFECT_CLASSES`: Changed to canonical names (open, short, mousebite, spur, copper, pin-hole)
  - `DEFECT_CLASS_ALIASES`: Updated to identity mapping (no name translation needed)
  - `DEFECT_MAPPING_NOTE`: Updated to reflect from-scratch model deployment

### Model Preservation
- **Renamed:** `defect_best.pt` → `defect_best_legacy.pt` (preserved for reference)
- **Discarded:** `defect_best_scratch.pt.backup` (temporary backup removed)

### Test Updates
- **Updated tests for canonical deployment:**
  - `tests/test_model_safety.py`: Updated defect normalization tests for canonical names
  - `tests/test_canonical_class_names.py`: Removed forbidden defect names (no longer applicable)
  - `tests/test_fastapi_health.py`: Updated health endpoint test description

### Documentation
- **Updated:** `VERIFICATION_LOG_DEFECT_MODEL.md` (added from-scratch resolution section)
- **Updated:** `FINAL_STATUS.md` (comprehensive status update)
- **Updated:** `FINAL_COMPONENT_MODEL_EVALUATION.md` (added board-count generalization risk)

---

## 2026-09-26 - Component Model Retrying Attempt (FAILED)

### Action: From-Scratch Retraining Failed
- **Attempted model:** `component_best_new.pt` (19.2 MB)
- **Root cause:** Dataset path bug - model trained on defect dataset, not component dataset
- **Evidence:** Model class names are {0: 'open', 1: 'short', 2: 'mousebite', 3: 'spur', 4: 'copper', 5: 'pin-hole'}
- **Kaggle metrics:** mAP50 0.9767 (on defect dataset, not component dataset)
- **Local evaluation:** mAP50 ~0 (on component dataset - completely different classes)

### Action Taken
- **Discarded:** `component_best_new.pt` (trained on wrong dataset)
- **Kept:** `component_best.pt` (legacy, mAP50 0.093) as current deployed model
- **Documented:** Failure details in `FINAL_COMPONENT_MODEL_EVALUATION.md`

### Required Fix
The component training notebook must be corrected to:
1. Hardcode the exact dataset path to the components_unified upload (no auto-detection)
2. Verify only ONE component dataset is uploaded to Kaggle
3. Confirm class names match canonical component taxonomy before training
4. Validate locally against `datasets/components_unified` immediately after training

---

## 2026-09-26 - Component Dataset Generalization Risk

### Action: Documented Board Count Risk
- **Test split analysis:** 9 distinct boards, but s1 dominates (64% of test images)
- **Risk level:** MODERATE to HIGH
- **Documentation:** Added to `FINAL_COMPONENT_MODEL_EVALUATION.md`
- **Recommendation:** Future data collection should aim for balanced board distribution

---

## 2026-09-24 - Phase 2.1: Component Dataset Cleanup

### Action: Excluded 4 Empty Tiles
- **Files removed (8 total):**
  - `datasets/components_unified/test/images/fics_s1_front_x2560_y1536.jpg`
  - `datasets/components_unified/test/labels/fics_s1_front_x2560_y1536.txt`
  - `datasets/components_unified/train/images/fics_s3_s3_front_x5632_y1024.jpg`
  - `datasets/components_unified/train/labels/fics_s3_s3_front_x5632_y1024.txt`
  - `datasets/components_unified/train/images/fics_s4_s4_front_x3072_y2560.jpg`
  - `datasets/components_unified/train/labels/fics_s4_s4_front_x3072_y2560.txt`
  - `datasets/components_unified/train/images/fics_s4_s4_front_x3584_y2560.jpg`
  - `datasets/components_unified/train/labels/fics_s4_s4_front_x3584_y2560.txt`

- **Reason:** These tiles had 0 remaining component boxes after removing class-7 out-of-range IDs in the previous fix. They contribute nothing to training/evaluation.

- **Evidence:** Annotated images saved to `reports/dataset/emptied_labels/` showing 0 boxes.

- **Updated Dataset Stats:**
  - Before: 1,013 images, 33,156 boxes
  - After: 1,009 images, 33,156 boxes
  - Removed: 4 images (0 boxes each)

- **Validation:** Re-ran `scripts/dataset/validate_dataset.py` - all checks pass.

---

## 2026-09-24 - Phase 0: Security Cleanup

### Action: Moved Credentials to Secrets
- **Files moved to `D:\SmartPCB-XAI-SECRETS\`:**
  - `metrics/auth_token.txt`
  - `metrics/auth_register.json`
  - `metrics/runcheck_token.txt`
  - `debug_outputs/` (entire directory with Bearer tokens)

- **Updated .gitignore:** Added secrets and archive directories.

---

## 2026-09-24 - Phase 0: Archive Stray Files

### Action: Archived Temporary Files
- **Moved to `archive\`:**
  - `scripts_temp_audit.py`
  - `train_fast_curated.py`
  - `tests_full_run.log`
  - `datasets/temp_deeppcb`
  - `scripts/temp`

- **Fixed broken paths:** Updated scripts to use `archive/temp_deeppcb` instead of `datasets/temp_deeppcb`.

---

## Previous Session - Component Dataset Fix

### Action: Fixed 13 Out-of-Range Class IDs
- **Issue:** 13 label files contained class ID 7 (invalid for 6-class dataset)
- **Fix:** Removed only the class-7 boxes using `scripts/dataset/fix_out_of_range_class_ids.py`
- **Backup:** Created `datasets/components_unified_backup_before_fix`
- **Result:** 13 files affected, 4 ended up with 0 boxes (now excluded in this session)