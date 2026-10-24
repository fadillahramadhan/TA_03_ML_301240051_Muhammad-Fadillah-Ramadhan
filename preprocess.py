"""
preprocess.py - Fungsi pra-pemrosesan bersama (dipakai train.py, notebook, dan app.py)
agar transformasi saat pelatihan dan saat prediksi PERSIS sama.
"""
import numpy as np
import pandas as pd

TARGET = "default"

NUMERIC = (
    ["LIMIT_BAL", "AGE"]
    + [f"PAY_{i}" for i in range(1, 7)]
    + [f"BILL_AMT{i}" for i in range(1, 7)]
    + [f"PAY_AMT{i}" for i in range(1, 7)]
)
# Dummy (baseline: Laki-laki, Pascasarjana, Menikah)
DUMMY = [
    "SEX_Perempuan",
    "EDU_Sarjana", "EDU_SMA", "EDU_Lainnya",
    "MARRIAGE_Lajang", "MARRIAGE_Lainnya",
]
FEATURES = NUMERIC + DUMMY

LABELS = {
    "LIMIT_BAL": "Batas kredit", "AGE": "Usia",
    "SEX_Perempuan": "Jenis kelamin perempuan",
    "EDU_Sarjana": "Pendidikan sarjana", "EDU_SMA": "Pendidikan SMA",
    "EDU_Lainnya": "Pendidikan lainnya",
    "MARRIAGE_Lajang": "Status lajang", "MARRIAGE_Lainnya": "Status pernikahan lainnya",
}
for i in range(1, 7):
    LABELS[f"PAY_{i}"] = f"Tunggakan bulan ke-{i}"
    LABELS[f"BILL_AMT{i}"] = f"Tagihan bulan ke-{i}"
    LABELS[f"PAY_AMT{i}"] = f"Pembayaran bulan ke-{i}"


def load_raw(path):
    """Membaca CSV dari beberapa varian (Kaggle UCI_Credit_Card.csv / mirror PyCaret)."""
    df = pd.read_csv(path)
    df = df.rename(columns={
        "PAY_0": "PAY_1",
        "default.payment.next.month": TARGET,
        "default payment next month": TARGET,
    })
    if "ID" in df.columns:
        df = df.drop(columns=["ID"])
    return df


def clean(df):
    """Merapikan kode kategori yang tidak terdokumentasi."""
    df = df.copy()
    df["EDUCATION"] = df["EDUCATION"].replace({0: 4, 5: 4, 6: 4})  # 4 = lainnya
    df["MARRIAGE"] = df["MARRIAGE"].replace({0: 3})                 # 3 = lainnya
    return df


def build_features(df):
    """DataFrame mentah (kode kategori asli) -> matriks fitur FEATURES (belum di-scale)."""
    df = clean(df)
    X = pd.DataFrame(index=df.index)
    for c in NUMERIC:
        X[c] = pd.to_numeric(df[c])
    # Kode PAY_x: -2/-1/0 sama-sama berarti TIDAK ada tunggakan; 1..9 = lama tunggakan (bulan).
    # Diubah menjadi "bulan tunggakan" agar hubungan dengan risiko monoton (cocok untuk model linear).
    for i in range(1, 7):
        X[f"PAY_{i}"] = X[f"PAY_{i}"].clip(lower=0)
    X["SEX_Perempuan"] = (df["SEX"] == 2).astype(int)
    X["EDU_Sarjana"] = (df["EDUCATION"] == 2).astype(int)
    X["EDU_SMA"] = (df["EDUCATION"] == 3).astype(int)
    X["EDU_Lainnya"] = (df["EDUCATION"] == 4).astype(int)
    X["MARRIAGE_Lajang"] = (df["MARRIAGE"] == 2).astype(int)
    X["MARRIAGE_Lainnya"] = (df["MARRIAGE"] == 3).astype(int)
    return X[FEATURES]
