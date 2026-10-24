"""
train.py - EDA, pra-pemrosesan, SMOTE, pelatihan Regresi Logistik, evaluasi, dan penyimpanan model.
Studi kasus : Prediksi risiko gagal bayar kartu kredit (TA-03)
Dataset     : UCI / Kaggle "Default of Credit Card Clients" (data/credit.csv)
Jalankan    : python train.py
"""
import json
import os

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from imblearn.over_sampling import SMOTENC
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, auc, classification_report,
                             confusion_matrix, f1_score, precision_score,
                             recall_score, roc_auc_score, roc_curve)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from preprocess import DUMMY, FEATURES, LABELS, NUMERIC, TARGET, build_features, clean, load_raw

DATA = os.environ.get("DATA_PATH", os.path.join("data", "credit.csv"))
IMG = os.path.join("static", "img")
os.makedirs(IMG, exist_ok=True)
os.makedirs("model", exist_ok=True)
SEED = 42
THRESHOLD = 0.5

IND, ROSE, SLATE = "#4f46e5", "#e11d48", "#64748b"
sns.set_theme(style="whitegrid", rc={"axes.edgecolor": "#cbd5e1", "grid.color": "#e2e8f0"})


def save(name):
    plt.tight_layout()
    plt.savefig(os.path.join(IMG, name), dpi=140, transparent=False, facecolor="white")
    plt.close()


# ------------------------------------------------------------------- 1. DATA
df = load_raw(DATA)
n_awal = len(df)
n_missing = int(df.isna().sum().sum())
n_dup = int(df.duplicated().sum())
df = df.drop_duplicates().reset_index(drop=True)
df = clean(df)
print(f"Data awal {n_awal}, missing {n_missing}, duplikat {n_dup}, akhir {len(df)}")

y_all = df[TARGET]
rate = float(y_all.mean())
print(f"Proporsi gagal bayar: {rate:.3%}")

# ------------------------------------------------------------------- 2. EDA
fig, ax = plt.subplots(figsize=(5.2, 4))
cnt = y_all.value_counts().sort_index()
bars = ax.bar(["Tidak gagal bayar (0)", "Gagal bayar (1)"], cnt.values, color=[IND, ROSE], width=.55)
for b, v in zip(bars, cnt.values):
    ax.text(b.get_x() + b.get_width() / 2, v + 200, f"{v:,}\n({v/len(df):.1%})".replace(",", "."),
            ha="center", fontsize=10)
ax.set_ylim(0, cnt.max() * 1.18)
ax.set_title("Distribusi Variabel Target")
ax.set_ylabel("Jumlah nasabah")
save("eda_target.png")

fig, ax = plt.subplots(figsize=(7, 4))
g = df.groupby("PAY_1")[TARGET].agg(["mean", "size"]).reset_index()
g = g[g["size"] >= 20]
ax.bar(g["PAY_1"].astype(str), g["mean"] * 100, color=IND)
ax.axhline(rate * 100, color=ROSE, ls="--", label=f"Rata-rata {rate:.1%}")
ax.set_xlabel("PAY_1 (-2/-1/0 = tanpa tunggakan; 1+ = bulan tunggakan)", fontsize=9)
ax.set_ylabel("% gagal bayar")
ax.set_title("Tingkat Gagal Bayar menurut Status Pembayaran Terakhir")
ax.legend()
save("eda_pay1.png")

fig, axes = plt.subplots(1, 3, figsize=(11, 3.6), sharey=True)
maps = {
    "SEX": {1: "Laki-laki", 2: "Perempuan"},
    "EDUCATION": {1: "Pascasarjana", 2: "Sarjana", 3: "SMA", 4: "Lainnya"},
    "MARRIAGE": {1: "Menikah", 2: "Lajang", 3: "Lainnya"},
}
for ax, (col, mp) in zip(axes, maps.items()):
    t = df.groupby(col)[TARGET].mean().rename(index=mp) * 100
    ax.bar(t.index, t.values, color=IND)
    ax.axhline(rate * 100, color=ROSE, ls="--")
    ax.set_title(col)
    ax.tick_params(axis="x", rotation=20)
axes[0].set_ylabel("% gagal bayar")
save("eda_kategori.png")

