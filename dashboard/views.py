from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.encoding import smart_str
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
import pandas as pd
import numpy as np

def health(_request):
    return JsonResponse({"status": "ok"})

def _read_csv_to_df(django_file):
    """
    Lectura robusta: detecta separador automáticamente (engine='python').
    Acepta archivos UTF-8; si recibes otros encodings, ajusta aquí.
    """
    django_file.seek(0)
    try:
        df = pd.read_csv(django_file, sep=None, engine="python", low_memory=False)
    except Exception:
        # Fallback clásico con coma
        django_file.seek(0)
        df = pd.read_csv(django_file, low_memory=False)
    return df

def _jsonize_number(v):
    if pd.isna(v):
        return None
    if isinstance(v, (np.floating,)):
        return float(v)
    if isinstance(v, (np.integer,)):
        return int(v)
    return v

def _build_payload(df: pd.DataFrame) -> dict:
    # Nulos
    null_counts = df.isna().sum()
    nulos_labels = list(null_counts.index.map(str))
    nulos_values = [int(x) for x in null_counts.values]

    # Duplicados (filas)
    dup_rows = int(df.duplicated().sum())
    unique_rows = int(len(df) - dup_rows)

    # Numéricas
    num = df.select_dtypes(include="number")
    means = {c: _jsonize_number(v) for c, v in num.mean(numeric_only=True).items()}
    medians = {c: _jsonize_number(v) for c, v in num.median(numeric_only=True).items()}
    stds = {c: _jsonize_number(v) for c, v in num.std(numeric_only=True).items()}
    counts = {c: int(v) for c, v in num.count().items()}
    mins = {c: _jsonize_number(v) for c, v in num.min(numeric_only=True).items()}
    maxs = {c: _jsonize_number(v) for c, v in num.max(numeric_only=True).items()}

    # Tabla de stats: filas = métricas, columnas = columnas numéricas
    metrics_order = ["count", "mean", "median", "std", "min", "max"]
    stats_table = {
        "columns": list(num.columns.map(str)),
        "metrics": metrics_order,
        "values": [
            [counts.get(c), means.get(c), medians.get(c), stds.get(c), mins.get(c), maxs.get(c)]
            for c in stats_table["columns"] if False  # placeholder; se reemplaza abajo
        ]
    }
    # reconstruimos correctamente 'values' alineando por métrica (lista de filas)
    # Queremos values como: filas=metrics, cols=columns
    cols = list(num.columns.map(str))
    stats_table = {
        "columns": cols,
        "metrics": metrics_order,
        "values": [
            [counts.get(c) for c in cols],
            [means.get(c)  for c in cols],
            [medians.get(c) for c in cols],
            [stds.get(c)   for c in cols],
            [mins.get(c)   for c in cols],
            [maxs.get(c)   for c in cols],
        ]
    }

    # Para la pestaña "Estadísticas" graficaremos por defecto la media
    stats_for_chart = {
        "labels": list(means.keys()),
        "values": list(means.values()),
    }

    # En "Otras" mostraremos duplicados (pie)
    otras = {
        "labels": ["Únicas", "Duplicadas"],
        "values": [unique_rows, dup_rows]
    }

    return {
        "columns": list(df.columns.map(str)),
        "rows": int(len(df)),
        "nulos": {"labels": nulos_labels, "values": nulos_values},
        "dupes": {"unique": unique_rows, "duplicates": dup_rows},
        "stats": stats_for_chart,
        "statsTable": stats_table,
        "otras": otras
    }

@csrf_exempt
@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def upload_csv(request):
    """
    Recibe form-data con clave 'csv_file' (coincide con tu form del front).
    Devuelve métricas genéricas para graficar: nulos, duplicados y estadísticas.
    """
    f = request.FILES.get("csv_file")
    if not f:
        return JsonResponse({"detail": "Falta el archivo 'csv_file'."}, status=400)

    df = _read_csv_to_df(f)
    payload = _build_payload(df)
    return JsonResponse(payload, safe=False)
# Nota: safe=False permite devolver listas; aquí devolvemos dicts, así que no es estrictamente necesario.   