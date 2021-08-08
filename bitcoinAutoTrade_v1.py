import time
import pyupbit
import datetime
import requests
from logger import Logger

access = "GQ48oKiTje9EdY7ZM7Ek4gbMm9Mi4tmbL9LIr7D7"
secret = "8yqUpmXMo0mk6SS9NpiXyrnHuizklVrvBWXrrnx0"


class Order:
    symbol: str
    '''"idle", "trading"'''
    state: str
    time: datetime
    price: int
    ticket: str

    def __init__(self, _symbol, _state):
        self.symbol = _symbol
        self.state = _state
        self.ticket = "KRW-" + _symbol

    def recycle(self):
        self.state = "idle"
        self.price = 0

    def to_string(self):
        return str(self.symbol) + " " + str(self.state) \
               + " " + str(self.time) + " " + str(self.price)


def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minutes" + str(time_interval), count=1)
    _price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return _price


def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minutes" + str(time_interval), count=1)
    start_time = df.index[0]
    return start_time


def get_balance(upbit, ticker):
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0


def get_avg_price(upbit, ticker):
    """평균 구매 가격"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['avg_buy_price'] is not None:
                return float(b['avg_buy_price'])
            else:
                return 0
    return 0


def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]


def is_time_equal(a: datetime.datetime, b: datetime.datetime):
    if a.hour == b.hour and a.minute == b.minute and a.second == b.second:
        return True
    else:
        return False


time_interval = 5
max_krw = 10000
sell_up_th = 1.2
sell_down_th = 0.9


def main():
    logger = Logger()
    logger.info("Starting")

    # 로그인
    upbit = pyupbit.Upbit(access, secret)
    logger.info("autotrade start")

    symbol = "DOGE"
    order = Order(symbol, "idle")

    base_time = get_start_time(order.ticket)
    logger.info("base " + str(base_time))

    time_out = base_time + datetime.timedelta(minutes=time_interval)
    target_price = get_target_price(order.ticket, 0.5)

    b = get_balance(upbit, symbol)
    p = get_current_price(order.ticket)
    logger.info("bid balance " + str(b) + ", " + str(p))

    if b * p > 5000:
        order.state = "trading"
        order.price = p
        order.time = base_time
        logger.info("set order with stored " + order.to_string())

    # 자동매매 시작
    while True:
        try:
            now = datetime.datetime.now()
            current_price = get_current_price(order.ticket)
            print("]]]now " + str(now) + ", tick " + str(time_out) + ", t_price " + str(
                target_price) + ", c_price " + str(current_price) + ", start_time " + str(get_start_time(order.ticket)))

            if order.state == "idle":
                if is_time_equal(now, time_out):
                    target_price = get_target_price(order.ticket, 0.5)
                    time_out = now + datetime.timedelta(minutes=time_interval)
                    logger.info(str(now) + ", target_price = " + str(target_price))

                if target_price <= current_price:
                    krw = get_balance(upbit, "KRW")
                    logger.info(str(now) + ", krw = " + str(krw))
                    trading_krw = min(krw, max_krw)
                    if trading_krw > 5000:
                        upbit.buy_market_order(order.ticket, trading_krw * 0.9995)
                        order.state = "trading"
                        order.price = current_price
                        order.time = now
                        logger.info(str(now) + ", buy : " + str(current_price) + " , order : " + order.to_string())
            else:
                print(">>>now " + str(now) + ", comp " + str(
                    order.time + datetime.timedelta(minutes=time_interval)) + ", o_price " + str(
                    order.price) + ", c_price " + str(current_price))

                if now >= order.time + datetime.timedelta(minutes=time_interval) \
                        and (order.price * sell_up_th < current_price\
                             or order.price * sell_down_th > current_price):  ## 가격이 마이너스 일때도 심각하게. 고민해야함,

                    balance = get_balance(upbit, order.symbol)
                    if balance * current_price > 5000:
                        upbit.sell_market_order(order.ticket, balance * 0.9995)
                        order.recycle()
                        logger.info(str(now) + ", sell : " + str(current_price) + " , order : " + order.to_string())
                        ##판매 후 target_price 업데이트 필요.
                        target_price = get_target_price(order.ticket, 0.5)
                        time_out = now + datetime.timedelta(minutes=time_interval)
            time.sleep(1)
        except Exception as e:
            print(e)
            time.sleep(1)


if __name__ == "__main__":
    main()
