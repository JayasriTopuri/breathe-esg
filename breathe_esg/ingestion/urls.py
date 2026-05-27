from django.urls import path
from .views import IngestFileView, DataSourceListView

urlpatterns = [
    path('ingest/', IngestFileView.as_view(), name='ingest-file'),
    path('sources/', DataSourceListView.as_view(), name='data-sources'),
]