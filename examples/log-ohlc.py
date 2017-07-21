#!/usr/bin/env python3
import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
from matplotlib.finance import candlestick2_ohlc

import krakenex
import decimal
import time

k = krakenex.API()

def psar(barsdata, iaf = 0.02, maxaf = 0.2):
    length = len(barsdata)
    dates = list(barsdata['Date'])
    high = list(barsdata['High'])
    low = list(barsdata['Low'])
    close = list(barsdata['Close'])
    psar = close[0:len(close)]
    psarbull = [None] * length
    psarbear = [None] * length
    bull = True
    af = iaf
    ep = low[0]
    hp = high[0]
    lp = low[0]

    for i in range(2,length):
        if bull:
            psar[i] = psar[i - 1] + af * (hp - psar[i - 1])
        else:
            psar[i] = psar[i - 1] + af * (lp - psar[i - 1])

        reverse = False

        if bull:
            if low[i] < psar[i]:
                bull = False
                reverse = True
                psar[i] = hp
                lp = low[i]
                af = iaf
        else:
            if high[i] > psar[i]:
                bull = True
                reverse = True
                psar[i] = lp
                hp = high[i]
                af = iaf

        if not reverse:
            if bull:
                if high[i] > hp:
                    hp = high[i]
                    af = min(af + iaf, maxaf)
                if low[i - 1] < psar[i]:
                    psar[i] = low[i - 1]
                if low[i - 2] < psar[i]:
                    psar[i] = low[i - 2]
            else:
                if low[i] < lp:
                    lp = low[i]
                    af = min(af + iaf, maxaf)
                if high[i - 1] > psar[i]:
                    psar[i] = high[i - 1]
                if high[i - 2] > psar[i]:
                    psar[i] = high[i - 2]

        if bull:
            psarbull[i] = psar[i]
        else:
            psarbear[i] = psar[i]

    return {"dates":dates, "high":high, "low":low, "close":close, "psar":psar, "psarbear":psarbear, "psarbull":psarbull}


def now():
    return decimal.Decimal(time.time())

def append_ohlc(prev_data, cur_data):
    for idx in cur_data.index:
        prev_data.loc[idx] = cur_data.loc[idx]
    prev_data.sort_index(inplace=True)

def request_ohlc(pair, since):
    response = None
    while(response == None):
        try:
            response = k.query_public('OHLC', req = {'pair': pair, 'since': since, 'interval': 15})
        except:
            print("Request failed, retry...")
    return response

def sar(ohlc_hist, sar_hist, i, acc_factor):
    if(sar_hist[i-1] < float(ohlc_hist[i-1][2])):
        return sar_hist[i-1] + acc_factor * (float(ohlc_hist[i][2]) - sar_hist[i-1])
    else:
        return sar_hist[i-1] + acc_factor * (float(ohlc_hist[i][3]) - sar_hist[i-1])



pair = 'XETHZEUR'
since = str(now() - 3600000)
ohlc_data = None

read_data = pd.read_csv("data.csv").set_index('time')
ohlc_data = read_data

while True:
    #request
    ohlc_req = request_ohlc(pair, since)

    #set since for next request with overlay
    since = ohlc_req['result']['last'] - 60

    #convert string fields to float
    for elt in ohlc_req['result'][pair]:
        for i in range(1, 7):
            elt[i] = float(elt[i])

    #create DataFrame
    request_data = pd.DataFrame(ohlc_req['result'][pair], columns=['time','open', 'high', 'low', 'close', 'vwap', 'volume', 'count']).set_index('time')

    # df.to_csv("data.csv")

    # if(ohlc_data == None):
    #     ohlc_data = request_data
    # else:
    ohlc_data = merge_ohlc(ohlc_data, request_data)

    print(ohlc_data)
    print(ohlc_data.loc[1499946300,"open"])

    exit(0)

    sar_hist = [0.0]
    for i in range(1, len(ohlc_hist)):
        sar_hist.append(sar(ohlc_hist, sar_hist, i, 0.02))

    fig, ax = plt.subplots()
    candlestick2_ohlc(ax, opens, highs, lows, closes, width=1, colorup='g', colordown='r', alpha=1.0)
    # plt.plot(vwap, color='k')
    plt.plot(sar_hist, color='k', linestyle=":")
    # plt.ion()
    plt.show()

    for block in ohlc_hist:
        print(block)

    time.sleep(20)
