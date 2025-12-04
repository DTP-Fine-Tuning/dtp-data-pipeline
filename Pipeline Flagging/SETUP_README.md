# Setup Pipeline Flagging Dataset Diploy

Panduan lengkap untuk setup dan menjalankan pipeline flagging okupasi TIK menggunakan Qdrant Vector Search dan Google Gemini AI.

---

## 📋 Persyaratan

- **Conda/Miniconda/Anaconda** (akan otomatis install Python 3.12.11)
- **Akses Internet** untuk API Gemini dan Qdrant
- **Dataset Input** yang sudah dipecah per 500 baris (format Excel)
- **API Keys**:
  - Google Gemini API Key
  - Qdrant Cloud URL dan API Key

---

## 🚀 Langkah 1: Install Conda

### macOS (Intel)
```bash
curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh
bash Miniconda3-latest-MacOSX-x86_64.sh
```

### macOS (Apple Silicon/M1/M2)
```bash
curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh
bash Miniconda3-latest-MacOSX-arm64.sh
```

### Linux
```bash
curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
```

### Windows
Download installer dari: https://docs.conda.io/en/latest/miniconda.html

Jalankan installer dan ikuti wizard.

### Verifikasi Instalasi
```bash
# Restart terminal terlebih dahulu
conda --version
```

---

## 🔧 Langkah 2: Setup Conda Environment

### Navigasi ke Folder Project
```bash
cd "/path/to/dtp-data-pipeline/Pipeline Flagging"
```

### Buat Conda Environment
```bash
conda create -n diploy_flagging python=3.12.11 pandas openpyxl numpy -y
```

### Aktivasi Environment
```bash
conda activate diploy_flagging
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

**Dependencies yang akan terinstall:**
- pandas >= 2.2.0
- openpyxl >= 3.1.0
- numpy >= 1.26.0
- qdrant-client >= 1.11.0
- google-generativeai >= 0.8.0
- sentence-transformers >= 3.0.0
- torch >= 2.2.0
- nest-asyncio >= 1.6.0
- tqdm >= 4.65.0
- tenacity >= 8.0.0

---

## 📁 Langkah 3: Persiapan Data

### Struktur Folder
```
Pipeline Flagging/
├── Data Diploy Not Flagged/    # ← Input folder
├── Data Diploy Flagged/         # ← Output folder
├── flagging_dataset_diploy_gemini.ipynb
├── requirements.txt
└── SETUP_README.md
```

### Buat Folder Output (jika belum ada)
```bash
mkdir -p "Data Diploy Flagged"
```

### Format Nama File Input
```
Data Diploy Not Flagged/
├── diploy_unflagged_1-500.xlsx
├── diploy_unflagged_501-1000.xlsx
├── diploy_unflagged_1001-1500.xlsx
└── ...
```

---

## ⚙️ Langkah 4: Konfigurasi

Buka file `flagging_dataset_diploy_gemini.ipynb` dan edit bagian **KONFIGURASI**:

### a. API Key Gemini
```python
API_KEY = "YOUR_GEMINI_API_KEY_HERE"
```
Dapatkan dari: https://makersuite.google.com/app/apikey

### b. Concurrency Setting
```python
CONCURRENCY = 3  # Default: 3 request parallel
```
- **Stabil**: 3 (recommended)
- **Koneksi cepat**: 5-10
- **Sering timeout**: 1-2

### c. File Input/Output
```python
INPUT_FILE  = f"{DRIVE_DATASET_DIR}/Data Diploy Not Flagged/diploy_unflagged_1-500.xlsx"
OUTPUT_FILE = f"{DRIVE_DATASET_DIR}/Data Diploy Flagged/diploy_flagged_gemini_1-500.xlsx"
```

### d. Qdrant Configuration
```python
QDRANT_URL = "YOUR_QDRANT_URL_HERE"
QDRANT_API_KEY = "YOUR_QDRANT_API_KEY_HERE"
QDRANT_COLLECTION = "OKUPASI_SFT_AITF_V2"
```

---

## ▶️ Langkah 5: Menjalankan Pipeline

### 1. Buka Notebook
```bash
# Menggunakan Jupyter Notebook
jupyter notebook flagging_dataset_diploy_gemini.ipynb

# Atau menggunakan VS Code
code flagging_dataset_diploy_gemini.ipynb
```

### 2. Pilih Kernel
- Klik **"Select Kernel"** di pojok kanan atas
- Pilih: **Python 3.12.11 ('diploy_flagging')**

### 3. Edit File Path
Edit cell konfigurasi untuk file yang ingin diproses:
```python
INPUT_FILE  = f"{DRIVE_DATASET_DIR}/Data Diploy Not Flagged/diploy_unflagged_1-500.xlsx"
OUTPUT_FILE = f"{DRIVE_DATASET_DIR}/Data Diploy Flagged/diploy_flagged_gemini_1-500.xlsx"
```

### 4. Jalankan Pipeline
- Run cell utama (cell terakhir dengan `await main()`)
- Atau run all cells

### 5. Monitor Progress
Pipeline akan menampilkan:
- ✅ Progress bar real-time
- ✅ Log status per row
- ✅ Error handling otomatis
- ✅ Auto-save ke output folder

---

## 🔍 Langkah 6: Monitoring & Troubleshooting

### Monitoring Normal
```
📊 Total: 500 baris
⚡ Concurrency: 3

Flagging rows: 100%|████████| 500/500 [25:30<00:00, 3.06s/it]
✅ Selesai! Output: .../diploy_flagged_gemini_1-500.xlsx
```

### ⚠️ Problem: Timeout Error
```bash
[TIMEOUT] Row 123
```
**Solusi:**
```python
# Turunkan concurrency
CONCURRENCY = 2

