#!/bin/bash
# Quick validation script untuk dataset multi-turn

echo "QUICK DATASET VALIDATION & SPLIT"
echo "======================================"
echo ""

# Check if validate_dataset.py exists
if [ ! -f "validate_dataset.py" ]; then
    echo "Error: validate_dataset.py not found!"
    exit 1
fi

# Check if split_valid_invalid.py exists
if [ ! -f "split_valid_invalid.py" ]; then
    echo "Error: split_valid_invalid.py not found!"
    exit 1
fi

# Default: validate all datasets
TARGET="${1:-../MultiturnDatasetOutput}"
OUTPUT="${2:-../MultiturnCombined}"

echo "Target: $TARGET"
echo "Output: $OUTPUT"
echo ""

# Step 1: Run validation
echo "STEP 1: VALIDATING DATASET..."
echo "======================================"
python3 validate_dataset.py "$TARGET"

EXIT_CODE=$?

echo ""
echo "======================================"

if [ $EXIT_CODE -eq 0 ]; then
    echo "[SUCCESS] ALL VALIDATIONS PASSED!"
    echo ""
    
    # Step 2: Split valid/invalid
    echo "STEP 2: SPLITTING VALID & INVALID..."
    echo "======================================"
    python3 split_valid_invalid.py "$TARGET" --output "$OUTPUT"
    
    SPLIT_EXIT=$?
    
    if [ $SPLIT_EXIT -eq 0 ]; then
        echo ""
        echo "======================================"
        echo "[SUCCESS] DATASET READY FOR FINE-TUNING!"
        echo ""
        echo "Output files:"
        echo "  Valid:   $OUTPUT/valid/SFTValid.jsonl"
        echo "  Invalid: $OUTPUT/invalid/SFTInvalid.jsonl"
        echo "======================================"
    else
        echo "[ERROR] Split failed!"
        exit $SPLIT_EXIT
    fi
else
    echo "[WARNING] VALIDATION FOUND ISSUES"
    echo "Review errors above and fix before deployment"
    echo ""
    echo "TIP: You can still split the dataset to see valid/invalid separately:"
    echo "  ./quick_split.sh $TARGET $OUTPUT"
    echo "======================================"
fi

exit $EXIT_CODE
