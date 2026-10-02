# GPU Training Guide - Kaggle/Colab

This guide explains how to train both defect and component detection models on GPU using Kaggle or Google Colab.

---

## Part 1: Defect Model Training

### Files to Upload

#### Kaggle Dataset Upload
1. Create a new Kaggle dataset
2. Upload: `kaggle_upload/defects.zip` (33.95 MB, contains train/val/test with images and labels)
3. Dataset name suggestion: `smartpcb-defects`

#### Notebook Upload
1. Upload: `notebooks/train_defect_from_scratch.ipynb`

### Kaggle Steps

#### 1. Enable GPU
1. Go to Kaggle → Code → Notebooks
2. Create new notebook
3. In notebook settings: Accelerator → GPU (T4 or P100)
4. Internet: Turn ON (needed for pip install)

#### 2. Upload Dataset
1. In notebook sidebar → Input → Add Data
2. Upload your `kaggle_upload/defects.zip`
3. Note the path (e.g., `/kaggle/input/smartpcb-defects/defects`)

#### 3. Update Dataset Path in Notebook
In the "Rewrite data.yaml path" cell, change:
```python
DATA_PATH = "/kaggle/input/smartpcb-defects/defects"  # Update to your actual path
```

#### 4. Run All Cells
1. Click "Run All" or run cells sequentially
2. Expected runtime: ~30-60 minutes on T4 GPU
3. Watch for progress in the training cell

#### 5. Download Outputs
After completion, download:
1. `defect_training_outputs.zip` (contains best.pt, metrics, results)
2. Send back to local repo: `models/defect_best_scratch.pt`

### Colab Steps

#### 1. Enable GPU
1. Runtime → Change runtime type → T4 GPU
2. Runtime → Run all

#### 2. Upload Dataset
1. In left sidebar, click folder icon
2. Upload `kaggle_upload/defects.zip`
3. Extract: `!unzip defects.zip`
4. Update DATA_PATH in notebook to the extraction path

#### 3. Upload and Run Notebook
1. Upload `notebooks/train_defect_from_scratch.ipynb`
2. Open and run all cells
3. Download `defect_training_outputs.zip`

### Expected Defect Results

After training completes, you should see:
- `defect_training_outputs.zip` (~200-300 MB)
- Contains: `defect_best.pt`, `defect_last.pt`, metrics JSON/CSV, confusion matrix
- Test mAP50 expected: ~0.90-0.95 (this is the real number we need)

---

## Part 2: Component Model Training

### Files to Upload

#### Kaggle Dataset Upload
1. Create a new Kaggle dataset
2. Upload: `kaggle_upload/components.zip` (93.14 MB, contains train/val/test with images and labels)
3. Dataset name suggestion: `smartpcb-components`

#### Notebook Upload
1. Upload: `notebooks/train_component_gpu.ipynb`

### Kaggle Steps

#### 1. Enable GPU
Same as defect training (enable GPU, internet ON)

#### 2. Upload Dataset
1. In notebook sidebar → Input → Add Data
2. Upload your `kaggle_upload/components.zip`
3. Note the path (e.g., `/kaggle/input/smartpcb-components/components`)

#### 3. Update Dataset Path in Notebook
In the "Rewrite data.yaml path" cell, change:
```python
DATA_PATH = "/kaggle/input/smartpcb-components/components"  # Update to your actual path
```

#### 4. Run All Cells
1. Click "Run All" or run cells sequentially
2. Expected runtime: ~45-90 minutes on T4 GPU (higher resolution 1024)
3. Watch for progress in the training cell

#### 5. Download Outputs
After completion, download:
1. `component_training_outputs.zip` (contains best.pt, metrics, results)
2. Send back to local repo: `models/component_best_new.pt`

### Colab Steps

#### 1. Enable GPU
Same as defect training

#### 2. Upload Dataset
1. In left sidebar, click folder icon
2. Upload `kaggle_upload/components.zip`
3. Extract: `!unzip components.zip`
4. Update DATA_PATH in notebook to the extraction path

#### 3. Upload and Run Notebook
1. Upload `notebooks/train_component_gpu.ipynb`
2. Open and run all cells
3. Download `component_training_outputs.zip`

### Expected Component Results

After training completes, you should see:
- `component_training_outputs.zip` (~200-300 MB)
- Contains: `component_best.pt`, `component_last.pt`, metrics JSON/CSV, confusion matrix
- Test mAP50 target: >= 0.60
- **Note:** If target not met, report honestly (dataset is small: 804 train images)

---

## Files to Send Back

### Defect Model
1. `defect_training_outputs.zip` (from Kaggle/Colab)
2. Rename to `defect_best_scratch.pt` after extraction
3. Place in `models/` directory
4. We'll then compare: deployed checkpoint vs. our trained model

### Component Model
1. `component_training_outputs.zip` (from Kaggle/Colab)
2. Rename to `component_best_new.pt` after extraction
3. Place in `models/` directory
4. We'll evaluate on board-disjoint test split

---

## Troubleshooting

**GPU not available:**
- Kaggle: Check weekly GPU quota (30 hrs/week)
- Colab: T4 GPU has session limits, reconnect if disconnected

**Dataset path error:**
- Print the actual Kaggle input path in the notebook first cell
- Update DATA_PATH accordingly

**Training too slow:**
- Reduce epochs from 100 to 50 for faster iteration
- Reduce batch size if GPU memory is full
- For component training, reduce imgsz from 1024 to 640 if OOM

**Component model not reaching target:**
- Dataset is small (804 train images)
- Target mAP50 >= 0.60 may not be achievable
- Report honest results if target not met