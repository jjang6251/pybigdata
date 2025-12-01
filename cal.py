import os
import requests
import pandas as pd
import matplotlib.pyplot as plt


# ------------------------------
# 1. 데이터 수집 (Upbit → DataFrame)
# ------------------------------
def fetch_upbit_data(market="KRW-BTC", count=365):
    """
    Upbit 일봉 캔들 데이터 가져오기 (기본: 최근 365일)
    """
    url = f"https://api.upbit.com/v1/candles/days?market={market}&count={count}"
    headers = {"Accept": "application/json"}
    res = requests.get(url, headers=headers)
    res.raise_for_status()  # 에러 시 예외 발생

    data = res.json()
    df = pd.DataFrame(data)

    # 날짜 및 필요한 컬럼 정리
    df["date"] = pd.to_datetime(df["candle_date_time_kst"])
    df = df[[
        "date",
        "opening_price",
        "high_price",
        "low_price",
        "trade_price",
        "candle_acc_trade_volume",
    ]]
    df = df.sort_values("date").reset_index(drop=True)
    return df


# ------------------------------
# 2. 엑셀 저장
# ------------------------------
def save_to_excel(df, filename="data/btc_data.xlsx"):
    """
    DataFrame을 엑셀로 저장 (data 폴더 자동 생성)
    """
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    df.to_excel(filename, index=False)
    print(f"[INFO] 엑셀 파일 저장 완료 → {filename}")


# ------------------------------
# 3. 변동성 레짐 분석
# ------------------------------
def analyze_regimes(df, stats_filename="output/regime_stats.csv"):
    """
    변동성 계산 → 분위수 기반 레짐(LOW/MID/HIGH) 분류 → 통계 저장
    """
    # 변동성: (고가 - 저가) / 종가
    df["volatility"] = (df["high_price"] - df["low_price"]) / df["trade_price"]

    # 일간 수익률: (오늘 종가 - 어제 종가) / 어제 종가
    df["return"] = df["trade_price"].pct_change()

    # 분위수 기준으로 레짐 나누기 (30%, 70%)
    low_thr = df["volatility"].quantile(0.3)
    high_thr = df["volatility"].quantile(0.7)

    def label_regime(v):
        if v <= low_thr:
            return "LOW_VOL"
        elif v >= high_thr:
            return "HIGH_VOL"
        else:
            return "MID_VOL"

    df["regime"] = df["volatility"].apply(label_regime)

    # output 폴더 생성
    os.makedirs(os.path.dirname(stats_filename), exist_ok=True)

    # 레짐별 통계량 저장
    stats = df.groupby("regime")[["return", "volatility", "candle_acc_trade_volume"]].mean()
    stats.to_csv(stats_filename)
    print(f"[INFO] 레짐 통계 저장 완료 → {stats_filename}")

    return df


# ------------------------------
# 4. 시각화 함수들
# ------------------------------
def plot_price_with_regimes(df, filename="output/price_with_regimes.png"):
    """
    비트코인 가격 + 레짐별 색 구분 그래프
    """
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    plt.figure(figsize=(16, 6))
    plt.plot(df["date"], df["trade_price"], label="BTC Price", linewidth=1)

    # 레짐별 색 (원하는 색으로 바꿔도 됨)
    regimes = {
        "LOW_VOL": "blue",
        "MID_VOL": "gray",
        "HIGH_VOL": "red",
    }

    for regime, color in regimes.items():
        mask = df["regime"] == regime
        plt.scatter(df["date"][mask], df["trade_price"][mask], s=8, label=regime, color=color)

    plt.title("BTC Price with Volatility Regimes")
    plt.xlabel("Date")
    plt.ylabel("Price (KRW)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    print(f"[INFO] 가격 + 레짐 그래프 저장 → {filename}")
    plt.close()


def plot_volatility_hist(df, filename="output/volatility_hist.png"):
    """
    변동성 분포 히스토그램
    """
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    plt.figure(figsize=(10, 5))
    plt.hist(df["volatility"].dropna(), bins=30)
    plt.title("BTC Daily Volatility Distribution")
    plt.xlabel("Volatility")
    plt.ylabel("Frequency")
    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    print(f"[INFO] 변동성 히스토그램 저장 → {filename}")
    plt.close()


def plot_regime_boxplot(df, filename="output/regime_boxplot.png"):
    """
    레짐별 수익률 박스플롯
    """
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    plt.figure(figsize=(8, 5))
    df.boxplot(column="return", by="regime")
    plt.title("Daily Return by Volatility Regime")
    plt.suptitle("")  # 상단 기본 타이틀 제거
    plt.xlabel("Regime")
    plt.ylabel("Daily Return")
    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    print(f"[INFO] 레짐별 수익률 박스플롯 저장 → {filename}")
    plt.close()


# ------------------------------
# 5. 메인 실행부
# ------------------------------
def main():
    print("[STEP 1] Upbit에서 BTC 데이터 수집 중...")
    df = fetch_upbit_data(market="KRW-BTC", count=365)

    print("[STEP 2] 엑셀 파일로 저장 중...")
    save_to_excel(df, filename="data/btc_data.xlsx")

    print("[STEP 3] 변동성 레짐 분석 중...")
    df = analyze_regimes(df, stats_filename="output/regime_stats.csv")

    print("[STEP 4] 시각화 이미지 생성 중...")
    plot_price_with_regimes(df, filename="output/price_with_regimes.png")
    plot_volatility_hist(df, filename="output/volatility_hist.png")
    plot_regime_boxplot(df, filename="output/regime_boxplot.png")

    print("\n✅ 모든 작업 완료!")
    print(" - data/btc_data.xlsx")
    print(" - output/regime_stats.csv")
    print(" - output/price_with_regimes.png")
    print(" - output/volatility_hist.png")
    print(" - output/regime_boxplot.png")


if __name__ == "__main__":
    main()