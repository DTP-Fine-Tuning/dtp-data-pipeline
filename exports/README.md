# Exports

Folder ini menyimpan hasil akhir pipeline yang diekspor dalam berbagai format.

## Status Saat Ini:
**Folder ini masih kosong** - output pipeline saat ini disimpan di `data_processed/cleaned_data_final.xlsx`

## Rencana Pengembangan:

### Format Export yang Direncanakan:

#### 1. **Dataset untuk Fine-tuning**
- `train.json`, `val.json`, `test.json` → Split dataset untuk training
- `dataset_full.json` → Complete dataset dalam format JSON
- `dataset.parquet` → Format Parquet untuk efisiensi storage

#### 2. **Format untuk Analysis**
- `cleaned_data.csv` → Format CSV untuk analisis umum
- `summary_stats.json` → Statistik dan metadata dataset
- `data_quality_report.html` → Report kualitas data

#### 3. **HuggingFace Format**
- `dataset_info.json` → Metadata untuk HuggingFace datasets
- `data/` → Folder dengan format HuggingFace datasets

## Contoh Struktur Export:
```
exports/
├── training/
│   ├── train.json
│   ├── val.json
│   └── test.json
├── analysis/
│   ├── cleaned_data.csv
│   └── summary_stats.json
└── huggingface/
    ├── dataset_info.json
    └── data/
```

## Format Target untuk SFT/DPO:
```json
{
  "instruction": "Analisis lowongan pekerjaan berikut",
  "input": "Posisi: [Pekerjaan], Deskripsi: [Deskripsi]",
  "output": "Level: [Level], Industri: [Industri], Skills: [Skillset]"
}
```

## Catatan:
- Implementasi export scripts akan ditambahkan setelah cleaning pipeline stabil
- Fokus pada format yang kompatibel dengan framework ML populer
- Pertimbangkan kompresі untuk dataset besar
