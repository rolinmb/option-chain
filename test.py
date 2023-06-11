from finoptions import *
from util import validateTicker, LOG_FLAG_OPTIONS, ADJ_FLAG_OPTIONS, CHAIN_BASE_URL
from surface import buildChainSurfacePlots
from av import fetchSeriesData
from sys import argv, exit
from time import time
from os import remove
import pandas as pd

def avAPIFetchTest(ticker, adj_flag, log_flag, ts_csv_name):
    print(f'run_test(): > avAPIFetchTest(): Fetching AlphaVantage API Time Series JSON for {ticker};')
    ft_start = time()
    try:
        fetchSeriesData(ticker=ticker, adj_flag=adj_flag, logging=log_flag, ts_csv_out=ts_csv_name) # if csv_out not provided, will auto_generate to '%s_daoily%stseries.csv'%(ticker, '_adj_' if adj_flag else '_')
    except Exception as e:
        exit('run_test(): > avAPIFetchTest():\t! ERROR %s: couldn''t fetch AlphaVantage API Time Series Data for %s'%(e, ticker))
    if log_flag:
        print(f'run_test(): > avAPIFetchTest():\t\t<Took {round(time() - ft_start, 2)} seconds to fetch JSON and build DataFrame into {ts_csv_name} file>')
    try:
        ts_df = pd.read_csv(ts_csv_name)
    except Exception as e:
        exit('run_test(): > avAPIFetchTest():\t! ERROR %s: Couldn''t locate %s'%(e, ts_csv_name))
    if log_flag:    
        print('run_test(): > avAPIFetchTest():\n\t* %s Time Series DataFrame Snapshot after loading from ''%s'':\n%s'%(ticker, ts_csv_name, str(ts_df)))
    return ts_df # Used later for HV calculations when building OptionChains

def chainConstructorTest(ticker, log_flag=True):
    print(f'run_test(): > chainConstructorTest():\n')
    ft_start = time()
    ts_csv_out = 'csv_outputs/ohlc/%s_adj_tseries.csv'%ticker
    chain_csv_out = 'csv_outputs/chains/%s_chain.csv'%ticker
    # From raw using default chain_csv_out, ts_csv_out, and fetching new ts_df
    chain = OptionChain(ticker=ticker, ts_csv_out=None, ts_df=None, fromCSV=False, logging=False, chain_csv_out=None)
    del(chain)
    remove(ts_csv_out)
    remove(chain_csv_out)
    # From raw using default chain_csv_out, fetching new ts_df
    chain = OptionChain(ticker=ticker, ts_csv_out=ts_csv_out, ts_df=None, fromCSV=False, logging=False, chain_csv_out=None)
    del(chain)
    remove(chain_csv_out)
    ts_df = pd.read_csv(ts_csv_out)
    # From raw using default chain_csv_out, ts_df passed in only
    chain = OptionChain(ticker=ticker, ts_csv_out=None, ts_df=ts_df, fromCSV=False, logging=False, chain_csv_out=None)
    del(chain)
    del(ts_df)
    remove(ts_csv_out)
    remove(chain_csv_out)
    fetchSeriesData(ticker=ticker, adj_flag=True, logging=False, ts_csv_out=ts_csv_out)
    ts_df = pd.read_csv(ts_csv_out)
    # From raw using all params
    chain = OptionChain(ticker=ticker, ts_csv_out=ts_csv_out, ts_df=ts_df, fromCSV=False, logging=True, chain_csv_out=chain_csv_out)
    del(chain)
    del(ts_df)
    remove(ts_csv_out)
    # From existing CSV using default chain_csv_out, ts_csv_out, and fetching new ts_df
    chain = OptionChain(ticker=ticker, ts_csv_out=None, ts_df=None, fromCSV=True, logging=False, chain_csv_out=None)
    del(chain)
    remove(ts_csv_out)
    # From existing CSV using default chain_csv_out, fetching new ts_df
    chain = OptionChain(ticker=ticker, ts_csv_out=ts_csv_out, ts_df=None, fromCSV=True, logging=False, chain_csv_out=None)
    del(chain)
    ts_df = pd.read_csv(ts_csv_out)
    # From existing CSV using default chain_csv_out, ts_df passed in only
    chain = OptionChain(ticker=ticker, ts_csv_out=None, ts_df=ts_df, fromCSV=True, logging=False, chain_csv_out=None)
    del(chain)
    del(ts_df)
    remove(ts_csv_out)
    fetchSeriesData(ticker=ticker, adj_flag=True, logging=False, ts_csv_out=ts_csv_out)
    ts_df = pd.read_csv(ts_csv_out)
    # From existing CSV using all params
    chain = OptionChain(ticker=ticker, ts_csv_out=ts_csv_out, ts_df=ts_df, fromCSV=True, logging=True, chain_csv_out=chain_csv_out)
    del(chain)
    remove(chain_csv_out)
    # Functions that quickly construct an OptionChain
    if log_flag:
        print('run_test(): > chainConstructorTest(): createChainAsCSV();')
    createChainAsCSV(ticker=ticker, ts_out=ts_csv_out, ts_df=ts_df, chain_out=chain_csv_out, log_flag=log_flag)
    if log_flag:
        print('run_test(): > chainConstructorTest(): createChainFromCSV();')
    chain = createChainFromCSV(ticker, ts_csv=ts_csv_out, ts_df=ts_df, chain_csv=chain_csv_out, log_flag=log_flag)
    del(ts_df)
    if log_flag:
            print(f'run_test(): > chainConstructorTest():\t\t<Took {round(time() - ft_start, 2)} seconds to test all OptionChain costructors>')
    return chain

