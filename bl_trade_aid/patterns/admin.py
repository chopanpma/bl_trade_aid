from django.contrib import admin
from .models import Experiment
from .models import Rule
from .models import ProcessedContract
from .models import ExcludedContract
from .models import Position
from .models import Alert


# Register your models here.
@admin.register(Experiment)
class ExperimentAdmin(admin.ModelAdmin):
    list_display = ['name']
    list_filter = ['name']


@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    list_display = (
            'name',
            'experiment',
            'control_point_band_ticks',
            )

    list_filter = ('name', 'experiment')


class AlertInline(admin.TabularInline):
    model = Position
    extra = 1


class PositionInline(admin.TabularInline):
    model = Position
    extra = 1


@admin.register(ProcessedContract)
class ProcessedContractsAdmin(admin.ModelAdmin):
    inlines = [PositionInline]
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
