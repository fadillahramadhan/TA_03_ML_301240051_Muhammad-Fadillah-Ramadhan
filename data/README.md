# Dataset

**Default of Credit Card Clients** (Yeh & Lien, 2009; UCI Machine Learning Repository, tersedia di Kaggle).
Target biner `default` (1 = gagal bayar bulan berikutnya). Fitur: LIMIT_BAL, SEX, EDUCATION, MARRIAGE, AGE,
PAY_1..6, BILL_AMT1..6, PAY_AMT1..6.

- `credit.csv` (disertakan): 24.000 baris, 23 fitur + target.
- Memakai versi Kaggle penuh (`UCI_Credit_Card.csv`, 30.000 baris)? Taruh di folder ini, lalu:
  `DATA_PATH=data/UCI_Credit_Card.csv python train.py` (nama kolom disesuaikan otomatis oleh `preprocess.load_raw`).
