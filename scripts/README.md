# Scripts

Folder ini berisi script Python untuk menjalankan pipeline data.

## File yang tersedia:

### 1. `data_clean.py`
- **Deskripsi**: Script utama untuk pembersihan dan imputasi data lowongan pekerjaan
- **Input**: 
  - `../data_raw/PON TIK FIX - Sheet1.csv`
  - `../data_raw/Data Lowongan Pekerjaan 9001-12057 - Sheet1.xlsx`
- **Output**: `../data_processed/cleaned_data_final.xlsx`
- **Dependensi**: Gemini API key di file `../gemini.env`

**Fitur utama:**
- Normalisasi missing values
- Imputasi Level Pekerjaan menggunakan data referensi PON TIK
- Kategorisasi level pekerjaan
- AI-powered imputasi menggunakan Gemini API untuk 6 kolom
- Rate limiting (4 detik per request) untuk API stability

**Cara menjalankan:**
```bash
cd scripts
python data_clean.py
```

## Dependensi:
- pandas, numpy, google-generativeai, python-dotenv, openpyxl
- API key Gemini di file `gemini.env`

## Catatan:
- Proses membutuhkan waktu cukup lama (±3-4 jam untuk 12K baris)
- Pastikan koneksi internet stabil untuk API calls
- Script berjalan secara sequential dengan rate limiting
