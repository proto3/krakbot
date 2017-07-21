#!/usr/bin/env python3
import numpy as np
import pandas as pd

import matplotlib.dates as da
import matplotlib.pyplot as plt
# from matplotlib.finance import candlestick2_ohlc
import matplotlib.ticker as ticker

import krakenex
import decimal
import time
import datetime

k = krakenex.API()

def psar(barsdata, iaf = 0.02, maxaf = 0.08):
    length = len(barsdata)
    dates = list(barsdata.index)
    high = list(barsdata['high'])
    low = list(barsdata['low'])
    close = list(barsdata['close'])
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

    # return {"dates":dates, "high":high, "low":low, "close":close, "psar":psar, "psarbear":psarbear, "psarbull":psarbull}
    return {"psar":psar, "psarbear":psarbear, "psarbull":psarbull}


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
            response = k.query_public('OHLC', req = {'pair': pair, 'since': since, 'interval' : 5})
        except:
            print("Request failed, retry...")
    return response

pair = 'XETHZEUR'
since = str(now() - 3600000)
ohlc_data = None

# read_data = pd.read_csv("data.csv").set_index('time')
# ohlc_data = read_data

start = True
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

    if(not isinstance(ohlc_data, pd.DataFrame)):
        ohlc_data = request_data
    else:
        append_ohlc(ohlc_data, request_data)

    # df.to_csv("data.csv")

    psar_data = psar(ohlc_data)

    # mdate = list()
    # for idx in ohlc_data.index:
    #     mdate.append(da.epoch2num(idx))
    #
    # fig, ax = plt.subplots()
    # candlestick2_ohlc(ax, ohlc_data['open'], ohlc_data['high'], ohlc_data['low'], ohlc_data['close'], width=0.6, colorup='g', colordown='r', alpha=1.0)
    # plt.plot(range(0,len(ohlc_data)), psar_data['psarbull'], color='k', marker='.')
    # plt.plot(range(0,len(ohlc_data)), psar_data['psarbear'], color='k', marker='.')
    # xdate = [datetime.datetime.fromtimestamp(i) for i in ohlc_data.index]
    #
    # ax.xaxis.set_major_locator(ticker.MaxNLocator(6))
    #
    # def mydate(x, pos):
    #     try:
    #         return xdate[int(x)]
    #     except IndexError:
    #         return ''
    #
    # ax.xaxis.set_major_formatter(ticker.FuncFormatter(mydate))
    #
    # fig.autofmt_xdate()
    # fig.tight_layout()
    #
    # plt.show()

    if(psar_data['psarbear'][-1] != None):
        print(datetime.datetime.fromtimestamp(ohlc_data.index[-1]).strftime('%Y-%m-%d %H:%M:%S'), "down")
    else:
        print(datetime.datetime.fromtimestamp(ohlc_data.index[-1]).strftime('%Y-%m-%d %H:%M:%S'), "up")

    time.sleep(20)
