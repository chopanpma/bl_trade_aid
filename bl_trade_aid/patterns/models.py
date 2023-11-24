from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel
from zoneinfo import ZoneInfo


# Create your models here.

# TPO
# TPO-PRINTS
# PERIODS
# CHART

# -*- coding: utf-8 -*-


class AuditableModel(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="created_%(class)s", null=True, on_delete=models.SET_NULL
    )
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="modified_%(class)s", null=True, on_delete=models.SET_NULL
    )

    class Meta:
        abstract = True


class ProfileChart(AuditableModel, TimeStampedModel):
    batch = models.ForeignKey('Batch',  verbose_name=_('Batch'), related_name='profile_charts',
                              on_delete=models.PROTECT)
    symbol = models.CharField(_('Symbol'), max_length=10)
    # specifying a directory within your MEDIA_ROOT to store the files
    chart_file = models.FileField(upload_to='charts/', null=True, blank=True)


class TPO(AuditableModel, TimeStampedModel):
    profile_chart = models.ForeignKey('ProfileChart',  verbose_name=_('ProfileChart'), related_name='tpos',
                                      on_delete=models.PROTECT)
    price = models.DecimalField(_('Price'), max_digits=12, decimal_places=2,
                                help_text=_('Price of the TPO'))


class Period(TimeStampedModel):
    """
    All Prints per TPO.
    """
    profile_chart = models.ForeignKey('ProfileChart',  verbose_name=_('ProfileChart'), related_name='periods',
                                      on_delete=models.PROTECT)
    period = models.CharField(_('Period'), max_length=1)
    tpo = models.ForeignKey('TPO',  verbose_name=_('TPO'), related_name='perids',
                            on_delete=models.PROTECT)


class TPOPrint(TimeStampedModel):
    """
    All Prints per TPO.
    """
    period = models.CharField(_('Period'), max_length=1)
    tpo = models.ForeignKey('TPO',  verbose_name=_('TPO'), related_name='prints',
                            on_delete=models.PROTECT)


class BarData(TimeStampedModel):
    batch = models.ForeignKey('Batch',  verbose_name=_('Batch'), related_name='bar_data',
                              on_delete=models.PROTECT)
    tz = ZoneInfo('America/New_York')

    date = models.DateTimeField(_('date'), null=True, blank=True)
    open = models.DecimalField(_('open'), max_digits=12, decimal_places=2,
                               help_text=_('open'))
    high = models.DecimalField(_('high'), max_digits=12, decimal_places=2,
                               help_text=_('high'))
    low = models.DecimalField(_('low'), max_digits=12, decimal_places=2,
                              help_text=_('low'))

    close = models.DecimalField(_('close'), max_digits=12, decimal_places=2,
                                help_text=_('close'))

    volume = models.DecimalField(_('volume'), max_digits=12, decimal_places=2,
                                 help_text=_('volume'))

    average = models.DecimalField(_('average'), max_digits=12, decimal_places=2,
                                  help_text=_('average'))

    barCount = models.IntegerField(_('barCount'), help_text=_('barCount'))

    symbol = models.CharField(_('Symbol'), max_length=10)

    experiment_positive = models.BooleanField(default=False)

#     def save(self, *args, **kwargs):
#         if self.date is not None:
#             # Convert the datetime to the appropriate timezone
#             self.date = timezone.make_aware(self.date, self.tz)
#         super().save(*args, **kwargs)


class Rule(TimeStampedModel):
    name = models.CharField(_('Name'), max_length=100, null=True, blank=True,
                            help_text=_('Name of the rule'))
    experiment = models.ForeignKey('Experiment',  verbose_name=_('Experiment'), related_name='rules',
                                   null=True, blank=True,
                                   on_delete=models.PROTECT)
    control_point_band_ticks = models.IntegerField(_('Control Point Band Ticks'), null=True, blank=True,
                                                   help_text=_('Ticks allowed for the band'))
    days_offset = models.IntegerField(_('DayOffset'), null=True, blank=True,
                                      help_text=_('Day(s) that will be compared with the rest'))


class Experiment(TimeStampedModel):
    name = models.CharField(_('Name'), max_length=100, null=True, blank=True,
                            help_text=_('Name of the experiment'))

    def __str__(self):
        return self.name


class ExcludedContract(TimeStampedModel):
    symbol = models.CharField(_('Symbol'), max_length=12,
                              help_text=_('Symbol'))
    exclude_active = models.BooleanField(default=True)

    def __str__(self):
        return self.symbol


