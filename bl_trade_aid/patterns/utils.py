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
from .models import BarData
from .models import Batch
from .models import ProfileChart
from .models import ProcessedContract
from .models import ExcludedContract
from django_pandas.io import read_frame
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import Q
from collections import defaultdict
import queue
import copy
import pandas as pd
import numpy as np
# import pickle
import prettytable

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

    def scannerParameters(self, xml: str):
        super().scannerParameters(xml)
        open('log/scanner.xml', 'w').write(xml)
        print("ScannerParameters received.")


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


class ProfileChartUtils():
    @staticmethod
    def create_profile_chart_wrapper(batch):

        profile_chart = ProfileChartWrapper(batch)
        return profile_chart

    @staticmethod
    def plot_tpo(prices_dict, min_price, max_price, tpo):
        # TODO: small bug about the high price not being plotted
        for price in range(min_price, max_price + 1):
            prices_dict[price] += tpo

        return prices_dict


class RuleExecutor():
    def __init__(self, batch):
        self.batch = batch

    def rules_passed(self,
                     max_point_of_control,
                     min_point_of_control,
                     ):
        response = True
        for experiment_rule in self.batch.experiment.experiment_rules.all():
            if experiment_rule.rule.control_point_band_ticks is not None:
                band_width = max_point_of_control - min_point_of_control
                if band_width >= experiment_rule.rule.control_point_band_ticks:
                    response = False

        return response


