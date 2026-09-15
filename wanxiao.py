import argparse
import json
import os
import requests
import sys
from datetime import datetime, timedelta
from calendar import monthrange
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://xqh5.17wanxiao.com/smartWaterAndElectricityService/SWAEServlet"
HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded",
    "X-Requested-With": "com.newcapec.mobile.ncp",
    "Origin": "https://xqh5.17wanxiao.com",
    "Referer": "https://xqh5.17wanxiao.com/userwaterelecmini/index.html",
}

BLUE = "\033[34m"
RED = "\033[31m"
CYAN = "\033[36m"
RESET = "\033[0m"

def blue(s):
    return f"{BLUE}{s}{RESET}"

def cyan(s):
    return f"{CYAN}{s}{RESET}"

def red(s):
    return f"{RED}{s}{RESET}"

COMMAND = "OWNWaterElecService"

class Wanxiao:
    def __init__(self, account, customercode):
        self.account = account
        self.customercode = customercode

    def call(self, method, **kw):
        param = {"cmd": method, "account": self.account, **kw}
        data = {
            "param": json.dumps(param, ensure_ascii=False),
            "customercode": self.customercode,
            "method": method,
            "command": COMMAND,
        }
        resp = requests.post(BASE_URL, data=data, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        r = resp.json()
        if r.get("result_") != "true":
            raise RuntimeError(r.get("message_") or r)
        body = r.get("body")
        if isinstance(body, str):
            try:
                body = json.loads(body)
            except ValueError:
                pass
        if not isinstance(body, dict):
            raise RuntimeError(f"返回数据格式异常: {body!r}")
        return body

    def get_bind_room(self):
        return self.call("getbindroom")

    def get_index_page(self, roomverify=""):
        return self.call("h5_getstuindexpage", roomverify=roomverify)

    def get_use_detail(self, roomverify, businesstype, yearmonth):
        return self.call("getusedetail", roomverify=roomverify,
                         businesstype=businesstype, yearmonth=yearmonth)

    def get_time_use_detail(self, roomverify, businesstype, startdate, enddate):
        return self.call("gettimeusedetail", roomverify=roomverify,
                         businesstype=businesstype,
                         startdate=startdate, enddate=enddate)

def iter_rooms(bind_room):
    if str(bind_room.get("existflag")) == "2" and bind_room.get("roomlist"):
        items = bind_room["roomlist"]
    else:
        items = [bind_room]
    for it in items:
        yield it.get("roomfullname"), it.get("roomverify"), it.get("detaillist", [])

def query_room(wx, roomfullname, roomverify, details, show_week=0, show_month=0):
    print(blue(f"[房间] {roomfullname}"))
    businesstype = int(details[0].get("businesstype", 0)) if details else 0

    try:
        mod = (wx.get_index_page(roomverify).get("modlist") or [{}])[0]
        print(blue(f"[设备] {mod.get('devicename')}"))
        today_use = mod.get("todayuse")
        if today_use is not None:
            print(blue(f"[今日用电] {today_use} 度"))
        print(blue(f"[剩余电量] {mod.get('odd')} 度"))
        print(blue(f"[电价] {mod.get('price')} 元/度"))
    except Exception as exc:
        print(red(f"[error] 首页数据获取失败: {exc}"))

    if show_week:
        _print_week(wx, roomverify, businesstype, show_week)
    if show_month:
        _print_month(wx, roomverify, businesstype, show_month)

def _print_week(wx, roomverify, businesstype, num):
    now = datetime.now()
    start = now - timedelta(days=now.weekday())
    end = start + timedelta(days=6)
    week_no = now.isocalendar()[1]
    try:
        d = wx.get_time_use_detail(roomverify, businesstype,
                                   start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
        t = float(d.get("sumuse", 0))
        print(cyan(f"[{week_no} 周] 总用量：{t:.2f} 度 平均值：{round(t / 7, 2):.2f} 度"))
        for w in reversed(d.get("dayuselist") or []):
            print(f"[{w.get('date')}] {w.get('use')} 度")
    except Exception as exc:
        print(red(f"[error] 第 {week_no} 周数据获取失败: {exc}"))

    for i in range(1, num):
        e = start - timedelta(days=7 * (i - 1) + 1)
        s = e - timedelta(days=6)
        wn = e.isocalendar()[1]
        try:
            d = wx.get_time_use_detail(roomverify, businesstype,
                                       s.strftime("%Y-%m-%d"), e.strftime("%Y-%m-%d"))
            t = float(d.get("sumuse", 0))
            print(cyan(f"[{wn} 周] 总用量：{t:.2f} 度 平均值：{round(t / 7, 2):.2f} 度"))
            for w in reversed(d.get("dayuselist") or []):
                print(f"[{w.get('date')}] {w.get('use')} 度")
        except Exception:
            break

def _print_month(wx, roomverify, businesstype, num):
    now = datetime.now()
    # 当前月份
    year, month = now.year, now.month
    days = monthrange(year, month)[1]
    start_date = datetime(year, month, 1)
    end_date = datetime(year, month, days)
    try:
        d = wx.get_time_use_detail(roomverify, businesstype,
                                   start_date.strftime("%Y-%m-%d"),
                                   end_date.strftime("%Y-%m-%d"))
        t = float(d.get("sumuse", 0))
        print(cyan(f"[{month:02d} 月] 总用量：{t:.2f} 度 平均值：{round(t / days, 2):.2f} 度"))
        for w in reversed(d.get("dayuselist") or []):
            print(f"[{w.get('date')}] {w.get('use')} 度")
    except Exception as exc:
        print(red(f"[error] {year}-{month:02d} 数据获取失败: {exc}"))

    # 历史月份
    for i in range(1, num):
        dt = now - timedelta(days=30 * i)
        year, month = dt.year, dt.month
        days = monthrange(year, month)[1]
        start_date = datetime(year, month, 1)
        end_date = datetime(year, month, days)
        try:
            d = wx.get_time_use_detail(roomverify, businesstype,
                                       start_date.strftime("%Y-%m-%d"),
                                       end_date.strftime("%Y-%m-%d"))
            t = float(d.get("sumuse", 0))
            print(cyan(f"[{month:02d} 月] 总用量：{t:.2f} 度 平均值：{round(t / days, 2):.2f} 度"))
            for w in reversed(d.get("dayuselist") or []):
                print(f"[{w.get('date')}] {w.get('use')} 度")
        except Exception:
            break

def main():
    p = argparse.ArgumentParser(description="完美校园电量查询")
    p.add_argument("--account", default=os.environ.get("ACCOUNT"))
    p.add_argument("--customercode", type=int,
                   default=int(os.environ.get("CUSTOMERCODE", "0")))
    p.add_argument("--week", nargs="?", const=1, type=int, default=0, metavar="N")
    p.add_argument("--month", nargs="?", const=1, type=int, default=0, metavar="N")
    args = p.parse_args()

    if args.week and args.month:
        sys.exit(red("[error] week 参数与 month 参数二选一"))
    if not args.account:
        sys.exit(red("[error] 缺失 --account 必要参数"))
    if not args.customercode:
        sys.exit(red("[error] 缺失 --customercode 必要参数"))

    wx = Wanxiao(args.account, args.customercode)
    bind_room = wx.get_bind_room()
    for room in iter_rooms(bind_room):
        query_room(wx, *room, show_week=args.week, show_month=args.month)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass