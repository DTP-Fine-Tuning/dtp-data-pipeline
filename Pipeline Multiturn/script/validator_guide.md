# Dataset Validator - User Guide

## Tujuan

Script `validate_dataset.py` adalah tool comprehensive untuk:
- Validasi format & struktur dataset multi-turn
- Deteksi corruption (JSON-in-string, escaped JSON)
- Analisis statistik dataset
- Generate detailed reports

---

## Cara Menggunakan

### 1. Basic Usage - Validate Single Directory

```bash
cd "/home/wildanaziz/dtp-data-pipeline/Pipeline Multiturn/script"
python3 validate_dataset.py ../MultiturnDatasetOutput/Pengembangan_Produk_Digital_2
```

**Output:**
- File-by-file validation progress
- Summary statistics
- Error details (jika ada)
- Quality score

---

### 2. Validate Single File

```bash
python3 validate_dataset.py ../MultiturnDatasetOutput/Pengembangan_Produk_Digital_2/batch_001.jsonl
```

---

### 3. Validate All Datasets

```bash
python3 validate_dataset.py --all
```

Akan validate semua dataset di folder `MultiturnDatasetOutput/`

---

### 4. Export Detailed Report

```bash
python3 validate_dataset.py ../MultiturnDatasetOutput/Pengembangan_Produk_Digital_2 --export report.json
```

**Report JSON berisi:**
- Summary statistics
- Error breakdown by type
- Distribution data (turns, modes, levels)
- File-by-file details
- First 100 validation errors

---

## Validasi yang Dilakukan

### Structure Validation

1. **JSON Format**
   - Valid JSON structure
   - Has `messages` field
   - Messages is array

2. **Message Fields**
   - All messages have `role` and `content`
   - Role values: `system`, `user`, `assistant`
   - No empty content

3. **Conversation Structure**
   - Minimum 2 messages
   - First message = `system` role
   - Last message = `assistant` role
   - Last assistant contains recommendation

4. **System Prompt**
   - Exact match dengan expected system prompt
   - No modifications allowed

5. **Role Sequence**
   - No consecutive system messages
   - Logical conversation flow

### Corruption Detection

1. **JSON-in-String**
   ```json
   // DETECTED
   {"role": "assistant", "content": "[{\"role\":\"system\"...}]"}
   ```

2. **Escaped JSON**
   ```json
   // DETECTED
   {"role": "assistant", "content": "...\\\"role\\\"..."}
   ```

---

## Output Interpretation

### Progress Indicators

```
[1/14] Validating: batch_001.jsonl... [SUCCESS] 30 valid
[2/14] Validating: batch_002.jsonl... [WARNING]  29 valid, 1 invalid
```

- [SUCCESS] = All conversations valid
- [SUCCESS] = Some invalid conversations found

### Quality Score

```
[SUCCESS] QUALITY SCORE: 100.0% - PERFECT!      // 100%
[SUCCESS] QUALITY SCORE: 98.2% - EXCELLENT      // 95-99%
[WARNING] QUALITY SCORE: 92.5% - GOOD          // 90-94%
[WARNING] QUALITY SCORE: 85.0% - FAIR          // 80-89%
[BAD] QUALITY SCORE: 65.0% - NEEDS IMPROVEMENT  // <80%
```

### Statistics Sections

1. **Files**: Total files, files with errors, clean files
2. **Conversations**: Total, valid %, invalid %
3. **Errors by Type**: Breakdown of error categories
4. **Turn Distribution**: How many conversations per turn count
5. **Mode Distribution**: Fast/Medium/Long breakdown
6. **Level Distribution**: Level 1-9 distribution
7. **Area Fungsi**: Top 10 most common areas

---

## Troubleshooting

### Q: Script menemukan error "empty content"
**A:** Ada message dengan content kosong. Penyebab:
- LLM generate empty string
- API error/timeout
- Parsing error

**Fix:** Re-generate conversations yang error, atau hapus conversation tersebut.

### Q: Script menemukan "JSON corruption"
**A:** LLM mengembalikan JSON array as string (bug utama yang sudah diperbaiki).

**Fix:** Pakai script `multiturn.ipynb` versi baru yang sudah ada validasi.

### Q: Script menemukan "system prompt tidak sesuai"
**A:** System message tidak exact match dengan expected prompt.

**Fix:** Regenerate dengan script terbaru.

### Q: Quality score rendah
**A:** Banyak invalid conversations.

**Action:**
1. Review error details di output
2. Check data input Excel
3. Regenerate dengan script yang sudah diperbaiki

---

## Best Practices

### 1. Validate After Generation

Selalu jalankan validator setelah generate dataset:

```bash
# Generate dataset
cd script
jupyter notebook multiturn.ipynb
# ... run generation ...

# Validate hasil
python3 validate_dataset.py --all
```

