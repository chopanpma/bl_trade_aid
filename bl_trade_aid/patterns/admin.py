from django.contrib import admin
from .models import Experiment
from .models import Rule
from .models import ProcessedContract
from .models import ExcludedContract


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


@admin.register(ProcessedContract)
class ProcessedContractsAdmin(admin.ModelAdmin):
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