class ProcessedContract(TimeStampedModel):
    symbol = models.CharField(_('Symbol'), max_length=12,
                              help_text=_('Symbol'))
    batch = models.ForeignKey('Batch',  verbose_name=_('Batch'), related_name='processed_contracts',
                              null=True, blank=True,
                              on_delete=models.PROTECT)
    positive_outcome = models.BooleanField(default=False)

    def __str__(self):
        return self.symbol


class Position(TimeStampedModel):
    LONG = 'L'
    SHORT = 'S'

    DIRECTION_CHOICES = [
            (LONG, 'Long'),
            (SHORT, 'Short')
            ]

    processed_contract = models.ForeignKey(
            'ProcessedContract',
            verbose_name=_('ProcessedContract'),
            related_name='positions',
            null=True, blank=True,
            on_delete=models.PROTECT)
    shadow_mode = models.BooleanField(default=False)
    open_price = models.DecimalField(_('open_price'), max_digits=12, decimal_places=2,
                                     help_text=_('open position price'))
    close_price = models.DecimalField(_('close_price'), max_digits=12, decimal_places=2,
                                      help_text=_('close position price'))
    direction = models.CharField(_('Direction'), max_length=1,
                                 help_text=_('Direction of the position'),
                                 choices=DIRECTION_CHOICES,
                                 default=LONG)

    def __str__(self):
        return f'{self.symbol} - {self.direction} - O:{self.open_price} - C:{self.close_price}'


class Batch(TimeStampedModel):
    experiment = models.ForeignKey('Experiment',  verbose_name=_('Experiment'), related_name='batches',
                                   null=True, blank=True,
                                   on_delete=models.PROTECT)

    def __str__(self):
        return f'{self.id} - {self.created}'


class ScanData(TimeStampedModel):
    batch = models.ForeignKey('Batch',  verbose_name=_('Batch'), related_name='scans',
                              null=True, blank=True,
                              on_delete=models.PROTECT)

    rank = models.IntegerField(_('Rank'), null=True, blank=True,
                               help_text=_('Not known yet'))
    price = models.DecimalField(_('Price'), max_digits=12, decimal_places=2, null=True, blank=True,
                                help_text=_('Price of the TPO'))
    contractDetails = models.ForeignKey('ContractDetails',  verbose_name=_('ContractDetails'), related_name='scandata',
                                        on_delete=models.PROTECT)

    distance = models.CharField(_('distance'), max_length=100, null=True, blank=True,
                                help_text=_('distance'))

    benchmark = models.CharField(_('benchmark'), max_length=100, null=True, blank=True,
                                 help_text=_('benchmark'))

    projection = models.CharField(_('projection'), max_length=100, null=True, blank=True,
                                  help_text=_('projection'))

    legsStr = models.CharField(_('legsStr'), max_length=100, null=True, blank=True,
                               help_text=_('legsStr'))


