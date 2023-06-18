from finoptions import OptionChain
from finmath import CND, PDF, BlackScholes
from av import fetchSeriesData
import numpy as np
from pandas import read_csv
import matplotlib.pyplot as plt

# theta = (r*V) - (r*S*delta) - ((sigma**2 * S**2 * gamma)/2)
def dvdt(v,iv,cp=True,S=100.0,K=100.0,T=1.0,q=0.0,r=0.01):
    try:
        d1 = (np.log(S/K)+(r+(v*v/2.0))*T)/(v*np.sqrt(T))
        d2 = d1-(v*np.sqrt(T))
        if cp:
            return (r*v) - (r*S*np.exp(-1.0*q*T)*CND(d1)) - ((iv*iv*S*S*(iv*np.exp(-1.0*q*T)*PDF(d2)))/2)
        else:
            return (r*v) + (r*S*np.exp(-1.0*q*T)*CND(-1.0*d1)) - ((iv*iv*S*S*(iv*np.exp(-1.0*q*T)*PDF(d2)))/2)
    except:
        print('\n[dvdt() err]\n')
        return 0.0

def runge_kutta4(tseries,option,h,N):
    t = np.zeros(N)
    Y = np.zeros(N)
    S = np.zeros(N)
    t[0] = 0.0
    v0 = max(0.01,option.getLast(),option.getBid(),option.getAsk(),option.getMid())
    Y[0] = v0
    S[0] = tseries.iloc[0]
    ffr = 0.0525
    for n in range(0,N-1):
        k1 = dvdt(
            Y[n],
            option.getIV(),
            cp=option.isCall(),
            S=S[n],
            K=option.getStrike(),
            T=option.getTTE(),
            q=option.getDivYield(),
            r=ffr
        )
        k2 = dvdt(
            Y[n]+(h*(k1/2)),
            option.getIV(),
            cp=option.isCall(),
            S=S[n],
            K=option.getStrike(),
            T=option.getTTE()-(h/2),
            q=option.getDivYield(),
            r=ffr
        )
        k3 = dvdt(
            Y[n]+(h*(k2/2)),
            option.getIV(),
            cp=option.isCall(),
            S=S[n],
            K=option.getStrike(),
            T=option.getTTE()-(h/2),
            q=option.getDivYield(),
            r=ffr
        )
        k4 = dvdt(
            Y[n]+(h*k3),
            option.getIV(),
            cp=option.isCall(),
            S=S[n],
            K=option.getStrike(),
            T=option.getTTE()-h,
            q=option.getDivYield(),
            r=ffr
        )
        Y[n+1] = Y[n] + ((h/6.0)*(k1+(2*k2)+(2*k3)+k4))
        t[n+1] = t[n] - h
        d1 = (np.log(S[n]/option.getStrike())+(ffr+(Y[n+1]*Y[n+1]/2.0))*t[n+1])/(Y[n+1]*np.sqrt(t[n+1]))
        d2 = d1-(Y[n+1]*np.sqrt(t[n+1]))
        deriv = ((ffr*Y[n+1])-option.getTheta()-((option.getIV()*option.getStrike()*np.exp(-1.0*(t[n+1])*ffr)*PDF(d2))/(2*np.sqrt(t[n+1]))))/(ffr*option.getDelta())
        S[n+1] = S[n] + deriv
    return Y,t

if __name__ == '__main__':
    ticker = 'AAPL'
    ts_csv = 'csv_outputs/ohlc/%s_adj_tseries.csv'%ticker
    chain_csv = 'csv_outputs/chains/%s_chain.csv'%ticker
    fetchSeriesData( # Rewrite series .csv out each time
        ticker=ticker,
        adj_flag=True,
        logging=False,
        ts_csv_out=ts_csv
    )
    ts_df = read_csv(ts_csv)
    chain = OptionChain(
        ticker=ticker,
        ts_csv_out=ts_csv,
        ts_df=ts_df,
        fromCSV=True, # Rewrite chain .csv out each time
        chain_csv_out=chain_csv,
        logging=False
    )
    calls = chain.getAllCalls()
    # puts = chain.getAllPuts()
    h = 1/260 # time-step stize (one trading day [260/yr])
    n = 10000 # how many steps to iterate
    [Vcall,t] = runge_kutta4(ts_df['Adj. Close'],calls[-1],h,n)
    plt.figure()
    plt.grid()
    plt.plot(t,Vcall,'v',label='Simulated Contract Price')
    plt.title('Call Option Runge-Kutta 4 Simulation')
    plt.legend()
    plt.xlabel('Time to Expriation (years)')
    plt.ylabel('Contract Price ($)')
    plt.show()