from finmath import *
from util import is_float, getQuoteMW, stripCommas, getSoup, CHAIN_BASE_URL
from av import fetchSeriesData
import os
from datetime import datetime
import pandas as pd

FULL_INIT_COLS = [
    'Ticker','Div. Yield','HV','dTime', 'Expiry',
    'cLast', 'cChange', 'cVol', 'cBid', 'cAsk','cOpen Int.', 
    'Strike Price', 'pLast', 'pChange', 'pVol', 'pBid', 'pAsk', 'pOpen Int.',
    'cMid', 'cTheoVal','cTheoDiff','cIV', 'cMid IV', 'cDelta', 'cElasticity',
    'cVega', 'cTheta', 'cGamma', 'cVanna', 'cCharm', 'cVomma', 
    'cVeta', 'cSpeed', 'cZomma', 'cColor', 'cUltima', 'cRho', 'cEpsilon',
    'pMid', 'pTheoVal', 'pTheoDiff', 'pIV', 'pMid IV','pDelta', 'pElasticity',
    'pVega', 'pRho', 'pEpsilon', 'pTheta', 'pGamma', 'pVanna', 'pCharm', 'pVomma',
    'pVeta', 'pSpeed', 'pZomma', 'pColor', 'pUltima'
]

FULL_FORMATTED_COLS = [
    'Ticker','Div. Yield', 'HV', 'dTime', 'Expiry', 'Strike Price',
    'cLast', 'cBid', 'cMid', 'cAsk', 'cTheoVal', 'cTheoDiff', 'cChange', 'cVol', 'cOpen Int.',
    'cIV', 'cMid IV', 'cDelta', 'cElasticity',
    'cVega','cRho','cEpsilon', 'cTheta',
    'cGamma', 'cVanna', 'cCharm', 'cVomma', 'cVeta',
    'cSpeed', 'cZomma', 'cColor', 'cUltima',
    'pLast', 'pBid', 'pMid', 'pAsk', 'pTheoVal', 'pTheoDiff', 'pChange', 'pVol', 'pOpen Int.',
    'pIV', 'pMid IV', 'pDelta', 'pElasticity',
    'pVega', 'pRho', 'pEpsilon', 'pTheta',
    'pGamma', 'pVanna', 'pCharm', 'pVomma', 'pVeta',
    'pSpeed', 'pZomma', 'pColor', 'pUltima'
]