class ContractDetails(TimeStampedModel):
    rank = models.IntegerField(_('Rank'), null=True, blank=True,
                               help_text=_('Not known yet'))

    contract = models.ForeignKey('Contract',  verbose_name=_('Contract'), null=True, blank=True,
                                 related_name='contract_details',
                                 on_delete=models.PROTECT)

    marketName = models.CharField(_('MarketName'), max_length=12, null=True, blank=True,
                                  help_text=_('MarketName'))

    minTick = models.DecimalField(_('Min Tick'), max_digits=12, decimal_places=2, null=True, blank=True,
                                  help_text=_('Min Tick'))

    orderTypes = models.CharField(_('OrderTypes'), max_length=100, null=True, blank=True,
                                  help_text=_('OrderTypes'))

    validExchanges = models.CharField(_('ValidExchanges'), max_length=100, null=True, blank=True,
                                      help_text=_('ValidExchanges'))

    validExchanges = models.CharField(_('ValidExchanges'), max_length=100, null=True, blank=True,
                                      help_text=_('ValidExchanges'))

    priceMagnifier = models.IntegerField(_('Price Magnifier'), null=True, blank=True,
                                         help_text=_('Price Magnifier'))

    unerConId = models.IntegerField(_('UnerConId'), null=True, blank=True,
                                    help_text=_('UnerConId'))

    longName = models.CharField(_('Long Name'), max_length=100, null=True, blank=True,
                                help_text=_('Long Name'))

    contractMonth = models.CharField(_('ContractMonth'), max_length=100, null=True, blank=True,
                                     help_text=_('ContractMonth'))

    industry = models.CharField(_('industry'), max_length=100, null=True, blank=True,
                                help_text=_('industry'))

    category = models.CharField(_('category'), max_length=100, null=True, blank=True,
                                help_text=_('category'))

    subcategory = models.CharField(_('subcategory'), max_length=100, null=True, blank=True,
                                   help_text=_('subcategory'))

    timeZoneId = models.CharField(_('timeZoneId'), max_length=100, null=True, blank=True,
                                  help_text=_('timeZoneId'))

    tradingHours = models.CharField(_('timeZoneId'), max_length=100, null=True, blank=True,
                                    help_text=_('timeZoneId'))

    liquidHours = models.CharField(_('liquidHours'), max_length=100, null=True, blank=True,
                                   help_text=_('liquidHours'))

    evRule = models.CharField(_('evRule'), max_length=100, null=True, blank=True,
                              help_text=_('evRule'))

    evMultiplier = models.CharField(_('evMultiplier'), max_length=100, null=True, blank=True,
                                    help_text=_('evMultiplier'))

    mdSizeMultiplier = models.CharField(_('mdSizeevMultiplier'), max_length=100, null=True, blank=True,
                                        help_text=_('mdSizeevMultiplier'))

    aggGroup = models.IntegerField(_('aggGroup'), null=True, blank=True,
                                   help_text=_('aggGroup'))

    underSymbol = models.CharField(_('underSymbol'), max_length=100, null=True, blank=True,
                                   help_text=_('underSymbol'))

    underSecType = models.CharField(_('underSecType'), max_length=100, null=True, blank=True,
                                    help_text=_('underSecType'))

    marketRulesId = models.CharField(_('marketRulesId'), max_length=100, null=True, blank=True,
                                     help_text=_('marketRulesId'))

    secIdList = models.CharField(_('marketRulesId'), max_length=100, null=True, blank=True,
                                 help_text=_('marketRulesId'))

    realExpirationDate = models.CharField(_('realExpirationDate'), max_length=100, null=True, blank=True,
                                          help_text=_('realExpirationDate'))

    lastTradeTime = models.CharField(_('lastTradeTime'), max_length=100, null=True, blank=True,
                                     help_text=_('lastTradeTime'))

    stockType = models.CharField(_('stockType'), max_length=100, null=True, blank=True,
                                 help_text=_('stockType'))

    sizeIncrement = models.DecimalField(_('sizeIncrement'), max_digits=12, decimal_places=2,
                                        help_text=_('sizeIncrement'))

    suggestedSizeIncrement = models.DecimalField(_('suggestedSizeIncrement'), max_digits=12, decimal_places=2,
                                                 help_text=_('suggestedSizeIncrement'))

    cusip = models.CharField(_('cusip'), max_length=100, null=True, blank=True,
                             help_text=_('cusip'))

    ratings = models.CharField(_('ratings'), max_length=100, null=True, blank=True,
                               help_text=_('ratings'))

    descAppend = models.CharField(_('descAppend'), max_length=100, null=True, blank=True,
                                  help_text=_('descAppend'))

    bondType = models.CharField(_('bondType'), max_length=100, null=True, blank=True,
                                help_text=_('bondType'))

    cuponType = models.CharField(_('cuponType'), max_length=100, null=True, blank=True,
                                 help_text=_('cuponType'))

    callable = models.BooleanField(default=False)

    putable = models.BooleanField(default=False)

    coupon = models.IntegerField(_('Coupon'), null=True, blank=True,
                                 help_text=_('Coupon'))

    convertible = models.BooleanField(default=False)

    maturity = models.CharField(_('maturity'), max_length=100, null=True, blank=True,
                                help_text=_('maturity'))

    issueDate = models.CharField(_('issueDate'), max_length=100, null=True, blank=True,
                                 help_text=_('issueDate'))

    nextOptionDate = models.CharField(_('nextOptionDate'), max_length=100, null=True, blank=True,
                                      help_text=_('nextOptionDate'))

    nextOptionType = models.CharField(_('nextOptionType'), max_length=100, null=True, blank=True,
                                      help_text=_('nextOptionType'))

    nextOptionPartial = models.BooleanField(default=False)

    notes = models.CharField(_('notes'), max_length=100, null=True, blank=True,
                             help_text=_('notes'))


class Contract(TimeStampedModel):
    secType = models.CharField(_('Security Type'), max_length=12,
                               help_text=_('Security type'))

    conId = models.IntegerField(_('Contract ID'), null=True, blank=True,
                                help_text=_('Not known yet'))

    symbol = models.CharField(_('Symbol'), max_length=12,
                              help_text=_('Symbol'))

    exchange = models.CharField(_('Exchange'), max_length=12,
                                help_text=_('Exchange'))
    currency = models.CharField(_('Currency'), max_length=12,
                                help_text=_('Currency'))

    localSymbol = models.CharField(_('LocalSymbol'), max_length=12,
                                   help_text=_('LocalSymbol'))

    tradeClass = models.CharField(_('TradeClass'), max_length=12,
                                  help_text=_('TradeClass'))
