from numpy import exp, log, sqrt
from math import isnan
from scipy import optimize
import scipy.stats
import pandas as pd

def sma(data,t): # Simple MA
    return data.rolling(t).mean()

def ema(data,t): # Exponential MA
    return data.ewm(span=t,adjust=False).mean()

def dema(data,t): # Double-Exponential MA
    e = ema(data,t)
    de = ema(e,t)
    return (2.0*e)-de

def typicalPrice(h,l,c): # Typical Price of asset
	return (h+l+c)/3
	
def averagePrice(o,h,l,c): # Average Price of Open, High, Low, Close
	return (o+h+l+c)/4
	
def tsi(c,r,s): # True Strength Index
	mom = []
	for i in range(1,c.size):
		m = c.iloc[i]-c.iloc[i-1]
		mom.append(m)
	mom = pd.Series(mom,index=c.index.values[1:])
	ema1 = ema(ema(mom,r),s)
	ema2 = ema(ema(abs(mom),r),s)
	return 100*(ema1/ema2)

def roc(data,t): # Rate-of-Change Indicator
	rates = []
	for i in range(t-1,data.size):
		rate = (data.iloc[i]-data.iloc[i-t])/data.iloc[i-t]
		rates.append(rate)
	return pd.Series(rates,index=data.index.values[t-1:])

def approxDeriv(data,t): # Finite-Difference Approximation of 1st Derivative
	approx = []
	rates = roc(data,t)
	for i in range(1,rates.size):
		if(i == rates.size-1):
			next = round(data.iloc[-1]+rates.iloc[-1],2)
			approx.append((next-data.iloc[-2])/2)
		else:
			approx.append((data.iloc[i+1]-data.iloc[i-1])/2)
	
	return pd.Series(approx,index=rates.index.values[1:])

def calc_histvol(close_data): # Standard Deviation of Underlying (or Hist. Vol)
    log_returns = log(close_data/close_data.shift())
    return log_returns.std()*252**0.5

def CND(X): # Normal Cumulative Distribution Funciton [ N(X) ]
    return float(scipy.stats.norm.cdf(X))

def PDF(X): # Normal Probability Density Function [derivative of CND(X) or N'(X) ]
    return float(scipy.stats.norm.pdf(X))

# Solution to Black-Scholes Option Pricing Model
def BlackScholes(v, c_p=True, S=100., K=100., T=1., q=0.0, R=0.01, logging=False):
    try:
        d1 = (log(S/K)+(R+(v*v/2.0))*T)/(v*sqrt(T))
        d2 = d1-(v*sqrt(T))
        if c_p: # True = Call
            return (S*exp(-1.0*q*T)*CND(d1))-(K*exp(-1.0*R*T)*CND(d2))
        else:   # False = Put
            return (K*exp(-1.0*R*T)*CND(-d2))-(S*exp(-1.0*q*T)*CND(-1.0*d1))
    except:
        if logging:
            print('BlackScholes(): Couldn''t calculate Option Contract Value; setting IV to 0.0')
        return 0.0
    
# Find zeros to the equation: f(x) = B.S.(x) - actual_contract_price
def calc_impvol(V=5., cp=True, s=100., k=100., t=1., r=0.01, logging=True):
    f = lambda x: BlackScholes(x, cp, s, k, t, r, logging=logging) - V
    try:
        return optimize.brentq(f, 0., 5.)
    except:
        if logging:
            print('calc_impvol(): Couldn''t find IV for TTE %s $%s strike; f(0) = %s f(1) = %s have same signs, setting IV to 0.0'%(t, k, f(0), f(5)))
        return 0.0

def calc_delta(iv, c_p=True, S=100., K=100., T=1., q=0.0, r=0.01): # Different fomula for Call of Put
    d1 = (log(S/K)+(r+(iv*iv/2.0))*T)/(iv*sqrt(T))
    if c_p:  # True = call
        return exp(-1.0*q*T)*CND(d1)
    else:    # False = put
        return -1.0*exp(-1.0*q*T)*CND(-d1)

