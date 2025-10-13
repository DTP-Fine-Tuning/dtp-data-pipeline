import pandas as pd
import numpy as np
import google.generativeai as genai
import os
from dotenv import load_dotenv
import time

# load dot env
env_file_name = "../gemini.env"

#fetch api gemini
if load_dotenv(dotenv_path=env_file_name):
    print(f"File {env_file_name} berhasil dimuat..")
else:
    print(f"File {env_file_name} tidak berhasil dimuat..")

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(f"API KEY gagal dimuat pada file {env_file_name}..")


genai.configure(api_key=api_key)

model = genai.GenerativeModel('gemini-2.5-flash-lite')
print(f"konfig berhasil")

try:
    df_pon_tik =  pd.read_csv("../data_raw/PON TIK FIX - Sheet1.csv", encoding='latin-1')
    df_lowongan = pd.read_excel("../data_raw/Data Lowongan Pekerjaan 9001-12057 - Sheet1.xlsx")
except FileNotFoundError as e:
    print(f"Error: {e}. Pastikan file CSV berada di direktori yang sama.")
    exit()
missing_values = ["Tidak Ada", "Tidak ada", "-", "", "Not Applicable"]

df_lowongan.replace(missing_values, np.nan, inplace=True)
print("Jumlah missing values awal di beberapa kolom:")
print(df_lowongan[['Level Pekerjaan', 'Industri', 'Spesial Info', 'Skillset', 'Tools']].isnull().sum())

okupasi_to_level = df_pon_tik.set_index('OKUPASI')['LEVEL'].to_dict()

# fungsi imputasi level pekerjaan
def impute_level_pekerjaan(row):
    if pd.notna(row['Level Pekerjaan']):
        return row['Level Pekerjaan']

    if pd.isna(row['Okupasi']):
        return None

    # clean okupasi row
    okupasi_lowongan = str(row['Okupasi'])
    okupasi_upper = okupasi_lowongan.upper()
    pos_separate = okupasi_upper.find(' - LEVEL')

    if pos_separate != -1:
        okupasi = okupasi_upper[:pos_separate].strip()
    else:
        okupasi = okupasi_upper.strip()

    for okupasi_pon_tik, level in okupasi_to_level.items():
        if okupasi in str(okupasi_pon_tik).upper():
            return level
    return None

df_lowongan['Level Pekerjaan'] = df_lowongan.apply(impute_level_pekerjaan, axis=1)

print("\\Normalisasi Level Pekerjaan selesai")

#pemetaan
def kategorisasi_level(level):
    try:
        level = int(float(level))
        if level <= 2:
            return 'Internship/Magang/OJT'
        elif level <= 4:
            return 'Lulusan Baru/Junior/Entry Level/Fresh Graduate'
        elif level == 5:
            return 'Associate'
        elif level == 6:
            return 'Mid Senior Level'
        elif level == 7:
            return 'Supervisor/Asisten Manager'
        elif level >= 8:
            return 'Direktur/Eksekutif'
        else:
            return np.nan
    except (ValueError, TypeError):
        return level

# categorized
df_lowongan['Level Pekerjaan'] = df_lowongan['Level Pekerjaan'].apply(kategorisasi_level)

print("Kategorisasi 'Level Pekerjaan' selesai.")
print("\nContoh hasil setelah perbaikan:")
print(df_lowongan[['Okupasi', 'Level Pekerjaan']].head())

# fungsi imputasi dengan gemini untuk kolom Industri, Spesial Info, Skillset, Tools
def impute_with_gemini_final(row, column_to_impute):
    if pd.notna(row[column_to_impute]):
        return row[column_to_impute]

    pekerjaan = row['Pekerjaan']
    deskripsi = row['Deskripsi Pekerjaan']

    if pd.isna(pekerjaan) or pd.isna(deskripsi):
        return np.nan

    # buat prompt
    prompts = {
        'Industri': f"Berdasarkan pekerjaan '{pekerjaan}' dan deskripsi '{deskripsi}', apa nama industri yang paling sesuai? Berikan satu jawaban singkat saja. Contoh: Teknologi Informasi.",
        'Spesial Info': f"Dari deskripsi pekerjaan '{deskripsi}' untuk posisi '{pekerjaan}', identifikasi 1-2 kualifikasi khusus yang paling menonjol. Jika tidak ada, tulis 'Tidak ada'. Berikan jawaban singkat.",
        'Skillset': f"Berdasarkan deskripsi '{deskripsi}' untuk posisi '{pekerjaan}', sebutkan 5 skill utama yang dibutuhkan, pisahkan dengan titik koma.",
        'Tools': f"Berdasarkan deskripsi '{deskripsi}' untuk posisi '{pekerjaan}', sebutkan 3 tools/software utama yang digunakan, pisahkan dengan titik koma."
    }

    prompt = prompts.get(column_to_impute)
    if not prompt:
        return np.nan

    try:
        response = model.generate_content(prompt)


        time.sleep(4)

        return response.text.strip()
    except Exception as e:
        print(f"Error pada baris {row.name} untuk kolom '{column_to_impute}': {e}")
        return np.nan

columns_to_impute_gemini = ['Industri', 'Spesial Info', 'Skillset', 'Tools']

