import requests
import pandas as pd
import os

def get_upbit_data_to_excel(market="KRW-BTC", count=200, filename="btc_data.xlsx"):
    url = f"https://api.upbit.com/v1/candles/days?market={market}&count={count}"
    headers = {"Accept": "application/json"}
    res = requests.get(url, headers=headers).json()

    df = pd.DataFrame(res)
    df["date"] = pd.to_datetime(df["candle_date_time_kst"])

    df = df[[
        "date",
        "opening_price",
        "high_price",
        "low_price",
        "trade_price",
        "candle_acc_trade_volume"
    ]]

    df = df.sort_values("date")

    # 🔍 디버깅용 출력
    print("현재 작업 디렉토리:", os.getcwd())
    print("저장될 파일 절대 경로:", os.path.abspath(filename))

    df.to_excel(filename, index=False)
    print(f"엑셀 파일 저장 완료: {filename}")

get_upbit_data_to_excel()