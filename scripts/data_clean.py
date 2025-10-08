#!/usr/bin/env python
# coding: utf-8

# In[69]:


import pandas as pd
import numpy as np
import google.generativeai as genai
import os
from dotenv import load_dotenv

# load dot env
env_file_name = "/home/wildanaziz/dtp-data-pipeline/gemini.env"

#fetch api gemini
if load_dotenv(dotenv_path=env_file_name):
    print(f"File{env_file_name} berhasil dimuat..")
else:
    print(f"File {env_file_name} tidak berhasil dimuat..")
    
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(f"API KEY gagal dimuat pada file {env_file_name}..")
    
    
genai.configure(api_key=api_key)

model = genai.GenerativeModel('gemini-2.5-flash-lite')
print(f"konfig berhasil")


# In[70]:


try:
    df_lowongan = pd.read_csv("/home/wildanaziz/dtp-data-pipeline/data_raw/Data Lowongan Pekerjaan 6001-9000 - Sheet1.csv")
    df_pon_tik = pd.read_csv("/home/wildanaziz/dtp-data-pipeline/data_raw/PON TIK FIX - Sheet1.csv")
except FileNotFoundError as e:
    print(f"Error: {e}. Pastikan file CSV berada di direktori yang sama.")
    exit()

missing_values = ["Tidak Ada", "Tidak ada", "-", "", "Not Applicable"]

df_lowongan.replace(missing_values, np.nan, inplace=True)
print("Jumlah missing values awal di beberapa kolom:")
print(df_lowongan[['Level Pekerjaan', 'Industri', 'Spesial Info', 'Skillset', 'Tools']].isnull().sum())


# In[71]:


okupasi_to_level = df_pon_tik.set_index('OKUPASI')['LEVEL'].to_dict()

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

print("\nImputasi selesai")


# In[72]:


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


# In[75]:


df_lowongan.head(100)


# In[76]:


import time
import numpy as np
import pandas as pd

def impute_with_gemini_final(row, column_to_impute):
    if pd.notna(row[column_to_impute]):
        return row[column_to_impute]

    pekerjaan = row['Pekerjaan']
    deskripsi = row['Deskripsi Pekerjaan']

    if pd.isna(pekerjaan) or pd.isna(deskripsi):
        return np.nan
    
    # buat prompt
    prompts = {
        'Industri': f"Berdasarkan pekerjaan '{pekerjaan}' dan deskripsi '{deskripsi}', apa nama industri yang paling sesuai? Berikan satu jawaban singkat saja. Contoh: Computer Software & Networking. Contoh output lain: Konsultasi & Layanan Manajemen",
        'Spesial Info': f"Dari deskripsi pekerjaan '{deskripsi}' untuk posisi '{pekerjaan}', identifikasi special info yang memudahkan dalam mencari pekerjaan sesuai pada bidangnya, Contoh Output: Project Management and Information Technology, atau Contoh Output lain: Web Programmer. Jika tidak ada, tulis 'Tidak ada'. Tolong untuk outputnya berikan jawaban singkat saja.",
        'Skillset': f"Berdasarkan deskripsi '{deskripsi}' untuk posisi '{pekerjaan}', sebutkan 5 skill utama yang dibutuhkan, pisahkan dengan titik koma. Contoh output: Web Development, Data Understanding, Tensorflow, PyTorch",
        'Tools': f"Berdasarkan deskripsi '{deskripsi}' untuk posisi '{pekerjaan}', sebutkan 3 tools/software utama yang digunakan, pisahkan dengan titik koma. Contoh output: Excel, Python, Power BI, MySQL"
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


# In[ ]:


columns_to_impute_gemini = ['Industri', 'Spesial Info', 'Skillset', 'Tools']


for col in columns_to_impute_gemini:
    mask_missing = df_lowongan[col].isnull()
    
    if df_lowongan[col].isnull().any():
        print(f"\nMemulai imputasi untuk {mask_missing.sum()} baris di kolom: {col}...")

        df_lowongan.loc[mask_missing, col] = df_lowongan[mask_missing].apply(
            lambda row: impute_with_gemini_final(row, col),
            axis=1
        )
        
        nama_file_sementara = f'/home/wildanaziz/dtp-data-pipeline/data_processed/6001-9000/Temporary/Data_Cleaned_Sementara_Setelah_{col}.csv'
        df_lowongan.to_csv(nama_file_sementara, index=False)
        print(f"Progres disimpan di '{nama_file_sementara}'")
    else:
        print(f"\nMelewati kolom '{col}' karena sudah terisi semua.")

print("\n[FINAL] Menyimpan hasil akhir ke file CSV...")
df_lowongan.to_csv('/home/wildanaziz/dtp-data-pipeline/data_processed/6001-9000/Data_Lowongan_Pekerjaan_Cleaned_6001-9000_Final.csv', index=False)
print("Proses selesai dan file final berhasil disimpan!")

