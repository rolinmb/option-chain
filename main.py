from time import time
from util import validateTicker, ETF_TICKERS, STOCK_TICKERS
from finoptions import *
from surface import *
from sys import argv, exit

funct_list_0 = [
    getOptionTheoDif, getOptionIV, getOptionMidIV, getOptionDelta, getOptionElasticity,
    getOptionVega, getOptionRho, getOptionEpsilon, getOptionTheta,
    getOptionGamma, getOptionVanna, getOptionCharm, getOptionVomma, getOptionVeta, getOptionSpeed,
    getOptionZomma, getOptionColor, getOptionUltima
]

# funct_list_1 = [getOptionIV, getOptionUltima, getOptionTheoDif]
# funct_list_2 = [getOptionIV, getOptionTheta, getOptionVomma, getOptionVeta, getOptionUltima]

def main_routine(ticker, ts_csv, chain_csv, plotting=True, logging=False, showing=False):
        # if not os.path.isfile(ts_csv): # Create ts_csv if doesn't already exist;
        fetchSeriesData( # Rewrite series .csv out each time
                ticker=ticker,
                adj_flag=True,
                logging=logging,
                ts_csv_out=ts_csv
        )
        ts_df = pd.read_csv(ts_csv)
        chain = OptionChain(
            ticker=ticker,
            ts_csv_out=ts_csv,
            ts_df=ts_df,
            fromCSV=False, # Rewrite chain .csv out each time
            chain_csv_out=chain_csv,
            logging=logging
        )
        if logging:
            print('*main_routine(): %s Captured Dividend Yield = %s%s'%(ticker, chain.getDividendYield(), '%'))
            print('*main_routine(): %s Option Chain Total Option Premia; $%s'%(ticker, chain.getTotalPremia()))
            print('*main_routine():\t-> Total Call Premia: $%s / Total Put Premia: $%s (call/put total premia ratio = %s)'%(chain.getTotalCallPremia(), chain.getTotalPutPremia(), chain.getTotalPremiaRatio()))
            print('*main_routine(): %s Option Chain Total Option OI; %s'%(ticker, chain.getTotalOI()))
            print('*main_routine():\t-> Total Call OI: %s / Total Put OI: %s (call/put total OI ratio = %s)'%(chain.getTotalCallOI(), chain.getTotalPutOI(), chain.getTotalOIRatio()))
            print('*main_routine(): %s Option Chain Total Option Volume; %s contracts'%(ticker, chain.getTotalVolume()))
            print('*main_routine():\t-> Total Call Volume: %s contracts / Total Put Volume: %s contracts (call/put total Volume ratio = %s)'%(chain.getTotalCallVolume(), chain.getTotalPutVolume(), chain.getTotalVolumeRatio()))
            print('*main_routine(): %s Option Chain Total OI + Volume; %s'%(ticker, chain.getTotalOIV()))
            print('*main_routine():\t-> Call Total OI/Volume: %s / Put Total OI/Volume: %s (chain OI/Volume = %s)'%(chain.getCallOIVRatio(), chain.getPutOIVRatio(), chain.getTotalOIVRatio()))
        if plotting:
            for calc_funct in funct_list_0:
                method_name = calc_funct.__name__.split('getOption', 1)[1]
                # if not os.path.isfile('png_outputs/chains/%s_%s_quadsurface.png'%(ticker, method_name)):
                buildChainSurfacePlots2(
                        chain=chain,
                        method_name=method_name,
                        calc_method=calc_funct,
                        logging=logging,
                        showing=showing)

if __name__ == '__main__':
    t_start = time()
    # 1st argujment is 'ticker'; must validate
    try:
        ticker = argv[1].strip().upper()
        validateTicker(ticker)
    except IndexError:
        exit('\t! INDEX ERROR: No 1st argument ''ticker'' entered => calling sys.exit()')

    # Call main_routine() for every ticker
    #for ticker in ETF_TICKERS:
    #for ticker in ['DIA','IWM','QQQ','SPY']:
    main_routine( # TODO: test .csv builds before/after calc_impvol() changes
        ticker,
        'csv_outputs/ohlc/%s_adj_tseries.csv'%ticker,
        'csv_outputs/chains/%s_chain.csv'%ticker,
        plotting=False,
        logging=False,
        showing=False
    )
    print(f'\nmain.py Total Execution Time: {str(round(time() - t_start, 2))} seconds')