class ProfileChartWrapper():

    days_offset = 2
    ticks_offset = None
    days_returned = None

    def __init__(self, batch, height_precision=100):

        qs = BarData.objects.filter(batch=batch)
        self.batch = batch
        self.symbols_df_dict = {}
        self.dates_df_dict = {}
        self.mp_dict = {}
        self.height_precision = height_precision
        self.rules_executor = RuleExecutor(batch)
        experiment_rules = self.batch.experiment.experiment_rules.all()
        for experiment_rule in experiment_rules:
            if experiment_rule.rule.days_offset is not None:
                self.days_offset = experiment_rule.rule.days_offset
            if experiment_rule.rule.ticks_offset is not None:
                self.ticks_offset = experiment_rule.rule.ticks_offset
            if experiment_rule.rule.days_returned is not None:
                self.days_returned = experiment_rule.rule.days_returned

        full_table_df = read_frame(qs)
        symbols = full_table_df['symbol'].unique()

        for symbol in symbols:
            filter_condition = full_table_df['symbol'] == symbol
            symbol_df = full_table_df[filter_condition]

            symbol_df = self.normalize_df(symbol_df)
            symbol_df[('High')] = symbol_df[('High')] * self.height_precision
            symbol_df[('Low')] = symbol_df[('Low')] * self.height_precision
            symbol_df = symbol_df.round({'Low': 0, 'High': 0})
            unique_dates = sorted(symbol_df['Date'].unique())
            dates_df = pd.DataFrame({'Date': unique_dates})

            # add chart column
            dates_df['ProfileChart'] = ''
            dates_df.set_index('Date', inplace=True)

            # map the letter to the price of the row
            # by the end you should have the pc of all days
            # build dictionary with all needed prices
            self.mp_dict[symbol] = defaultdict(str)

            tot_min_price = min(np.array(symbol_df['Low']))
            tot_max_price = max(np.array(symbol_df['High']))
            for price in range(int(tot_min_price), int(tot_max_price)):
                self.mp_dict[symbol][price] += ('')

            # loop throught original ds then create the dict if it does not existe

            mapper = HourLetterMapper()
            for index, row in symbol_df.iterrows():
                only_date = pd.Timestamp(row['Date'].normalize())

                # TODO: find a safer way to locate an element in the list
                day_chart = None
                if dates_df.loc[only_date]['ProfileChart'] == '':
                    day_chart = copy.deepcopy(self.mp_dict[symbol])
                else:
                    day_chart = dates_df.loc[only_date]['ProfileChart']

                localized_time = row['DateTime'].tz_convert(tz='America/New_York')
                letter = mapper.get_letter(localized_time.strftime('%H:%M'))
                min_price = int(row['Low'])
                max_price = int(row['High'])
                day_chart = ProfileChartUtils.plot_tpo(day_chart, min_price, max_price, letter)

                dates_df.loc[only_date]['ProfileChart'] = day_chart

            # dates_df.to_csv(f'{symbol}.csv')
            self.dates_df_dict[symbol] = dates_df
            self.symbols_df_dict[symbol] = symbol_df

            #  with open('mp_pf_dataframe.pickle', 'wb') as file:
            #     pickle.dump(self.df, file)
    def get_dates_df_dict(self):
        return self.dates_df_dict

    def periods(self, symbol):
        return self.symbols_df_dict[symbol]['DateTime'].to_dict()

    def get_day_tpos(self, day, symbol):
        return self.dates_df_dict[symbol].loc[pd.Timestamp(day)]['ProfileChart']

    def check_symbol_positive_experiment(
            self,
            control_points,
            max_point_of_control,
            min_point_of_control):

        dates = list(control_points.keys())
        if self.days_returned is not None:
            if len(dates) < self.days_returned:
                return False

        responses = []
        ticks_delta = 0

        for date in dates[-self.days_offset:]:
            if control_points[date] <= min_point_of_control:
                ticks_delta = min_point_of_control - control_points[date]
                responses.append(('DOWN', ticks_delta))
            else:
                if control_points[date] >= max_point_of_control:
                    # last two are inside the range
                    ticks_delta = control_points[date] - max_point_of_control
                    responses.append(('UP', ticks_delta))
                else:
                    return False
        # Both have to be outside the band in the same direction

        first_element = responses[0][0]
        for element in responses[1:]:
            if self.ticks_offset is not None:
                if element[1] < self.ticks_offset:
                    return False
            if element[0] != first_element:
                return False
        if not self.rules_executor.rules_passed(max_point_of_control, min_point_of_control):
            return False

        return True

    def get_control_point(self, date, charts):
        max_length = 0
        control_point = 0
        for price in charts['ProfileChart'].keys():
            if len(charts['ProfileChart'][price]) > max_length:
                max_length = len(charts['ProfileChart'][price])
                control_point = price

        return control_point

    def get_control_points(self, symbol):
        control_points = {}
        for date, charts in self.dates_df_dict[symbol].iterrows():
            control_points[date] = self.get_control_point(date, charts)

        return control_points

    def set_participant_symbols(self):
        excluded_symbols = ExcludedContract.objects.filter(
                exclude_active=True,
                ).values_list('symbol')
        for excluded_symbol in excluded_symbols:
            if self.dates_df_dict.get(excluded_symbol[0], None) is not None:
                del self.dates_df_dict[excluded_symbol[0]]

        for symbol in self.dates_df_dict.keys():
            control_points = self.get_control_points(symbol)
            if len(control_points) > self.days_offset:
                max_point_of_control = max(list(control_points.values())[:-self.days_offset])
                min_point_of_control = min(list(control_points.values())[:-self.days_offset])
                if self.check_symbol_positive_experiment(control_points,
                                                         max_point_of_control,
                                                         min_point_of_control):
                    ProcessedContract.objects.create(symbol=symbol,
                                                     batch=self.batch,
                                                     positive_outcome=True)
                else:
                    ProcessedContract.objects.create(symbol=symbol,
                                                     batch=self.batch,
                                                     positive_outcome=False)

    def normalize_df(self, df):
        df = df.rename(columns={'date': 'DateTime'})
        df = df.rename(columns={'open': 'Open'})
        df = df.rename(columns={'high': 'High'})
        df = df.rename(columns={'low': 'Low'})
        df = df.rename(columns={'close': 'Close'})
        df = df.rename(columns={'volume': 'Volume'})
        df = df.drop(columns=df.columns.difference(
            [
                'DateTime',
                'Open',
                'High',
                'Low',
                'Close',
                'Volume',
                'symbol',
                'tz',
                ]),
                     axis=1,
                     inplace=False)
        df['Date'] = pd.to_datetime(pd.to_datetime(df['DateTime']).dt.date)
        df = df.set_index(pd.DatetimeIndex(df['Date']))

        return df

    def price_text_formatting(self, price):
        return f"{((price * 1.0)/self.height_precision):.3f}"

    def format_price(self, df):
        df['Price'] = df['Price'].apply(lambda p: self.price_text_formatting(p))
        return df

    def generate_profile_charts(self):
        for symbol in self.dates_df_dict.keys():
            self.profile_chart_df = pd.DataFrame({'Price': self.mp_dict[symbol].keys()})
            for date, charts in self.dates_df_dict[symbol].iterrows():
                date_label = date.strftime('%y/%m/%d')
                self.profile_chart_df[date_label] = ''

                for index, row in self.profile_chart_df.iterrows():
                    self.profile_chart_df.at[index, date_label] = self.dates_df_dict[symbol].loc[date][0][
                            self.profile_chart_df.iloc[index]['Price']]
            self.profile_chart_df.sort_values(by='Price', ascending=False, inplace=True)
            print_df = self.format_price(self.profile_chart_df.copy())

            # self.profile_chart_df.to_csv('output.csv', sep='\t', index=False)
            pt = prettytable.PrettyTable()
            pt.field_names = list(print_df.columns)
            for index, row in print_df.iterrows():
                pt.add_row(row)

            pt.align = 'l'
            content = bytes(pt.get_string(title=f"{symbol} - {self.dates_df_dict[symbol].index[0]} "), 'utf-8')
            content_txt = pt.get_string(title=f"{symbol} - {self.dates_df_dict[symbol].index[0]} ")
            with open(f"{self.dates_df_dict[symbol].index[0].strftime('%y-%m-%d')}-{symbol}.txt", "w") as f:
                f.write(content_txt)
            chart_file = SimpleUploadedFile("profile", content)

            ProfileChart.objects.create(
                batch=self.batch,
                symbol=symbol,
                chart_file=chart_file
            )


