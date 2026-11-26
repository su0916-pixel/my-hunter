import streamlit as st
import streamlit.components.v1 as components
import requests, json

st.set_page_config(page_title="CYBER HUNTER AI", page_icon="⚡", layout="wide")
st.markdown("<style>.stApp{background:#070a10;color:#e2e8f0;}header[data-testid='stHeader']{background:transparent;}.block-container{padding-top:1rem;}</style>", unsafe_allow_html=True)

with st.sidebar:
    st.header("🧭 戰情室分頁導航")
    page = st.radio("選擇要查看的看板：", ["🔥 熱門幣種", "🟢 做多排行", "🔴 做空排行", "🌐 全部總覽"])
    st.divider()
    st.header("⚙️ 停損止盈設定")
    sl_p = st.slider("停損 (%)", 1.0, 5.0, 2.0, 0.5)
    tp_p = st.slider("止盈 (%)", 2.0, 15.0, 4.0, 0.5)
    if st.button("🔄 重新掃描 AI"):
        st.cache_data.clear()
        st.rerun()

@st.cache_data(ttl=60)
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
                s_sc, l_sc, s_m, l_m = 40, 40, [], []
                if c1h >= 2.0: s_sc += 24; s_m.append(f"1H急漲+{c1h:.1f}%")
                elif c1h >= 0.8: s_sc += 10; s_m.append(f"1H偏強+{c1h:.1f}%")
                if c1h <= -2.0: l_sc += 24; l_m.append(f"1H急跌{c1h:.1f}%")
                elif c1h <= -0.8: l_sc += 10; l_m.append(f"1H回調{c1h:.1f}%")
                if pos >= 88: s_sc += 20; s_m.append(f"逼近高點({pos:.0f}%)")
                elif pos <= 12: l_sc += 20; l_m.append(f"逼近低點({pos:.0f}%)")
                if c24h >= 10: s_sc += 15; s_m.append(f"暴漲+{c24h:.1f}%")
                elif c24h <= -10: l_sc += 15; l_msg.append(f"深跌{c24h:.1f}%")
                if turn >= 20:
                    if s_sc > l_sc: s_sc += 10; s_m.append(f"高換手{turn:.0f}%")
                    elif l_sc > s_sc: l_sc += 10; l_m.append(f"高換手{turn:.0f}%")
                rows.append({"sym":sym,"price":p,"c24h":round(c24h,2),"logo":f"{lp}{sym.lower()}@2x.png","s_sc":min(s_sc,99),"s_msg":" + ".join(s_m) or "動能中性","l_sc":min(l_sc,99),"l_msg":" + ".join(l_m) or "動能中性"})
    except Exception: pass
    return rows

data = get_data()
if not data:
    st.error("行情連線中，請點左上角選單「重新掃描 AI」重試...")
