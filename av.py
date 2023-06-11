from av_config import AV_KEY
from sys import exit
import pandas as pd
import datetime as dt
import urllib.request, json


def getQuoteAV(ticker):
    url = 'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=%s&apikey=%s'%(ticker, AV_KEY)
    with urllib.request.urlopen(url) as source:
        try: # Attempt to read JSON, if no JSON then maybe 404 error or other type of error
            data = json.loads(source.read().decode())
        except Exception as e:
            exit(f'getQuoteAV(): ! ERROR {e}: Couldn''t fetch the AlphaVantage API URL => calling sys.exit()')
        try:
            return data['Global Quote']['05. price']
        except KeyError:
            exit(f'getQuoteAV():\t! KEY ERROR: {ticker} is not valid to query on AlphaVantage => calling sys.exit()')

def buildSeriesDataFrame(ticker, adj_flag, data):
    # print(f'JSON Snapshot before building DataFrame:\n{data}\n') # Checking raw JSON before potentially adjusting
    # Creating empty DataFrame but specifying columns we will populate from the JSON
    df = pd.DataFrame(columns=['Ticker','Date','Open','High','Low','Close','Adj. Close','Volume'])
    # JSON is a python dictionary data structure
    for k,v in data.items():
        date = dt.datetime.strptime(k, '%Y-%m-%d')
        # Append nre data to end of DataFrame (8 columns of data including date and ticker)
        if adj_flag:
            adj_factor = 1/(float(v['5. adjusted close'])/float(v['4. close']))
            df.loc[-1,:] = [ticker, date.date(),
                round(float(v['1. open'])/adj_factor, 3), round(float(v['2. high'])/adj_factor, 3),
                round(float(v['3. low'])/adj_factor, 3), round(float(v['4. close'])/adj_factor, 3),
                float(v['5. adjusted close']), round(float(v['6. volume'])/adj_factor, 1)]
        else: # Case: shouldAdjust = False
            df.loc[-1,:] = [ticker, date.date(),
                float(v['1. open']), float(v['2. high']),
                float(v['3. low']), float(v['4. close']),
                float(v['5. adjusted close']), float(v['6. volume'])]
        # Need to manually increment size of DataFrame
        df.index += 1
    # DataFrame now populated; sorting chronologically and saving as .csv
    df.sort_values('Date') # Reverse chronological sort; Present(start/top)-> Past(end/bottom)
    return df[::-1]        # Now Chronologically sorted; Past(start/top)   -> Present(end/bottom)

def fetchSeriesData(ticker, adj_flag=True, logging=True, ts_csv_out=None):
    # If no csv_out provided, auto-generate filename
    if (ts_csv_out is None
        or ts_csv_out.strip() == ''
        or ts_csv_out.strip() == '.csv'
        or not ts_csv_out.endswith('.csv')):
        ts_csv_out = 'csv_outputs/ohlc/%s%stseries.csv'%(ticker, '_adj_' if adj_flag else '_')
        print('fetchSeriesData():\t\t\t!! NOTICE: Invalid/no .csv filename entered for AlphaVantage Time Series data; using default option ''%s''!!))'%ts_csv_out)
    url = 'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol=%s&outputsize=full&apikey=%s'%(ticker, AV_KEY)
    with urllib.request.urlopen(url) as source:
        try: # Attempt to read JSON, if no JSON then maybe 404 error or other type of error
            data = json.loads(source.read().decode())
        except Exception as e:
            exit(f'fetchSeriesData(): ! ERROR {e}: Couldn''t fetch the AlphaVantage API URL => calling sys.exit()')
        try: # If JSON loaded correctly, isolate the Time Series OHLC+ data from the AlphaVantage API
            data = data['Time Series (Daily)']
        except KeyError:
            exit(f'fetchSeriesData():\t! KEY ERROR: {ticker} is not valid to query on AlphaVantage => calling sys.exit()')
        if logging:
            print(f'fetchSeriesData():\t* urllib.request.urlopen() successfully navigated to\n\t{url}')
        # Call helper function to process 'data' into DataFrame object and write to csv
        df = buildSeriesDataFrame(ticker, adj_flag, data)
        df.to_csv(ts_csv_out, index=False) 
        del(df)
        if logging:
            print('fetchSeriesData():\t\t(Successfully created/refreshed ''%s'')'%ts_csv_out)

if __name__ == '__main__':
    pass