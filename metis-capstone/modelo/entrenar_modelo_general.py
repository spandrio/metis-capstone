"""Entrena el modelo general de Metis a partir de los CSV crudos de Apify.

Uso:  python entrenar_modelo_general.py salida.pickle rubro=archivo1.csv,archivo2.csv [rubro2=...]
Ejemplo: python entrenar_modelo_general.py modelo_general.pickle "Seguridad electrónica=cctv.csv,wifi.csv"
"""
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import cross_val_score, train_test_split

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "actor" / "src"))
from metis_core import FEATURES, metricas_negocio, preparar, target_vende_mucho  # noqa: E402


def cargar(args):
    partes = []
    for a in args:
        rubro, archivos = a.split("=", 1)
        crudo = pd.concat([pd.read_csv(f, low_memory=False) for f in archivos.split(",")], ignore_index=True)
        df = metricas_negocio(preparar(crudo, rubro))
        df["vende_mucho"] = target_vende_mucho(df)
        partes.append(df)
    return pd.concat(partes, ignore_index=True)


def main():
    salida, *rubros = sys.argv[1:]
    df = cargar(rubros)
    X, y = df[FEATURES], df["vende_mucho"]
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    modelo = RandomForestClassifier(n_estimators=200, max_depth=6, min_samples_leaf=5,
                                    class_weight="balanced", random_state=42, n_jobs=-1)
    modelo.fit(X_tr, y_tr)
    pred = modelo.predict(X_te)
    m = {
        "filas": int(len(df)),
        "rubros": sorted(df["rubro"].unique().tolist()),
        "pct_vende_mucho": round(float(y.mean() * 100), 1),
        "accuracy_train": round(float(accuracy_score(y_tr, modelo.predict(X_tr))), 4),
        "accuracy_cv": round(float(cross_val_score(modelo, X_tr, y_tr, cv=5).mean()), 4),
        "accuracy_test": round(float(accuracy_score(y_te, pred)), 4),
        "precision": round(float(precision_score(y_te, pred)), 4),
        "recall": round(float(recall_score(y_te, pred)), 4),
        "f1": round(float(f1_score(y_te, pred)), 4),
        "matriz_confusion": confusion_matrix(y_te, pred).tolist(),
        "importancias": dict(sorted(zip(FEATURES, np.round(modelo.feature_importances_, 4).tolist()), key=lambda kv: -kv[1])),
    }
    m["dif_train_cv"] = round(m["accuracy_train"] - m["accuracy_cv"], 4)
    modelo.fit(X, y)  # modelo final con todos los datos
    with open(salida, "wb") as f:
        pickle.dump({"modelo": modelo, "features": FEATURES, "metricas": m,
                     "versiones": {"scikit-learn": sklearn.__version__, "pandas": pd.__version__, "numpy": np.__version__}}, f)
    print(json.dumps(m, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
