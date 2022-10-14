from django.urls import path

from .views import (
    ListBarDataView,
)

app_name = "api"

urlpatterns = [
    path(r'broker/bars',
         ListBarDataView.as_view(), name='list-bar-data'),
]
