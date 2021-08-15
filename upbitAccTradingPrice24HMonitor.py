import datetime
import json
import time

import pyupbit
import requests

from logger import Logger

def get_acc_trade_price_24h(ticker: str):
    try:
        url = "https://api.upbit.com/v1/ticker"
        querystring = {"markets": ticker}
        headers = {"Accept": "application/json"}
        response = requests.request("GET", url, headers=headers, params=querystring)
        res_json = response.json()
        ##print("### " + str(response) + " , " + str(res_json))
        acc_trade_price_24h = res_json[0]['acc_trade_price_24h']
        return acc_trade_price_24h
    except Exception as ex:
        print(ticker + " : " + str(ex))
        return None


def update_acc_trade_price_24h_top10():
    acc_trade_price_24h_top10 = []
    acc_trade_price_24h_list = []
    tickers = pyupbit.get_tickers(fiat="KRW")

    for ticker in tickers:
        acc_trade_price_24h = get_acc_trade_price_24h(ticker)
        ##print(str(ticker) + " : " + str(acc_trade_price_24h))
        if acc_trade_price_24h is not None:
            acc_trade_price_24h_list.append([ticker, acc_trade_price_24h])
        time.sleep(0.1)

    acc_trade_price_24h_list.sort(key=lambda r: r[1], reverse=True)

    for i in range(10):
        item = acc_trade_price_24h_list.pop(0)
        acc_trade_price_24h_top10.append(item)
    return acc_trade_price_24h_top10


def get_report(stored, updated):
    report_msg = "report : "
    print("store : " + str(stored))
    print("updated : " + str(updated))

    # 신규 진입 체크
    for i in range(len(updated)):
        found = False
        for j in range(len(stored)):
            if updated[i][0] == stored[j][0]:
                found = True
                break
        if not found:
            report_msg += "\n" + str(updated[i][0]) + "is entered in top10"
            print(str(updated[i][0]) + " is entered in top10")

    # 내부 변동 체크 to top level
    for i in range(len(stored)):
        for j in range(i + 1, len(updated)):
            if stored[i][0] == updated[j][0]:
                report_msg += "\n" + str(stored[i][0]) + " is moved from " + i + " to " + j
                print(str(stored[i][0]) + " is moved from " + i + " to " + j)
                continue

    print(report_msg)

    if report_msg == "report : ":
        return None

    return report_msg


def send_report_to_me(report):
    url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
    # 사용자 토큰
    headers = {
        "Authorization": "Bearer kakaotalk access token"
    }

    data = {
        "template_object": json.dumps({"object_type": "text",
                                       "text": report,
                                       "link": {
                                           "web_url": "www.naver.com"
                                       }
                                       })
    }
    response = requests.post(url, headers=headers, data=data)
    print(response.status_code)
    if response.json().get('result_code') == 0:
        return '메시지를 성공적으로 보냈습니다.'
    else:
        return '메시지를 성공적으로 보내지 못했습니다. 오류메시지 : ' + str(response.json())


def main():
    # logger 설정
    logger = Logger()
    logger.info("Starting")

    acc_trade_price_24h_top10_store = update_acc_trade_price_24h_top10()
    while True:
        try:
            now = datetime.datetime.now()
            print(str(now) + ":")
            top10 = update_acc_trade_price_24h_top10()
            print("top10 : " + str(top10))
            report = get_report(acc_trade_price_24h_top10_store, top10)
            print("report : " + str(report))

            if report is not None:
                logger.info(str(now) + report)
                resp = send_report_to_me(report)
                logger.info(str(now) + " resp for kakaotalk - " + resp)
            acc_trade_price_24h_top10_store = top10
            time.sleep(30)
        except Exception as e:
            print(e)
            time.sleep(30)


if __name__ == "__main__":
    main()
