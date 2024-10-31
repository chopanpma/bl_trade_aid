from django.core.management.base import BaseCommand
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.scanner import ScannerSubscription, TagValue
from ibapi.utils import iswrapper


class Command(BaseCommand):
    help = 'Scans stocks using TWS API testing CHANGEPERC parameter'

    def handle(self, *args, **options):
        equity_scan()


class MarketScanner(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)

    @iswrapper
    def scannerData(self, reqId, rank, contractDetails, distance, benchmark, projection, legsStr):
        print(f"Equity ScannerData: {rank}, {contractDetails.contract.symbol}, "
              f"{contractDetails.contract.secType}, {contractDetails.contract.exchange}, Change: {distance}")

    @iswrapper
    def scannerDataEnd(self, reqId):
        print(f"ScannerDataEnd. ReqId: {reqId}\n")
        self.disconnect()


def equity_scan():
    app = MarketScanner()
    app.connect("127.0.0.1", 7497, 0)

    # Create a scanner subscription object for equities
    scan = ScannerSubscription()
    scan.instrument = "STK"  # For stocks
    scan.locationCode = "STK.US.MAJOR"  # US Major exchanges
    scan.scanCode = "TOP_PERC_GAIN"  # Top percentage gainers

    # Add a filter for CHANGEPERC > 2%
    scan_filter = [TagValue("CHANGEPERC", "2")]  # Change percentage filter

    # Request the scanner subscription
    app.reqScannerSubscription(7001, scan, [], scan_filter)

    app.run()
