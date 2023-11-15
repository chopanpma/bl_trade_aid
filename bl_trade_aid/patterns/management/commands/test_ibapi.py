# myapp/management/commands/scan_stocks.py
import threading
from django.core.management.base import BaseCommand
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.scanner import ScannerSubscription


class StockScanner(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.scan_data = []

    def error(self, reqId, errorCode, errorString):
        print(f"Error: {reqId}, {errorCode}, {errorString}")

    def scannerData(self, reqId, rank, contractDetails, distance, benchmark, projection, legsStr):
        print("ScannerData:", reqId, "Rank:", rank, contractDetails.contract, distance, benchmark, projection, legsStr)
        self.scan_data.append(contractDetails)

    def scannerDataEnd(self, reqId):
        print("ScannerDataEnd:", reqId)
        self.disconnect()


def run_scanner():
    app = StockScanner()
    app.connect("192.168.0.20", 7496, clientId=1)
    subscription = ScannerSubscription()
    subscription.instrument = 'STK'
    subscription.locationCode = 'STK.US.MAJOR'
    subscription.scanCode = 'TOP_PERC_GAIN'
    subscription.aboveMarketCap = 20000000
    subscription.aboveVolume = 100

    app.reqScannerSubscription(1, subscription, [], [])

    app.run()


class Command(BaseCommand):
    help = 'Scans stocks using TWS API'

    def handle(self, *args, **options):
        scanner_thread = threading.Thread(target=run_scanner)
        scanner_thread.start()
        scanner_thread.join()
        self.stdout.write(self.style.SUCCESS('Successfully scanned stocks.'))
