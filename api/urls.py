from django.urls import path
from .views import health, upload_csv

urlpatterns = [
    path('health/', health),
    path('upload-csv/', upload_csv),
]
