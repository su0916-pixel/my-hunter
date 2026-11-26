import streamlit as st
import requests
import pandas as pd
import numpy as np
import time
from datetime import datetime

st.set_page_config(
    page_title="CYBER HUNTER AI · 量化戰情終端",
    page_icon="⚡",
    layout="wide"
)

# ================= 暗黑賽博龐克專屬視覺樣式 (CSS) =================
st.markdown("""
<style>
    /* 全局深空暗黑背景 */
    .stApp {
        background: radial-gradient(circle at top right, #111927 0%, #070a10 60%, #030508 100%);
        color: #e2e8f0;
    }
    header[data-testid="stHeader"] {
        background: rgba(7, 10, 16, 0.85);
        backdrop-filter: blur(10px);
    }
    section[data-testid="stSidebar"] {
        background-color: #0b0f19 !important;
        border-right: 1px solid #1e293b;
    }
    /* 霓虹標題 */
    .cyber-title {
        font-size: 2.0rem;
        font-weight: 900;
        background: linear-gradient(90deg, #00f5d4 0%, #00bbf9 50%, #f15bb5 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: 1px;
        margin-bottom: 0.2rem;
    }
    .cyber-sub {
        color: #94a3b8;
        font-size: 0.88rem;
        margin-bottom: 1.2rem;
    }
    /* 熱門幣種：一種幣一個專屬獨立框 */
    .single-coin-box {
        background: linear-gradient(145deg, #111827, #0b1120);
        border: 1px solid #38bdf8;
        border-radius: 14px;
        padding: 14px 16px;
        margin-bottom: 12px;
        box-shadow: 0 0 14px rgba(56, 189, 248, 0.15);
    }
    /* 做空 TOP 5 專屬大外框 */
    .short-master-box {
        background: rgba(25, 10, 15, 0.85);
        border: 2px solid #ff2a5f;
        border-radius: 18px;
        padding: 18px 16px 8px 16px;
        margin-bottom: 18px;
        box-shadow: 0 0 25px rgba(255, 42, 95, 0.22);
    }
    .short-master-title {
        font-size: 1.3rem;
        font-weight: 900;
        color: #ff4d79;
        margin-bottom: 14px;
        padding-bottom: 8px;
        border-bottom: 1px solid rgba(255, 42, 95, 0.35);
    }
    /* 做多 TOP 5 專屬大外框 */
    .long-master-box {
        background: rgba(9, 24, 19, 0.85);
        border: 2px solid #00f59b;
        border-radius: 18px;
        padding: 18px 16px 8px 16px;
        margin-bottom: 18px;
        box-shadow: 0 0 25px rgba(0, 245, 155, 0.22);
    }
    .long-master-title {
        font-size: 1.3rem;
        font-weight: 900;
        color: #00f59b;
        margin-bottom: 14px;
        padding-bottom: 8px;
        border-bottom: 1px solid rgba(0, 245, 155, 0.35);
    }
    /* 大外框內部的單筆排名小卡 */
    .rank-item-short {
        background: rgba(255, 42, 95, 0.08);
        border-left: 4px solid #ff2a5f;
        border-radius: 10px;
        padding: 12px 14px;
        margin-bottom: 12px;
    }
    .rank-item-long {
        background: rgba(0, 245, 155, 0.08);
        border-left: 4px solid #00f59b;
        border-radius: 10px;
        padding: 12px 14px;
        margin-bottom: 12px;
    }
    .badge-short {
        background: rgba(255, 42, 95, 0.25);
        color: #ff7597;
        border: 1px solid #ff2a5f;
        padding: 2px 10px;
        border-radius: 20px;
        font-weight: 800;
        font-size: 0.82rem;
    }
    .badge-long {
        background: rgba(0, 245, 155, 0.2);
        color: #00f59b;
        border: 1px solid #00f59b;
        padding: 2px 10px;
        border-radius: 20px;
        font-weight: 800;
        font-size: 0.82rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="cyber-title">⚡ CYBER HUNTER AI · 量化戰情終端</div>', unsafe_allow_html=True)
st.markdown('<div class="cyber-sub">全市場實時掃描 · 熱門幣獨立單框 · 做空 / 做多雙戰情艙系統</div>', unsafe_allow_html=True)

@st.cache_data(ttl=20)
def scan_market_fast():
    p1 = "https://api." + "coingecko.com"
    p2 = "/api/v3/coins/markets?vs_currency=usd&order=volume_desc&per_page=60&page=1&price_change_percentage=1h,24h,7d"
    headers = {"Accept": "application/json", "User-Agent": "Mozilla/5.0"}

    try:
        res = requests.get(p1 + p2, headers=headers, timeout=10)
        if res.status_code != 200:
            return []
        coins = res.json()
    except Exception:
        return []

    results = []
    stable_coins = {"USDT", "USDC", "FDUSD", "DAI", "TUSD", "USDE", "PYUSD", "BUSD", "USDS", "WBTC", "WETH"}

    for c in coins:
        symbol = c.get("symbol", "").upper()
        if not symbol or symbol in stable_coins:
            continue

        price = float(c.get("current_price") or 0)
        if price <= 0:
            continue

        c1h = float(c.get("price_change_percentage_1h_in_currency") or 0)
        c24h = float(c.get("price_change_percentage_24h_in_currency") or 0)
        vol_24h = float(c.get("total_volume") or 0)
        mcap = float(c.get("market_cap") or 1)
        high_24h = float(c.get("high_24h") or price)
        low_24h = float(c.get("low_24h") or price)

        turnover = (vol_24h / mcap) * 100 if mcap > 0 else 0
        range_pos = ((price - low_24h) / (high_24h - low_24h) * 100) if high_24h > low_24h else 50.0

        short_score = 40
        short_reasons = []

        long_score = 40
        long_reasons = []

        if c1h >= 2.0:
            short_score += 24
            short_reasons.append(f"1H急漲+{c1h:.1f}%過熱")
        elif c1h >= 0.8:
            short_score += 10
            short_reasons.append(f"1H偏強+{c1h:.1f}%")

        if c1h <= -2.0:
            long_score += 24
            long_reasons.append(f"1H急跌{c1h:.1f}%超賣")
        elif c1h <= -0.8:
            long_score += 10
            long_reasons.append(f"1H回調{c1h:.1f}%")

        if range_pos >= 90:
            short_score += 20
            short_reasons.append(f"逼近24H頂部({range_pos:.0f}%)")
        elif range_pos <= 10:
            long_score += 20
            long_reasons.append(f"逼近24H底部({range_pos:.0f}%)")

        if c24h >= 10:
            short_score += 15
            short_reasons.append(f"日內暴漲+{c24h:.1f}%防回調")
        elif c24h <= -10:
            long_score += 15
            long_reasons.append(f"日內深跌{c24h:.1f}%博反彈")

        if turnover >= 25:
            if short_score > long_score:
                short_score += 10
                short_reasons.append(f"高換手({turnover:.0f}%)")
            elif long_score > short_score:
                long_score += 10
                long_reasons.append(f"高換手({turnover:.0f}%)")

        bias = "做空優勢" if short_score > long_score else ("做多優勢" if long_score > short_score else "中性盤整")

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
            "做多依據": " + ".join(long_reasons) if long_reasons else "動能中性觀望",
            "AI方向": bias
        })

    return results

with st.sidebar:
    st.header("⚙️ 戰情終端控制")
    auto_refresh = st.toggle("🟢 開啟全自動即時跳動", value=True)
    refresh_sec = st.slider("自動刷新間隔 (秒)", 20, 120, 30, 5)
    stop_loss_pct = st.slider("建議停損幅度 (%)", 1.0, 5.0, 2.0, 0.5)
    take_profit_pct = st.slider("建議止盈幅度 (%)", 2.0, 15.0, 4.0, 0.5)
    if st.button("🔄 立即手動刷新"):
        st.cache_data.clear()
        st.rerun()
    st.divider()
    st.info("🛡️ **合約風控守則**：\n• 務必開啟「逐倉模式」\n• 下單同步設定止盈止損\n• 評分 ≥ 75 分再考慮進場")

with st.spinner("⚡ 正在連線全球節點掃描最新資金流向..."):
    market_data = scan_market_fast()

if not market_data:
    st.error("行情介面忙碌中，請稍候 10 秒自動重試，或點擊左上角選單「立即手動刷新」。")
else:
    df = pd.DataFrame(market_data)
    now_str = datetime.now().strftime("%H:%M:%S")
    st.caption(f"🟢 系統連線正常 · 最後更新：`{now_str}`（每 `{refresh_sec}` 秒自動跳動）· 已掃描 `{len(df)}` 檔合約標的")

    # ================= 區塊 1：熱門主流幣種（一種幣一個獨立框） =================
    st.markdown("### 🔥 熱門主流幣種獨立戰情（一幣一框）")
    hot_list = ["BTC", "ETH", "SOL", "XRP", "DOGE", "SUI"]
    hot_df = df[df["幣種"].isin(hot_list)].copy()
    hot_df["order"] = hot_df["幣種"].apply(lambda x: hot_list.index(x) if x in hot_list else 99)
    hot_df = hot_df.sort_values("order")

    hot_cols = st.columns(3)
    for i, (_, row) in enumerate(hot_df.iterrows()):
        with hot_cols[i % 3]:
            price = row["現價"]
            fmt = f"${price:,.4f}" if price < 10 else f"${price:,.2f}"
            c24 = row["24H漲跌"]
            c24_color = "#00f59b" if c24 >= 0 else "#ff2a5f"
            is_short = row["做空評分"] > row["做多評分"]
            is_long = row["做多評分"] > row["做空評分"]

            if is_short:
                dir_tag = f"🔴 偏空 {row['做空評分']}分"
                tp = price * (1 - take_profit_pct / 100)
                sl = price * (1 + stop_loss_pct / 100)
                border_color = "#ff2a5f"
            elif is_long:
                dir_tag = f"🟢 偏多 {row['做多評分']}分"
                tp = price * (1 + take_profit_pct / 100)
                sl = price * (1 - stop_loss_pct / 100)
                border_color = "#00f59b"
            else:
                dir_tag = "⚪ 盤整觀望"
                tp = price * (1 + take_profit_pct / 100)
                sl = price * (1 - stop_loss_pct / 100)
                border_color = "#38bdf8"

            tp_fmt = f"${tp:,.4f}" if price < 10 else f"${tp:,.2f}"
            sl_fmt = f"${sl:,.4f}" if price < 10 else f"${sl:,.2f}"

            st.markdown(f"""
            <div class="single-coin-box" style="border-color:{border_color};">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size:1.15rem; font-weight:900; color:#ffffff;">💎 {row['幣種']}/USDT</span>
                    <span style="font-size:0.85rem; font-weight:800; color:#e2e8f0;">{dir_tag}</span>
                </div>
                <div style="margin:6px 0;">
                    <span style="font-family:monospace; font-size:1.2rem; font-weight:900; color:#f8fafc;">{fmt}</span>
                    <span style="color:{c24_color}; font-weight:700; margin-left:6px;">({c24:+.2f}%)</span>
                </div>
