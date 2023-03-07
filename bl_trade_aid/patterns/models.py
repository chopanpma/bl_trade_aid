from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel

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
    price = models.DecimalField(_('Price'), max_digits=12, decimal_places=2,
                                help_text=_('Price of the TPO'))


class TPO(AuditableModel, TimeStampedModel):
    price = models.DecimalField(_('Price'), max_digits=12, decimal_places=2,
                                help_text=_('Price of the TPO'))


class TPOPrint(TimeStampedModel):
    """
    All Prints per TPO.
    """
    print = models.CharField(_('Print'), max_length=1)
    tpo = models.ForeignKey('TPO',  verbose_name=_('TPO'), related_name='prints',
                            on_delete=models.PROTECT)


class ScanData(TimeStampedModel):
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

    unerConId = models.IntegerField(_(''), null=True, blank=True,
                                    help_text=_(''))

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

    aggGroup = models.IntegerField(_(''), null=True, blank=True,
                                   help_text=_(''))

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

    coupon = models.IntegerField(_(''), null=True, blank=True,
                                 help_text=_(''))

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
