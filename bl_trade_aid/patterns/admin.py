from django.contrib import admin
from .models import Experiment
from .models import QueryParameter
from .models import Rule
from .models import ProcessedContract
from .models import ExcludedContract
from .models import RuleExperiment
from .models import Position
from .models import Alert
from .models import Batch


# Register your models here.
class QueryParameterInline(admin.TabularInline):
    model = QueryParameter
    extra = 1


class RuleExperimentInline(admin.TabularInline):
    model = RuleExperiment
    extra = 1


@admin.register(Experiment)
class ExperimentAdmin(admin.ModelAdmin):
    inlines = [QueryParameterInline, RuleExperimentInline]

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
            )

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


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = (
            'experiment',
            )
