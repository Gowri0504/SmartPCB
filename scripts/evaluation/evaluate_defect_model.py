import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from evaluate_component_model import main_defect

if __name__ == "__main__":
    main_defect()
