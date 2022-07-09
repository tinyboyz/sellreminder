# encoding=utf-8
import time
import schedule
import win32serviceutil
import win32service
import win32event
from datetime import datetime
from common import get_3_prices, should_sell, notify_wechat


class PythonService(win32serviceutil.ServiceFramework):
    # 服务名
    _svc_name_ = "ShouldSell"
    # 服务在windows系统中显示的名称
    _svc_display_name_ = "Should Sell"
    # 服务的描述
    _svc_description_ = "Should Sell"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.stock = '0.002977'
        self.buy_date = datetime(2022, 7, 8)
        self.buy_price = 44.40
        self.max_hold_days = 9

    def job_everyday_0915(self):
        self.hold_days, self.highest, self.lowest, self.lowest_aft_highest, = get_3_prices(self.stock, self.buy_date)
        schedule.every(3).seconds.until("15:00").do(self.job_everyday_0915_1500)
        notify_wechat('{}:{}:持有{}天'.format(self.stock, ' 初始化完成', self.hold_days))

    def job_everyday_0915_1500(self):
        # 判断是否卖出
        op, price = should_sell(self.stock, self.buy_date, self.max_hold_days, self.hold_days, self.highest,
                                self.lowest, self.lowest_aft_highest,
                                self.buy_price)
        if price != 0:
            notify_wechat('{}:{}:{}'.format(self.stock, op, price))

    def SvcDoRun(self):
        # 把自己的代码放到这里，就OK
        # 等待服务被停止
        schedule.every().day.at('09:15').do(self.job_everyday_0915)

        while win32event.WaitForSingleObject(self.hWaitStop, 1000) == win32event.WAIT_TIMEOUT:
            schedule.run_pending()


    def SvcStop(self):
        # 先告诉SCM停止这个过程
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        # 设置事件
        win32event.SetEvent(self.hWaitStop)


if __name__ == '__main__':
    # 括号里参数可以改成其他名字，但是必须与class类名一致；
    win32serviceutil.HandleCommandLine(PythonService)
