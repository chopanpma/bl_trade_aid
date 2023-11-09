from django.contrib import admin
from .models import Experiment
from .models import Rule
from .models import PositiveOutcome
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


@admin.register(PositiveOutcome)
class PositiveOutcomeAdmin(admin.ModelAdmin):
    list_display = (
            'symbol',
            'batch',
            )

    list_filter = ('symbol', 'batch')