### 2. Monitor Quality Score

Target minimal: **95% quality score**

Jika < 95%:
- Review error messages
- Fix input data
- Regenerate invalid batches

### 3. Export Reports untuk Audit

```bash
# Generate report dengan timestamp
python3 validate_dataset.py --all --export "validation_$(date +%Y%m%d_%H%M%S).json"
```

### 4. Continuous Validation

Setup sebagai part of workflow:

```bash
#!/bin/bash
# generate_and_validate.sh

# Step 1: Generate dataset
echo "Generating dataset..."
python3 -c "import multiturn; await multiturn.process_all_files(...)"

# Step 2: Validate
echo "Validating dataset..."
python3 validate_dataset.py --all --export validation_report.json

# Step 3: Check exit code
if [ $? -eq 0 ]; then
    echo "[SUCCESS] All validations passed!"
else
    echo "[FAILED] Validation failed! Check validation_report.json"
    exit 1
fi
```

---

## Error Categories

### Critical Errors (Auto-detected)

1. **json_corruption**
   - JSON array as string
   - Escaped JSON in content
   - Action: Reject & regenerate

2. **role_sequence**
   - Invalid role order
   - Consecutive system messages
   - Action: Regenerate

3. **system_prompt**
   - Modified system prompt
   - Missing system message
   - Action: Regenerate

4. **json_decode**
   - Invalid JSON syntax
   - Malformed JSONL
   - Action: Fix or remove line

### Warning Errors (Review needed)

1. **empty_content**
   - Message with no content
   - Action: Regenerate conversation

2. **missing_recommendation**
   - Last assistant without recommendation
   - Action: Regenerate

---

## Advanced Usage

### Programmatic Usage

```python
from validate_dataset import DatasetValidator
from pathlib import Path

# Create validator
validator = DatasetValidator()

# Validate directory
results = validator.validate_directory(Path("/path/to/dataset"))

# Print summary
validator.print_summary(results)

# Export report
validator.export_report(Path("report.json"), results)

# Access statistics
print(f"Quality: {validator.stats['valid_conversations']/validator.stats['total_conversations']*100:.1f}%")
```

### Custom Validation Rules

Edit `validate_dataset.py` untuk add custom rules:

```python
def validate_conversation_structure(self, messages, line_num, filename):
    # Existing validations...
    
    # Custom rule: Check minimum user messages
    user_count = sum(1 for m in messages if m['role'] == 'user')
    if user_count < 2:
        return False, "Conversation must have at least 2 user messages"
    
    return True, None
```

---

## Sample Output

```
======================================================================
VALIDATING DATASET
======================================================================
Directory: ../MultiturnDatasetOutput/Pengembangan_Produk_Digital_2
Found: 14 JSONL files
======================================================================

[1/14] Validating: batch_001.jsonl... [SUCCESS] 30 valid
[2/14] Validating: batch_002.jsonl... [WARNING]  29 valid, 1 invalid
...

======================================================================
VALIDATION SUMMARY
======================================================================

Files:
   Total files: 14
   Files with errors: 1
   Clean files: 13

Conversations:
   Total: 420
   Valid: 419 (99.8%)
   Invalid: 1 (0.2%)

Turn Distribution:
   3 turns: 35 (8.4%)
   5 turns: 245 (58.5%)
   9 turns: 139 (33.2%)

Mode Distribution:
   FAST_DIRECT: 35 (8.4%)
   MEDIUM: 245 (58.5%)
   LONG: 139 (33.2%)

Level Distribution:
   Level 2: 419 (100.0%)

======================================================================
[SUCCESS] QUALITY SCORE: 99.8% - EXCELLENT
======================================================================
```

---

## Integration dengan Workflow

### Pre-Deployment Check

```bash
# Before uploading to OpenAI
python3 validate_dataset.py --all

if [ $? -eq 0 ]; then
    echo "Dataset ready for fine-tuning"
    # Upload to OpenAI
else
    echo "Fix errors before deployment"
    exit 1
fi
```

### CI/CD Pipeline

```yaml
# .github/workflows/validate-dataset.yml
name: Validate Dataset

on:
  push:
    paths:
      - 'Pipeline Multiturn/MultiturnDatasetOutput/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Validate Dataset
        run: |
          cd "Pipeline Multiturn/script"
          python3 validate_dataset.py --all --export validation_report.json
      - name: Upload Report
        uses: actions/upload-artifact@v2
        with:
          name: validation-report
          path: validation_report.json
```

---

## Support

Jika menemukan bug atau perlu bantuan:
1. Check error message details
2. Re-run dengan `--export` untuk detailed report
3. Check validation_report.json untuk full context

---