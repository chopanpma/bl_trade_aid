from django.shortcuts import render

# Create your views here.
from django.db.models import Sum
from django.db.models import Count
from slick_reporting.views import ReportView, Chart
from slick_reporting.fields import ComputationField
from .models import ProcessedContract


class TotalExperimentSuccess(ReportView):
    report_model = ProcessedContract
    date_field = "created"
    group_by = "batch__experiment"
    columns = [
        ComputationField.create(
            Count, "id", verbose_name="Hits", is_summable=False
        ),
        ComputationField.create(
            Count, "positive_outcome", name="Positive", verbose_name="Positives"
        ),
    ]

    chart_settings = [
        Chart(
            "Experiment",
            Chart.BAR,
            data_source=["Positive"],
            title_source=["experiment"],
        ),
        Chart(
            "Experiments [PIE]",
            Chart.PIE,
            data_source=["Positive"],
            title_source=["experiment"],
        ),
    ]
