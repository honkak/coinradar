##############################################
# 업비트 급등코인 레이더 서비스 개발_2024.11.29 #
##############################################

import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from telegram import Bot

# Streamlit Secrets에서 민감한 정보 불러오기
TELEGRAM_BOT_TOKEN = st.secrets["telegram"]["TELEGRAM_BOT_TOKEN"]
CHAT_ID = st.secrets["telegram"]["CHAT_ID"]

# 텔레그램 봇 설정
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# 업비트 API에서 데이터 가져오기
def fetch_upbit_data(market="KRW-BTC", interval="minute30", count=50):
    url = f"https://api.upbit.com/v1/candles/{interval}"
    params = {"market": market, "count": count}
    response = requests.get(url, params=params)
    data = response.json()
    return pd.DataFrame([{
        "timestamp": datetime.fromisoformat(item['candle_date_time_kst']),
        "trade_price": item["trade_price"],
        "candle_acc_trade_volume": item["candle_acc_trade_volume"]
    } for item in data])

# 거래량 및 가격 변화율 계산
def calculate_trends(df):
    df = df.sort_values("timestamp")
    df["volume_change"] = df["candle_acc_trade_volume"].pct_change() * 100
    df["price_change"] = df["trade_price"].pct_change() * 100
    return df

# 조건 필터링
def filter_trends(df, volume_threshold, price_threshold):
    latest = df.iloc[-1]
    if latest["volume_change"] > volume_threshold and latest["price_change"] > price_threshold:
        return True, latest
    return False, latest

# 텔레그램 알림 보내기
def send_telegram_message(message):
    bot.send_message(chat_id=CHAT_ID, text=message)

# Streamlit UI
st.title("업비트 거래량 & 가격 분석")

# 사용자 입력
market = st.sidebar.selectbox("코인 선택", ["KRW-BTC", "KRW-ETH", "KRW-XRP"])
volume_threshold = st.sidebar.slider("거래량 증가율 기준 (%)", 0, 500, 200)
price_threshold = st.sidebar.slider("가격 상승률 기준 (%)", 0, 200, 50)

# 데이터 가져오기
st.write(f"현재 선택된 코인: {market}")
data = fetch_upbit_data(market)
trends = calculate_trends(data)

# 차트 표시
st.line_chart(trends.set_index("timestamp")[["trade_price"]], height=300)
st.line_chart(trends.set_index("timestamp")[["candle_acc_trade_volume"]], height=300)

# 조건 필터링 및 알림
detected, latest = filter_trends(trends, volume_threshold, price_threshold)
if detected:
    st.success("🚀 폭등 신호 감지!")
    alert_message = (
        f"폭등 신호 감지!\n"
        f"코인: {market}\n"
        f"가격 상승률: {latest['price_change']:.2f}%\n"
        f"거래량 증가율: {latest['volume_change']:.2f}%\n"
        f"현재 가격: {latest['trade_price']:.2f}원"
    )
    st.write(alert_message)
    send_telegram_message(alert_message)
else:
    st.warning("📉 현재 조건을 만족하는 신호가 없습니다.")

st.write("최근 데이터")
st.dataframe(trends)


