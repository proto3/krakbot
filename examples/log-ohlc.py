#!/usr/bin/env python3
import matplotlib.pyplot as plt
from matplotlib.finance import candlestick2_ohlc
import krakenex
import decimal
import time

k = krakenex.API()

def now():
    return decimal.Decimal(time.time())

def merge_hist(old_h, new_h):
    if(not old_h):
        old_h = new_h
        return

    old_it = len(old_h)-1
    new_it = 0

    while(old_h[old_it][0] > new_h[new_it][0]):
        old_it -= 1

    if(old_h[old_it][0] < new_h[new_it][0]):
        old_it += 1

    while(new_it < len(new_h)):
        if(old_it < len(old_h)):
            if(old_h[old_it][0] == new_h[new_it][0]):
                #replace
                old_h[old_it] = new_h[new_it]
            elif(old_h[old_it][0] > new_h[new_it][0]):
                #insert
                old_h.insert(old_it, new_h[new_it])
            else:
                new_it -= 1
        else:
            # append new_it
            old_h.append(new_h[new_it])
        old_it += 1
        new_it += 1

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
ohlc_hist = list()
while True:
    ohlc_req = request_ohlc(pair, since)

    since = ohlc_req['result']['last'] - 60

    if(not ohlc_hist):
        ohlc_hist = ohlc_req['result'][pair]
    else:
        merge_hist(ohlc_hist, ohlc_req['result'][pair])

    opens =  [row[1] for row in ohlc_hist]
    highs =  [row[2] for row in ohlc_hist]
    lows =   [row[3] for row in ohlc_hist]
    closes = [row[4] for row in ohlc_hist]
    vwap =   [row[5] for row in ohlc_hist]

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