def surfaceFromChainTest(chain, log_flag=True):
    print(f'run_test(): > surfaceTest(): Building Call and Put surface plots for {chain.getTicker()};')
    ft_start = time()
    buildChainSurfacePlots(chain, logging=log_flag)
    if log_flag:
        print(f'run_test(): > surfaceTest():\t\t<Took {round(time() - ft_start, 2)} seconds to build surface plots>')

def run_test(ticker, adj_flag=True, log_flag=True):
    ts_csv_out = 'csv_outputs/ohlc/%s%stseries.csv'%(ticker, '_adj_' if adj_flag else '_')
    # Fetch Time Series test
    test_ts_df = avAPIFetchTest(ticker, adj_flag, log_flag, ts_csv_out)
    del(test_ts_df)
    chain_csv_out = 'csv_outputs/chains/%s_chain.csv'%ticker
    # Full Option Chain test => checking all possible constructor combinations
    test_chain = chainConstructorTest(ticker, log_flag)
    surfaceFromChainTest(test_chain, log_flag=log_flag)
    del(test_chain)
    print('\nrun_test(): > Deleting test output files ''%s'' and ''%s'''%(chain_csv_out, ts_csv_out))
    remove(chain_csv_out)
    remove(ts_csv_out)

def parseInputs():
    if len(argv[1:]) != 3:
        exit('''ARGUMENT INDEX ERROR: Not enough arguments entered, you must enter the 3 items separated by spaces:
        [1] ''TICKER'' (must be alphabetical and no more than 5 characters)
        [2] ''adjust_flag'' %s
        [3] ''logging_flag'' %s'''%(ADJ_FLAG_OPTIONS, LOG_FLAG_OPTIONS))
    try:
        ticker = argv[1].strip().upper()
        validateTicker(ticker)
    except:
        pass
    # 2nd argument is 'adjustment_flag', need to parse to True/False
    try:
        adjust_flag = argv[2].strip().upper()
        # Check if valid 2nd argument was entered
        if adjust_flag not in ADJ_FLAG_OPTIONS:
            exit('\tARGUMENT ERROR: Invalid text entered for 2nd argument ''adj_flag'' (options %s) => calling sys.exit()'%ADJ_FLAG_OPTIONS)
    except:
        pass
    # 3rd argument is 'logging_flag', need to parse to True/False
    try:
        logging_flag = argv[3].strip().upper()
        # Check if valid 2nd argument was entered
        if logging_flag not in LOG_FLAG_OPTIONS:
            exit('\tARGUMENT ERROR: Invalid text entered for 3rd argument ''logging_flag'' (options %s) => calling sys.exit()'%LOG_FLAG_OPTIONS)
    except:
        pass
    # inline parsing ajdust_flag and logging_flag to True or Flase
    return [
        ticker,
        True if adjust_flag in ADJ_FLAG_OPTIONS[:6] else False,
        True if logging_flag in LOG_FLAG_OPTIONS[:8] else False
    ]

if __name__ == '__main__':
    t_start = time()
    input_data = parseInputs()
    # run_test() with 3 passed arguments
    run_test(ticker=input_data[0], adj_flag=input_data[1], log_flag=input_data[2])
    print(f'\ntest.py Total Execution Time: {str(round(time() - t_start, 2))} seconds')