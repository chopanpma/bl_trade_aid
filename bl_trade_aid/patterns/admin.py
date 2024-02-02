from django.contrib import admin
from django.utils.html import format_html
from .models import Experiment
from .models import QueryParameter
from .models import Rule
from .models import ProcessedContract
from .models import ExcludedContract
from .models import RuleExperiment
from .models import Position
from .models import Alert
from .models import Batch
from .models import ProfileChart


# Register your models here.
class QueryParameterInline(admin.TabularInline):
    model = QueryParameter
    extra = 1


class RuleExperimentInline(admin.TabularInline):
    model = RuleExperiment
    extra = 1


@admin.register(Experiment)
class ExperimentAdmin(admin.ModelAdmin):
    inlines = [QueryParameterInline,
               RuleExperimentInline,
               ]

    list_display = ['name',
                    'instrument',
                    'location_code',
                    'scan_code',
                    'description']
    list_filter = ['name']


@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    list_display = (
            'name',
            'control_point_band_ticks',
            'days_offset',
            'ticks_offset',
            'days_returned',
            'difference_direction',
            )

    list_filter = ('name', 'experiment')


class AlertInline(admin.TabularInline):
    model = Alert
    extra = 1


class PositionInline(admin.TabularInline):
    model = Position
    extra = 1


@admin.register(ProcessedContract)
class ProcessedContractsAdmin(admin.ModelAdmin):
    inlines = [PositionInline, AlertInline]
    list_display = (
            'symbol',
            'batch',
            'positive_outcome',
            'get_profile_chart',
            )

    def get_profile_chart(self, obj):
        if obj.profile_chart and obj.profile_chart.chart_file:
            file_url = obj.profile_chart.chart_file.url
            file_name = obj.profile_chart.chart_file.name
            return format_html("<a href='{}' target='_blank'>{}</a>", file_url, file_name)
        return "No file"
    get_profile_chart.short_description = "File Link"

    list_filter = ('positive_outcome', 'batch', 'symbol')


@admin.register(ExcludedContract)
class ExcludeContractsAdmin(admin.ModelAdmin):
    list_display = (
            'symbol',
            'exclude_active',
            )

    list_filter = ('exclude_active', 'symbol')


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = (
            'processed_contract',
            'direction',
            'open_price',
            'close_price',
            )


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = (
            'processed_contract',
            'operator',
            'alert_price',
            )


@admin.register(QueryParameter)
class QueryParameterAdmin(admin.ModelAdmin):
    list_display = (
            'parameter_name',
            'parameter_value',
            )


@admin.register(RuleExperiment)
class RuleExperimentAdmin(admin.ModelAdmin):
    list_display = (
            'rule',
            'experiment',
            )


class RuleSetExperimentAdmin(admin.ModelAdmin):
    list_display = (
            'rule_set',
            'experiment',
            )


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = (
            'experiment',
            'id',
            )
    list_filter = ('experiment', 'id')


@admin.register(ProfileChart)
class ProfileChartAdmin(admin.ModelAdmin):
    list_display = (
            'batch',
            'symbol',
            'chart_file',
            )
    list_filter = ('symbol', 'batch')