class MarketUtils():

    @staticmethod
    def get_single_profile_chart(
            symbol,
            experiment
            ):

        batch = Batch.objects.create()
        batch.experiment = experiment
        batch.save()

        MarketUtils.get_bars_from_single_symbol(batch, symbol)
        pc = ProfileChartUtils.create_profile_chart_wrapper(batch)
        pc.generate_profile_charts()

    @staticmethod
    def filter_contracts(batch):
        processed_symbols = ProcessedContract.objects.filter(
                created__date=batch.created.date(),
                batch__experiment=batch.experiment).values_list('symbol')

        excluded_symbols = ExcludedContract.objects.filter(
                exclude_active=True,
                ).values_list('symbol')
        filtered_list = ScanData.objects.filter(
                (Q(batch=batch) &
                 ~Q(contractDetails__contract__symbol__in=processed_symbols))
                ).filter(~Q(contractDetails__contract__symbol__in=excluded_symbols))

        return filtered_list

    @staticmethod
    def get_current_profile_charts(
            profile_chart_generation_limit,
            experiment,
            ):
        batch = MarketUtils.get_contracts(experiment)
        batch.experiment = experiment
        batch.save()

        scan_data_list = MarketUtils.filter_contracts(batch)
        MarketUtils.get_bars_from_scandata(
                scan_data_list,
                batch=batch,
                profile_chart_generation_limit=profile_chart_generation_limit,
                )
        pc = ProfileChartUtils.create_profile_chart_wrapper(batch)
        pc.generate_profile_charts()
        pc.set_participant_symbols()

    @staticmethod
    def get_scanner_parameters():

        # Connect to TWS API
        ib = IB()
        ib.connect('192.168.0.20', 7497, clientId=1, account='U3972489')

        scanner_parameters = ib.reqScannerParameters()
        open('scanner.xml', 'w').write(scanner_parameters)
        ib.disconnect()

    @staticmethod
    def get_contracts(experiment):

        # Connect to TWS API
        ib = IB()
        ib.connect('192.168.0.20', 7497, clientId=1, account='U3972489')

        #  create the batch and link the experiment to it
        batch = Batch()
        batch.experiment = experiment
        batch.save()

        # Request scanner data
        # TODO: get this from the experiment
        # scanner = ScannerSubscription(instrument='STK', locationCode='STK.US.MAJOR', scanCode='HOT_BY_VOLUME')
        scanner = MarketUtils.create_scanner(experiment)

        query_parameters = MarketUtils.create_parameters(experiment)

        data = ib.reqScannerData(scanner, query_parameters)
        # Serialize contracts for mocking
        # print(f'type data:{type(data)}')
        # with open('scan_results.pickle', 'wb') as file:
        #     pickle.dump(data, file)

        # insert results
        for scan_data in data:
            contract_dict = scan_data.contractDetails.contract.__dict__
            contract_instance = Contract()
            ModelUtil.update_model_fields(contract_instance, contract_dict)
            contract_instance.save()

            contract_details_dict = scan_data.contractDetails.__dict__
            contract_details_instance = ContractDetails()
            ModelUtil.update_model_fields(contract_details_instance, contract_details_dict)
            contract_details_instance.contract = contract_instance
            contract_details_instance.save()

            scan_data_dict = scan_data.__dict__
            scan_data_instance = ScanData()
            ModelUtil.update_model_fields(scan_data_instance, scan_data_dict)
            scan_data_instance.contractDetails = contract_details_instance
            scan_data_instance.batch = batch
            scan_data_instance.save()
        # Disconnect from TWS API
        ib.disconnect()
        return batch

    def get_bars_from_single_symbol(
            batch,
            symbol
            ):
        MarketUtils.get_bars_in_date_range(symbol,
                                           'SMART',
                                           batch=batch)

    def get_bars_from_scandata(
            scan_data_queryset,
            batch,
            profile_chart_generation_limit=None
            ):
        counter = 0
        for scan_data_instance in scan_data_queryset:
            MarketUtils.get_bars_in_date_range(scan_data_instance.contractDetails.contract.symbol,
                                               scan_data_instance.contractDetails.contract.exchange,
                                               batch=batch)
            counter = counter + 1

            if MarketUtils.exit_on_limit_reached(
                    profile_chart_generation_limit,
                    counter):
                return

    def exit_on_limit_reached(
            profile_chart_generation_limit,
            counter):
        if profile_chart_generation_limit is None:
            return False

        if counter >= profile_chart_generation_limit:
            return True

    def get_bars_in_date_range(symbol, exchange, batch):

        # Connect to TWS API
        ib = IB()
        ib.connect('192.168.0.20', 7497, clientId=1)

        contract = Stock(
                symbol,
                exchange,
                'USD'
                )

        # Request scanner data
        bars = ib.reqHistoricalData(
                contract,
                endDateTime='',
                durationStr='14 D',  # add param for days
                barSizeSetting='30 mins',
                whatToShow='TRADES',
                useRTH=True,  # TODO: create param for extended hours
                formatDate=1)

        # Serialize bar result
        #  print(f'type bars:{type(bars)}')
        #  print(f'bars:{bars}')
        #  with open('bar_data_range_results.pickle', 'wb') as file:
        #      pickle.dump(bars, file)

        # Insert data into the tables.
        for bar in bars:
            bar_data_dict = bar.__dict__
            bar_data_dict['symbol'] = symbol
            bar_data_instance = BarData()
            ModelUtil.update_model_fields(bar_data_instance, bar_data_dict)
            bar_data_instance.batch = batch
            bar_data_instance.save()

        # Disconnect from TWS API
        ib.disconnect()

    @staticmethod
    def create_parameters(experiment):
        parameters = []
        for parameter in experiment.query_parameters.all():
            parameters.append(
                    TagValue(
                        parameter.parameter_name,
                        parameter.parameter_value
                        )
                    )
        return parameters

    @staticmethod
    def create_scanner(experiment):
        return ScannerSubscription(
                instrument=experiment.instrument,
                locationCode=experiment.location_code,
                scanCode=experiment.scan_code)


