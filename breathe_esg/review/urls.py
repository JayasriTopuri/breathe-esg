from django.urls import path
from .views import ActivityRowListView, ReviewRowView, DashboardStatsView

urlpatterns = [
    path('rows/', ActivityRowListView.as_view(), name='activity-rows'),
    path('rows/<int:row_id>/review/', ReviewRowView.as_view(), name='review-row'),
    path('stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
]