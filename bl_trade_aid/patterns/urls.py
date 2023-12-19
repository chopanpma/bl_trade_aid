
from django.urls import path

from .views import (
    TotalExperimentSuccess,
)

app_name = "patterns"

urlpatterns = [
    path("experiment-hits-report", TotalExperimentSuccess.as_view())
]
