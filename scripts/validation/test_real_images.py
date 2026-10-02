"""
Run full pipeline on available real PCB images.
Full pipeline: upload -> defect + component -> severity -> XAI -> report -> MongoDB -> analytics
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ai.inference.engine import SmartPCBInspectionEngine

# Available real images
REAL_IMAGES = [
    "test.jpg",
    "t2.jpg",
    "defect-pcb.jpg"
]

OUTPUT_DIR = "reports/real_images"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def run_pipeline(image_path):
    """Run full inspection pipeline on a single image."""
    print(f"\n{'='*80}")
    print(f"Processing: {image_path}")
    print(f"{'='*80}")
    
    # Initialize engine
    engine = SmartPCBInspectionEngine(device='cpu')
    
    # Run inspection
    start_time = time.time()
    result = engine.inspect(str(image_path))
    inference_time = time.time() - start_time
    
    # Extract key metrics
    components = result.get('components', [])
    defects = result.get('defects', [])
    quality_score = result.get('quality_score', {})
    
    # Save result JSON
    output_json = Path(OUTPUT_DIR) / f"{Path(image_path).stem}_result.json"
    with open(output_json, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    
    # Summary
    summary = {
        'image': image_path,
        'num_components': len(components),
        'num_defects': len(defects),
        'component_classes': list(set(c['class'] for c in components)),
        'defect_classes': list(set(d['class'] for d in defects)),
        'confidence_range': (
            min([c['confidence'] for c in components] + [d['confidence'] for d in defects]) if components or defects else None,
            max([c['confidence'] for c in components] + [d['confidence'] for d in defects]) if components or defects else None
        ),
        'inference_seconds': inference_time,
        'quality_score': quality_score.get('overall_score') if quality_score else None,
        'grade': quality_score.get('grade') if quality_score else None
    }
    
    print(f"Components: {summary['num_components']}")
    print(f"Defects: {summary['num_defects']}")
    print(f"Component classes: {summary['component_classes']}")
    print(f"Defect classes: {summary['defect_classes']}")
    print(f"Confidence range: {summary['confidence_range']}")
    print(f"Inference time: {summary['inference_seconds']:.2f}s")
    print(f"Quality score: {summary['quality_score']}")
    print(f"Grade: {summary['grade']}")
    
    return summary

def main():
    print("="*80)
    print("FULL PIPELINE TEST ON REAL PCB IMAGES")
    print("="*80)
    
    results = []
    
    for image_name in REAL_IMAGES:
        image_path = Path(image_name)
        if not image_path.exists():
            print(f"WARNING: {image_name} not found, skipping")
            continue
        
        try:
            summary = run_pipeline(image_path)
            results.append(summary)
        except Exception as e:
            print(f"ERROR processing {image_name}: {e}")
            results.append({
                'image': image_name,
                'error': str(e),
                'status': 'FAILED'
            })
    
    # Save CSV summary
    import csv
    csv_path = Path(OUTPUT_DIR) / "pipeline_results.csv"
    with open(csv_path, 'w', newline='') as f:
        if results:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
    
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Total images processed: {len(results)}")
    print(f"Successful: {sum(1 for r in results if 'error' not in r)}")
    print(f"Failed: {sum(1 for r in results if 'error' in r)}")
    print(f"\nResults saved to: {OUTPUT_DIR}")
    print(f"CSV summary: {csv_path}")
    
    # Note about 30+ image requirement
    print(f"\n{'='*80}")
    print("NOTE: 30+ IMAGE REQUIREMENT")
    print(f"{'='*80}")
    print(f"Only 3 real PCB images available in repository.")
    print(f"To meet the 30+ image requirement, please provide additional")
    print(f"real PCB photos in data/real_photos/ directory.")
    print(f"Available images: {REAL_IMAGES}")

if __name__ == "__main__":
    main()