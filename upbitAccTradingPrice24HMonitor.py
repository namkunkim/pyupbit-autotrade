import time
import pyupbit
import datetime

import requests
import schedule
from fbprophet import Prophet
from logger import Logger

access = "GQ48oKiTje9EdY7ZM7Ek4gbMm9Mi4tmbL9LIr7D7"
secret = "8yqUpmXMo0mk6SS9NpiXyrnHuizklVrvBWXrrnx0"


def regular_report():
    print(str(datetime.datetime.now()) + "regular_report")


def get_acc_trade_price_24h(ticker: str):
    try:
        url = "https://api.upbit.com/v1/ticker"
        querystring = {"markets": ticker}
        headers = {"Accept": "application/json"}
        response = requests.request("GET", url, headers=headers, params=querystring)
        res_json = response.json()
        print("### " + str(response) + " , " + str(res_json))
        acc_trade_price_24h = res_json[0]['acc_trade_price_24h']
        return acc_trade_price_24h
    except Exception as ex:
        print(ticker + " : " + str(ex))
        return None


def update_acc_trade_price_24h_top10():
    acc_trade_price_24h_top10 = []
    acc_trade_price_24h_list = []
    tickers = pyupbit.get_tickers(fiat="KRW")
    print(tickers)
    for i in range(12):
        ticker = tickers.pop()
        acc_trade_price_24h = get_acc_trade_price_24h(ticker)
        print(str(ticker) + " : " + str(acc_trade_price_24h))
        if acc_trade_price_24h is None:
            logger.error(str(datetime.datetime.now()) + ticker + " is wrong")
        else:
            acc_trade_price_24h_list.append([ticker, acc_trade_price_24h])
        #time.sleep(1)

    print("acc_trade_price_24h_list : " + str(acc_trade_price_24h_list))
    acc_trade_price_24h_list.sort(key=lambda r: r[1], reverse=True)
    print(">>acc_trade_price_24h_list : " + str(acc_trade_price_24h_list))
    for i in range(10):
        item = acc_trade_price_24h_list.pop(0)
        acc_trade_price_24h_top10.append(item)
    return acc_trade_price_24h_top10


# logger 설정
logger = Logger()
logger.info("Starting")

# 로그인
upbit = pyupbit.Upbit(access, secret)
acc_trade_price_24h_top10_store = []

##매 단위 시간 마다 레포팅
schedule.every(1).minutes.do(lambda: regular_report)
# 자동매매 시작
while True:
    try:
        now = datetime.datetime.now()
        print(str(now) + ":")
        schedule.run_pending()
        top10 = update_acc_trade_price_24h_top10()
        print("top10 : " + str(top10))
        time.sleep(1)
    except Exception as e:
        print(e)
        time.sleep(1)