fig, ax = plt.subplots(figsize=(6.5, 4.6))
dfb = df.copy()
dfb["Kelompok"] = np.where(dfb[TARGET] == 1, "Gagal bayar", "Tidak gagal bayar")
sns.boxplot(data=dfb, x="Kelompok", y="LIMIT_BAL", palette=[IND, ROSE],
            hue="Kelompok", legend=False, ax=ax, showfliers=False)
ax.set_ylabel("Batas kredit (NT$)")
ax.set_xlabel("")
ax.set_title("Batas Kredit menurut Status Gagal Bayar")
save("eda_limit.png")

Xraw = build_features(df)
corr = pd.concat([Xraw, y_all], axis=1).corr()[TARGET].drop(TARGET).sort_values()
top = pd.concat([corr.head(5), corr.tail(8)])
fig, ax = plt.subplots(figsize=(7, 4.4))
ax.barh([LABELS[i] for i in top.index], top.values, color=[ROSE if v > 0 else IND for v in top.values])
ax.set_title("Korelasi Fitur dengan Gagal Bayar (Pearson)")
save("eda_korelasi.png")

# ----------------------------------------------------- 3. SPLIT, SCALE, SMOTE
X = Xraw
y = y_all
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=SEED
)

scaler = StandardScaler()
Xtr = X_train.copy()
Xte = X_test.copy()
Xtr[NUMERIC] = scaler.fit_transform(X_train[NUMERIC])   # fit hanya pada data latih
Xte[NUMERIC] = scaler.transform(X_test[NUMERIC])

# SMOTE-NC: menjaga kolom dummy tetap bernilai 0/1 (SMOTE biasa menghasilkan nilai pecahan)
cat_idx = [Xtr.columns.get_loc(c) for c in DUMMY]
sm = SMOTENC(categorical_features=cat_idx, random_state=SEED)
Xtr_sm, ytr_sm = sm.fit_resample(Xtr, y_train)           # SMOTE hanya pada data latih
print("Latih sebelum SMOTE:", y_train.value_counts().to_dict(),
      "| sesudah:", pd.Series(ytr_sm).value_counts().to_dict())


# ---------------------------------------------------------------- 4. MODEL
def evaluate(model, name, thr=THRESHOLD):
    p = model.predict_proba(Xte)[:, 1]
    pred = (p >= thr).astype(int)
    return {
        "nama": name,
        "accuracy": accuracy_score(y_test, pred),
        "precision": precision_score(y_test, pred, zero_division=0),
        "recall": recall_score(y_test, pred),
        "f1": f1_score(y_test, pred),
        "auc": roc_auc_score(y_test, p),
    }


base = LogisticRegression(max_iter=2000, random_state=SEED).fit(Xtr, y_train)
cw = LogisticRegression(max_iter=2000, random_state=SEED, class_weight="balanced").fit(Xtr, y_train)
model = LogisticRegression(max_iter=2000, random_state=SEED).fit(Xtr_sm, ytr_sm)  # model final (SMOTE)

perbandingan = [
    evaluate(base, "Tanpa penyeimbangan"),
    evaluate(cw, "class_weight='balanced'"),
    evaluate(model, "SMOTE (model final)"),
]
print(pd.DataFrame(perbandingan).round(4).to_string(index=False))

proba = model.predict_proba(Xte)[:, 1]
pred = (proba >= THRESHOLD).astype(int)
cm = confusion_matrix(y_test, pred)
tn, fp, fn, tp = [int(v) for v in cm.ravel()]
rep = classification_report(y_test, pred, target_names=["Tidak gagal bayar", "Gagal bayar"],
                            output_dict=True)
final = perbandingan[2]
print(classification_report(y_test, pred, target_names=["Tidak gagal bayar", "Gagal bayar"]))
print("Confusion matrix:", cm.tolist(), "| AUC:", round(final["auc"], 4))

# Confusion matrix
fig, ax = plt.subplots(figsize=(5.4, 4.6))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", cbar=False, ax=ax, annot_kws={"size": 16},
            xticklabels=["Tidak berisiko", "Berisiko"], yticklabels=["Tidak gagal bayar", "Gagal bayar"])
ax.set_xlabel("Prediksi")
ax.set_ylabel("Aktual")
ax.set_title("Confusion Matrix (data uji)")
save("model_cm.png")

