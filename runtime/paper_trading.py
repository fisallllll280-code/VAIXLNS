"""Offline simulated trading arithmetic; no market/network/order connector."""
import math
from runtime.supervised_runtime import digest

def simulate_paper_trades(prices, *, initial_cash=10000.0, fee_bps=10):
    values=list(prices)
    if len(values)<2 or any(not isinstance(p,(int,float)) or isinstance(p,bool) or not math.isfinite(p) or p<=0 for p in values): raise ValueError("POSITIVE_FINITE_PRICE_SERIES_REQUIRED")
    if not isinstance(initial_cash,(int,float)) or isinstance(initial_cash,bool) or not math.isfinite(initial_cash) or initial_cash<=0: raise ValueError("INVALID_INITIAL_CASH")
    if not isinstance(fee_bps,int) or isinstance(fee_bps,bool) or not 0<=fee_bps<=1000: raise ValueError("INVALID_FEE_BPS")
    cash=float(initial_cash); units=0.0; events=[]
    for i in range(1,len(values)):
        previous,price=values[i-1],values[i]
        if price<previous and units==0:
            units=cash/(price*(1+fee_bps/10000)); spent=units*price*(1+fee_bps/10000); cash-=spent
            events.append({"event":"PAPER_BUY","index":i,"price":price,"units":units,"cash_after":cash,"mode":"SIMULATED"})
        elif price>previous and units>0:
            cash+=units*price*(1-fee_bps/10000); events.append({"event":"PAPER_SELL","index":i,"price":price,"units":units,"cash_after":cash,"mode":"SIMULATED"}); units=0.0
    result={"mode":"SIMULATED","orders_are_paper_only":True,"real_money_orders":False,"financial_credentials_used":False,"initial_cash":initial_cash,"final_equity":round(cash+units*values[-1],8),"simulated_pnl":round(cash+units*values[-1]-initial_cash,8),"currency":"UNSPECIFIED_UNITS","trade_events":events,"input_series_hash":digest(values)}
    result["result_hash"]=digest(result); return result
