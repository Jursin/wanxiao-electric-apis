# 完美校园电量查询接口

示例脚本用法：

```bash
python wanxiao.py --account 学号 --customercode 学校编码 [--week N | --month N]
```

`account`、`customercode` 参数必填，优先级：命令行参数 > .env > 终端环境变量。

从 APP 打开“智能水电”页面时 `AloneEntrance` 请求的响应头 location 里有 `customerid`，也可用 [`decrypt.py`](decrypt.py) 解 APP/微信小程序 抓包的 `SWAEEncryptServlet` 请求的请求体得到。

## 调用方式

`POST https://xqh5.17wanxiao.com/smartWaterAndElectricityService/SWAEServlet`


**请求头：**

```http
Content-Type: application/x-www-form-urlencoded
X-Requested-With: com.newcapec.mobile.ncp
Origin: https://xqh5.17wanxiao.com
Referer: https://xqh5.17wanxiao.com/userwaterelecmini/index.html
```

**请求体：**

```properties
param={"cmd":"接口","account":"学号", ...}
customercode=学校编码
method=接口
command=OWNWaterElecService
```

`method` 与 `param.cmd` 必须一致，`param` 内除 `cmd`、`account` 外，是各接口自己的参数。

**响应：**

```json
{"code_":0,"result_":"true","message_":"获取成功！","body":"{...}"}
```

`result_` 非 `"true"` 即按 `message_` 抛错；`body` 是 JSON 字符串，需二次 `json.loads`；`body` 内的 `result`（`"0"` 成功）与 `message` 各接口含义相同。

## 接口

### getbindroom — 获取绑定房间

方法 `get_bind_room()`，无额外参数。

| 响应 `body` 字段 | 含义 |
| --- | --- |
| `existflag` | `"1"` 单房间，`"2"` 多房间（房间列表在 `roomlist`，元素结构相同） |
| `roomfullname` | 房间全路径，下划线分隔 |
| `roomverify` | 房间标识，后续接口必传 |
| `detaillist[].businesstype` | 业务类型，后续接口必传 |
| `detaillist[].use` / `odd` | 累计量 / 剩余量（度） |

### h5_getstuindexpage — 获取首页数据

方法 `get_index_page(roomverify)`，`roomverify` 可传空串。

| 响应 `body.modlist[]` 字段 | 含义 |
| --- | --- |
| `devicename` | 表具型号 |
| `todayuse` | 今日用量（度，数字） |
| `odd` | 余额（度，数字） |
| `price` | 电价（元/度） |

另含 `weekuselist`（本周每日用量）、`monthuselist`（历史月度用量）、`sumbuy`、`linestatus`、`isshowpay` 等。

### gettimeusedetail — 获取区间用量

方法 `get_time_use_detail(roomverify, businesstype, startdate, enddate)`，日期格式 `YYYY-MM-DD`。

| 响应 `body` 字段 | 含义 |
| --- | --- |
| `sumuse` | 区间合计用量（度，字符串） |
| `dayuselist[].date` / `use` | 日期 / 当日用量（度，数字） |
| `dayuselist[].firstcolldate` / `lastcolldate` | 当日首末次抄表时间 |

### getusedetail — 获取月度用量

方法 `get_use_detail(roomverify, businesstype, yearmonth)`，`yearmonth` 格式 `YYYY-MM`。

返回 `monthuse`（当月总用量）与 `dayuselist`，字段为 `daydate` / `dayuse`，其余同上。

## 备注

- 字段类型以实际返回为准：`odd`、`use` 在多数接口是字符串（如 `"28.4"`），在 `modlist`、`dayuselist` 中是数字。