'''
Notice:
html_params & init_chain_cols (when building OptionChain from raw HTML) are in FULL_INIT_COLS[:18],
also grks_params = FULL_INIT_COLS[18:] after OptionChain.df is updated in OptionChain.__refactorChainFrame()
-----------------------------------------------------
-> An Option contract represents a Call or a Put of a specific underyling for a specific strike price for a specific ChainExpiration date;
  and contains information on Greeks/derivatives of the option contract w.r.t variables of the BlackSholes equation.
  Option Greeks & IV Calculation notes: https://en.wikipedia.org/wiki/Greeks_(finance)
'''
class Option:
    def __init__(self,
        ticker, logging, chain_csv_out,
        cp, html_params, initial_quote,
        underlying_hv, div_yield,
        greek_params=[]):
        self.ticker = ticker
        self.logging = logging
        self.chain_csv_out = chain_csv_out
        self.cp = cp # true = CALL; false = PUT
        self.underlying_quote = initial_quote
        self.strike = html_params[0]
        self.dateStr = html_params[1]
        self.tte = html_params[2]
        self.oi = html_params[3]
        self.volume = html_params[4]
        self.last = html_params[5]
        self.bid = html_params[6]
        self.ask = html_params[7]
        self.change = html_params[8]
        self.div_yield = div_yield
        self.hv = underlying_hv
        self.mid = float(0.0)
        if greek_params == []: # Option constructed from raw HTML; need to calculate Greeks values for .csv file
            self.mid = (self.bid+self.ask)/2.0
            # Implied Volatility (IV) is a measure of expected stock volatility over an option's TTE
            self.iv = calc_impvol(
                V=max(0.01, self.last, self.bid, self.ask),
                cp=self.cp,
                s=self.underlying_quote,
                k=self.strike, 
                t=self.tte,
                r=0.0525,
                logging=logging
            )
            self.miv = calc_impvol( 
                V=max(0.01, self.mid),
                cp=self.cp,
                s=self.underlying_quote,
                k=self.strike,
                t=self.tte,
                r=0.0525,
                logging=logging
            )
            # First-Order Derivatives
            self.delta = calc_delta( # 1st deriv. option value w.r.t  underlying price (dValue/dSpot)
                iv=self.iv,
                c_p=self.cp,
                S=self.underlying_quote,
                K=self.strike,
                T=self.tte,
                q=self.div_yield, 
                r=0.0525
            )
            self.elasticity = calc_elasticity( # %delta of option value w.r.t. %delta of underlying price
                delta=self.delta,
                V=max(0.001, self.last, self.bid, self.ask),
                S=self.underlying_quote
            )
            self.vega = calc_vega( # 1st deriv. option value w.r.t. vol (dValue/dVol)
                iv=self.iv,
                S=self.underlying_quote,
                K=self.strike,
                T=self.tte,
                r=0.0525
            )
            self.theta = calc_theta( # 1st deriv. option value w.r.t. TTE (dValue/dTTE)
                iv=self.iv,
                c_p=self.cp,
                S=self.underlying_quote,
                K=self.strike,
                T=self.tte,
                q=self.div_yield,
                r=0.0525
            )
            # Second-Order Derivatives
            self.gamma = calc_gamma( # 2nd deriv. option value w.r.t. underlying price (dDelta/dSpot))
                iv=self.iv,
                S=self.underlying_quote,
                K=self.strike,
                T=self.tte,
                r=0.0525
            )
            self.vanna = calc_vanna( # 2nd deriv. option value w.r.t. underlying and vol (dVega/dSpot or dDelta/dVol)
                iv=self.iv,
                vega=self.vega,
                S=self.underlying_quote,
                K=self.strike,
                T=self.tte,
                r=0.0525
            )
            self.charm = calc_charm( # 2nd deriv. option value w.r.t. underlying and TTE (dDelta/dTTE)
                iv=self.iv, 
                c_p=self.cp,
                S=self.underlying_quote,
                K=self.strike,
                T=self.tte,
                q=self.div_yield,
                r=0.0525
            )
            self.vomma = calc_vomma( # 2nd deriv. option value w.r.t. vol (dVega/dVol)
                iv=self.iv,
                vega=self.vega,
                S=self.underlying_quote,
                K=self.strike,
                T=self.tte,
                r=0.0525
            )
            self.veta = calc_veta( # 2nd deriv. option value w.r.t. vol and TTE (dVega/dTTE)
                iv=self.iv,
                S=self.underlying_quote,
                K=self.strike,
                T=self.tte,
                q=self.div_yield,
                r=0.0525
            )
            # Third-Order Derivatives
            self.speed = calc_speed( # 3rd deriv. option value w.r.t. underlying price (dGamma/dSpot)
                gamma=self.gamma,
                iv=self.iv,
                S=self.underlying_quote,
                K=self.strike,
                T=self.tte,
                r=0.0525
            )
            self.zomma = calc_zomma( # 3rd deriv. option value w.r.t  underlying pricex2 and vol (dGamma/dVol)
                gamma=self.gamma,
                iv=self.iv,
                S=self.underlying_quote,
                K=self.strike,
                T=self.tte,
                r=0.0525
            )
            self.color = calc_color( # 3rd deriv. option value w.r.t  underlying pricex2 and TTE (dGamma/dTTE)
                iv=self.iv,
                S=self.underlying_quote,
                K=self.strike,
                T=self.tte,
                q=self.div_yield,
                r=0.0525
            )
            self.ultima = calc_ultima( # 3rd deriv. option value w.r.t. vol (dVomma/dTTE)
                iv=self.iv,
                vega=self.vega,
                S=self.underlying_quote,
                K=self.strike,
                T=self.tte,
                r=0.0525
            )
            # Misc. greeks
            self.rho = calc_rho( # Sensitivty to interest rates (fed funds rate in specific)
                iv=self.iv,
                c_p=self.cp,
                S=self.underlying_quote,
                K=self.strike,
                T=self.tte,
                r=0.025
            ) 
            self.epsilon = calc_epsilon( # % change in option value per % change in div_yield
                iv=self.iv,
                c_p=self.cp,
                S=self.underlying_quote,
                K=self.strike,
                T=self.tte,
                q=self.div_yield,
                r=0.025
            )
        else: # Option constructed from esisting .csv file, use 'greek_params' to get mid, IV, Mid IV & Greeks values
            # Implied Volatility (IV) is a measure of expected stock volatility over an option's TTE
            self.mid = greek_params[0]
            self.iv = greek_params[1]
            self.miv = greek_params[2]
            # Option Greeks & IV Calculations https://en.wikipedia.org/wiki/Greeks_(finance)
            # First-Order Derivatives
            self.delta = greek_params[3]      # 1st deriv. option value w.r.t  underlying price (dValue/dSpot)
            self.elasticity = greek_params[4] # %delta of option value w.r.t. %delta of underlying price
            self.vega = greek_params[5]  # 1st deriv. option value w.r.t. vol (dValue/dVol)
            self.theta = greek_params[6] # 1st deriv. option value w.r.t. TTE (dValue/dTTE)
            # Second-Order Derivatives
            self.gamma = greek_params[7]   # 2nd deriv. option value w.r.t. underlying price (dDelta/dSpot))
            self.vanna = greek_params[8]   # 2nd deriv. option value w.r.t. underlying and vol (dVega/dSpot or dDelta/dVol)
            self.charm = greek_params[9]   # 2nd deriv. option value w.r.t. underlying and TTE (dDelta/dTTE)
            self.vomma = greek_params[10]  # 2nd deriv. option value w.r.t. vol (dVega/dVol)
            self.veta = greek_params[11]   # 2nd deriv. option value w.r.t. vol and TTE (dVega/dTTE)
            # Third-Order Derivatives
            self.speed = greek_params[12]  # 3rd deriv. option value w.r.t. underlying price (dGamma/dSpot)
            self.zomma = greek_params[13]  # 3rd deriv. option value w.r.t  underlying pricex2 and vol (dGamma/dVol)
            self.color = greek_params[14]  # 3rd deriv. option value w.r.t  underlying pricex2 and TTE (dGamma/dTTE)
            self.ultima = greek_params[15] # 3rd deriv. option value w.r.t. vol (dVomma/dTTE)
            # Misc. greeks
            self.rho = greek_params[16]     # Sensitivty to interest rates (fed funds rate in specific)
            self.epsilon = greek_params[17] # % change in option value per % change in div_yield
        self.theo_val = option_value_theoretical(
            self.delta, self.gamma, self.iv,
            S=self.underlying_quote, r=0.0525
        )
        self.theo_dif = max(0.01, self.last, self.bid, self.ask, self.mid) - self.theo_val

    def getTicker(self):
        return self.ticker
    
    # True = 'CALL'; False = 'PUT'
    def setCallOrPut(self, c_or_p):
        self.cp = c_or_p

    def isCall(self):
        return self.cp

    def isPut(self):
        return not self.cp

    def callOrPut(self):
        return 'CALL' if self.cp else 'PUT'

    def __setUnderlyingQuote(self, quote):
        self.underlying_quote = quote

    def getUnderlyingQuote(self):
        q = getQuoteMW(self.ticker)
        if q != self.underlying_quote and q is not None:
            self.__setUnderlyingQuote(float(q))
        return round(self.underlying_quote, 3)

    def updateUnderlyingQuote(self, quote):
        self.__setUnderlyingQuote(quote)

    def setChainCSV(self, new_chain_csv_out):
        self.chain_csv_out = new_chain_csv_out

    def getChainCSV(self):
        return self.chain_csv_out

    def setStrike(self, new_strike):
        self.strike = new_strike

    def getStrike(self):
        return self.strike

    def setDateStr(self, new_date_text):
        self.dateStr = new_date_text

    def getDateStr(self):
        return self.dateStr

    def setTTE(self, new_tte):
        self.tte = new_tte

    def getTTE(self):
        return self.tte

    def setOI(self, new_oi):
        self.oi = new_oi

    def getOI(self):
        return self.oi

    def setVolume(self, new_volume):
        self.volume = new_volume

    def getVolume(self):
        return self.volume

    def setLast(self, new_last):
        self.last = new_last

    def getLast(self):
        return self.last

    def setBid(self, new_bid):
        self.bid = new_bid

    def getBid(self):
        return self.bid

    def setAsk(self, new_ask):
        self.ask = new_ask

    def getAsk(self):
        return self.ask

    def setMid(self, new_mid):
        self.mid = new_mid

    def getMid(self):
        return self.mid

    def setChange(self, new_change):
        self.change = new_change

    def getChange(self):
        return self.change

    def setIV(self, new_iv):
        self.iv = new_iv

    def getIV(self):
        return self.iv

    def setMidIV(self, new_miv):
        self.miv = new_miv

    def getMidIV(self):
        return self.miv
    
    def setDivYield(self, new_divy):
        self.div_yield = new_divy

    def getDivYield(self):
        return self.div_yield

    def setHV(self, new_hv):
        self.hv = new_hv

    def getHV(self):
        return self.hv

    def setDelta(self, new_delta):
        self.delta = new_delta

    def getDelta(self):
        return self.delta
    
    def setElasticity(self, new_elasticity):
        self.elasticity = new_elasticity

    def getElasticity(self):
        return self.elasticity
    
    def setVega(self, new_vega):
        self.vega = new_vega

    def getVega(self):
        return self.vega

    def setTheta(self, new_theta):
        self.theta = new_theta

    def getTheta(self):
        return self.theta

    def setGamma(self, new_gamma):
        self.gamma = new_gamma

    def getGamma(self):
        return self.gamma
    
    def setVanna(self, new_vanna):
        self.vanna = new_vanna

    def getVanna(self):
        return self.vanna
    
    def setCharm(self, new_charm):
        self.charm = new_charm

    def getCharm(self):
        return self.charm
    
    def setVomma(self, new_vomma):
        self.vomma = new_vomma
    
    def getVomma(self):
        return self.vomma
    
    def setVeta(self, new_veta):
        self.veta = new_veta

    def getVeta(self):
        return self.veta
    
    def setSpeed(self, new_speed):
        self.speed = new_speed

    def getSpeed(self):
        return self.speed

    def setZomma(self, new_zomma):
        self.zomma = new_zomma

    def getZomma(self):
        return self.zomma

    def setColor(self, new_color):
        self.color = new_color

    def getColor(self):
        return self.color

    def setUltima(self, new_ultima):
        self.ultima = new_ultima

    def getUltima(self):
        return self.ultima

    def setRho(self, new_rho):
        self.rho = new_rho

    def getRho(self):
        return self.rho
    
    def setEpsilon(self, new_eps):
        self.epsilon = new_eps

    def getEpsilon(self):
        return self.epsilon

    def getTheoreticalValue(self):
        new_theo_val = option_value_theoretical(
            self.delta, self.gamma, self.iv,
            S=self.underlying_quote, r=0.0525
        )
        if new_theo_val is not None and self.theo_val != new_theo_val:
            self.theo_val = new_theo_val
            return new_theo_val
        else:
            return self.theo_val

    def getTheoDifference(self):
        return self.theo_dif

    def __repr__(self):
        return f"""<Option Object {self.ticker} {self.dateStr} ${self.strike} {self.callOrPut()}> 
                    (Time to Expiration [years]: {round(self.tte, 8)}, Bid/Last/Ask: ${self.bid} / ${self.last} / ${self.ask}
                    Change: ${self.change}, Volume: {self.volume}, Open Interest: {self.oi}
                    IV: {self.iv})"""

