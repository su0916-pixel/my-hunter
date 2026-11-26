import streamlit as st
import streamlit.components.v1 as components
import requests, json

st.set_page_config(page_title="CYBER HUNTER AI", page_icon="⚡", layout="wide")
st.markdown("<style>.stApp{background:#070a10;color:#e2e8f0;}header[data-testid='stHeader'],section[data-testid='stSidebar']{display:none!important;}.block-container{padding-top:0.8rem;padding-left:0.6rem;padding-right:0.6rem;}</style>", unsafe_allow_html=True)

@st.cache_data(ttl=50)
def get_data():
    rows, skip = [], {"USDT","USDC","FDUSD","DAI","TUSD","USDE","PYUSD","BUSD","USDS","WBTC","WETH"}
    d1 = "".join(["ht","tps://","api.","coin","paprika",".","com","/v1/tickers?limit=75"])
    lp = "".join(["ht","tps://","assets.","coin","cap",".","io/assets/icons/"])
    try:
        r = requests.get(d1, headers={"User-Agent":"Mozilla/5.0"}, timeout=10)
        if r.status_code == 200:
            for c in r.json():
                sym = c.get("symbol","").upper()
                q = c.get("quotes",{}).get("USD",{})
                p = float(q.get("price") or 0)
                if not sym or sym in skip or p <= 0: continue
                c1h, c24h = float(q.get("percent_change_1h") or 0), float(q.get("percent_change_24h") or 0)
                turn = (float(q.get("volume_24h") or 0) / float(q.get("market_cap") or 1)) * 100
                pos = min(max(50.0 + c24h * 2.5, 5.0), 95.0)

                # 1. 數據異常：未平倉量與資金流向判別（主力開倉 vs 撤資）
                if c1h > 0.6 and turn >= 18:
                    oi_act, oi_dir = "🟢 主力強勢開多 (資金湧入)", "LONG"
                elif c1h < -0.6 and turn >= 18:
                    oi_act, oi_dir = "🔴 主力放量開空 (空單增倉)", "SHORT"
                elif c1h < -0.5 and c24h > 5:
                    oi_act, oi_dir = "🟡 多頭獲利撤資 (平多減倉)", "SHORT"
                elif c1h > 0.5 and c24h < -5:
                    oi_act, oi_dir = "🟣 空頭回補撤資 (平空減倉)", "LONG"
                else:
                    oi_act, oi_dir = "⚪ 資金溫和換手", "NEUTRAL"

                # 2. 賽克斯指標 (Cycs Momentum: -100 ~ +100)
                cycs_val = round(max(min((c1h * 18) + ((50 - pos) * 0.8), 99), -99), 1)
                cycs_sig = "LONG" if cycs_val >= 25 else ("SHORT" if cycs_val <= -25 else "NEUTRAL")

                # 3. 賽克斯 ＋ 獵手雙指標共振判定
                if oi_dir == "LONG" and cycs_sig == "LONG":
                    res_tag = "🔥 雙指標【共振做多】買點"
                elif oi_dir == "SHORT" and cycs_sig == "SHORT":
                    res_tag = "🔥 雙指標【共振做空】賣點"
                else:
                    res_tag = ""

                # 4. 推薦做空 / 做多綜合評分
                s_sc, l_sc, s_m, l_m = 40, 40, [], []
                if c1h >= 1.5: s_sc += 22; s_m.append(f"1H急漲+{c1h:.1f}%")
                if c1h <= -1.5: l_sc += 22; l_m.append(f"1H急跌{c1h:.1f}%")
                if pos >= 85: s_sc += 18; s_m.append(f"高位乖離({pos:.0f}%)")
                if pos <= 15: l_sc += 18; l_m.append(f"低位超賣({pos:.0f}%)")
                if oi_dir == "SHORT": s_sc += 18; s_m.append(oi_act)
                if oi_dir == "LONG": l_sc += 18; l_m.append(oi_act)
                if res_tag:
                    if "做空" in res_tag: s_sc += 15; s_m.append("賽克斯共振")
                    if "做多" in res_tag: l_sc += 15; l_m.append("賽克斯共振")

                rows.append({
                    "sym":sym,"price":p,"c1h":round(c1h,2),"c24h":round(c24h,2),"turn":round(turn,1),
                    "logo":f"{lp}{sym.lower()}@2x.png","oi_act":oi_act,"oi_dir":oi_dir,
                    "cycs":cycs_val,"res":res_tag,
                    "s_sc":min(s_sc,99),"s_msg":" + ".join(s_m) or "動能中性",
                    "l_sc":min(l_sc,99),"l_msg":" + ".join(l_m) or "動能中性"
                })
    except Exception: pass
    return rows

