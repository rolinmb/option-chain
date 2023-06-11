from av import getQuoteAV
from sys import exit
from time import time, sleep
import os
import re
import requests
from requests.exceptions import ConnectionError
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

# for selenium webdriver
HEADLESS_ARG = Options()
HEADLESS_ARG.add_argument("--headless")
# other webpages/sources to potentially scrape when current method breaks
# CHAIN_BASE_URL = "https://www.optionistics.com/f/option_chains/" + ticker
CHAIN_BASE_URL = "https://bigcharts.marketwatch.com/quickchart/options.asp?symb="
# CHAIN_BASE_URL = "https://finance.yahoo.com/quote/" + ticker + "/options?p=" + ticker

LOG_FLAG_OPTIONS = [
    'Y', 'YES', 'T', 'TRUE',
    'L', 'LOG', 'LOGING', 'LOGGING',
    'N', 'NO', 'NONE', 'F','FALSE'
]

ADJ_FLAG_OPTIONS = [
    'Y', 'YES', 'T', 'TRUE',
    'ADJ', 'ADJUST',
    'N', 'NO', 'NONE', 'F', 'FALSE'
]

STOCK_TICKERS = [
     'AAPL', 'ABC', 'ABNB', 'ADM',
     'ADMA', 'ALB', 'APO', 'BAH',
     'BE', 'CBOE', 'CBT', 'CMP',
     'COIN', 'COST', 'CPNG', 'CRSP', 'CTVA',
     'CVS', 'DLTR', 'ETN', 'FDX',
     'GD', 'GOOG', 'HSY', 'HRL',
     'ICE', 'INTU', 'IR', 'IRM',
     'LAND','LIN', 'LQDA', 'MA', 'MMM',
     'MO', 'MPW', 'MSCI', 'MSFT',
     'NVO', 'RSG', 'SBUX', 'SCL',
     'SLCA', 'SWBI', 'SYK', 'TGT',
     'TSLA', 'ULTA', 'UWMC', 'V',
     'WCN', 'WM', 'WMG'
]

ETF_TICKERS = [
    'DIA','IWM','QQQ','SPY',
    'XLU','XLV','XHB','XPH','XRT','XLI',
    'XLF','XLK','XLK','XLRE','XLP',
    'EEM','FEZ','KIE','SOCL','ARKK','MJ',
    'TAN','ICLN','QYLD','JETS','IYT','TLT'
]

def getSoup(ticker, sTime, logging=True):
    chain_url = CHAIN_BASE_URL + ticker
    driver = webdriver.Firefox(options = HEADLESS_ARG)
    if logging:
        print('getSoup():\t* Selenium webdriver opening ''%s'''%chain_url)
    dt_start = time()
    driver.get(chain_url)
    if logging:
        print('getSoup():\t\t-> Selenium webdriver successfully requested ''%s'''%chain_url)
        print("getSoup():\t* Selenium webdriver fetching toggleables to make chains visible")
    toggles = driver.find_elements(By.CLASS_NAME, "ajaxpartial")
    if len(toggles[1:]) < 1:
        exit('getSoup():\t! ERROR: Couldn''t parse HTML from %s; %s is not optionable => calling sys.exit()'%(CHAIN_BASE_URL+ticker, ticker))
    for t in toggles[1:]:
        t.click()
        if logging:
            print(f'getSoup():\t\t---SLEEPING {sTime} SECONDS AFTER TOGGLE---')
        sleep(sTime)
    if logging:
        print('getSoup():\t\t-> Successfully toggled to make all expiries visible')
    toggled_html = driver.page_source
    driver.close()
    if logging:
        print(f'getSoup():\t\t<Took {round(time() - dt_start, 2)} to toggle everything; closed Selenium webriver>')
    return BeautifulSoup(toggled_html, "html.parser")

def stripCommas(s):
    return re.sub(',(?!\s+\d$)','',s)

def parsePrice(html):
    soup = BeautifulSoup(html, 'html.parser')
    valStr = soup.find('div', attrs={'class' : 'intraday__data'}).find('h2', recursive=False).find('bg-quote', recursive=False)
    content = [c.text for c in valStr]
    return float(stripCommas(''.join(content)))

def getQuoteMW(ticker):
    trys = 1
    quote_url = f'https://www.marketwatch.com/investing/stock/{ticker}?mod=search_symbol'
    while trys <= 5:
        try:
            s = requests.Session()
            resp = s.get(quote_url)
            s.close()
            html = resp.text
            price = parsePrice(html)
            return price
        except TypeError:
            
            print('getQuoteMW():\n\t! TYPE ERROR: %s potentially invalid ticker, couldn''t get quote from ''%s'''%(ticker, quote_url))
            return None
        except ConnectionError:
            print('getQuoteMW():\n\t! CONNECTION ERROR [Attempt %s]: Couldn''t get %s quote from ''%s''; reattempting...'%(trys, ticker, quote_url))
            trys += 1
        except AttributeError:
            try:
                return getQuoteAV(ticker)
            except:    
                exit('getQuoteMW():\t! ATTRIBUTE ERROR: %s most likely invalid; if not, potentially just unsupported by AlphaVantage, or lapse in web connection occurred => calling sys.exit()'%ticker)
    # If we maxed out our trys, try AlphaVantage API for quote
    try:
        return getQuoteAV(ticker)
    except Exception as E:
        exit('getQuoteMW():\n\t! CONNECTION ERROR: Max attemptes reached, couldn''t get %s quote from ''%s'' => calling sys.exit()'%(ticker, quote_url))

def validateTicker(ticker):
    if not ticker.isalpha() or len(ticker) > 5:
        exit('validateTicker():\t! INPUT ERROR: Non-alphabetical characters/too many characters entered for 1st argument ''ticker'' => calling sys.exit()')
    # Get quote to verify without AlphaVantage first
    q = getQuoteMW(ticker)
    if q is None:
        exit(f'validateTicker()\t! TYPE ERROR: {ticker} likely invalid => calling sys.exit()')

def is_float(num_str):
    try:
        float(num_str)
        return True
    except:
        return False
    
if __name__ == '__main__':
    pass