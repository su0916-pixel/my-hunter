import streamlit as st
import requests
import pandas as pd
import numpy as np
import time
from datetime import datetime

st.set_page_config(
    page_title="AI 全市場合約獵手 Pro v2.5",
    page_icon="🏆",
    layout="wide"
)

st.title("🏆 AI 全市場合約多空排行榜 (全自動實時跳動版)")
st.caption("全自動掃描全市場前 50 大熱門合約幣種 · 隨時間自動更新報價與勝率評分 · 僅供交易輔助參考")

@st.cache_data(ttl=20)
def scan_market_fast():
    # 使用 CoinGecko 全球無地域限制批量行情接口（一次請求直接拿 50 個幣種 1H / 24H / 7D 數據，絕不超速）
    p1 = "https://api." + "coingecko.com"
    p2 = "/api/v3/coins/markets?vs_currency=usd&order=volume_desc&per_page=50&page=1&price_change_percentage=1h,24h,7d"
    headers = {"Accept": "application/json", "User-Agent": "Mozilla/5.0"}

    try:
        res = requests.get(p1 + p2, headers=headers, timeout=10)
        if res.status_code != 200:
            return []
        coins = res.json()
    except Exception:
        return []

    results = []
    stable_coins = {"USDT", "USDC", "FDUSD", "DAI", "TUSD", "USDE", "PYUSD", "BUSD"}

    for c in coins:
        symbol = c.get("symbol", "").upper()
        if not symbol or symbol in stable_coins:
            continue

        price = float(c.get("current_price") or 0)
        if price <= 0:
            continue

        c1h = float(c.get("price_change_percentage_1h_in_currency") or 0)
        c24h = float(c.get("price_change_percentage_24h_in_currency") or 0)
        c7d = float(c.get("price_change_percentage_7d_in_currency") or 0)
        vol_24h = float(c.get("total_volume") or 0)
        mcap = float(c.get("market_cap") or 1)
        high_24h = float(c.get("high_24h") or price)
        low_24h = float(c.get("low_24h") or price)

        # 計算換手率 (24H成交量 / 市值，越高代表主力資金越活躍)
        turnover = (vol_24h / mcap) * 100 if mcap > 0 else 0

        # 計算目前價格在 24H 高低點區間的位置 (0% = 最低點, 100% = 最高點)
        range_pos = ((price - low_24h) / (high_24h - low_24h) * 100) if high_24h > low_24h else 50.0

        # ================= AI 量化評分模型 =================
        short_score = 40
        short_reasons = []

        long_score = 40
        long_reasons = []

        # 1. 短線 1 小時急漲 / 急跌動能
        if c1h >= 2.0:
            short_score += 22
            short_reasons.append(f"1H急漲+{c1h:.1f}%短線過熱")
        elif c1h >= 1.0:
            short_score += 10
            short_reasons.append(f"1H偏強+{c1h:.1f}%")

        if c1h <= -2.0:
            long_score += 22
            long_reasons.append(f"1H急跌{c1h:.1f}%超賣區")
        elif c1h <= -1.0:
            long_score += 10
            long_reasons.append(f"1H回調{c1h:.1f}%")

        # 2. 日內區間極端位置 (摸頂防回調 / 探底博反彈)
        if range_pos >= 92:
            short_score += 18
            short_reasons.append(f"逼近24H最高點({range_pos:.0f}%位置)")
        elif range_pos <= 8:
            long_score += 18
            long_reasons.append(f"逼近24H最低點({range_pos:.0f}%位置)")

        # 3. 24H 暴漲暴跌乖離率
        if c24h >= 10:
            short_score += 15
            short_reasons.append(f"日內暴漲+{c24h:.1f}%易獲利了結")
        elif c24h <= -10:
            long_score += 15
            long_reasons.append(f"日內深跌{c24h:.1f}%具反彈空間")

        # 4. 資金換手活躍度加權 (高換手代表合約流動性佳、波動大)
        if turnover >= 25:
            short_score += 10
            long_score += 10
            short_reasons.append(f"主力高換手({turnover:.0f}%)")
            long_reasons.append(f"主力高換手({turnover:.0f}%)")

        results.append({
            "幣種": symbol,
            "現價": price,
            "1H漲跌": round(c1h, 2),
            "24H漲跌": round(c24h, 2),
            "日內位置(%)": round(range_pos, 1),
            "換手率(%)": round(turnover, 1),
            "做空評分": min(short_score, 99),
            "做空依據": " + ".join(short_reasons) if short_reasons else "動能中性觀望",
            "做多評分": min(long_score, 99),
            "做多依據": " + ".join(long_reasons) if long_reasons else "動能中性觀望"
        })

    return results

