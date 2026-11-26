import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(
    page_title="AI 全市場合約獵手 Pro v2.0",
    page_icon="🏆",
    layout="wide"
)

st.title("🏆 AI 全市場合約多空排行榜 (OKX 實時掃描)")
st.caption("全自動掃描 OKX 前 40 大活躍合約 · 多維度量化評分 · 僅供交易輔助參考")

def calculate_rsi(closes, period=14):
    if len(closes) < period + 1:
        return 50.0
    deltas = np.diff(closes)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

@st.cache_data(ttl=60)
def scan_okx_market():
    base_url = "https://okx.com"
    tickers_res = requests.get(f"{base_url}/market/tickers?instType=SWAP", timeout=10).json()
    if tickers_res.get("code") != "0":
        return []
    
    usdt_swaps = [
        t for t in tickers_res["data"] 
        if t["instId"].endswith("-USDT-SWAP")
    ]
    usdt_swaps.sort(key=lambda x: float(x["volCcy24h"]) * float(x["last"]), reverse=True)
    top_coins = usdt_swaps[:40]

    results = []
    for item in top_coins:
        inst_id = item["instId"]
        coin = inst_id.replace("-USDT-SWAP", "")
        last_price = float(item["last"])
        open_24h = float(item["open24h"])
        change_24h = ((last_price - open_24h) / open_24h) * 100 if open_24h else 0

        try:
            kline_res = requests.get(f"{base_url}/market/candles?instId={inst_id}&bar=15m&limit=20", timeout=5).json()
            candles = kline_res.get("data", [])
            if len(candles) < 15:
                continue
            closes = [float(c[4]) for c in reversed(candles)]
            rsi_15m = calculate_rsi(closes)
            change_15m = ((closes[-1] - closes[-2]) / closes[-2]) * 100

            fr_res = requests.get(f"{base_url}/public/funding-rate?instId={inst_id}", timeout=5).json()
            fr = float(fr_res["data"][0]["fundingRate"]) * 100 if fr_res.get("data") else 0

            oi_res = requests.get(f"{base_url}/rubik/stat/contracts/open-interest-volume?ccy={coin}&period=15m", timeout=5).json()
            oi_data = oi_res.get("data", [])
            oi_change_15m = 0.0
            if len(oi_data) >= 2:
                curr_oi = float(oi_data[0][1])
                prev_oi = float(oi_data[1][1])
                oi_change_15m = ((curr_oi - prev_oi) / prev_oi) * 100 if prev_oi else 0

            short_score = 40
            short_reasons = []

            long_score = 40
            long_reasons = []

            if rsi_15m >= 72:
                short_score += 25
                short_reasons.append(f"15m嚴重超買(RSI:{rsi_15m:.0f})")
            elif rsi_15m >= 65:
                short_score += 12
                short_reasons.append(f"短線偏高(RSI:{rsi_15m:.0f})")

            if rsi_15m <= 28:
                long_score += 25
                long_reasons.append(f"15m嚴重超賣(RSI:{rsi_15m:.0f})")
            elif rsi_15m <= 35:
                long_score += 12
                long_reasons.append(f"短線超跌(RSI:{rsi_15m:.0f})")

            if change_15m < -0.5 and oi_change_15m > 0.8:
                short_score += 25
                short_reasons.append(f"主力放量開空(OI+{oi_change_15m:.1f}%)")
            elif change_15m > 0.5 and oi_change_15m > 0.8:
                long_score += 25
                long_reasons.append(f"大資金追多(OI+{oi_change_15m:.1f}%)")

            if fr >= 0.03:
                short_score += 15
                short_reasons.append(f"多軍擁擠(費率+{fr:.3f}%)")
            elif fr <= -0.02:
                long_score += 15
                long_reasons.append(f"空軍擁擠易軋空(費率{fr:.3f}%)")

            if change_24h >= 15:
                short_score += 10
                short_reasons.append(f"日內暴漲+{change_24h:.1f}%防回調")
            elif change_24h <= -15:
                long_score += 10
                long_reasons.append(f"日內深跌{change_24h:.1f}%博反彈")

            results.append({
                "幣種": coin,
                "現價": last_price,
                "24H漲跌": change_24h,
                "15mRSI": rsi_15m,
                "15m持倉變化": oi_change_15m,
                "資金費率": fr,
                "做空評分": min(short_score, 99),
                "做空依據": " + ".join(short_reasons) if short_reasons else "動能中性",
                "做多評分": min(long_score, 99),
                "做多依據": " + ".join(long_reasons) if long_reasons else "動能中性"
            })
        except Exception:
            continue

    return results

with st.sidebar:
    st.header("⚙️ AI 策略參數")
    stop_loss_pct = st.slider("建議停損幅度 (%)", 1.0, 5.0, 2.0, 0.5)
    take_profit_pct = st.slider("建議止盈幅度 (%)", 2.0, 15.0, 4.0, 0.5)
    if st.button("🔄 立即重新掃描全市場"):
        st.cache_data.clear()
        st.rerun()
    st.divider()
    st.warning("⚠️ **合約風控鐵律**：\n1. 務必使用「逐倉模式」\n2. 進場同時掛好停損單\n3. 評分高代表盈虧比佳，非 100% 必勝")

with st.spinner("🤖 AI 正在即時掃描 OKX 前 40 大熱門合約資金流向與 K 線..."):
    market_data = scan_okx_market()

if not market_data:
    st.error("暫時無法連線至 OKX 行情伺服器，請點擊左側「立即重新掃描」重試。")
else:
    df = pd.DataFrame(market_data)
    st.success(f"✅ 掃描完成！共分析 {len(df)} 個高流動性合約幣種（更新時間：{datetime.now().strftime('%H:%M:%S')}）")

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
                st.markdown(f"**進場參考價**：`{fmt}` ｜ **24H漲跌**：`{row['24H漲跌']:+.2f}%`")
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
                st.markdown(f"**進場參考價**：`{fmt}` ｜ **24H漲跌**：`{row['24H漲跌']:+.2f}%`")
                st.markdown(f"🎯 **建議止盈**：`{tp_fmt}` (+{take_profit_pct}%) ｜ 🛡️ **嚴格停損**：`{sl_fmt}` (-{stop_loss_pct}%)")
                st.caption(f"🔍 **AI 觸發訊號**：{row['做多依據']}")

    st.divider()
    st.subheader("📊 全市場 40 大活躍幣種即時量化總表")
    display_df = df[["幣種", "現價", "24H漲跌", "15mRSI", "15m持倉變化", "資金費率", "做空評分", "做多評分"]].copy()
    st.dataframe(display_df, use_container_width=True, hide_index=True)
