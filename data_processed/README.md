# Data Processed

Folder ini menyimpan data hasil pembersihan (cleaning) dan preprocessing.

## File yang tersedia:

### 1. `cleaned_data_final.xlsx`
- **Deskripsi**: Hasil akhir pembersihan data menggunakan AI-powered imputation
- **Format**: Excel (.xlsx)
- **Ukuran**: ±12K baris data lowongan pekerjaan yang telah dibersihkan
- **Proses yang dilakukan**:
  - Normalisasi missing values
  - Imputasi Level Pekerjaan menggunakan data referensi PON TIK
  - Kategorisasi level pekerjaan ke 6 kategori standar
  - AI-powered imputasi untuk kolom: Industri, Spesial Info, Skillset, Tools, Status Pekerjaan, Deskripsi Pekerjaan
  
## Struktur Data:
- **Kolom lengkap**: Semua kolom telah diisi dengan metode imputasi yang sesuai
- **Kategori Level Pekerjaan**:
  - Internship/Magang/OJT (Level ≤ 2)
  - Lulusan Baru/Junior/Entry Level/Fresh Graduate (Level 3-4)
  - Associate (Level 5)
  - Mid Senior Level (Level 6)
  - Supervisor/Asisten Manager (Level 7)
  - Direktur/Eksekutif (Level ≥ 8)

## Catatan:
- Data di sini siap untuk digunakan dalam proses lebih lanjut (SFT/DPO)
- File dihasilkan dari script `data_clean.py`