with st.sidebar:
    st.header("⚙️ AI 策略與即時更新")
    auto_refresh = st.toggle("🟢 開啟全自動即時跳動", value=True)
    refresh_sec = st.slider("自動刷新間隔 (秒)", 20, 120, 30, 5)
    stop_loss_pct = st.slider("建議停損幅度 (%)", 1.0, 5.0, 2.0, 0.5)
    take_profit_pct = st.slider("建議止盈幅度 (%)", 2.0, 15.0, 4.0, 0.5)
    if st.button("🔄 立即手動刷新"):
        st.cache_data.clear()
        st.rerun()
    st.divider()
    st.warning("⚠️ **合約風控鐵律**：\n1. 務必使用「逐倉模式」\n2. 進場同時掛好停損單\n3. 評分高代表盈虧比佳，非 100% 必勝")

with st.spinner("🤖 AI 正在極速掃描全市場前 50 大活躍合約幣種..."):
    market_data = scan_market_fast()

if not market_data:
    st.error("行情介面忙碌中，請稍候 10 秒自動重試，或點擊左上角選單「立即手動刷新」。")
else:
    df = pd.DataFrame(market_data)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.success(f"🟢 實時監控中（最後更新：`{now_str}` · 每 `{refresh_sec}` 秒自動跳動）｜共掃描 {len(df)} 個活躍幣種")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🔴 AI 最佳【做空】機會 TOP 5")
        short_top = df.sort_values(by="做空評分", ascending=False).head(5)
        for idx, row in short_top.iterrows():
            price = row["現價"]
            sl = price * (1 + stop_loss_pct / 100)
            tp = price * (1 - take_profit_pct / 100)
            fmt = f"${price:,.4f}" if price < 10 else f"${price:,.2f}"
            sl_fmt = f"${sl:,.4f}" if price < 10 else f"${sl:,.2f}"
            tp_fmt = f"${tp:,.4f}" if price < 10 else f"${tp:,.2f}"

            with st.container(border=True):
                st.markdown(f"### 📉 {row['幣種']}/USDT ｜ 勝率評分：**`{row['做空評分']} 分`**")
                st.markdown(f"**進場參考價**：`{fmt}` ｜ **1H漲跌**：`{row['1H漲跌']:+.2f}%` ｜ **24H**：`{row['24H漲跌']:+.2f}%`")
                st.markdown(f"🎯 **建議止盈**：`{tp_fmt}` (-{take_profit_pct}%) ｜ 🛡️ **嚴格停損**：`{sl_fmt}` (+{stop_loss_pct}%)")
                st.caption(f"🔍 **AI 觸發訊號**：{row['做空依據']}")

    with col2:
        st.subheader("🟢 AI 最佳【做多】機會 TOP 5")
        long_top = df.sort_values(by="做多評分", ascending=False).head(5)
        for idx, row in long_top.iterrows():
            price = row["現價"]
            sl = price * (1 - stop_loss_pct / 100)
            tp = price * (1 + take_profit_pct / 100)
            fmt = f"${price:,.4f}" if price < 10 else f"${price:,.2f}"
            sl_fmt = f"${sl:,.4f}" if price < 10 else f"${sl:,.2f}"
            tp_fmt = f"${tp:,.4f}" if price < 10 else f"${tp:,.2f}"

            with st.container(border=True):
                st.markdown(f"### 📈 {row['幣種']}/USDT ｜ 勝率評分：**`{row['做多評分']} 分`**")
                st.markdown(f"**進場參考價**：`{fmt}` ｜ **1H漲跌**：`{row['1H漲跌']:+.2f}%` ｜ **24H**：`{row['24H漲跌']:+.2f}%`")
                st.markdown(f"🎯 **建議止盈**：`{tp_fmt}` (+{take_profit_pct}%) ｜ 🛡️ **嚴格停損**：`{sl_fmt}` (-{stop_loss_pct}%)")
                st.caption(f"🔍 **AI 觸發訊號**：{row['做多依據']}")

    st.divider()
    st.subheader("📊 全市場活躍幣種即時量化總表")
    display_df = df[["幣種", "現價", "1H漲跌", "24H漲跌", "日內位置(%)", "換手率(%)", "做空評分", "做多評分"]].copy()
    st.dataframe(display_df, use_container_width=True, hide_index=True)

if auto_refresh:
    time.sleep(refresh_sec)
    st.cache_data.clear()
    st.rerun()