def getOptionIV(option):
    return option.getIV()

def getOptionMidIV(option):
    return option.getMidIV()

def getOptionDelta(option):
    return option.getDelta()

def getOptionElasticity(option):
    return option.getElasticity()

def getOptionVega(option):
    return option.getVega()

def getOptionTheta(option):
    return option.getTheta()

def getOptionGamma(option):
    return option.getGamma()

def getOptionVanna(option):
    return option.getVanna()

def getOptionCharm(option):
    return option.getCharm()

def getOptionVomma(option):
    return option.getVomma()

def getOptionVeta(option):
    return option.getVeta()

def getOptionSpeed(option):
    return option.getSpeed()

def getOptionZomma(option):
    return option.getZomma()

def getOptionColor(option):
    return option.getColor()

def getOptionUltima(option):
    return option.getUltima()

def getOptionRho(option):
    return option.getRho()

def getOptionEpsilon(option):
    return option.getEpsilon()

def getOptionTheoDif(option):
    return option.getTheoDifference()

'''
-----------------------------------------------------
-> A ChainExpiration is a list of strike prices for an specific underlying on a specific expiration date,
   but a more useful representation of a ChainExpiration is also 2 lists, one for puts and one for calls;
   which is stored in self.options = [[calls], [puts]] (parsed from OptionChain constructor)
'''
class ChainExpiration:
    def __init__(self, 
        ticker, logging, chain_csv_out,
        dateStr, tte, strikes, options, initial_quote):
        self.logging = logging
        self.ticker = ticker
        self.chain_csv_out = chain_csv_out
        self.dateStr = dateStr
        self.tte = tte
        self.underlying_quote = initial_quote
        self.strikes = strikes
        self.options = options

    def getTicker(self):
        return self.ticker

    def __setUnderlyingQuote(self, quote):
        self.underlying_quote = quote

    def getUnderlyingQuote(self):
        q = getQuoteMW(self.ticker)
        if q != self.underlying_quote:
            self.__setUnderlyingQuote(q)
        return round(self.underlying_quote, 3)

    def setChainCSV(self, new_chain_csv_out):
        self.chain_csv_out = new_chain_csv_out

    def getChainCSV(self):
        return self.chain_csv_out

    def getDateStr(self):
        return self.dateStr

    def getTTE(self):
        return self.tte
    
    def getExpirationStrikes(self):
        return self.strikes
    
    def getStrikeCount(self):
        return len(self.strikes)

    def getOptions(self):
        return self.options

    def getCalls(self):
        return self.options[0]
    
    def getPuts(self):
        return self.options[1]

    def __repr__(self):
        out = f"<-{self.ticker} {self.dateStr} ChainExpiration Object (Time to Expiration [years] = {self.tte})->\n"
        for i in range(0, len(self.strikes)):
            out = out+'\t[$'+str(self.strikes[i])+'] '+str(self.options[0][i])+'\n\t\t'+str(self.options[1][i])+'\n'
        return out