def calc_elasticity(delta, V=0.01, S=100.): # V = option contract value, S = underlying price
    return delta*(S/V)

def calc_vega(iv, S=100., K=100., T=1., r=0.01): # Vega formula is same for Call/Put
    d1 = (log(S/K)+(r+(iv*iv/2.0))*T)/(iv*sqrt(T))
    # return S*PDF(d1) # also valid
    d2 = d1-(iv*sqrt(T))
    vega_ret = K*PDF(d2)*sqrt(T)
    return 0.0 if isnan(vega_ret) else vega_ret

def calc_theta(iv, c_p=True, S=100., K=100., T=1., q=0.0, r=0.01):
    d1 = (log(S/K)+(r+(iv*iv/2.0))*T)/(iv*sqrt(T))
    d2 = d1-(iv*sqrt(T))
    if c_p:  # True = call
        c_ret = (((-1.0*exp(-1.0*q*T))*((S*PDF(d1)*iv)/(2*sqrt(T)))) - (r*K*exp(-1.0*r*T)*CND(d2))) + (q*S*exp(-1.0*q*T)*CND(d1))
        return 0.0 if isnan(c_ret) else c_ret
    else:    # False = put
        p_ret = (((-1.0*exp(-1.0*q*T))*((S*PDF(d1)*iv)/(2*sqrt(T)))) + (r*K*exp(-1.0*r*T)*CND(-1.0*d2))) - (q*S*exp(-1.0*q*T)*CND(-1.0*d1))
        return 0.0 if isnan(p_ret) else p_ret

def calc_rho(iv, c_p=True, S=100., K=100., T=1., r=0.01):
    d1 = (log(S/K)+(r+(iv*iv/2.0))*T)/(iv*sqrt(T))
    d2 = d1-(iv*sqrt(T))
    if c_p:
        c_ret = K*T*exp(-1.0*r*T)*CND(d2)
        return 0.0 if isnan(c_ret) else c_ret 
    else:
        p_ret = -1.0*K*T*exp(-1.0*r*T)*CND(-1.0*d2)
        return 0.0 if isnan(p_ret) else p_ret

def calc_epsilon(iv, c_p=True, S=100., K=100., T=1., q=0.0, r=0.01):
    d1 = (log(S/K)+(r+(iv*iv/2.0))*T)/(iv*sqrt(T))
    if c_p:
        c_ret = -1.0*S*T*exp(-1.0*q*T)*CND(d1)
        return 0.0 if isnan(c_ret) else c_ret
    else:
        p_ret = S*T*exp(-1.0*r*T)*CND(-1.0*d1)
        return 0.0 if isnan(p_ret) else p_ret

def calc_gamma(iv, S=100., K=100., T=1., r=0.01):
    d1 = (log(S/K)+(r+(iv*iv/2.0))*T)/(iv*sqrt(T))
    # return PDF(d1)/(S*iv*sqrt(T)) # also valid
    d2 = d1-(iv*sqrt(T))
    gam_ret = K*exp(-1.0*r*T)*(PDF(d2)/(S*S*iv*sqrt(T)))
    return 0.0 if isnan(gam_ret) else gam_ret

def calc_vanna(iv, vega, S=100., K=100., T=1., r=0.01): # Vanna formula is same for Call/Put
    d1 = (log(S/K)+(r+(iv*iv/2.0))*T)/(iv*sqrt(T))
    van_ret = (vega/S)*(1.0-(d1/(iv*sqrt(T))))
    return 0.0 if isnan(van_ret) else van_ret

