from django.urls import path

from . import views

app_name = "vedic"

urlpatterns = [
    path("profiles/<uuid:pk>/chart/", views.ChartView.as_view(), name="chart"),
    path("profiles/<uuid:pk>/vargas/<str:code>/", views.VargaView.as_view(), name="varga"),
    path("profiles/<uuid:pk>/dashas/", views.DashaTreeView.as_view(), name="dasha-tree"),
    path("profiles/<uuid:pk>/dashas/drill/", views.DashaDrillView.as_view(), name="dasha-drill"),
    path("profiles/<uuid:pk>/dashas/current/", views.DashaCurrentView.as_view(), name="dasha-current"),
    path("profiles/<uuid:pk>/shadbala/", views.ShadbalaView.as_view(), name="shadbala"),
    path("profiles/<uuid:pk>/bhavabala/", views.BhavabalaView.as_view(), name="bhavabala"),
    path("profiles/<uuid:pk>/strength-report/", views.StrengthReportView.as_view(), name="strength-report"),
    path("vedic/panchang/", views.PanchangView.as_view(), name="panchang"),
]
