#!/bin/bash
# Quick validation script untuk dataset multi-turn

echo "QUICK DATASET VALIDATION"
echo "======================================"
echo ""

# Check if validate_dataset.py exists
if [ ! -f "validate_dataset.py" ]; then
    echo "Error: validate_dataset.py not found!"
    exit 1
fi

# Default: validate all datasets
TARGET="${1:-../MultiturnDatasetOutput}"

echo "Target: $TARGET"
echo ""

# Run validation
python3 validate_dataset.py "$TARGET"

EXIT_CODE=$?

echo ""
echo "======================================"

if [ $EXIT_CODE -eq 0 ]; then
    echo "[SUCCESS] ALL VALIDATIONS PASSED!"
    echo "Dataset ready for fine-tuning"
else
    echo "[WARNING] VALIDATION FOUND ISSUES"
    echo "Review errors above and fix before deployment"
fi

echo "======================================"

exit $EXIT_CODE