else:
    ho = ["BTC","ETH","SOL","XRP","DOGE","SUI"]
    hots = sorted([x for x in data if x["sym"] in ho], key=lambda x: ho.index(x["sym"]))
    shorts = sorted([x for x in data if x["s_sc"] >= x["l_sc"]], key=lambda x: x["s_sc"], reverse=True)[:5]
    longs = sorted([x for x in data if x["l_sc"] > x["s_sc"]], key=lambda x: x["l_sc"], reverse=True)[:5]
    ws_url = "".join(["w","ss://","ws.","okx",".","com:8443/ws/v5/public"])
    payload = json.dumps({"page":page,"hots":hots,"shorts":shorts,"longs":longs,"syms":list({x["sym"] for x in hots+shorts+longs}),"ws":ws_url,"tp":tp_p,"sl":sl_p})

    html = f"""<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1.0"><style>
    body{{background:#070a10;color:#e2e8f0;font-family:sans-serif;margin:0;padding:4px;}}
    .title{{font-size:23px;font-weight:900;color:#00f5d4;text-shadow:0 0 10px rgba(0,245,212,0.5);margin-bottom:8px;}}
    .bar{{display:flex;gap:8px;align-items:center;margin-bottom:12px;font-size:13px;flex-wrap:wrap;}}
    .clk{{font-family:monospace;color:#00f5d4;background:#0f172a;border:1px solid #1e293b;padding:4px 10px;border-radius:8px;font-weight:bold;}}
    .sec{{font-size:17px;font-weight:800;margin:10px 0 8px 0;}}
    .ghot{{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:10px;}}
    .cbox{{background:#0f172a;border:1.5px solid #38bdf8;border-radius:12px;padding:12px;}}
    .sbox{{background:#190a0f;border:2px solid #ff2a5f;border-radius:14px;padding:12px;margin-bottom:12px;}}
    .lbox{{background:#091813;border:2px solid #00f59b;border-radius:14px;padding:12px;margin-bottom:12px;}}
    .its{{background:rgba(255,42,95,0.1);border-left:4px solid #ff2a5f;border-radius:8px;padding:10px;margin-bottom:8px;}}
    .itl{{background:rgba(0,245,155,0.1);border-left:4px solid #00f59b;border-radius:8px;padding:10px;margin-bottom:8px;}}
    .lg{{width:20px;height:20px;border-radius:50%;vertical-align:middle;margin-right:6px;}}
    .pv{{font-family:monospace;font-size:17px;font-weight:900;padding:1px 4px;border-radius:4px;}}
    .up{{background:rgba(0,245,155,0.35);color:#00f59b;}}.dn{{background:rgba(255,42,95,0.35);color:#ff5c85;}}
    .hide{{display:none;}}
    </style></head><body>
    <div class="title">⚡ CYBER HUNTER AI · 量化戰情終端</div>
    <div class="bar"><div class="clk">🕒 台灣時間：<span id="ck">--:--:--</span></div><div id="st" style="color:#00f59b;font-weight:bold;">⚡ 連線 OKX 毫秒報價...</div></div>
    <div id="sec-hot"><div class="sec">🔥 熱門主流幣種（一幣一框 · 實時成交價）</div><div class="ghot" id="hc"></div></div>
    <div id="sec-long"><div class="sec" style="color:#00f59b;">🟢 AI 最佳【做多】TOP 5</div><div class="lbox" id="lc"></div></div>
    <div id="sec-short"><div class="sec" style="color:#ff5c85;">🔴 AI 最佳【做空】TOP 5</div><div class="sbox" id="sc"></div></div>
    <script>
    const D={payload},LP={{}};
    if(D.page==='🔥 熱門幣種'){{document.getElementById('sec-long').classList.add('hide');document.getElementById('sec-short').classList.add('hide');}}
    else if(D.page==='🟢 做多排行'){{document.getElementById('sec-hot').classList.add('hide');document.getElementById('sec-short').classList.add('hide');}}
    else if(D.page==='🔴 做空排行'){{document.getElementById('sec-hot').classList.add('hide');document.getElementById('sec-long').classList.add('hide');}}
    const fmt=p=>p<10?'$'+p.toFixed(4):'$'+p.toLocaleString('en-US',{{minimumFractionDigits:2,maximumFractionDigits:2}});
    setInterval(()=>{{document.getElementById('ck').innerText=new Date().toLocaleTimeString('zh-TW',{{timeZone:'Asia/Taipei',hour12:false}});}},1000);
    let hh='';D.hots.forEach(c=>{{LP[c.sym]=c.price;const isS=c.s_sc>c.l_sc,bc=isS?'#ff2a5f':(c.l_sc>c.s_sc?'#00f59b':'#38bdf8'),tg=isS?`🔴偏空${{c.s_sc}}分`:(c.l_sc>c.s_sc?`🟢偏多${{c.l_sc}}分`:'⚪盤整'),tp=isS?c.price*(1-D.tp/100):c.price*(1+D.tp/100),sl=isS?c.price*(1+D.sl/100):c.price*(1-D.sl/100);
    hh+=`<div class="cbox" style="border-color:${{bc}}"><img src="${{c.logo}}" class="lg" onerror="this.style.display='none'"><b>${{c.sym}}/USDT</b>｜<span style="color:${{bc}};font-weight:bold">${{tg}}</span><div style="margin:5px 0"><span class="pv p-${{c.sym}}">${{fmt(c.price)}}</span> (${{c.c24h>=0?'+':''}}${{c.c24h}}%)</div><small>🎯止盈:<span class="tph-${{c.sym}}">${{fmt(tp)}}</span>｜🛡️停損:<span class="slh-${{c.sym}}">${{fmt(sl)}}</span></small></div>`;}});
    document.getElementById('hc').innerHTML=hh;
    let sh='';D.shorts.forEach((c,i)=>{{LP[c.sym]=c.price;sh+=`<div class="its"><b>#${{i+1}}</b> <img src="${{c.logo}}" class="lg" onerror="this.style.display='none'"><b>${{c.sym}}/USDT</b>｜<span style="color:#ff5c85;font-weight:bold">勝率${{c.s_sc}}分</span><div style="margin:4px 0">現價:<span class="pv p-${{c.sym}}">${{fmt(c.price)}}</span> (${{c.c24h>=0?'+':''}}${{c.c24h}}%)</div><small>🎯止盈:<b class="tps-${{c.sym}}">${{fmt(c.price*(1-D.tp/100))}}</b>｜🛡️停損:<b class="sls-${{c.sym}}">${{fmt(c.price*(1+D.sl/100))}}</b><br>🔍${{c.s_msg}}</small></div>`;}});
    document.getElementById('sc').innerHTML=sh;
    let lh='';D.longs.forEach((c,i)=>{{LP[c.sym]=c.price;lh+=`<div class="itl"><b>#${{i+1}}</b> <img src="${{c.logo}}" class="lg" onerror="this.style.display='none'"><b>${{c.sym}}/USDT</b>｜<span style="color:#00f59b;font-weight:bold">勝率${{c.l_sc}}分</span><div style="margin:4px 0">現價:<span class="pv p-${{c.sym}}">${{fmt(c.price)}}</span> (${{c.c24h>=0?'+':''}}${{c.c24h}}%)</div><small>🎯止盈:<b class="tpl-${{c.sym}}">${{fmt(c.price*(1+D.tp/100))}}</b>｜🛡️停損:<b class="sll-${{c.sym}}">${{fmt(c.price*(1-D.sl/100))}}</b><br>🔍${{c.l_msg}}</small></div>`;}});
    document.getElementById('lc').innerHTML=lh;
    function conn(){{const ws=new WebSocket(D.ws);ws.onopen=()=>{{document.getElementById('st').innerText='🟢 OKX 實時成交跳動中';ws.send(JSON.stringify({{op:'subscribe',args:D.syms.map(s=>({{channel:'tickers',instId:s+'-USDT-SWAP'}}))}}));}};
    ws.onmessage=e=>{{const m=JSON.parse(e.data);if(!m.data||!m.data)return;const d=m.data,s=d.instId.replace('-USDT-SWAP',''),np=parseFloat(d.last),op=LP[s]||np;if(np===op)return;LP[s]=np;const cl=np>op?'up':'dn';
    document.querySelectorAll('.p-'+s).forEach(el=>{{el.innerText=fmt(np);el.classList.remove('up','dn');void el.offsetWidth;el.classList.add(cl);}});
    const hc=D.hots.find(x=>x.sym===s);if(hc){{const isS=hc.s_sc>hc.l_sc;document.querySelectorAll('.tph-'+s).forEach(el=>el.innerText=fmt(isS?np*(1-D.tp/100):np*(1+D.tp/100)));document.querySelectorAll('.slh-'+s).forEach(el=>el.innerText=fmt(isS?np*(1+D.sl/100):np*(1-D.sl/100)));}}
    document.querySelectorAll('.tps-'+s).forEach(el=>el.innerText=fmt(np*(1-D.tp/100)));document.querySelectorAll('.sls-'+s).forEach(el=>el.innerText=fmt(np*(1+D.sl/100)));
    document.querySelectorAll('.tpl-'+s).forEach(el=>el.innerText=fmt(np*(1+D.tp/100)));document.querySelectorAll('.sll-'+s).forEach(el=>el.innerText=fmt(np*(1-D.sl/100)));}};
    ws.onclose=()=>setTimeout(conn,3000);}}conn();
    </script></body></html>"""
    components.html(html, height=1300, scrolling=True)