# Atau naikkan timeout
REQUEST_TIMEOUT = 600  # 10 menit
```

### ⚠️ Problem: JSON Parsing Error
```bash
[ERROR] Row 45: Invalid JSON response
```
**Solusi:**
- Otomatis di-handle dengan fallback
- Row akan memiliki Area_Fungsi dan Level_Okupasi kosong
- Bisa diproses ulang manual jika perlu

### ⚠️ Problem: File Output Kosong (0 baris)
**Solusi:**
```python
# Debug: Cek file input
import pandas as pd
import os

print(os.path.exists(INPUT_FILE))  # Harus True
df = pd.read_excel(INPUT_FILE)
print(f"Rows: {len(df)}")
print(df.head())
```

### ⚠️ Problem: API Quota Exceeded
```bash
[ERROR] 429: Quota exceeded
```
**Solusi:**
- Tunggu reset quota (biasanya per hari)
- Gunakan API key alternatif
- Turunkan `CONCURRENCY` ke 1-2

---

## ✅ Langkah 7: Verifikasi Hasil

### 1. Cek File Output
```bash
ls -lh "Data Diploy Flagged/"
```

### 2. Buka File Excel
Verifikasi kolom baru:
- ✅ `Area_Fungsi` terisi
- ✅ `Level_Okupasi` terisi
- ✅ Jumlah baris = input

### 3. Analisis Statistik
```python
import pandas as pd

df = pd.read_excel("Data Diploy Flagged/diploy_flagged_gemini_1-500.xlsx")

# Distribusi Area Fungsi
print(df['Area_Fungsi'].value_counts())

# Distribusi Level
print(df['Level_Okupasi'].value_counts())

# Non TIK
non_tik = df[df['Area_Fungsi'] == 'Okupasi Non TIK']
print(f"Non TIK: {len(non_tik)} rows")
```

---

## 💡 Tips & Best Practices

| ✅ DO | ❌ DON'T |
|-------|----------|
| Backup data sebelum processing | Interrupt proses di tengah jalan |
| Test dengan sample kecil (10-20 baris) | Processing semua data sekaligus |
| Monitor log untuk error pattern | Ignore error messages |
| Process per batch 500-1000 baris | Set concurrency terlalu tinggi |
| Verifikasi output setelah selesai | Langsung hapus file input |
| Simpan log error | Skip validasi hasil |

---

## ⏱️ Estimasi Waktu

| Jumlah Baris | Concurrency | Waktu Estimasi |
|--------------|-------------|----------------|
| 500 | 3 | 25-40 menit |
| 1,000 | 3 | 50-80 menit |
| 2,000 | 3 | 1.5-3 jam |
| 5,000 | 3 | 4-7 jam |
| 13,594 (full) | 3 | 12-18 jam |

**Catatan**: Waktu per baris ~3-5 detik (tergantung API response time)

---

## 📊 Output Format

### Kolom Input (Existing)
- Jenjang_Pendidikan
- Jurusan
- Judul_Tugas_Akhir
- Bidang_Pelatihan
- Nama_Pelatihan
- Sertifikasi
- Bidang_Sertifikasi
- Posisi_Pekerjaan
- Deskripsi_tugas_dan_tanggung_jawab
- Lama_Bekerja
- Keterampilan

### Kolom Output (New)
- **Area_Fungsi**: Area Fungsi TIK atau "Okupasi Non TIK"
- **Level_Okupasi**: Level 1-9 atau kosong

### Contoh Output
| Area_Fungsi | Level_Okupasi |
|-------------|---------------|
| Sains Data-Kecerdasan Artifisial | 6 |
| Pengembangan Produk Digital | 5 |
| Okupasi Non TIK | |
| Teknologi Dan Infrastruktur | 7 |

---

## 🆘 Contact & Support

### Jika Ada Masalah:

1. **Check Dokumentasi**
   - [Google Gemini API Docs](https://ai.google.dev/docs)
   - [Qdrant Documentation](https://qdrant.tech/documentation/)

2. **Verify Installation**
   ```bash
   conda activate diploy_flagging
   pip list | grep -E "pandas|qdrant|google-generativeai"
   ```

3. **Check Service Status**
   - [Qdrant Cloud Status](https://cloud.qdrant.io)
   - [Google AI Status](https://status.cloud.google.com)

4. **Restart Kernel**
   - Jika ada memory leak atau stuck
   - Kernel → Restart Kernel

5. **Create Issue**
   - Buka issue di repository GitHub
   - Sertakan error log lengkap

---

## 🔐 Security Notes

⚠️ **JANGAN commit API keys ke Git!**

File yang di-ignore (`.gitignore`):
- `*.xlsx` - Data files
- `*.env` - Environment files
- `.ipynb_checkpoints/` - Jupyter checkpoints
- `__pycache__/` - Python cache

**Best Practice:**
```python
# Gunakan environment variable
import os
API_KEY = os.getenv('GEMINI_API_KEY')
QDRANT_API_KEY = os.getenv('QDRANT_API_KEY')
```

---

## 📚 Additional Resources

- [Main README](../README.md) - Project overview
- [SETUP_INSTRUCTIONS.txt](SETUP_INSTRUCTIONS.txt) - Original setup guide
- [requirements.txt](requirements.txt) - Full dependencies list
- [flagging_dataset_diploy_gemini.ipynb](flagging_dataset_diploy_gemini.ipynb) - Main pipeline notebook

---

## 📝 Changelog

### Version 1.0 (December 2025)
- Initial release
- Support untuk 6 Area Fungsi TIK
- Async processing dengan semaphore
- Auto retry mechanism
- Level validation & fallback

---

**Developed by**: DTP Fine-Tuning Team  
**Last Updated**: December 4, 2025  
**Python Version**: 3.12.11  
**License**: Internal Use Only
