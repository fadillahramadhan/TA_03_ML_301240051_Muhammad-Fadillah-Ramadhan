"""
app.py - Aplikasi web Flask: Prediksi Risiko Gagal Bayar Kartu Kredit (Regresi Logistik)
Lokal      : python app.py
Produksi   : gunicorn app:app
"""
import json
import os

import joblib
import pandas as pd
from flask import Flask, jsonify, render_template, request

from preprocess import FEATURES, LABELS, NUMERIC, build_features

BASE = os.path.dirname(os.path.abspath(__file__))
M = lambda *p: os.path.join(BASE, "model", *p)

app = Flask(__name__)
model = joblib.load(M("model_logreg.joblib"))
scaler = joblib.load(M("scaler.joblib"))
META = json.load(open(M("meta.json"), encoding="utf-8"))
METRICS = json.load(open(M("metrics.json"), encoding="utf-8"))
THRESHOLD = META["threshold"]
COEF = dict(zip(FEATURES, model.coef_[0]))

# ------------------------------------------------------------ validasi input
RANGES = {  # (min, max, label)
    "LIMIT_BAL": (10_000, 1_000_000, "Batas kredit"),
    "AGE": (18, 100, "Usia"),
}
for i in range(1, 7):
    RANGES[f"PAY_{i}"] = (0, 9, f"Tunggakan bulan ke-{i}")
    RANGES[f"BILL_AMT{i}"] = (-500_000, 2_000_000, f"Tagihan bulan ke-{i}")
    RANGES[f"PAY_AMT{i}"] = (0, 2_000_000, f"Pembayaran bulan ke-{i}")
CATS = {"SEX": {1, 2}, "EDUCATION": {1, 2, 3, 4}, "MARRIAGE": {1, 2, 3}}


def parse(payload):
    row, errors = {}, []
    for k, (lo, hi, label) in RANGES.items():
        try:
            v = float(str(payload.get(k, "")).replace(",", "."))
        except ValueError:
            errors.append(f"{label} harus berupa angka.")
            continue
        if not lo <= v <= hi:
            errors.append(f"{label} harus antara {lo:,} dan {hi:,}.".replace(",", "."))
        row[k] = v
    for k, allowed in CATS.items():
        try:
            v = int(payload.get(k, ""))
        except ValueError:
            v = None
        if v not in allowed:
            errors.append(f"Pilihan {k.lower()} tidak valid.")
        row[k] = v
    return row, errors


def band(p):
    if p < 0.30:
        return "rendah", "Rendah"
    if p < THRESHOLD:
        return "sedang", "Sedang"
    return "tinggi", "Tinggi"


ADVICE = {
    "rendah": "Profil pembayaran sehat. Pengajuan atau perpanjangan limit dapat diproses dengan prosedur standar.",
    "sedang": "Risiko moderat. Pertimbangkan verifikasi tambahan atau pemantauan berkala sebelum menaikkan limit.",
    "tinggi": "Risiko tinggi. Disarankan review manual, penurunan eksposur, atau program pengingat dan restrukturisasi dini.",
}


def predict(row):
    X = build_features(pd.DataFrame([row]))
    Xs = X.copy()
    Xs[NUMERIC] = scaler.transform(X[NUMERIC])
    Xs = Xs[FEATURES]
    p = float(model.predict_proba(Xs)[0, 1])
    contrib = {f: float(COEF[f] * Xs.iloc[0][f]) for f in FEATURES}
    top = sorted(contrib.items(), key=lambda kv: abs(kv[1]), reverse=True)[:5]
    key, name = band(p)
    risky = p >= THRESHOLD
    return {
        "probability": round(p, 4),
        "label": "Berisiko Gagal Bayar" if risky else "Tidak Berisiko",
        "risky": risky,
        "band": key,
        "band_label": name,
        "advice": ADVICE[key],
        "threshold": THRESHOLD,
        "factors": [
            {"name": LABELS[f], "impact": round(v, 3),
             "direction": "naik" if v > 0 else "turun"}
            for f, v in top if abs(v) > 0.005
        ],
    }


# ------------------------------------------------------------------- routes
@app.route("/")
def index():
    return render_template("index.html", m=METRICS)


@app.route("/api/predict", methods=["POST"])
def api_predict():
    payload = request.get_json(silent=True) or request.form.to_dict()
    row, errors = parse(payload)
    if errors:
        return jsonify(ok=False, errors=errors), 400
    return jsonify(ok=True, **predict(row))


@app.route("/health")
def health():
    return jsonify(status="ok")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
