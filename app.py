import streamlit as st
import streamlit.components.v1 as components
import requests
import json
from datetime import datetime, timezone, timedelta

st.set_page_config(page_title="CYBER HUNTER AI v4.0", page_icon="⚡", layout="wide")

st.markdown("""
<style>
.stApp { background: #070a10; color: #e2e8f0; }
header[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 1.5rem; padding-bottom: 1rem; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ 戰情終端設定")
    sl_p = st.slider("建議停損 (%)", 1.0, 5.0, 2.0, 0.5)
    tp_p = st.slider("建議止盈 (%)", 2.0, 15.0, 4.0, 0.5)
    if st.button("🔄 重新掃描 AI 排行榜"):
        st.cache_data.clear()
        st.rerun()
    st.divider()
    st.info("⚡ **即時串流說明**：\n價格已直連 OKX 永續合約即時報價，成交即刻跳動（綠閃＝上漲、紅閃＝下跌）。")

@st.cache_data(ttl=60)
def get_market_data():
    rows = []
    skip = {"USDT", "USDC", "FDUSD", "DAI", "TUSD", "USDE", "PYUSD", "BUSD", "USDS", "WBTC", "WETH"}
    d1 = "".join(["ht", "tps://", "api.", "coin", "paprika", ".", "com", "/v1/tickers?limit=75"])
    logo_prefix = "".join(["ht", "tps://", "assets.", "coin", "cap", ".", "io/assets/icons/"])
    try:
        r = requests.get(d1, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
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

                rows.append({
                    "sym": sym, "price": p, "c1h": round(c1h, 2), "c24h": round(c24h, 2),
                    "logo": f"{logo_prefix}{sym.lower()}@2x.png",
                    "s_sc": min(s_sc, 99), "s_msg": " + ".join(s_msg) if s_msg else "動能中性",
                    "l_sc": min(l_sc, 99), "l_msg": " + ".join(l_msg) if l_msg else "動能中性"
                })
    except Exception:
        pass
    return rows

data = get_market_data()
if not data:
    st.error("正在建立行情通道，請點擊左側「重新掃描 AI 排行榜」或稍候自動重載...")
else:
    hots_order = ["BTC", "ETH", "SOL", "XRP", "DOGE", "SUI"]
    hot_coins = sorted([x for x in data if x["sym"] in hots_order], key=lambda x: hots_order.index(x["sym"]))
    short_top = sorted([x for x in data if x["s_sc"] >= x["l_sc"]], key=lambda x: x["s_sc"], reverse=True)[:5]
    long_top = sorted([x for x in data if x["l_sc"] > x["s_sc"]], key=lambda x: x["l_sc"], reverse=True)[:5]

    all_syms = list({x["sym"] for x in hot_coins + short_top + long_top})
    ws_endpoint = "".join(["w", "ss://", "ws.", "okx", ".", "com:8443/ws/v5/public"])
    tw_scan_time = datetime.now(timezone(timedelta(hours=8))).strftime("%H:%M:%S")

    payload = json.dumps({
        "hots": hot_coins, "shorts": short_top, "longs": long_top,
        "syms": all_syms, "ws": ws_endpoint, "tp": tp_p, "sl": sl_p, "scan_time": tw_scan_time
    })

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
      body {{ background: #070a10; color: #e2e8f0; font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 0; padding: 4px; }}
      .title {{ font-size: 26px; font-weight: 900; color: #00f5d4; text-shadow: 0 0 12px rgba(0,245,212,0.5); margin-bottom: 8px; }}
      .status-bar {{ display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-bottom: 16px; font-size: 13px; }}
      .clock-box {{ font-family: 'Courier New', monospace; color: #00f5d4; background: #0f172a; border: 1px solid #1e293b; padding: 5px 10px; border-radius: 8px; font-weight: bold; }}
      .live-dot {{ color: #00f59b; font-weight: bold; }}
      .sec-title {{ font-size: 18px; font-weight: 800; margin: 14px 0 10px 0; color: #f8fafc; }}
      .grid-hot {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 10px; }}
      .coin-box {{ background: #0f172a; border: 1.5px solid #38bdf8; border-radius: 12px; padding: 12px; box-shadow: 0 0 12px rgba(56,189,248,0.18); }}
      .grid-main {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 14px; margin-top: 12px; }}
      .short-box {{ background: #190a0f; border: 2px solid #ff2a5f; border-radius: 16px; padding: 14px; box-shadow: 0 0 20px rgba(255,42,95,0.22); }}
      .long-box {{ background: #091813; border: 2px solid #00f59b; border-radius: 16px; padding: 14px; box-shadow: 0 0 20px rgba(0,245,155,0.22); }}
      .item-s {{ background: rgba(255,42,95,0.1); border-left: 4px solid #ff2a5f; border-radius: 8px; padding: 10px; margin-bottom: 10px; }}
      .item-l {{ background: rgba(0,245,155,0.1); border-left: 4px solid #00f59b; border-radius: 8px; padding: 10px; margin-bottom: 10px; }}
      .logo {{ width: 22px; height: 22px; border-radius: 50%; vertical-align: middle; margin-right: 6px; }}
      .price-val {{ font-family: 'Courier New', monospace; font-size: 18px; font-weight: 900; padding: 1px 4px; border-radius: 4px; transition: background 0.25s, color 0.25s; }}
      .flash-up {{ background: rgba(0, 245, 155, 0.35); color: #00f59b; }}
      .flash-dn {{ background: rgba(255, 42, 95, 0.35); color: #ff5c85; }}
      .sub-info {{ font-size: 12px; color: #cbd5e1; margin-top: 4px; }}
      .reason {{ font-size: 11.5px; color: #94a3b8; margin-top: 4px; }}
    </style>
    </head>
    <body>
      <div class="title">⚡ CYBER HUNTER AI · 量化戰情終端</div>
      <div class="status-bar">
        <div class="clock-box">🕒 台灣時間：<span id="tw-clock">--:--:--</span></div>
        <div class="live-dot" id="ws-status">⚡ 正在連線 OKX 毫秒級報價...</div>
      </div>

      <div class="sec-title">🔥 熱門主流幣種（一幣一框 · 實時成交價）</div>
      <div class="grid-hot" id="hot-container"></div>

      <div class="grid-main">
        <div>
          <div class="sec-title" style="color:#ff5c85;">🔴 AI 最佳【做空】TOP 5</div>
          <div class="short-box" id="short-container"></div>
        </div>
        <div>
          <div class="sec-title" style="color:#00f59b;">🟢 AI 最佳【做多】TOP 5</div>
          <div class="long-box" id="long-container"></div>
        </div>
      </div>

      <script>
        const DATA = {payload};
        const lastPrices = {{}};

        function fmtPrice(p) {{
          return p < 10 ? '$' + p.toFixed(4) : '$' + p.toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
        }}

        function updateClock() {{
          const now = new Date();
          document.getElementById('tw-clock').innerText = now.toLocaleTimeString('zh-TW', {{ timeZone: 'Asia/Taipei', hour12: false }});
        }}
        setInterval(updateClock, 1000);
        updateClock();

        function renderAll() {{
          let hotHtml = '';
          DATA.hots.forEach(c => {{
            lastPrices[c.sym] = c.price;
            const isS = c.s_sc > c.l_sc;
            const bc = isS ? '#ff2a5f' : (c.l_sc > c.s_sc ? '#00f59b' : '#38bdf8');
            const tag = isS ? `🔴 偏空 ${{c.s_sc}}分` : (c.l_sc > c.s_sc ? `🟢 偏多 ${{c.l_sc}}分` : '⚪ 盤整');
            const tp = isS ? c.price * (1 - DATA.tp/100) : c.price * (1 + DATA.tp/100);
            const sl = isS ? c.price * (1 + DATA.sl/100) : c.price * (1 - DATA.sl/100);
            hotHtml += `<div class="coin-box" style="border-color:${{bc}};">
              <div><img src="${{c.logo}}" class="logo" onerror="this.style.display='none'"><b>${{c.sym}}/USDT</b> ｜ <span style="color:${{bc}};font-weight:bold;">${{tag}}</span></div>
              <div style="margin:6px 0;"><span class="price-val p-${{c.sym}}">${{fmtPrice(c.price)}}</span> <span style="font-size:13px;">(${{c.c24h >= 0 ? '+' : ''}}${{c.c24h}}%)</span></div>
              <div class="sub-info">🎯 止盈: <span class="tp-hot-${{c.sym}}">${{fmtPrice(tp)}}</span> ｜ 🛡️ 停損: <span class="sl-hot-${{c.sym}}">${{fmtPrice(sl)}}</span></div>
            </div>`;
          }});
          document.getElementById('hot-container').innerHTML = hotHtml;

          let shortHtml = '';
          DATA.shorts.forEach((c, idx) => {{
            lastPrices[c.sym] = c.price;
            const tp = c.price * (1 - DATA.tp/100);
            const sl = c.price * (1 + DATA.sl/100);
            shortHtml += `<div class="item-s">
              <div><b>#${{idx+1}}</b> <img src="${{c.logo}}" class="logo" onerror="this.style.display='none'"><b>${{c.sym}}/USDT</b> ｜ <span style="color:#ff5c85;font-weight:bold;">勝率 ${{c.s_sc}} 分</span></div>
              <div style="margin:4px 0;">現價: <span class="price-val p-${{c.sym}}">${{fmtPrice(c.price)}}</span> <small>(24H: ${{c.c24h >= 0 ? '+' : ''}}${{c.c24h}}%)</small></div>