# ROC
fpr, tpr, _ = roc_curve(y_test, proba)
fig, ax = plt.subplots(figsize=(5.4, 4.6))
ax.plot(fpr, tpr, color=IND, lw=2.4, label=f"Regresi Logistik (AUC = {final['auc']:.3f})")
ax.plot([0, 1], [0, 1], ls="--", color=SLATE, label="Tebakan acak")
ax.fill_between(fpr, tpr, alpha=.08, color=IND)
ax.set_xlabel("False Positive Rate")
ax.set_ylabel("True Positive Rate (Recall)")
ax.set_title("Kurva ROC")
ax.legend(loc="lower right")
save("model_roc.png")

# Trade-off threshold
rows = []
for t in np.arange(0.2, 0.81, 0.05):
    pr = (proba >= t).astype(int)
    rows.append({"threshold": round(float(t), 2),
                 "precision": float(precision_score(y_test, pr, zero_division=0)),
                 "recall": float(recall_score(y_test, pr)),
                 "f1": float(f1_score(y_test, pr)),
                 "fp": int(((pr == 1) & (y_test == 0)).sum()),
                 "fn": int(((pr == 0) & (y_test == 1)).sum())})
th = pd.DataFrame(rows)
fig, ax = plt.subplots(figsize=(6.4, 4.4))
ax.plot(th["threshold"], th["precision"], color=IND, lw=2.2, label="Precision")
ax.plot(th["threshold"], th["recall"], color=ROSE, lw=2.2, label="Recall")
ax.plot(th["threshold"], th["f1"], color="#059669", lw=2.2, label="F1-Score")
ax.axvline(THRESHOLD, color=SLATE, ls="--")
ax.set_xlabel("Ambang batas (threshold)")
ax.set_ylabel("Skor")
ax.set_title("Trade-off Precision vs Recall")
ax.legend()
save("model_threshold.png")

# Koefisien
coef = pd.DataFrame({"fitur": FEATURES, "koef": model.coef_[0]})
coef["odds_ratio"] = np.exp(coef["koef"])
coef["label"] = coef["fitur"].map(LABELS)
coef = coef.reindex(coef["koef"].abs().sort_values(ascending=False).index)
t10 = coef[coef["fitur"].isin(NUMERIC)].head(10).iloc[::-1]
fig, ax = plt.subplots(figsize=(7, 4.4))
ax.barh(t10["label"], t10["koef"], color=[ROSE if v > 0 else IND for v in t10["koef"]])
ax.axvline(0, color="#334155", lw=.8)
ax.set_title("10 Koefisien Numerik Terbesar (fitur terstandarisasi)")
save("model_koefisien.png")

# ---------------------------------------------------------- 5. PERSISTENCE
joblib.dump(model, os.path.join("model", "model_logreg.joblib"))
joblib.dump(scaler, os.path.join("model", "scaler.joblib"))

meta = {
    "features": FEATURES,
    "numeric": NUMERIC,
    "threshold": THRESHOLD,
    "scaler_mean": dict(zip(NUMERIC, scaler.mean_.tolist())),
    "scaler_scale": dict(zip(NUMERIC, scaler.scale_.tolist())),
}
json.dump(meta, open(os.path.join("model", "meta.json"), "w"), indent=2)

metrics = {
    "n_awal": n_awal, "n_missing": n_missing, "n_dup": n_dup, "n_akhir": int(len(df)),
    "rate_default": rate,
    "n_default": int(y_all.sum()), "n_tidak": int((y_all == 0).sum()),
    "n_train": int(len(X_train)), "n_test": int(len(X_test)),
    "n_train_smote": int(len(ytr_sm)),
    "train_default_before": int(y_train.sum()), "train_tidak_before": int((y_train == 0).sum()),
    "threshold": THRESHOLD,
    "perbandingan": perbandingan,
    "final": final,
    "cm": {"tn": tn, "fp": fp, "fn": fn, "tp": tp},
    "report": rep,
    "threshold_table": th.round(4).to_dict(orient="records"),
    "coef": coef.round(4)[["fitur", "label", "koef", "odds_ratio"]].to_dict(orient="records"),
    "intercept": float(model.intercept_[0]),
    "corr_pay1": float(corr["PAY_1"]),
    "rate_by_pay1": df.groupby("PAY_1")[TARGET].agg(["mean", "size"]).round(4).reset_index()
                      .to_dict(orient="records"),
}
json.dump(metrics, open(os.path.join("model", "metrics.json"), "w"), indent=2, default=float)
print("Model, scaler, meta, metrics tersimpan di model/")