'''
-----------------------------------------------------
-> An OptionChain is a list of ChainExpirations which contains 2 lists;
   one for calls and one for puts, thus ChainExpirations.expirationss_list/.getExpirationsList()
   = [ [[ex1Calls], [ex1Puts]] , [[ex2Calls], [ex2Puts]] , ... ] (Notice: ChainExpiration.options = [[calls], [puts]])
-> An OptionChain is also a Pandas DataFrame; get with OptionChain.df/.getChainFrame(),
   a list of unique options with calculations for strikes in all ChainExpirations)
-> An OptionChain is also a .csv file created using Pandas.to_csv() (has same format as OptionChain.df/.getChainFrame());
   you can construct the .csv without making an OptionChain using createChainAsCSV()
-> An OptionChain is also a list of calls and puts; OptionChain.all_options/.getAllOptions() = [[calls], [puts]];
   this data structure resembles OptionChain.df/.getChainFrame()
'''
class OptionChain:
    def __init__(self,
        ticker='', ts_csv_out=None, ts_df=None,
        fromCSV=False, logging=True, chain_csv_out=None
    ):
        validChainCSVEntered = False
        self.logging = logging
        self.ticker = ticker
        self.ts_csv_out = ts_csv_out
        # Check if ts_csv_out was provided
        if (ts_csv_out is None
            or ts_csv_out.strip() == ''
            or ts_csv_out.strip() == '.csv'
            or not ts_csv_out.endswith('.csv')):
            self.ts_csv_out = 'csv_outputs/ohlc/%s_adj_tseries.csv'%ticker
            if logging:
                print('OptionChain():\t\t-> OptionChain ts_csv_out entered is invalid/empty (using default Time Series .csv name: %s)'%self.ts_csv_out)
        self.from_csv = fromCSV
        self.chain_csv_out = chain_csv_out
        # Check if chain_csv_out was provided
        if (chain_csv_out is None
            or chain_csv_out.strip() == ''
            or chain_csv_out.strip() == '.csv'
            or not chain_csv_out.endswith('.csv')):
            self.chain_csv_out = 'csv_outputs/chains/%s_chain.csv'%ticker # Default if chain_csv_out is None or invalid
            if logging:
                print('OptionChain():\t\t-> OptionChain chain_csv_out entered is invalid/empty (using default OptionChain .csv name: %s)'%self.chain_csv_out)
        else: # If chain_csv_out was provided
            if fromCSV and not os.path.isfile(chain_csv_out): # If building from CSV and chain_csv_out doesn't exist, set self.from_csv = False
                self.chain_csv_out = 'csv_outputs/chains/%s_chain.csv'%ticker
                self.from_csv = False
            elif not fromCSV: # Hard set self.from_csv = True if bulding fromCSV = False
                validChainCSVEntered = True
                self.from_csv = False
            else: # Otherwise we must be building from CSV, set self.from_csv = True
                validChainCSVEntered = True
                self.chain_csv_out = chain_csv_out
                self.from_csv = True
        self.tseries = ts_df
        # If ts_df was not passed in
        if ts_df is None:
            # Call class method to build new self.ts_df if ts_csv_out provided
            self.refreshUnderlyingTimeSeries()
            if logging:
                print('OptionChain(): FETCHED AND LOADED TIME SERIES SINCE ts_df NOT PASSED AS PARAMETER (ts_csv_out: %s): %s'%(self.ts_csv_out, self.tseries))
        else: # Otherwise, use ts_df since it was passed as a parameter
            self.tseries = ts_df
            if logging:    
                print('OptionChain(): TIME SERIES DATAFRAME ts_df PASSED IN AS PARAMETER (ts_csv_out: %s): %s'%(self.ts_csv_out, self.tseries))
        self.hv = calc_histvol(self.tseries['Adj. Close'])
        self.df = pd.DataFrame()
        self.underlying_quote = 0.0
        self.div_yield = float(0.0)
        self.exp_strs = []
        self.expirations_list = []
        self.all_options = [[],[]]
        self.call_premia = 0.0
        self.put_premia = 0.0
        self.call_oi = 0
        self.put_oi = 0
        self.call_volume = 0
        self.put_volume = 0
        # If fromCSV = True, try to construct from self.chain_csv_out
        if self.from_csv:
            if logging:
                print('OptionChain():\t* Constructing OptionChain object from %s'%self.chain_csv_out)
            self.df = self.__buildFromCSV() # build OptionChain from .csv; columns already formatted for Mid/IV/MidIV + Call/Put Greeks
            self.underlying_quote = getQuoteMW(ticker) # Fetch quote this way since not constructing with self.__fetchRawChainData()
            self.div_yield = self.df['Div. Yield'].iloc[0]
            self.hv = self.df['HV'].iloc[0]
            for e in self.df['Expiry']:  # Populate self.exp_strs from self.df since not constructing with self.__buildChainFromRaw()
                if e not in self.exp_strs:
                    self.exp_strs.append(e)
            self.expirations_list = self.__buildExpirationsFromFrame() # Build List of ChainExpirations from d
            self.__getStatistics()
            if logging:
                print('OptionChain():\t\t\t(%s OptionChain has been created from %s)'%(self.ticker, self.chain_csv_out))
                print('OptionChain():\t\t\t((Successfuly constructed OptionChain from %s))'%self.chain_csv_out)
        # If fromCSV=False, fetch HTML to construct OptionChain create new .csv file at self.chain_csv_out (.csv will have option greeks)
        else:
            if logging:
                msg = 'OptionChain():\t* Constructing OptionChain object from raw HTML'
                if validChainCSVEntered:
                    print(msg)
                else:
                    print(msg+' since couldnt build from %s'%chain_csv_out)
            self.__isTickerOptionable()
            raw_data, self.underlying_quote = self.__fetchRawChainData() # Fetching new option chain HTML
            if logging:
                print(f'OptionChain():\t* RAW CHAIN DATA FROM HTML: {raw_data}')
            self.df, self.exp_strs = self.__buildChainFromRaw(raw_data) # Parsing list of raw_data into pd.DataFrame
            del(raw_data) # not saving raw_data for later use, now using self.df or self.expirations_list (below)
            self.expirations_list = self.__buildExpirationsFromFrame() # Build List of ChainExpirations from df
            self.__getStatistics()
            self.__refactorChainFrame() # Still need to refactor and populate self.df to hold Call & Put Option Greeks since building from raw HTML
            self.df.to_csv(self.chain_csv_out, index=False) # Cretate CSV of self.df for use elsewhere now that Greeks are in self.df
            if logging:
                print('OptionChain():\t\t\t(%s has been created/updated while constructing %s OptionChain)'%(self.chain_csv_out, self.ticker))
                print('OptionChain():\t\t\t((Successfuly constructed %s OptionChain and %s from raw HTML))'%(ticker, self.chain_csv_out))
        del(validChainCSVEntered) # Delete boolean used for constructing
        self.call_premia = round(self.call_premia, 3) # Round off Call & put premia calculations
        self.put_premia = round(self.put_premia, 3)
        if logging:
            print('OptionChain():\t* Finished constructing OptionChain instance for %s'%self.ticker)
            print('OptionChain():\t\t-> Net Call Premia: $%s'%self.call_premia)
            print('OptionChain():\t\t-> Net Put Premia: $%s'%self.put_premia)
        
    def __buildFromCSV(self):
        try:
            df = pd.read_csv(self.chain_csv_out)
            return df
        except Exception as e:
            print('OptionChain():\t! ERROR %s: Couldn''t locate ''%s'''%(e, self.chain_csv_out))
 
    def __isTickerOptionable(self):
        if self.logging:
            print('OptionChain():\t* Validating that ''%s'' is optionable'%self.ticker)
        soup = getSoup(self.ticker, 1, False)
        try:
            initial_underlying_quote = stripCommas(soup.find('div', attrs={'class' : 'fleft price'}).text)
        except Exception as e:
            exit('OptionChain():\t! ERROR %s: Couldn''t fetch %s; %s is not optionable => calling sys.exit()'%(e, CHAIN_BASE_URL+self.ticker, self.ticker))

    def __getStatistics(self):
        for ex in self.expirations_list: # Populating self.all_options and finding Total Call/Put premia, OI, and Volume
            ex_options = ex.getOptions()
            for i in range(0, ex.getStrikeCount()):
                self.all_options[0].append(ex_options[0][i])
                self.all_options[1].append(ex_options[1][i])
                self.call_premia += max(0.01, ex_options[0][i].getLast(),
                    ex_options[0][i].getBid(), ex_options[0][i].getAsk(), ex_options[0][i].getMid())
                self.put_premia += max(0.01, ex_options[1][i].getLast(),
                    ex_options[1][i].getBid(), ex_options[1][i].getAsk(), ex_options[1][i].getMid())
                self.call_volume += ex_options[0][i].getVolume()
                self.put_volume += ex_options[1][i].getVolume()
                self.call_oi += ex_options[0][i].getOI()
                self.put_oi += ex_options[1][i].getOI()

    def __refactorChainFrame(self):
        # Call data additions
        self.df['cMid'] = [o.getMid() for o in self.all_options[0]]
        self.df['cTheoVal'] = [o.getTheoreticalValue() for o in self.all_options[0]]
        self.df['cTheoDiff'] = [o.getTheoDifference() for o in self.all_options[0]]
        self.df['cIV'] = [o.getIV() for o in self.all_options[0]]
        self.df['cMid IV'] = [o.getMidIV() for o in self.all_options[0]]
        self.df['cDelta'] = [o.getDelta() for o in self.all_options[0]]
        self.df['cElasticity'] = [o.getElasticity() for o in self.all_options[0]]
        self.df['cVega'] = [o.getVega() for o in self.all_options[0]]
        self.df['cRho'] = [o.getRho() for o in self.all_options[0]]
        self.df['cEpsilon'] = [o.getEpsilon() for o in self.all_options[0]]
        self.df['cTheta'] = [o.getTheta() for o in self.all_options[0]]
        self.df['cGamma'] = [o.getGamma() for o in self.all_options[0]]
        self.df['cVanna'] = [o.getVanna() for o in self.all_options[0]]
        self.df['cCharm'] = [o.getCharm() for o in self.all_options[0]]
        self.df['cVomma'] = [o.getVomma() for o in self.all_options[0]]
        self.df['cVeta'] = [o.getVeta() for o in self.all_options[0]]
        self.df['cSpeed'] = [o.getSpeed() for o in self.all_options[0]]
        self.df['cZomma'] = [o.getZomma() for o in self.all_options[0]]
        self.df['cColor'] = [o.getColor() for o in self.all_options[0]]
        self.df['cUltima'] = [o.getUltima() for o in self.all_options[0]]
        # Put data additions
        self.df['pMid'] = [o.getMid() for o in self.all_options[1]]
        self.df['pTheoVal'] = [o.getTheoreticalValue() for o in self.all_options[0]]
        self.df['pTheoDiff'] = [o.getTheoDifference() for o in self.all_options[0]]
        self.df['pIV'] = [o.getIV() for o in self.all_options[1]]
        self.df['pMid IV'] = [o.getMidIV() for o in self.all_options[1]]
        self.df['pDelta'] = [o.getDelta() for o in self.all_options[1]]
        self.df['pElasticity'] = [o.getElasticity() for o in self.all_options[1]]
        self.df['pVega'] = [o.getVega() for o in self.all_options[1]]
        self.df['pRho'] = [o.getRho() for o in self.all_options[1]]
        self.df['pEpsilon'] = [o.getEpsilon() for o in self.all_options[1]]
        self.df['pTheta'] = [o.getTheta() for o in self.all_options[1]]
        self.df['pGamma'] = [o.getGamma() for o in self.all_options[1]]
        self.df['pVanna'] = [o.getVanna() for o in self.all_options[1]]
        self.df['pCharm'] = [o.getCharm() for o in self.all_options[1]]
        self.df['pVomma'] = [o.getVomma() for o in self.all_options[1]]
        self.df['pVeta'] = [o.getVeta() for o in self.all_options[1]]
        self.df['pSpeed'] = [o.getSpeed() for o in self.all_options[1]]
        self.df['pZomma'] = [o.getZomma() for o in self.all_options[1]]
        self.df['pColor'] = [o.getColor() for o in self.all_options[1]]
        self.df['pUltima'] = [o.getUltima() for o in self.all_options[1]]
        self.df = self.df[FULL_FORMATTED_COLS]

    def __fetchRawChainData(self):
        raw_data = []
        soup = getSoup(self.ticker, 3.69, self.logging) # helper function defined at top
        # capture usable quote string from the HTML source
        initial_underlying_quote = soup.find('div', attrs={'class' : 'fleft price'}).text
        if is_float(stripCommas(initial_underlying_quote)):
            initial_underlying_quote = stripCommas(initial_underlying_quote)
        # capture dividend yield if stock has a dividend, otherwise dividend yield is 0
        divy_table = soup.find('table', attrs={'id' : 'quote'})
        divy = divy_table.findAll('tr')[2].findAll('td')[1].text.replace('%','') #3rd table row; 2nd data in row (remove % symbol)
        if is_float(stripCommas(divy)):
            self.div_yield = float(stripCommas(divy))
        # parsing HTML tables into 'raw_data'
        full_chain_html = soup.find('table', attrs={'class' : 'optionchain shaded'})
        if self.logging:
            print('OptionChain():\t* Parsing toggled HTML into list w/ BeautifulSoup')
        html_table_body = full_chain_html.find('tbody')
        try:
            html_rows = html_table_body.find_all('tr')
            for html_row in html_rows:
                html_cols = html_row.find_all('td')
                html_cols = [ele.text.strip() for ele in html_cols]
                raw_data.append([ele for ele in html_cols])
        except AttributeError:
            exit('OptionChain():\t! ATTRIBUTE ERROR: Couldn''t parse HTML from %s; %s is not optionable => calling sys.exit()'%(CHAIN_BASE_URL+self.ticker, self.ticker))
        if self.logging:
            print('OptionChain():\t\t-> Successfully parsed HTML into list')
        return raw_data, float(initial_underlying_quote)

    def __buildChainFrame(self, data):
        chain_frame = pd.DataFrame(
            data=data,
            columns=FULL_INIT_COLS[:18])
        return chain_frame

    def __buildChainFromRaw(self, raw_data):
        dt_start = datetime.now()
        chain_data = []
        exp = ''
        exp_strs = []
        delta_t_seconds = 0.0
        for i in range(0, len(raw_data)):
            # capture expiration dates and build str, then find time to expiry w/ datetime
            if raw_data[i][0] == "CALLS":
                exp = raw_data[i+1][0].split()[1:] # won't ever exceed len(raw_data); i+1 is safe
                exp_strs.append(' '.join(exp))
                dt_expiry = datetime.strptime(' '.join(exp), "%B %d, %Y")
                delta_t = dt_expiry - dt_start
                delta_t_seconds = (delta_t.days*24.*3600. + delta_t.seconds)/(365.*24.*3600.)
            # Append Expiry dateStr and TTE to raw_data[i] row
            raw_data[i].insert(0, ' '.join(exp))   # append expiration date text to start of 'raw_data' row
            raw_data[i].insert(0, delta_t_seconds) # append time to expiration datetime to start of 'raw_data' row
            # cleaning up empty rows in raw_data to get only numerical values for building new OptionChain DataFrame
            if ((is_float(raw_data[i][2]) or raw_data[i][2] == '' or raw_data[i][2] == ' ' ) and len(raw_data[i]) == 15):
                new_data = []
                new_data.append(self.ticker)
                new_data.append(self.div_yield)
                new_data.append(self.hv)
                for e in raw_data[i]:
                    if is_float(e): # append numerical val as float
                        new_data.append(float(e))
                    elif e == '' or e == ' ': # empty numerical vals set to 0.0       
                        new_data.append(float(0.0))
                    elif is_float(stripCommas(e)): # Larger values (OI, Volume), stocks with 4-figure underlying price/option strikes
                        new_data.append(float(stripCommas(e)))
                    else: # append string of text as is      
                        new_data.append(e)
                # finally, add the formatted row 'new_data' to our new 'chain_data' list
                chain_data.append(new_data)
        return self.__buildChainFrame(chain_data), exp_strs

    def __buildExpirationsFromFrame(self):
        if self.logging:
            print(f'OptionChain():\t* Building All {self.ticker} Expirations:')
        exp_index = 0 # start by detecting the first expiry
        chain_expirations = []
        exp_strikes = []
        exp_options = [[], []]
        prev_tte = 0.0
        this_strike = 0.0
        cgrks = []
        pgrks = []
        # every row in df has data to build a call and put for a specific strike and expiration date
        for i, row in self.df.iterrows():
            this_strike = row['Strike Price']
            if isinstance(this_strike, str) :
                this_strike = float(stripCommas(this_strike))
            # Get Call and Put parameters for each row
            cvals = [
                this_strike, row['Expiry'], row['dTime'], row['cOpen Int.'], row['cVol'], 
                row['cLast'], row['cBid'], row['cAsk'], row['cChange']
            ]
            pvals = [
                this_strike, row['Expiry'], row['dTime'], row['pOpen Int.'], row['pVol'], 
                row['pLast'], row['pBid'], row['pAsk'], row['pChange']
            ]
            # If self.from_csv, construct options with greeks passed as parameters
            if self.from_csv:
                # Get Call and Put Greeks for each row if self.from_csv
                cgrks = [
                    row['cMid'], row['cIV'], row['cMid IV'],
                    row['cDelta'], row['cElasticity'], row['cVega'], row['cTheta'],
                    row['cGamma'], row['cVanna'], row['cCharm'], row['cVomma'], row['cVeta'],
                    row['cSpeed'], row['cZomma'], row['cColor'], row['cUltima'], row['cRho'], row['cEpsilon']
                ]
                cgrks = [float(cgrk) for cgrk in cgrks]
                pgrks = [
                    row['pMid'], row['pIV'], row['pMid IV'],
                    row['pDelta'], row['pElasticity'], row['pVega'], row['pTheta'],
                    row['pGamma'], row['pVanna'], row['pCharm'], row['pVomma'], row['pVeta'],
                    row['pSpeed'], row['pZomma'], row['pColor'], row['pUltima'], row['pRho'], row['pEpsilon']
                ]
                pgrks = [float(pgrk) for pgrk in pgrks]
            # if self.from_csv = False, we use cgrks = [] and pgrks = [] default options fpr each row Call and Put
            if row['Expiry'] == self.exp_strs[exp_index]: # check if we are on current expiration expiration_strs[exp_count]
                if self.logging:
                    print(f'OptionChain():\t\t# Creating {self.ticker} {self.exp_strs[exp_index]} ${this_strike} CALL & PUT')
                prev_tte = row['dTime'] # capture tte in case we detect new expiration date on next row/iteration
                exp_strikes.append(row['Strike Price'])
                # Create and append CALL for strike to 'exp_options[0]'
                exp_options[0].append(Option(
                    ticker=self.ticker,
                    logging=self.logging,
                    chain_csv_out=self.chain_csv_out,
                    cp=True,
                    html_params=cvals,
                    initial_quote=self.underlying_quote,
                    underlying_hv=self.hv,
                    div_yield=self.div_yield,
                    greek_params=cgrks
                ))
                # Create and append PUT for strike to 'exp_options[1]'
                exp_options[1].append(Option(
                    ticker=self.ticker,
                    logging=self.logging,
                   chain_csv_out=self.chain_csv_out,
                    cp=False,
                    html_params=pvals,
                    initial_quote=self.underlying_quote,
                    underlying_hv=self.hv,
                    div_yield=self.div_yield,
                    greek_params=pgrks
                ))
            # New/Next ChainExpiration detected
            else:
                # Add current list of srikes and options expiration to list before incrementing exp_index
                chain_expirations.append(ChainExpiration(
                    ticker=self.ticker,
                    logging=self.logging,
                    chain_csv_out=self.chain_csv_out,
                    dateStr=self.exp_strs[exp_index],
                    tte=prev_tte,
                    strikes=exp_strikes,
                    options=exp_options,
                    initial_quote=self.underlying_quote
                ))
                if self.logging:
                    print(f'OptionChain():\t\t~ Created {self.ticker} {self.exp_strs[exp_index]} ChainExpiration object')
                # Reset lists, increment counter and check again before proceeding to next row
                exp_strikes = []
                exp_options = [[], []]
                exp_index += 1
                if row['Expiry'] == self.exp_strs[exp_index]: # make sure row['Expiry'] matches exp_strs[exp_index] after incrementing
                    if self.logging:
                        print(f'OptionChain():\t\t# Creating {self.ticker} {self.exp_strs[exp_index]} ${this_strike} CALL & PUT')
                    prev_tte = row['dTime'] # now update tte for new row after 
                    exp_strikes.append(row['Strike Price'])
                    # create and append CALL for strike to 'exp_options[0]'
                    exp_options[0].append(Option(
                        ticker=self.ticker,
                        logging=self.logging,
                        chain_csv_out=self.chain_csv_out,
                        cp=True,
                        html_params=cvals,
                        initial_quote=self.underlying_quote,
                        underlying_hv=self.hv,
                        div_yield=self.div_yield,
                        greek_params=cgrks
                    ))
                    # create and append PUT for strike to 'exp_options[1]'
                    exp_options[1].append(Option(
                        ticker=self.ticker,
                        logging=self.logging,
                        chain_csv_out=self.chain_csv_out,
                        cp=False,
                        html_params=pvals,
                        initial_quote=self.underlying_quote,
                        underlying_hv=self.hv,
                        div_yield=self.div_yield,
                        greek_params=pgrks
                    ))
            # If we are on the last iteration make sure to append the final ChainExpiration object
            if i == len(self.df.index) - 1:
                chain_expirations.append(ChainExpiration(
                    ticker=self.ticker,
                    logging=self.logging, 
                    chain_csv_out=self.chain_csv_out,
                    dateStr=self.exp_strs[exp_index],
                    tte=prev_tte,
                    strikes=exp_strikes,
                    options=exp_options,
                    initial_quote=self.underlying_quote
                ))
                if self.logging:
                    print(f'OptionChain():\t\t~ Created {self.ticker} {self.exp_strs[exp_index]} ChainExpiration object')
        return chain_expirations

    def getTicker(self):
        return self.ticker
   
    def __setUnderlyingQuote(self, quote):
        self.underlying_quote = quote
        for type in self.all_options:
            for o in type:
                o.updateUnderlyingQuote(quote)

    def getUnderlyingQuote(self):
        q = getQuoteMW(self.ticker)
        if q != self.underlying_quote:
            self.__setUnderlyingQuote(q)
        return round(self.underlying_quote, 3)
    
    def getDividendYield(self):
        return self.div_yield

    # Call fetchSeriesData() from av.py with new_ts_csv_name
    # Change self.ts_csv_out and refresh self.tseries
    def setNewTimeSeriesCSV(self, new_ts_csv_name):
        if self.logging:
            print('OptionChain(): DELETING TIME SERIES CSV FILE %s'%self.ts_csv_out)
        os.remove(self.ts_csv_out)
        if self.logging:
            print('OptionChain(): FETCHING NEW TIME SERIES AND SAVING TO CSV FILE: %s'%new_ts_csv_name)
        fetchSeriesData(self.ticker, adj_flag=True, logging=self.logging, ts_csv_out=new_ts_csv_name)
        self.ts_csv_out = new_ts_csv_name
        new_tseries = pd.read_csv(self.ts_csv_out)
        self.tseries = new_tseries
        self.__updateUnderlyingHV()

    # Call fetchSeriesData() from av.py to refresh self.ts_csv_out
    def refreshUnderlyingTimeSeries(self):
        if self.logging:
            print('OptionChain(): REFRESHING TIME SERIES USING FILENAME %s'%self.ts_csv_out)
        fetchSeriesData(self.ticker, adj_flag=True, logging=self.logging, ts_csv_out=self.ts_csv_out)
        new_tseries = pd.read_csv(self.ts_csv_out)
        self.tseries = new_tseries
        self.__updateUnderlyingHV()

    def getUnderlyingTimeSeries(self):
        return self.tseries

    def __updateUnderlyingHV(self):
        self.hv = calc_histvol(self.tseries['Adj. Close'])
        for type in self.all_options:
            for o in type:
                o.setHv(self.hv)

    def getUnderlyingHV(self):
        return self.hv

    def setChainCSV(self, new_chain_csv_out):
        self.chain_csv_out = new_chain_csv_out
        for type in self.all_options:
            for o in type:
                o.setChainCSV(self.chain_csv_out)

    def getChainCSV(self):
        return self.chain_csv_out

    def getExpStrs(self):
        return self.exp_strs
    
    def getExpiryCount(self):
        return len(self.exp_strs)

    def getExpirationsList(self):
        return self.expirations_list

    def getUniqueStrikesCount(self):
        return len(self.df.index)

    def getChainFrame(self):
        return self.df

    def getAllCalls(self):
        return self.all_options[0]

    def getAllPuts(self):
        return self.all_options[1]

    def getAllOptions(self):
        return self.all_options

    def getTotalCallPremia(self):
        return self.call_premia

    def getTotalPutPremia(self):
        return self.put_premia

    def getTotalPremia(self):
        return round((self.call_premia + self.put_premia), 2)

    def getTotalPremiaRatio(self):
        return round((self.call_premia / self.put_premia), 2)
    
    def getTotalCallOI(self):
        return self.call_oi
    
    def getTotalPutOI(self):
        return self.put_oi
    
    def getTotalOI(self):
        return self.call_oi + self.put_oi
    
    def getTotalOIRatio(self):
        try:
            return round((self.call_oi / self.put_oi), 2)
        except:
            return 0.0

    def getTotalCallVolume(self):
        return self.call_volume

    def getTotalPutVolume(self):
        return self.put_volume

    def getTotalVolume(self):
        return self.call_volume + self.put_volume
    
    def getTotalVolumeRatio(self):
        try:
            return round((abs(self.call_volume / self.put_volume)), 2)
        except:
            return 0.0

    def getTotalOIV(self):
        return self.getTotalOI() + self.getTotalVolume()

    def getCallOIVRatio(self):
        try:
            return round((self.getTotalCallOI() / self.getTotalCallVolume()), 2)
        except:
            return 0.0

    def getPutOIVRatio(self):
        try:
            return round((self.getTotalPutOI() / self.getTotalPutVolume()), 2)
        except:
            return 0.0

    def getTotalOIVRatio(self):
        try:
            return round((abs(self.getTotalOI() / self.getTotalVolume())), 2)
        except:
            return 0.0

    def __repr__(self):
        return f'{self.expirations_list}'
    
def createChainFromCSV(ticker='', ts_csv=None, ts_df= None, chain_csv=None, log_flag=False):
    return OptionChain(
        ticker=ticker,
        ts_csv_out=ts_csv,
        ts_df=ts_df,
        fromCSV=True,
        logging=log_flag,
        chain_csv_out=chain_csv
    )

def createChainAsCSV(ticker='', ts_out=None, ts_df=None, chain_out=None, log_flag=False):
    chain = OptionChain(
        ticker=ticker,
        ts_csv_out=ts_out,
        ts_df=ts_df,
        fromCSV=False,
        logging=log_flag,
        chain_csv_out=chain_out
    )
    del(chain)

if __name__ == '__main__':
    pass