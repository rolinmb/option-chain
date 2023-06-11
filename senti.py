from finmath import sma, ema, dema
import os
import time
from datetime import datetime
from math import isnan
from senti_config import *
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt
import nltk
# nltk.downloader.download('vader_lexicon') #only needed first run
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Parse HTML tables (returned from BeautifulSoup) for data to analyze. 
# Returns news as list of lists (headlines per ticker per day)
def parse_tables(tbls):
    print('\nParsing fetched data:')
    parsed_tables = []
    for fname, tbl in tbls.items():
        for tr in [e for e in tbl.findAll('tr') if e.a is not None]:
            headline = tr.a.get_text()
            t = fname.split('_')[0]
            dt_string = tr.td.text.split()
            if len(dt_string) == 1:
                now = datetime.now()
                date = now.strftime('%M-%d-%y')
                time = now.strftime('%H:%M')
            else:
                date = dt_string[0]
                time = dt_string[1][:-2]
            print('* %s %s %s Headline: %s\n'%(t, date, time, headline))
            parsed_tables.append([t, date, time, headline])
    print('* Successfully parsed all fetched data')
    return parsed_tables

# Process already parsed tables {post parsed_tables() call}.
# Returns parsed and scored news-table
def score_tables(parsed_tbls):
    print('\nCreating sentiment scores:')
    vader = SentimentIntensityAnalyzer()
    vader.lexicon.update(new_words)
    cols = ['ticker', 'date', 'time', 'headline']
    parsed_scored_tbls = pd.DataFrame(parsed_tbls, columns=cols)
    scores = parsed_scored_tbls['headline'].apply(vader.polarity_scores).tolist()
    scores_df = pd.DataFrame(scores)
    parsed_scored_tbls = parsed_scored_tbls.join(scores_df, rsuffix='_right')
    parsed_scored_tbls['date'] = pd.to_datetime(parsed_scored_tbls.date).dt.date
    return parsed_scored_tbls

# For all days, get the daily average score, or set daily avg to 0 if no data.
# Returns same DataFrame with new 'Daily Mean' column
def getDailyAvg(scores_df):
    daily_avg = []
    for i in range(scores_df.shape[0]):
        daily_score = 0.0
        in_news = 0
        for t in scores_df.columns:
            if not isnan(scores_df[t][i]):
                in_news += 1
                daily_score += scores_df[t][i]
        if in_news > 0:
            daily_avg.append(daily_score/in_news)
        else:
            daily_avg.append(0)
    scores_df['Daily Mean'] = daily_avg
    return scores_df
    
def fetch_headlines_html():
    fv_url = 'https://finviz.com/quote.ashx?t='
    headlines_dict = {}
    # Fetching all tickers (in senti_config.py)
    print('\nFetching headline data from FinViz:')
    for t in FULL_TICKERS:
        print('\t* Fetching ticker %s'%t)
        t_url = fv_url + t
        req = Request(url=t_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:20.0)'})
        resp = urlopen(req)
        html = BeautifulSoup(resp, 'html.parser')
        table = html.find(id='news-table')
        headlines_dict[t] = table
        time.sleep(3.777)
    return headlines_dict

def eval_headlines(parsed_hdlns_dict, csv_out):
    parsed_scored_news = score_tables(parsed_hdlns_dict) 
    mean_scores = parsed_scored_news.groupby(['ticker', 'date']).mean(numeric_only=True)
    mean_scores = mean_scores.unstack()
    mean_scores = mean_scores.xs('compound',axis='columns').transpose() # Reshape Scores DataFrame
    mean_scores = getDailyAvg(mean_scores) # Calculate Daily Avg Sentiment Score across all Tickers used
    print(' * Successfully scored all headlines for every ticker')
    print('\nWriting all score data to %s:'%csv_out)
    mean_scores.to_csv('csv_outputs/senti/sentiment_results.csv') # Save Scores (DataFrame) as CSV
    print('\t* Successfully written to %s'%csv_out)
    return mean_scores

if __name__ == '__main__':
    start = time.time()
    csv_out = 'csv_outputs/senti/sentiment_results.csv'
    news_tbl_dict = fetch_headlines_html() # Fetching all Tickers (in data.py)  
    parsed_news_dict = parse_tables(news_tbl_dict) # Formatting html into lists
    evaluated_df = eval_headlines(parsed_news_dict, csv_out) # Analyze/Process with weights given in data.py 
    # Build Plots & Show
    print('\nPlotting Sentiment Results:')
    fig = plt.figure()
    plt.xlabel('Date')
    plt.ylabel('Score')
    plt.plot(evaluated_df['Daily Mean'],color='red',label='Calculated Daily Mean')
    plt.plot(sma(evaluated_df['Daily Mean'], 56),color='green',label='SMA(56)')
    plt.plot(sma(evaluated_df['Daily Mean'], 112),color='green',label='SMA(112)')
    plt.plot(sma(evaluated_df['Daily Mean'], 224),color='cyan',label='SMA(224)')
    plt.plot(ema(evaluated_df['Daily Mean'], 42),color='blue',label='EMA(42)')
    plt.plot(dema(evaluated_df['Daily Mean'], 42),color='black',label='DEMA(42)',linestyle=':')
    plt.axhline(y=0.0,color='black',linestyle='solid')
    plt.title('Daily Average Finviz News Sentiment Score')
    plt.grid()
    plt.legend(title='Technical Indicators')
    plt.show()
    plt.close()
    print('\nTotal Program Runtime: '+str(round(time.time()-start,2))+' seconds.')