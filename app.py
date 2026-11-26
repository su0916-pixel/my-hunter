import streamlit as st
import requests
import pandas as pd
import numpy as np
import time
from datetime import datetime

st.set_page_config(
    page_title="AI 全市場合約獵手 Pro v2.4",
    page_icon="🏆",
    layout="wide"
)

st.title("🏆 AI 全市場合約多空排行榜 (全自動實時跳動版)")
st.caption("全自動掃描前 40 大活躍合約幣種 · 隨時間自動更新報價與勝率評分 · 僅供交易輔助參考")

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

@st.cache_data(ttl=25)
def scan_global_market():
    headers = {"User-Agent": "Mozilla/5.0"}
    host = "https://min-api." + "cryptocompare.com"
    url = host + "/data/top/totalvolfull?limit=40&tsym=USDT"
    try:
        res = requests.get(url, headers=headers, timeout=10).json()
        raw_list = res.get("Data", [])
    except Exception:
        return []

    results = []
    for item in raw_list:
        coin_info = item.get("CoinInfo", {})
        raw_data = item.get("RAW", {}).get("USDT", {})
        coin = coin_info.get("Name", "")
        if not coin or not raw_data or coin in ["USDT", "USDC", "FDUSD", "DAI"]:
            continue

        last_price = float(raw_data.get("PRICE", 0))
        change_24h = float(raw_data.get("CHANGEPCT24HOUR", 0))
        change_1h = float(raw_data.get("CHANGEPCTHOUR", 0))

        try:
            k_url = host + f"/data/v2/histominute?fsym={coin}&tsym=USDT&limit=20&aggregate=15"
            k_res = requests.get(k_url, headers=headers, timeout=5).json()
            candles = k_res.get("Data", {}).get("Data", [])
            if len(candles) < 15:
                continue

            closes = [float(c["close"]) for c in candles]
            vols = [float(c["volumeto"]) for c in candles]
            rsi_15m = calculate_rsi(closes)
            change_15m = ((closes[-1] - closes[-2]) / closes[-2]) * 100 if closes[-2] else 0

            avg_vol = np.mean(vols[-11:-1]) if len(vols) >= 11 else np.mean(vols)
            vol_ratio = (vols[-1] / avg_vol) if avg_vol > 0 else 1.0

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

            if change_15m < -0.35 and vol_ratio > 1.4:
                short_score += 25
                short_reasons.append(f"主力放量砸盤({vol_ratio:.1f}倍量)")
            elif change_15m > 0.35 and vol_ratio > 1.4:
                long_score += 25
                long_reasons.append(f"大資金放量拉升({vol_ratio:.1f}倍量)")

            if change_1h >= 2.5:
                short_score += 15
                short_reasons.append(f"1H急漲+{change_1h:.1f}%易獲利了結")
            elif change_1h <= -2.5:
                long_score += 15
                long_reasons.append(f"1H急跌{change_1h:.1f}%具反彈動能")

            if change_24h >= 12:
                short_score += 10
                short_reasons.append(f"24H暴漲+{change_24h:.1f}%防回調")
            elif change_24h <= -12:
                long_score += 10
                long_reasons.append(f"24H深跌{change_24h:.1f}%博反彈")

            results.append({
                "幣種": coin,
                "現價": last_price,
                "1H漲跌": round(change_1h, 2),
                "24H漲跌": round(change_24h, 2),
                "15mRSI": round(rsi_15m, 1),
                "量能倍數": round(vol_ratio, 2),
                "做空評分": min(short_score, 99),
                "做空依據": " + ".join(short_reasons) if short_reasons else "動能中性觀望",
                "做多評分": min(long_score, 99),
                "做多依據": " + ".join(long_reasons) if long_reasons else "動能中性觀望"
            })
        except Exception:
            continue

    return results

with st.sidebar:
    st.header("⚙️ AI 策略與即時更新")
    auto_refresh = st.toggle("🟢 開啟全自動即時跳動", value=True)
    refresh_sec = st.slider("自動刷新間隔 (秒)", 15, 120, 30, 5)
    stop_loss_pct = st.slider("建議停損幅度 (%)", 1.0, 5.0, 2.0, 0.5)
    take_profit_pct = st.slider("建議止盈幅度 (%)", 2.0, 15.0, 4.0, 0.5)
    if st.button("🔄 立即手動刷新"):
        st.cache_data.clear()
        st.rerun()
    st.divider()
    st.warning("⚠️ **合約風控鐵律**：\n1. 務必使用「逐倉模式」\n2. 進場同時掛好停損單\n3. 評分高代表盈虧比佳，非 100% 必勝")

with st.spinner("🤖 AI 正在即時掃描全市場前 40 大熱門合約資金流向與 K 線..."):
    market_data = scan_global_market()

if not market_data:
    st.error("暫時無法連線至行情伺服器，請點擊左上角選單「立即手動刷新」重試。")
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
    st.subheader("📊 全市場活躍幣種即時量化總表")
    display_df = df[["幣種", "現價", "1H漲跌", "24H漲跌", "15mRSI", "量能倍數", "做空評分", "做多評分"]].copy()
    st.dataframe(display_df, use_container_width=True, hide_index=True)

if auto_refresh:
    time.sleep(refresh_sec)
    st.cache_data.clear()
    st.rerun()
