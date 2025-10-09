# Data Raw

Folder ini digunakan untuk menyimpan dataset mentah (belum diproses).

## File yang tersedia:

### 1. `PON TIK FIX - Sheet1.csv`
- **Deskripsi**: Data referensi okupasi dan level pekerjaan dari PON TIK
- **Format**: CSV dengan encoding latin-1
- **Kolom utama**: OKUPASI, LEVEL
- **Fungsi**: Digunakan untuk mapping okupasi ke level pekerjaan dalam proses imputasi

### 2. `Data Lowongan Pekerjaan 9001-12057 - Sheet1.xlsx`
- **Deskripsi**: Dataset utama lowongan pekerjaan (±12K baris)
- **Format**: Excel (.xlsx)
- **Kolom utama**: Pekerjaan, Deskripsi Pekerjaan, Okupasi, Level Pekerjaan, Industri, Spesial Info, Skillset, Tools, Status Pekerjaan
- **Fungsi**: Data utama yang akan dibersihkan dan diproses

## Catatan:
- Pastikan file berada di direktori ini sebelum menjalankan pipeline
- Jangan edit file asli, gunakan copy jika perlu modifikasi manual
