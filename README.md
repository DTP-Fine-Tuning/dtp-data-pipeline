# DTP Data Pipeline Repository

Pipeline ini dirancang untuk **membersihkan, memproses, dan menyiapkan dataset** dalam skala besar (±40K baris) untuk digunakan pada proses **Supervised Fine-Tuning (SFT)** dan **Direct Preference Optimization (DPO)**.

---

## Fitur Utama
- Pembersihan data (duplicate removal, normalisasi whitespace, filter baris kosong).
- Preprocessing format standar: `instruction`, `input`, `output`.
- Validasi panjang teks & encoding.
- Splitting dataset: train / validation / test.
- Ekspor dalam format JSON / Parquet / CSV.

---

## Struktur dalam bentuk Tree
```
dtp-data-pipeline/
│
├── data_raw/             # Data mentah sebelum diproses
├── data_processed/       # Data hasil cleaning & preprocessing
├── scripts/              # Script Python untuk pipeline
│   ├── clean_data.py
│   ├── preprocess.py
│   ├── split_dataset.py
│   └── export.py
├── configs/              # Config YAML untuk pipeline
│   └── default_config.yaml
├── docs/                 # Dokumentasi pipeline hasil pengerjaan disini
│   ├── data_format.md
│   └── pipeline_overview.md
├── tests/                # Unit tests untuk pipeline
│   └── test_clean_data.py
├── requirements.txt      # Dependensi Python
├── git-set-me.sh         # Script untuk set identitas Git per user
└── README.md             # Dokumentasi utama repo ini
```

---

## Instalasi
### 1. Clone Repo (Gaperlu diclone karena udah diclone, kecuali maw taruh dilocal)
```bash
git clone https://github.com/org/llm-data-pipeline.git
cd dtp-data-pipeline
```

### 2. Buat Virtual Environment (bebas dari temen-temen)
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependensi
```bash
pip install -r requirements.txt
```

---

## Cara Menjalankan Pipeline (ini formalnya aja karena sesuai direktori)
### 1. Cleaning
```bash
python scripts/clean_data.py --input data_raw/raw.json --output data_processed/cleaned.json
```

### 2. Preprocessing
```bash
python scripts/preprocess.py --input data_processed/cleaned.json --output data_processed/preprocessed.json
```

### 3. Splitting
```bash
python scripts/split_dataset.py --input data_processed/preprocessed.json --train 0.8 --val 0.1 --test 0.1
```

### 4. Export
```bash
python scripts/export.py --input data_processed/preprocessed.json --format parquet
```

---

## Dokumentasi Tambahan (Usahakan taruh di direktori docs)
- [Data Format](docs/data_format.md) → Spesifikasi format dataset (instruction/input/output).
- [Pipeline Overview](docs/pipeline_overview.md) → Diagram alur pipeline & penjelasan step.

---

## How to Contribute? kek gini
1. Set identitas Git per repo (Wajib dilakuin):
   ```bash
   ./git-set-me.sh "Nama Lengkap" email@example.com
   ```
2. Buat branch baru untuk fitur/pekerjaan (sesuaikan dengan task temen-temen):
   ```bash
   git checkout -b feature/nama-fitur
   ```
3. Commit & push seperti biasa.

---