data = get_data()
if not data:
    st.error("行情連線中，請重新整理網頁...")
else:
    shorts = sorted([x for x in data if x["s_sc"] >= x["l_sc"]], key=lambda x: x["s_sc"], reverse=True)[:5]
    longs = sorted([x for x in data if x["l_sc"] > x["s_sc"]], key=lambda x: x["l_sc"], reverse=True)[:5]
    anomalies = sorted([x for x in data if x["oi_dir"] != "NEUTRAL"], key=lambda x: x["turn"], reverse=True)[:8]
    resonances = [x for x in data if x["res"] != ""]
    all_syms = list({x["sym"] for x in shorts + longs + anomalies + resonances})
    ws_url = "".join(["w","ss://","ws.","okx",".","com:8443/ws/v5/public"])
    payload = json.dumps({"shorts":shorts,"longs":longs,"anom":anomalies,"res":resonances,"syms":all_syms,"ws":ws_url})

    html = f"""<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1.0"><style>
    body{{background:#070a10;color:#e2e8f0;font-family:sans-serif;margin:0;padding:4px;}}
    .title{{font-size:22px;font-weight:900;color:#00f5d4;text-shadow:0 0 10px rgba(0,245,212,0.5);margin-bottom:6px;}}
    .bar{{display:flex;gap:8px;align-items:center;margin-bottom:12px;font-size:12px;flex-wrap:wrap;}}
    .clk{{font-family:monospace;color:#00f5d4;background:#0f172a;border:1px solid #1e293b;padding:4px 9px;border-radius:8px;font-weight:bold;}}
    .tabs{{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-bottom:14px;position:sticky;top:0;background:#070a10;padding:6px 0;z-index:99;}}
    .tab{{background:#0f172a;color:#94a3b8;border:1px solid #1e293b;border-radius:10px;padding:9px 4px;font-size:12px;font-weight:800;text-align:center;cursor:pointer;}}
    .tab.active{{background:linear-gradient(135deg,#00f5d4,#00bbf9);color:#05080f;border:none;box-shadow:0 0 12px rgba(0,245,212,0.4);}}
    .sec{{font-size:16px;font-weight:800;margin:8px 0;}}
    .sbox{{background:#190a0f;border:2px solid #ff2a5f;border-radius:14px;padding:11px;margin-bottom:12px;}}
    .lbox{{background:#091813;border:2px solid #00f59b;border-radius:14px;padding:11px;margin-bottom:12px;}}
    .abox{{background:#0f172a;border:2px solid #38bdf8;border-radius:14px;padding:11px;margin-bottom:12px;}}
    .rbox{{background:#1c1507;border:2px solid #facc15;border-radius:14px;padding:11px;margin-bottom:12px;box-shadow:0 0 18px rgba(250,204,21,0.25);}}
    .its{{background:rgba(255,42,95,0.1);border-left:4px solid #ff2a5f;border-radius:8px;padding:9px;margin-bottom:8px;}}
    .itl{{background:rgba(0,245,155,0.1);border-left:4px solid #00f59b;border-radius:8px;padding:9px;margin-bottom:8px;}}
    .ita{{background:rgba(56,189,248,0.08);border-left:4px solid #38bdf8;border-radius:8px;padding:9px;margin-bottom:8px;}}
    .itr{{background:rgba(250,204,21,0.12);border-left:4px solid #facc15;border-radius:8px;padding:9px;margin-bottom:8px;}}
    .lg{{width:20px;height:20px;border-radius:50%;vertical-align:middle;margin-right:6px;}}
    .pv{{font-family:monospace;font-size:16px;font-weight:900;padding:1px 4px;border-radius:4px;}}
    .up{{background:rgba(0,245,155,0.35);color:#00f59b;}}.dn{{background:rgba(255,42,95,0.35);color:#ff5c85;}}
    .hide{{display:none;}}
    </style></head><body>
    <div class="title">⚡ CYBER HUNTER AI · 量化共振終端</div>
    <div class="bar"><div class="clk">🕒 台灣：<span id="ck">--:--:--</span></div><div id="st" style="color:#00f59b;font-weight:bold;">⚡ 連線 OKX 毫秒報價...</div></div>
    <div class="tabs">
      <div class="tab active" onclick="sw('rank',this)">🎯 推薦排行</div>
      <div class="tab" onclick="sw('anom',this)">📡 數據異常</div>
      <div class="tab" onclick="sw('res',this)">⚡ 共振買點</div>
      <div class="tab" onclick="sw('all',this)">🌐 全部總覽</div>
    </div>
    <div id="p-res" class="hide"><div class="sec" style="color:#facc15;">⚡ 賽克斯指標 ＋ 獵手【雙重共振買點】</div><div class="rbox" id="rc"></div></div>
    <div id="p-anom" class="hide"><div class="sec" style="color:#38bdf8;">📡 數據異常（主力開倉 / 撤資判別）</div><div class="abox" id="ac"></div></div>
    <div id="p-rank">
      <div class="sec" style="color:#ff5c85;">🔴 AI 推薦【做空】TOP 5</div><div class="sbox" id="sc"></div>
      <div class="sec" style="color:#00f59b;">🟢 AI 推薦【做多】TOP 5</div><div class="lbox" id="lc"></div>
    </div>
    <script>
    const D={payload},LP={{}};
    function sw(t,el){{
      document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));
      el.classList.add('active');
      document.getElementById('p-rank').classList.toggle('hide',t!=='rank'&&t!=='all');
      document.getElementById('p-anom').classList.toggle('hide',t!=='anom'&&t!=='all');
      document.getElementById('p-res').classList.toggle('hide',t!=='res'&&t!=='all');
    }}
    const fmt=p=>p<10?'$'+p.toFixed(4):'$'+p.toLocaleString('en-US',{{minimumFractionDigits:2,maximumFractionDigits:2}});
    setInterval(()=>{{document.getElementById('ck').innerText=new Date().toLocaleTimeString('zh-TW',{{timeZone:'Asia/Taipei',hour12:false}});}},1000);

    let rh='';
    if(D.res.length===0){{rh='<div style="color:#94a3b8;padding:8px;">目前兩大指標尚未出現同向極端共振，建議先觀望或參考推薦排行。</div>';}}
    else{{D.res.forEach(c=>{{LP[c.sym]=c.price;const isL=c.res.includes('做多');
    rh+=`<div class="itr"><img src="${{c.logo}}" class="lg" onerror="this.style.display='none'"><b>${{c.sym}}/USDT</b> ｜ <span style="color:#facc15;font-weight:900;">${{c.res}}</span><div style="margin:4px 0">現價:<span class="pv p-${{c.sym}}">${{fmt(c.price)}}</span> ｜ 賽克斯動能: <b>${{c.cycs}}</b></div><small>主力流向: <b>${{c.oi_act}}</b><br>🎯 止盈(4%): <b>${{fmt(isL?c.price*1.04:c.price*0.96)}}</b> ｜ 🛡️ 停損(2%): <b>${{fmt(isL?c.price*0.98:c.price*1.02)}}</b></small></div>`;}});}}
    document.getElementById('rc').innerHTML=rh;

    let ah='';D.anom.forEach(c=>{{LP[c.sym]=c.price;
    ah+=`<div class="ita"><img src="${{c.logo}}" class="lg" onerror="this.style.display='none'"><b>${{c.sym}}/USDT</b> ｜ <b>${{c.oi_act}}</b><div style="margin:4px 0">現價:<span class="pv p-${{c.sym}}">${{fmt(c.price)}}</span> (1H: ${{c.c1h>=0?'+':''}}${{c.c1h}}% / 換手: ${{c.turn}}%)</div><small style="color:#94a3b8;">賽克斯讀數: ${{c.cycs}} ${{c.res?'｜ '+c.res:''}}</small></div>`;}});
    document.getElementById('ac').innerHTML=ah;