def calc_charm(iv, c_p=True, S=100., K=100., T=1., q=0.0, r=0.01): # Different formula for Call or put
    d1 = (log(S/K)+(r+(iv*iv/2.0))*T)/(iv*sqrt(T))
    d2 = d1-(iv*sqrt(T))
    if c_p: # True = call
        c_ret = (q*exp(-1.0*q*T)*CND(d1)) - ((exp(-1.0*q*T)*PDF(d1))*(((2.0*(r-q)*T)-(d2*iv*sqrt(T)))/(2.0*T*iv*sqrt(T))))
        return 0.0 if isnan(c_ret) else c_ret
    else:
        p_ret = (-1.0*q*exp(-1.0*q*T)*CND(-1.0*d1)) - ((exp(-1.0*q*T)*PDF(d1))*(((2.0*(r-q)*T)-(d2*iv*sqrt(T)))/(2.0*T*iv*sqrt(T))))
        return 0.0 if isnan(p_ret) else p_ret

def calc_vomma(iv, vega, S=100., K=100., T=1., r=0.01): # Vomma formula is same for Call/Put
    d1 = (log(S/K)+(r+(iv*iv/2.0))*T)/(iv*sqrt(T))
    d2 = d1-(iv*sqrt(T))
    vom_ret = (vega*d1*d2)/iv
    return 0.0 if isnan(vom_ret) else vom_ret

def calc_veta(iv, S=100., K=100., T=1., q=0.0, r=0.01): # Veta formula is same for Call/Put
    d1 = (log(S/K)+(r+(iv*iv/2.0))*T)/(iv*sqrt(T))
    d2 = d1-(iv*sqrt(T))
    factor = -1.0*S*exp(-1.0*q*T)*PDF(d1)*sqrt(T)
    veta_ret = factor*(q+(((r-q)*d1)/(iv*sqrt(T)))-((1.0+(d1*d2))/(2.0*T)))
    return 0.0 if isnan(veta_ret) else veta_ret

def calc_speed(gamma, iv, S=100., K=100., T=1., r=0.01): # Speed formula is same for Call/Put
    d1 = (log(S/K)+(r+(iv*iv/2.0))*T)/(iv*sqrt(T))
    speed_ret = (-1.0*gamma/S)*((d1/(iv*sqrt(T)))+1.0)
    return 0.0 if isnan(speed_ret) else speed_ret

def calc_zomma(gamma, iv, S=100., K=100., T=1., r=0.01): # Zomma formula is same for Call/Put
    d1 = (log(S/K)+(r+(iv*iv/2.0))*T)/(iv*sqrt(T))
    d2 = d1-(iv*sqrt(T))
    zom_ret = gamma*(((d1*d2)-1.0)/iv)
    return 0.0 if isnan(zom_ret) else zom_ret

def calc_color(iv, S=100., K=100., T=1., q=0.0, r=0.01): # Color formula is same for Call/Put
    d1 = (log(S/K)+(r+(iv*iv/2.0))*T)/(iv*sqrt(T))
    d2 = d1-(iv*sqrt(T))
    factor1 = -1.0*exp(-1.0*q*T)*PDF(d1)/(2.0*S*T*iv*sqrt(T))
    factor2 = (((2.0*(r-q)*T)-(d2*iv*sqrt(T)))/(iv*sqrt(T)))*d1
    clr_ret = factor1*((2.0*q*T)+1.0+factor2)
    return 0.0 if isnan(clr_ret) else clr_ret

def calc_ultima(iv, vega, S=100., K=100., T=1., r=0.01): # ultima formula is same for Call/Put
    d1 = (log(S/K)+(r+(iv*iv/2.0))*T)/(iv*sqrt(T))
    d2 = d1-(iv*sqrt(T))
    factor = (-1.0*vega)/(iv**2)
    ult_ret = factor*(((d1*d2)*(1.0-(d1*d2)))+(d1**2)+(d2**2))
    return 0.0 if isnan(ult_ret) else ult_ret

def option_value_theoretical(delta, gamma, iv, S=100., r=0.01):
    return (iv+(0.5*iv*iv*S*S*gamma)+(r*S*delta))/r

if __name__ == '__main__':
    pass