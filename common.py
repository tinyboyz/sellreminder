import pandas as pd
import json
import requests
from datetime import datetime

state_no_quote = -1
state_continue = 0
state_stop_loss = 1
state_stop_retrace = 2
state_stop_hold = 3

highest_changed = False

# 得到持有天数和三个价格[持有天数, 最高价, 最低价, 最高价后的最低价]
def get_3_prices(stock, buy_date):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36 QIHU 360SE'
    }
    url = 'http://61.152.230.191/api/qt/stock/kline/get?ut=fa5fd1943c7b386f172d6893dbfba10b&secid={}&klt=5&fqt=1&beg={}&end={}&fields1=f1,f2&fields2=f51,f53,f54,f55'
    start_date = buy_date.strftime('%Y%m%d')
    end_date = datetime.today().strftime('%Y%m%d')
    r = requests.get(url.format(stock, start_date, end_date), headers=headers)
    d = json.loads(r.content)
    df = pd.DataFrame(d['data']['klines'])
    df[['date', 'close', 'high', 'low']] = df[0].str.split(",", expand=True)
    df.date = pd.to_datetime(df.date)
    df.high = pd.to_numeric(df.high)
    df.low = pd.to_numeric(df.low)
    return [len(df.date.dt.date.unique()), df.high.max(), df.low.min(), df.loc[df['high'].idxmax():, 'low'].min()]


# 卖出条件:
# 1. 收益率小于等于-6% 卖出
# 2. 收益率大于等于+9% 持有 直到最高收益率回撤+5% 卖出
# 3. 持股第9个交易日，收盘价卖出
# 返回值: '操作', '价格'
def should_sell(stock, buy_date, max_hold_days, hold_days, highest, lowest, lowest_aft_highest, buy_price):
    sina_code = stock.replace('0.', 'sz').replace('1.', 'sh')
    headers = {'Referer': 'http://finance.sina.com.cn'}
    url = 'http://hq.sinajs.cn/list={}'.format(sina_code)
    r = requests.get(url, headers=headers)
    if r.status_code != 200 or len(r.text.split(',')) < 6:
        return (state_no_quote, 0)
    price = float(r.text.split(',')[3])
    high = float(r.text.split(',')[4])
    low = float(r.text.split(',')[5])

    global highest_changed

    # 最高最低价变化检测
    if low < lowest:
        # 最低价变化时，最高价回撤价格应该被更新，同时历史最低价也应该被更新，同时不管最高价变动标识是否设置都重置
        lowest_aft_highest = lowest = low
        highest_changed = False
    elif high > highest:
        # 最高价变化时，最高价回撤价格应该被清空并重新用持续的最新价较低值赋值直到当日最低价变动为止，同时历史最高价也应该被更新
        lowest_aft_highest = price
        highest_changed = True
        highest = high
    elif highest_changed:
        # 最高价变化后不断的更新回撤的最低价格
        lowest_aft_highest = min(price, lowest_aft_highest)

    # summary = '代码:{}, 买入日期:{}, 最新价格:{:.2f}, 持有日期:{}天, 买入价格:{}, 最新收益率:{:.2f}%, 止损收益率:{:.2f}%, 止损价格:{:.2f}, 最高收益率:{:.2f}%, 最高收益回撤:{:.2f}%, 最高回撤卖出价:{:.2f}'
    # print(summary.format(stock[2:], buy_date.strftime('%Y-%m-%d'), price, hold_days, buy_price,
    #                      (price - buy_price) / buy_price * 100,
    #                      (lowest - buy_price) / buy_price * 100, buy_price * 0.94,
    #                      (highest - buy_price) / buy_price * 100,
    #                      (lowest_aft_highest - highest) / highest * 100, highest * 0.95))

    # 确认卖点或继续持有
    if (lowest - buy_price) / buy_price <= -0.06:
        # 止损卖出
        return '止损卖出', buy_price * 0.94
    elif (highest - buy_price) / buy_price >= 0.09 and (highest - lowest_aft_highest) / highest > 0.05:
        # 涨幅超过9%，最高价回扯5%卖出
        return '回扯卖出', highest * 0.95
    elif hold_days >= max_hold_days:
        # 持有到期卖出
        return '到期卖出', price
    elif (highest - buy_price) / buy_price >= 0.09 and highest_changed:
        # 更新卖出价格
        return '更新卖价', highest * 0.95
    else:
        return '继续持有', 0

# 微信通知
# message:内容
def notify_wechat(message):
    requests.get('https://api.day.app/4UPTFKupLPA2FznSbB7M7R/{}'.format(message))
