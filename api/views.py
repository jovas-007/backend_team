# api/views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
import pandas as pd
import numpy as np

def health(_request):
    return JsonResponse({"status": "ok"})

# ---------- helpers ----------
def _read_csv_to_df(django_file):
    django_file.seek(0)
    try:
        # sep=None + engine="python" intenta detectar separador
        df = pd.read_csv(django_file, sep=None, engine="python", low_memory=False)
    except Exception:
        django_file.seek(0)
        df = pd.read_csv(django_file, low_memory=False)
    return df

def _json_num(v):
    if pd.isna(v): return None
    if isinstance(v, (np.floating, float)): return float(v)
    if isinstance(v, (np.integer, int)):   return int(v)
    return v

def _build_payload(df: pd.DataFrame) -> dict:
    # ---------- Nulos por columna ----------
    null_counts = df.isna().sum()
    nulos_labels = [str(c) for c in null_counts.index]
    nulos_values = [int(v) for v in null_counts.values]

    # ---------- Duplicados por columna ----------
    dup_counts = {}
    dup_percents = {}
    for col in df.columns:
        s = df[col].dropna()
        total = len(s)
        if total == 0:
            dup_counts[col] = 0
            dup_percents[col] = 0.0
            continue
        vc = s.value_counts()
        # Cuenta de celdas que pertenecen a valores repetidos (todas las ocurrencias de valores con freq > 1)
        dup_count = int(vc[vc > 1].sum())
        dup_percent = round((dup_count / total) * 100, 2)
        dup_counts[col] = dup_count
        dup_percents[col] = dup_percent

    # ---------- Duplicados de FILA (totales) ----------
    dup_rows = int(df.duplicated().sum())
    unique_rows = int(len(df) - dup_rows)

    # ---------- Estadísticos numéricos ----------
    num = df.select_dtypes(include="number")
    cols = [str(c) for c in num.columns]

    means   = {c: _json_num(v) for c, v in num.mean(numeric_only=True).items()}
    medians = {c: _json_num(v) for c, v in num.median(numeric_only=True).items()}
    stds    = {c: _json_num(v) for c, v in num.std(numeric_only=True).items()}
    counts  = {c: int(v)       for c, v in num.count().items()}
    mins    = {c: _json_num(v) for c, v in num.min(numeric_only=True).items()}
    maxs    = {c: _json_num(v) for c, v in num.max(numeric_only=True).items()}

    metrics = ["count", "mean", "median", "std", "min", "max"]
    values = [
        [counts.get(c)  for c in cols],
        [means.get(c)   for c in cols],
        [medians.get(c) for c in cols],
        [stds.get(c)    for c in cols],
        [mins.get(c)    for c in cols],
        [maxs.get(c)    for c in cols],
    ]
    stats_table = {"columns": cols, "metrics": metrics, "values": values}
    stats_for_chart = {"labels": cols, "values": [means.get(c) for c in cols]}

    # ---------- Otras (pie de filas únicas vs duplicadas) ----------
    otras = {"labels": ["Únicas", "Duplicadas"], "values": [unique_rows, dup_rows]}

    # ---------- Respuesta completa ----------
    return {
        "columns": [str(c) for c in df.columns],
        "rows": int(len(df)),

        "nulos": {"labels": nulos_labels, "values": nulos_values},

        "dupes": {"unique": unique_rows, "duplicates": dup_rows},
        "dupes_by_column": {
            "labels": list(dup_counts.keys()),
            "counts": list(dup_counts.values()),
            "percent": list(dup_percents.values())
        },

        "stats": stats_for_chart,
        "statsTable": stats_table,
        "otras": otras
    }

# ---------- endpoint ----------
@csrf_exempt
@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def upload_csv(request):
    """
    Recibe form-data con clave 'csv_file'.
    Devuelve métricas para graficar: nulos, duplicados y estadísticas.
    """
    f = request.FILES.get("csv_file")
    if not f:
        return JsonResponse({"detail": "Falta el archivo 'csv_file'."}, status=400)

    df = _read_csv_to_df(f)
    payload = _build_payload(df)
    return JsonResponse(payload, safe=False)
