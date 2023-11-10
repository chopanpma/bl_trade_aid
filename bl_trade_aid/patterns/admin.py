from django.contrib import admin
from .models import Experiment
from .models import Rule
from .models import ProcessedContract
from .models import Batch


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

    list_filter = ('symbol', 'batch', 'positive_outcome')