# lakukan imputasi untuk kolom Industri, Spesial Info, Skillset, Tools
for col in columns_to_impute_gemini:
    print(f"\nMemulai imputasi penuh untuk kolom: {col} (ini akan memakan waktu)...")
    df_lowongan[col] = df_lowongan.apply(
        lambda row: impute_with_gemini_final(row, col) if pd.isna(row[col]) else row[col],
        axis=1
    )
    print(f"Imputasi untuk kolom '{col}' selesai.")

print("\nProses imputasi menggunakan Gemini telah selesai sepenuhnya.")

# fungsi imputasi dengan gemini untuk kolom Level Pekerjaan, Status Pekerjaan, Tools
def impute_with_gemini_final(row, column_to_impute):
    if pd.notna(row[column_to_impute]):
        return row[column_to_impute]

    pekerjaan = row['Pekerjaan']
    deskripsi = row['Deskripsi Pekerjaan']
    level = row['Level Pekerjaan']

    if pd.isna(pekerjaan) or pd.isna(deskripsi):
        return np.nan

    # buat prompt
    prompts = {
        'Level Pekerjaan': f"Berdasarkan pekerjaan '{pekerjaan}' dan deskripsi '{deskripsi}', apa level pekerjaan yang paling sesuai? Jawaban singkat terdiri dari Associate, Direktur/Eksekutif, Internship/Magang/OJT, Lulusan Baru/Junior/Entry Level/Fresh Graduate, Mid Senior Level, Supervisor/Asisten Manager.",
        'Status Pekerjaan': f"Dari deskripsi pekerjaan '{deskripsi}' untuk posisi '{pekerjaan}', dan level pekerjaan '{level}', apa status pekerjaan yang paling sesuai? Jawaban singkat terdiri dari Full Time, Kontrak/Temporer, Internship, Kasual, Part-Time.",
        'Tools': f"Berdasarkan deskripsi '{deskripsi}' untuk posisi '{pekerjaan}', sebutkan 3 tools/software utama yang digunakan, pisahkan dengan titik koma."
    }

    prompt = prompts.get(column_to_impute)
    if not prompt:
        return np.nan

    try:
        response = model.generate_content(prompt)


        time.sleep(4)

        return response.text.strip()
    except Exception as e:
        print(f"Error pada baris {row.name} untuk kolom '{column_to_impute}': {e}")
        return np.nan

columns_to_impute_gemini = ['Level Pekerjaan', 'Status Pekerjaan', 'Tools']

# lakukan imputasi untuk kolom Level Pekerjaan, Status Pekerjaan, Tools
for col in columns_to_impute_gemini:
    print(f"\nMemulai imputasi penuh untuk kolom: {col} (ini akan memakan waktu)...")
    df_lowongan[col] = df_lowongan.apply(
        lambda row: impute_with_gemini_final(row, col) if pd.isna(row[col]) else row[col],
        axis=1
    )
    print(f"Imputasi untuk kolom '{col}' selesai.")

print("\nProses imputasi menggunakan Gemini telah selesai sepenuhnya.")

# fungsi imputasi dengan gemini untuk kolom Deskripsi Pekerjaan & Industri yang kosong di baris yang sama
def impute_with_gemini_final(row, column_to_impute):
    if pd.notna(row[column_to_impute]):
        return row[column_to_impute]

    pekerjaan = row['Pekerjaan']
    level = row['Level Pekerjaan']
    spesial_info = row['Spesial Info']
    skillset = row['Skillset']
    tools = row['Tools']

    # buat prompt
    prompts = {
        'Deskripsi Pekerjaan': f"Berdasarkan pekerjaan '{pekerjaan}' pada level '{level}',  spesial info '{spesial_info}', skillset '{skillset}', dan tools '{tools}', buatkan deskripsi singkat lowongan pekerjaan untuk posisi/role ini. Jawaban singkat terdiri dari deskripsi lowongan pekerjaan.",
        'Industri': f"Berdasarkan pekerjaan '{pekerjaan}' pada level '{level}',  spesial info '{spesial_info}', skillset '{skillset}', dan tools '{tools}', apa nama industri yang paling sesuai? Berikan satu jawaban singkat saja. Contoh: Teknologi Informasi.",
        }

    prompt = prompts.get(column_to_impute)
    if not prompt:
        return np.nan

    try:
        response = model.generate_content(prompt)


        time.sleep(4)

        return response.text.strip()
    except Exception as e:
        print(f"Error pada baris {row.name} untuk kolom '{column_to_impute}': {e}")
        return np.nan

columns_to_impute_gemini = ['Deskripsi Pekerjaan', 'Industri']

for col in columns_to_impute_gemini:
    print(f"\nMemulai imputasi penuh untuk kolom: {col} (ini akan memakan waktu)...")
    df_lowongan[col] = df_lowongan.apply(
        lambda row: impute_with_gemini_final(row, col) if pd.isna(row[col]) else row[col],
        axis=1
    )
    print(f"Imputasi untuk kolom '{col}' selesai.")

print("\nProses imputasi menggunakan Gemini telah selesai sepenuhnya.")

print("Jumlah missing values akhir di beberapa kolom:")
print(df_lowongan.isnull().sum())
df_lowongan.to_excel("../data_processed/cleaned_data_final.xlsx")
