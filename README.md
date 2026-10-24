# KreditSense: Prediksi Risiko Gagal Bayar Kartu Kredit (TA-03, Regresi Logistik)

Aplikasi web Flask untuk memprediksi apakah nasabah **Berisiko** atau **Tidak Berisiko** gagal bayar, lengkap dengan skor probabilitas
dan faktor utama yang memengaruhinya. Model: Regresi Logistik + StandardScaler + SMOTE-NC.

## Struktur
| Berkas | Fungsi |
|---|---|
| `preprocess.py` | Pembersihan & pembuatan fitur (dipakai bersama oleh train, notebook, app) |
| `train.py` | EDA, split, scaling, SMOTE-NC, pelatihan, evaluasi, simpan model (Joblib) |
| `notebooks/analisis_risiko_kredit.ipynb` | Notebook analisis lengkap (sudah dieksekusi) |
| `app.py`, `templates/`, `static/` | Aplikasi Flask (UI modern, mode terang/gelap, responsif) |
| `model/` | `model_logreg.joblib`, `scaler.joblib`, `meta.json`, `metrics.json` |
| `build_jurnal_ta3.py` | Membuat laporan DOCX format Jurnal COMPUTING |

## Menjalankan
```bash
pip install -r requirements.txt
python train.py        # opsional: latih ulang (model sudah disertakan)
python app.py          # http://127.0.0.1:5000
```

## Deploy ke Render
1. Push repo ke GitHub (sertakan folder `model/` dan `static/img/`).
2. Render: New > Web Service > pilih repo. Build: `pip install -r requirements.txt`. Start: `gunicorn app:app`.
(Railway: otomatis membaca `Procfile`.)

## API
`POST /api/predict` (JSON) berisi LIMIT_BAL, AGE, SEX, EDUCATION, MARRIAGE, PAY_1..6, BILL_AMT1..6, PAY_AMT1..6. `GET /health` untuk cek status.