class HourLetterMapper():
    def __init__(self):
        self.hours_to_letter = {
            '07:00': 'v',
            '07:30': 'w',
            '08:00': 'x',
            '08:30': 'y',
            '09:00': 'z',
            '09:30': 'A',
            '10:00': 'B',
            '10:30': 'C',
            '11:00': 'D',
            '11:30': 'E',
            '12:00': 'F',
            '12:30': 'G',
            '13:00': 'H',
            '13:30': 'I',
            '14:00': 'J',
            '14:30': 'K',
            '15:00': 'L',
            '15:30': 'M',
            '16:00': 'N',
            '16:30': 'O',
            '17:00': 'o',
            '17:30': 's',
            '18:00': 't',
            '18:30': 'P',
            '19:00': 'Q',
            '19:30': 'R',
            '20:00': 'S',
            '20:30': 'T',
            '21:00': 'U',
            }

        self.hours_to_letter_extended = {
            '00:00': 'A',
            '00:30': 'B',
            '01:00': 'C',
            '01:30': 'D',
            '02:00': 'E',
            '02:30': 'F',
            '03:00': 'G',
            '03:30': 'H',
            '04:00': 'I',
            '04:30': 'J',
            '05:00': 'K',
            '05:30': 'L',
            '06:00': 'M',
            '06:30': 'N',
            '07:00': 'O',
            '07:30': 'P',
            '08:00': 'Q',
            '08:30': 'R',
            '09:00': 'S',
            '09:30': 'T',
            '10:00': 'U',
            '10:30': 'V',
            '11:00': 'W',
            '11:30': 'X',
            '12:00': 'a',
            '12:30': 'b',
            '13:00': 'c',
            '13:30': 'd',
            '14:00': 'e',
            '14:30': 'f',
            '15:00': 'g',
            '15:30': 'h',
            '16:00': 'i',
            '16:30': 'j',
            '17:00': 'k',
            '17:30': 'l',
            '18:00': 'm',
            '18:30': 'n',
            '19:00': 'o',
            '19:30': 'p',
            '20:00': 'q',
            '20:30': 'r',
            '21:00': 's',
            '21:30': 't',
            '22:00': 'u',
            '22:30': 'v',
            '23:00': 'w',
            '23:30': 'x',
            }

    def get_letter(self, hour):
        #  dt = datetime.datetime.fromtimestamp(hour)
        #  # Format the datetime object as HH:MM string
        #  time_str = dt.strftime('%H:%M')
        return self.hours_to_letter.get(hour, 'X')


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
