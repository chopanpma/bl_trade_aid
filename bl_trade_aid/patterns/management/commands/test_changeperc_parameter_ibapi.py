from django.core.management.base import BaseCommand
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.tag_value import TagValue
from ibapi.scanner import ScannerSubscription
from ibapi.utils import iswrapper


class Command(BaseCommand):
    help = 'Scans stocks using TWS API testing CHANGEPERC parameter'

    def handle(self, *args, **options):
        for filter in options['filters']:
            equity_scan(filter)

    def add_arguments(self, parser):
        parser.add_argument("filters", nargs="+")


class MarketScanner(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)

    @iswrapper
    def scannerData(self, reqId, rank, contractDetails, distance, benchmark, projection, legsStr):
        print(f"Equity ScannerData: {rank}, {contractDetails.contract.symbol}, "
              f"{contractDetails.contract.secType}, {contractDetails.contract.exchange}, Change: {distance}")

    @iswrapper
    def ScannerDataEnd(self, reqId):
        print('ScannerDataEnd!')
        self.cancelScannerSubscription(reqId)
        self.disconnect()


def equity_scan(filter):
    app = MarketScanner()
    app.connect('192.168.0.13', 7497, 3)
    # ib.connect('192.168.0.13', 7497, clientId=1, account='U3972489')

    # Create a scanner subscription object for equities
    scan = ScannerSubscription()
    scan.instrument = "STK"  # For stocks
    scan.locationCode = "STK.US.MAJOR"  # US Major exchanges
    scan.scanCode = "TOP_PERC_GAIN"  # Top percentage gainers

    # Add a filter for CHANGEPERC > 2%

    scan_filter = [TagValue(f"{filter}", "0")]  # Change percentage filter
    # scan_filter = []  # Change percentage filter

    # Request the scanner subscription
    app.reqScannerSubscription(7001, scan, [], scan_filter)

    app.run()
