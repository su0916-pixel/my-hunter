import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime

st.set_page_config(page_title="CYBER HUNTER AI", page_icon="⚡", layout="wide")

st.markdown("""
<style>
.stApp { background: linear-gradient(135deg, #070a10 0%, #111927 100%); color: #e2e8f0; }
header[data-testid="stHeader"] { background: transparent; }
.cyber-title { font-size: 1.9rem; font-weight: 900; color: #00f5d4; text-shadow: 0 0 12px rgba(0,245,212,0.5); }
.coin-box { background: #0f172a; border: 1.5px solid #38bdf8; border-radius: 12px; padding: 12px; margin-bottom: 10px; box-shadow: 0 0 12px rgba(56,189,248,0.2); }
.short-box { background: #190a0f; border: 2px solid #ff2a5f; border-radius: 16px; padding: 14px; margin-bottom: 14px; box-shadow: 0 0 20px rgba(255,42,95,0.25); }
.long-box { background: #091813; border: 2px solid #00f59b; border-radius: 16px; padding: 14px; margin-bottom: 14px; box-shadow: 0 0 20px rgba(0,245,155,0.25); }
.item-s { background: rgba(255,42,95,0.1); border-left: 4px solid #ff2a5f; border-radius: 8px; padding: 10px; margin-bottom: 8px; }
.item-l { background: rgba(0,245,155,0.1); border-left: 4px solid #00f59b; border-radius: 8px; padding: 10px; margin-bottom: 8px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="cyber-title">⚡ CYBER HUNTER AI · 量化戰情終端</div>', unsafe_allow_html=True)

@st.cache_data(ttl=35)
def get_market():
    rows = []
    skip = {"USDT", "USDC", "FDUSD", "DAI", "TUSD", "USDE", "PYUSD", "BUSD", "USDS", "WBTC", "WETH"}
    headers = {"User-Agent": "Mozilla/5.0"}

    # 防手機自動截短網域保護組裝
    d1 = "".join(["ht", "tps://", "api.", "coin", "paprika", ".", "com", "/v1/tickers?limit=70"])
    try:
        r = requests.get(d1, headers=headers, timeout=10)
        if r.status_code == 200:
            for c in r.json():
                sym = c.get("symbol", "").upper()
                q = c.get("quotes", {}).get("USD", {})
                p = float(q.get("price") or 0)
                if not sym or sym in skip or p <= 0:
                    continue
                c1h = float(q.get("percent_change_1h") or 0)
                c24h = float(q.get("percent_change_24h") or 0)
                vol = float(q.get("volume_24h") or 0)
                mc = float(q.get("market_cap") or 1)
                turn = (vol / mc) * 100 if mc > 0 else 0
                pos = min(max(50.0 + c24h * 2.5, 5.0), 95.0)
                rows.append((sym, p, c1h, c24h, pos, turn))
    except Exception:
        pass

    final_data = []
    for sym, p, c1h, c24h, pos, turn in rows:
        s_sc, l_sc = 40, 40
        s_msg, l_msg = [], []

        if c1h >= 2.0: s_sc += 24; s_msg.append(f"1H急漲+{c1h:.1f}%")
        elif c1h >= 0.8: s_sc += 10; s_msg.append(f"1H偏強+{c1h:.1f}%")
        if c1h <= -2.0: l_sc += 24; l_msg.append(f"1H急跌{c1h:.1f}%")
        elif c1h <= -0.8: l_sc += 10; l_msg.append(f"1H回調{c1h:.1f}%")

        if pos >= 88: s_sc += 20; s_msg.append(f"逼近高點({pos:.0f}%)")
        elif pos <= 12: l_sc += 20; l_msg.append(f"逼近低點({pos:.0f}%)")

        if c24h >= 10: s_sc += 15; s_msg.append(f"日內暴漲+{c24h:.1f}%")
        elif c24h <= -10: l_sc += 15; l_msg.append(f"日內深跌{c24h:.1f}%")

        if turn >= 20:
            if s_sc > l_sc: s_sc += 10; s_msg.append(f"高換手{turn:.0f}%")
            elif l_sc > s_sc: l_sc += 10; l_msg.append(f"高換手{turn:.0f}%")

        final_data.append({
            "幣種": sym, "現價": p, "1H": round(c1h, 2), "24H": round(c24h, 2),
            "位置": round(pos, 1), "換手": round(turn, 1),
            "空分": min(s_sc, 99), "空因": " + ".join(s_msg) if s_msg else "動能中性",
            "多分": min(l_sc, 99), "多因": " + ".join(l_msg) if l_msg else "動能中性"
        })
    return final_data

with st.sidebar:
    st.header("⚙️ 戰情控制")
    auto_ref = st.toggle("🟢 全自動即時跳動", value=True)
    sec = st.slider("刷新秒數", 30, 120, 45, 5)
    sl_p = st.slider("停損 (%)", 1.0, 5.0, 2.0, 0.5)
    tp_p = st.slider("止盈 (%)", 2.0, 15.0, 4.0, 0.5)
    if st.button("🔄 立即刷新"):
        st.cache_data.clear()
        st.rerun()

data = get_market()
if not data:
    st.error("行情連線中，請稍候自動刷新...")
else:
    df = pd.DataFrame(data)
    st.caption(f"🟢 實時連線中 · 更新：`{datetime.now().strftime('%H:%M:%S')}`（每 {sec} 秒自動跳動）")

    st.markdown("### 🔥 熱門主流幣種（一幣一框）")
    hots = ["BTC", "ETH", "SOL", "XRP", "DOGE", "SUI"]
    hdf = df[df["幣種"].isin(hots)].copy()
    hdf["ord"] = hdf["幣種"].apply(lambda x: hots.index(x) if x in hots else 99)
    hdf = hdf.sort_values("ord")

    cols = st.columns(3)
    for i, (_, r) in enumerate(hdf.iterrows()):
        with cols[i % 3]:
            p = r["現價"]
            fmt = f"${p:,.4f}" if p < 10 else f"${p:,.2f}"
            is_s = r["空分"] > r["多分"]
            bc = "#ff2a5f" if is_s else ("#00f59b" if r["多分"] > r["空分"] else "#38bdf8")
            tag = f"🔴 偏空 {r['空分']}分" if is_s else (f"🟢 偏多 {r['多分']}分" if r["多分"] > r["空分"] else "⚪ 盤整")
            tp = p * (1 - tp_p/100) if is_s else p * (1 + tp_p/100)
            sl = p * (1 + sl_p/100) if is_s else p * (1 - sl_p/100)
            tpf = f"${tp:,.4f}" if p < 10 else f"${tp:,.2f}"
            slf = f"${sl:,.4f}" if p < 10 else f"${sl:,.2f}"
            st.markdown(f'<div class="coin-box" style="border-color:{bc};"><b>💎 {r["幣種"]}/USDT</b> ｜ <span style="color:{bc};font-weight:bold;">{tag}</span><br><span style="font-size:1.15rem;font-weight:900;">{fmt}</span> ({r["24H"]:+.2f}%)<br><small>🎯 止盈: {tpf} ｜ 🛡️ 停損: {slf}</small></div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 🔴 AI 最佳【做空】TOP 5")
        st_df = df[df["空分"] >= df["多分"]].sort_values("空分", ascending=False).head(5)
        html_s = '<div class="short-box">'
        for idx, (_, r) in enumerate(st_df.iterrows(), 1):
            p = r["現價"]
            fmt = f"${p:,.4f}" if p < 10 else f"${p:,.2f}"
            tpf = f"${p*(1-tp_p/100):,.4f}" if p < 10 else f"${p*(1-tp_p/100):,.2f}"
            slf = f"${p*(1+sl_p/100):,.4f}" if p < 10 else f"${p*(1+sl_p/100):,.2f}"
            html_s += f'<div class="item-s"><b>#{idx} 📉 {r["幣種"]}/USDT</b> ｜ <span style="color:#ff5c85;font-weight:bold;">勝率 {r["空分"]} 分</span><br>進場: <b>{fmt}</b> (1H: {r["1H"]:+.2f}% / 24H: {r["24H"]:+.2f}%)<br>🎯 止盈: <b>{tpf}</b> ｜ 🛡️ 停損: <b>{slf}</b><br><small style="color:#94a3b8;">🔍 {r["空因"]}</small></div>'
        html_s += '</div>'
        st.markdown(html_s, unsafe_allow_html=True)

    with c2:
        st.markdown("### 🟢 AI 最佳【做多】TOP 5")
        lg_df = df[df["多分"] > df["空分"]].sort_values("多分", ascending=False).head(5)
        html_l = '<div class="long-box">'
        for idx, (_, r) in enumerate(lg_df.iterrows(), 1):
            p = r["現價"]
            fmt = f"${p:,.4f}" if p < 10 else f"${p:,.2f}"
            tpf = f"${p*(1+tp_p/100):,.4f}" if p < 10 else f"${p*(1+tp_p/100):,.2f}"
            slf = f"${p*(1-sl_p/100):,.4f}" if p < 10 else f"${p*(1-sl_p/100):,.2f}"
            html_l += f'<div class="item-l"><b>#{idx} 📈 {r["幣種"]}/USDT</b> ｜ <span style="color:#00f59b;font-weight:bold;">勝率 {r["多分"]} 分</span><br>進場: <b>{fmt}</b> (1H: {r["1H"]:+.2f}% / 24H: {r["24H"]:+.2f}%)<br>🎯 止盈: <b>{tpf}</b> ｜ 🛡️ 停損: <b>{slf}</b><br><small style="color:#94a3b8;">🔍 {r["多因"]}</small></div>'
        html_l += '</div>'
        st.markdown(html_l, unsafe_allow_html=True)

    st.divider()
    st.markdown("### 📊 全市場合約即時總表")
    st.dataframe(df[["幣種", "現價", "1H", "24H", "位置", "換手", "空分", "多分"]], use_container_width=True, hide_index=True)

if auto_ref:
    time.sleep(sec)
    st.cache_data.clear()
    st.rerun()
