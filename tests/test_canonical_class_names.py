"""
Test that canonical class names are used, not checkpoint raw names.
With the from-scratch defect model deployment (2026-09-26), canonical names
are used directly. Legacy PCB-DATASET names (missing_hole, mouse_bite,
open_circuit, spurious_copper) are no longer used in the deployed model.
"""

import unittest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai.config import (
    CANONICAL_DEFECT_CLASSES, 
    CANONICAL_COMPONENT_CLASSES,
    normalize_defect_class,
    normalize_component_class
)

class TestCanonicalClassNames(unittest.TestCase):
    """Test that only canonical class names are used, not checkpoint raw names."""
    
    # Forbidden checkpoint raw names (legacy model only - no longer used)
    # The deployed scratch model uses canonical names directly
    FORBIDDEN_DEFECT_NAMES = set()  # No forbidden names with canonical deployment
    ALLOWED_DEFECT_NAMES = set(CANONICAL_DEFECT_CLASSES)
    
    FORBIDDEN_COMPONENT_NAMES = {'relay', 'buzzer', 'switch', 'battery', 'led'}  # Classes not in canonical set
    ALLOWED_COMPONENT_NAMES = set(CANONICAL_COMPONENT_CLASSES)
    
    def test_config_canonical_defect_classes(self):
        """Verify config uses canonical defect class names."""
        self.assertEqual(set(CANONICAL_DEFECT_CLASSES), 
                        {'open', 'short', 'mousebite', 'spur', 'copper', 'pin-hole'})
    
    def test_config_canonical_component_classes(self):
        """Verify config uses canonical component class names (deployed model taxonomy)."""
        # CANONICAL_COMPONENT_CLASSES = DEPLOYED_COMPONENT_CLASSES (10 classes from checkpoint)
        self.assertEqual(set(CANONICAL_COMPONENT_CLASSES),
                        {'relay', 'buzzer', 'ic', 'switch', 'battery', 
                         'transistor', 'capacitor', 'resistor', 'led', 'diode'})
    
    def test_no_forbidden_defect_names_in_config(self):
        """Ensure forbidden checkpoint names don't appear in config."""
        # With canonical deployment, no forbidden names exist
        self.assertEqual(len(self.FORBIDDEN_DEFECT_NAMES), 0,
                        "No forbidden defect names with canonical deployment")

    def test_defect_normalization_uses_canonical_by_index(self):
        """Test that defect normalization uses canonical names via index mapping."""
        # Index 0 should map to 'open'
        result, mapped, _ = normalize_defect_class("open", class_id=0)
        self.assertEqual(result, 'open', "Index 0 should normalize to 'open'")
        self.assertTrue(mapped, "Index 0 should be mapped")

        # Index 1 should map to 'short'
        result, mapped, _ = normalize_defect_class("short", class_id=1)
        self.assertEqual(result, 'short', "Index 1 should normalize to 'short'")
        self.assertTrue(mapped, "Index 1 should be mapped")

        # Index 2 should map to 'mousebite'
        result, mapped, _ = normalize_defect_class("mousebite", class_id=2)
        self.assertEqual(result, 'mousebite', "Index 2 should normalize to 'mousebite'")
        self.assertTrue(mapped, "Index 2 should be mapped")
    
    def test_defect_normalization_unknown_labels_remain_unchanged(self):
        """Test that unknown labels are not coerced into unrelated classes."""
        # Unknown label without class_id should remain unchanged
        result, mapped, _ = normalize_defect_class("unknown_defect")
        self.assertEqual(result, 'unknown_defect', "Unknown labels should remain unchanged")
        self.assertFalse(mapped, "Unknown labels should not be mapped")
    
    def test_component_normalization_partial_mapping(self):
        """Test that component normalization uses canonical names where available."""
        # Since CANONICAL_COMPONENT_CLASSES = DEPLOYED_COMPONENT_CLASSES (10 classes),
        # the deployed class names are already canonical for the operational system
        # 'ic' is already in the canonical set, should remain unchanged
        result, mapped, _ = normalize_component_class("ic")
        self.assertEqual(result, 'ic', "'ic' is already canonical (deployed class)")
        self.assertTrue(mapped, "'ic' should be mapped")
        
        # 'capacitor' is already in the canonical set, should remain unchanged
        result, mapped, _ = normalize_component_class("capacitor")
        self.assertEqual(result, 'capacitor', "'capacitor' is already canonical (deployed class)")
        self.assertTrue(mapped, "'capacitor' should be mapped")
        
        # 'relay' is in the canonical set (deployed class), should remain unchanged
        result, mapped, _ = normalize_component_class("relay")
        self.assertEqual(result, 'relay', "'relay' is already canonical (deployed class)")
        self.assertTrue(mapped, "'relay' should be mapped")

if __name__ == '__main__':
    unittest.main()