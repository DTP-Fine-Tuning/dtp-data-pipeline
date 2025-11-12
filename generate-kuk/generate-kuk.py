import os, re, argparse
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

# ---------- Utilities ----------
def clean_text(s: str) -> str:
    if pd.isna(s): 
        return ""
    s = str(s).lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def get_col_case_insensitive(df: pd.DataFrame, candidates) -> str | None:
    lower_map = {c.lower(): c for c in df.columns}
    for name in candidates:
        if name.lower() in lower_map:
            return lower_map[name.lower()]
    return None

def require_title_col(kuk_df: pd.DataFrame) -> str:
    # Prioritaskan berbagai kemungkinan nama kolom judul
    title = get_col_case_insensitive(
        kuk_df, 
        ["judul_kuk","judul kuk","judul","title_kuk","title"]
    )
    if title is None:
        raise ValueError(
            "Tidak ditemukan kolom judul KUK. "
            "Pastikan ada salah satu: judul_kuk / 'Judul KUK' / judul / title_kuk / title"
        )
    return title

def build_kuk_text(kuk_df: pd.DataFrame) -> pd.Series:
    # Gabungkan semua kolom KUK agar representasi kaya (untuk vectorizer)
    return kuk_df.astype(str).apply(lambda r: " ".join(r.values.tolist()), axis=1).apply(clean_text)

def build_talent_text(tdf: pd.DataFrame) -> pd.Series:
    # Gunakan SEMUA kolom teks yang disepakati
    cols = ["pelatihan","sertifikasi","pengalaman_kerja_jabatan","deskripsi_pekerjaan","keterampilan"]
    for c in cols:
        if c not in tdf.columns:
            tdf[c] = ""
    return (
        tdf["pelatihan"].fillna("") + " " +
        tdf["sertifikasi"].fillna("") + " " +
        tdf["pengalaman_kerja_jabatan"].fillna("") + " " +
        tdf["deskripsi_pekerjaan"].fillna("") + " " +
        tdf["keterampilan"].fillna("")
    ).apply(clean_text)

# ---------- Core ----------
def main(kuk_csv, talent_csv, out_csv, max_features=5000, ngram_max=2, batch_size=150):
    # Load
    kuk_df = pd.read_csv(kuk_csv)
    talent_df = pd.read_csv(talent_csv)

    # Pastikan kolom judul KUK ada
    judul_col = require_title_col(kuk_df)

    # Siapkan teks
    kuk_df["kuk_text"] = build_kuk_text(kuk_df)
    talent_df["profil_talenta_text"] = build_talent_text(talent_df)

    # Vectorizer (fit pada KUK -> stabil & cepat)
    vectorizer = TfidfVectorizer(
        max_features=max_features,
        ngram_range=(1, ngram_max),
        norm="l2"
    )
    X_kuk = vectorizer.fit_transform(kuk_df["kuk_text"])
    X_kuk_T = X_kuk.T  # pre-transpose

    # Batch scoring
    n = len(talent_df)
    labels_judul, scores = [], []
    for start in range(0, n, batch_size):
        end = min(start + batch_size, n)
        batch_txt = talent_df["profil_talenta_text"].iloc[start:end].tolist()
        X_tal = vectorizer.transform(batch_txt)
        sim = X_tal @ X_kuk_T                       # (b x F) @ (F x m) -> (b x m)
        best_idx = sim.argmax(axis=1).A1
        best_sc = np.array([sim[i, j] for i, j in enumerate(best_idx)])
        labels_judul.extend(kuk_df.iloc[best_idx][judul_col].astype(str).tolist())
        scores.extend(best_sc.round(6).tolist())

    # Output kolom judul sebagai label
    talent_df["label_KUK_judul"] = labels_judul
    talent_df["label_KUK_score"] = scores

    # Simpan
    talent_df.to_csv(out_csv, index=False)
    print(f"✅ Selesai. Judul KUK tersimpan di kolom 'label_KUK_judul'.")
    print(f"   File: {out_csv}")
    print(f"   Kolom judul yang dipakai: {judul_col}")
    print(f"   Parameter: max_features={max_features}, ngram_max={ngram_max}, batch_size={batch_size}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--kuk_csv", default="kuk_tik_combined.csv")
    ap.add_argument("--talent_csv", default="data_sintetis_diploy.csv")
    ap.add_argument("--out_csv", default="data_sintetis_diploy_labeled.csv")
    ap.add_argument("--max_features", type=int, default=5000)
    ap.add_argument("--ngram_max", type=int, default=2)
    ap.add_argument("--batch_size", type=int, default=150)
    args = ap.parse_args()
    main(**vars(args))