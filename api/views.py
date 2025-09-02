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
    # Nulos por columna
    null_counts = df.isna().sum()
    nulos_labels = list(map(str, null_counts.index))
    nulos_values = list(map(int, null_counts.values))

    # Duplicados (filas)
    dup_rows = int(df.duplicated().sum())
    unique_rows = int(len(df) - dup_rows)

    # Estadísticos numéricos
    num = df.select_dtypes(include="number")
    means   = {c: _json_num(v) for c, v in num.mean(numeric_only=True).items()}
    medians = {c: _json_num(v) for c, v in num.median(numeric_only=True).items()}
    stds    = {c: _json_num(v) for c, v in num.std(numeric_only=True).items()}
    counts  = {c: int(v)       for c, v in num.count().items()}
    mins    = {c: _json_num(v) for c, v in num.min(numeric_only=True).items()}
    maxs    = {c: _json_num(v) for c, v in num.max(numeric_only=True).items()}

    cols = list(map(str, num.columns))
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
    otras = {"labels": ["Únicas", "Duplicadas"], "values": [unique_rows, dup_rows]}

    return {
        "columns": list(map(str, df.columns)),
        "rows": int(len(df)),
        "nulos": {"labels": nulos_labels, "values": nulos_values},
        "dupes": {"unique": unique_rows, "duplicates": dup_rows},
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
