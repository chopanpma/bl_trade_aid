from ibapi.wrapper import EWrapper
from ibapi.client import EClient
from threading import Thread
from ib_insync import IB
from ib_insync import Stock
from ib_insync import util
from ib_insync import ScannerSubscription
from ib_insync import TagValue
from .models import ScanData
from .models import Contract
from .models import ContractDetails
import queue
# import pickle

import logging
logger = logging.getLogger(__name__)
# Below is the TestWrapper/EWrapper class

'''Here we will override the methods found inside api files'''


class TestWrapper(EWrapper):
    # error handling methods
    def init_error(self):
        error_queue = queue.Queue()
        self.my_errors_queue = error_queue

    def is_error(self):
        error_exist = not self.my_errors_queue.empty()
        return error_exist

    def get_error(self, timeout=6):
        if self.is_error():
            try:
                return self.my_errors_queue.get(timeout=timeout)
            except queue.Empty:
                return None
        return None

    def error(self, id, errorCode, errorString):
        # # Overrides the native method
        errormessage = "IB returns an error with %d errorcode %d that says %s" % (id, errorCode, errorString)
        self.my_errors_queue.put(errormessage)

# time handling methods
    def init_time(self):
        time_queue = queue.Queue()
        self.my_time_queue = time_queue
        return time_queue

    def currentTime(self, server_time):
        # # Overriden method
        self.my_time_queue.put(server_time)

# Below is the TestClient/EClient Class


'''Here we will call our own methods, not overriding the api methods'''


class TestClient(EClient):

    def __init__(self, wrapper):
        # # Set up with a wrapper inside
        EClient.__init__(self, wrapper)

    def server_clock(self):

        print("Asking server for Unix time")

        # Creates a queue to store the time
        time_storage = self.wrapper.init_time()

        # Sets up a request for unix time from the Eclient
        self.reqCurrentTime()

        # Specifies a max wait time if there is no connection
        max_wait_time = 10

        try:
            requested_time = time_storage.get(timeout=max_wait_time)
        except queue.Empty:
            print("The queue was empty or max time reached")
            requested_time = None

        while self.wrapper.is_error():
            print("Error:")
            print(self.get_error(timeout=5))

        return requested_time


class TestApp(TestWrapper, TestClient):
    # Intializes our main classes
    def __init__(self, ipaddress, portid, clientid):
        TestWrapper.__init__(self)
        TestClient.__init__(self, wrapper=self)
        self.connect(ipaddress, portid, clientid)

        # Connects to the server with the ipaddress, portid, and clientId
        # specified in the program execution area self.connect(ipaddress, portid, clientid)
        # Initializes the threading

        thread = Thread(target=self.run)
        thread.start()
        setattr(self, "_thread", thread)
        # Starts listening for errors
        self.init_error()

# Below is the program execution


if __name__ == '__main__':
    print("before start")
    # Specifies that we are on local host with port 7497 (paper trading port number)
    app = TestApp("192.168.43.121", 7497, 0)
    # A printout to show the program began
    print("The program has begun")
    # assigning the return from our clock method to a variable
    requested_time = app.server_clock()
    # printing the return from the server
    print("This is the current time from the server ")
    print(requested_time)


class APIUtils():
    @staticmethod
    def get_dataframe_from_broker(
            symbol,
            height_precision,
            exchange,
            security_type,
            use_extended_hours=False):
        logger.info(f'symbol:{symbol}')
        logger.info(f'height_precision:{height_precision}')
        logger.info(f'exchange:{exchange}')
        logger.info(f'security_type:{security_type}')
        logger.info(f'use_extended_hours:{use_extended_hours}')
        # TODO: Create integration test
        # TODO: Implement function
        return APIUtils.call_ib_service(
                symbol, height_precision, exchange,
                security_type, use_extended_hours=False)

    @staticmethod
    def call_ib_service(
            symbol,
            height_precision,
            exchange,
            security_type,
            use_extended_hours=False):

        # command
        util.startLoop()
        ib = IB()
        ib.connect('192.168.0.15', 7497, clientId=1)

        contract = Stock(
                symbol,
                exchange,
                'USD'
                )

        dt = ''
        bars = ib.reqHistoricalData(
                contract,
                endDateTime=dt,
                durationStr='14  D',
                barSizeSetting='30 mins',
                whatToShow='TRADES',
                useRTH=use_extended_hours,
                formatDate=1)

        print(f'type bars:{type(bars)}')

        print(f'bars:{bars}')

        df = util.df(bars)
        return df


class MarketUtils():
    @staticmethod
    def get_contracts():

        # Connect to TWS API
        ib = IB()
        ib.connect('192.168.0.20', 7497, clientId=1)

        # Request scanner data
        scanner = ScannerSubscription(instrument='STK', locationCode='STK.US.MAJOR', scanCode='HOT_BY_VOLUME')
        data = ib.reqScannerData(scanner, [TagValue('averageOptVolumeAbove', '100'),
                                           TagValue('marketCapAbove', '100000000'),
                                           TagValue('scannerSettingPairs', 'StockType=STOCK')])

        # Serialize contracts for mocking
        # print(f'type data:{type(data)}')
        # with open('scan_results.picle', 'wb') as file:
        #     pickle.dump(data, file)

        # Insert data into the tables.
        for scan_data in data:
            contract_dict = scan_data.contractDetails.contract.__dict__
            contract_instance = Contract()
            ModelUtil.update_model_fields(contract_instance, contract_dict)

            contract_details_dict = scan_data.contractDetails.__dict__
            contract_details_instance = ContractDetails()
            ModelUtil.update_model_fields(contract_details_instance, contract_details_dict)

            contract_details_instance.contract = contract_instance

            scan_data_dict = scan_data.__dict__
            scan_data_instance = ScanData()
            ModelUtil.update_model_fields(scan_data_instance, scan_data_dict)

            scan_data_instance.contractDetais = contract_details_instance

            scan_data_instance.save()

        # Disconnect from TWS API
        ib.disconnect()


class ModelUtil():

    def update_model_fields(model_instance, fields_dict):
        """
        Updates the fields of a Django model instance with the values in a dictionary.
        """
        for field_name in fields_dict:
            # Only update fields that are in the dictionary
            model_fields = model_instance.__dict__.keys()

            if field_name in model_fields:
                setattr(model_instance, field_name, fields_dict[field_name])
