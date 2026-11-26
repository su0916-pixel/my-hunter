import streamlit as st
import streamlit.components.v1 as components
import requests, json

st.set_page_config(page_title="CYBER HUNTER AI", page_icon="⚡", layout="wide")
st.markdown("<style>.stApp{background:#070a10;color:#e2e8f0;}header[data-testid='stHeader'],section[data-testid='stSidebar']{display:none!important;}.block-container{padding-top:0.5rem;padding-left:0.5rem;padding-right:0.5rem;}</style>", unsafe_allow_html=True)

@st.cache_data(ttl=50)
def get_data():
    rows = []
    skip = {"USDT","USDC","FDUSD","DAI","TUSD","USDE","PYUSD","BUSD","USDS","WBTC","WETH","WBNB","STETH","WSTETH","WEETH","CBETH","BETH"}
    d1 = "".join(["ht","tps://","api.","coin","paprika",".","com","/v1/tickers?limit=80"])
    lp = "".join(["ht","tps://","assets.","coin","cap",".","io/assets/icons/"])
    try:
        r = requests.get(d1, headers={"User-Agent":"Mozilla/5.0"}, timeout=8)
        if r.status_code == 200:
            for c in r.json():
                sym = c.get("symbol","").upper()
                q = c.get("quotes",{}).get("USD",{})
                p = float(q.get("price") or 0)
                if not sym or sym in skip or p <= 0: continue
                c1h, c24h = float(q.get("percent_change_1h") or 0), float(q.get("percent_change_24h") or 0)
                turn = (float(q.get("volume_24h") or 0) / float(q.get("market_cap") or 1)) * 100
                pos = min(max(50.0 + c24h * 2.5, 5.0), 95.0)
                if c1h > 0.6 and turn >= 18: oi_act, oi_dir = "🟢 主力強勢開多 (資金湧入)", "LONG"
                elif c1h < -0.6 and turn >= 18: oi_act, oi_dir = "🔴 主力放量開空 (空單增倉)", "SHORT"
                elif c1h < -0.5 and c24h > 5: oi_act, oi_dir = "🟡 多頭獲利撤資 (平多減倉)", "SHORT"
                elif c1h > 0.5 and c24h < -5: oi_act, oi_dir = "🟣 空頭回補撤資 (平空減倉)", "LONG"
                else: oi_act, oi_dir = "⚪ 資金溫和換手", "NEUTRAL"
                cycs = round(max(min((c1h * 18) + ((50 - pos) * 0.8), 99), -99), 1)
                csig = "LONG" if cycs >= 25 else ("SHORT" if cycs <= -25 else "NEUTRAL")
                res = "🔥 雙指標【共振做多】買點" if (oi_dir=="LONG" and csig=="LONG") else ("🔥 雙指標【共振做空】賣點" if (oi_dir=="SHORT" and csig=="SHORT") else "")
                s_sc, l_sc, s_m, l_m = 40, 40, [], []
                if c1h >= 1.5: s_sc += 22; s_m.append(f"1H急漲+{c1h:.1f}%")
                if c1h <= -1.5: l_sc += 22; l_m.append(f"1H急跌{c1h:.1f}%")
                if pos >= 85: s_sc += 18; s_m.append(f"高位乖離({pos:.0f}%)")
                if pos <= 15: l_sc += 18; l_m.append(f"低位超賣({pos:.0f}%)")
                if oi_dir == "SHORT": s_sc += 18; s_m.append(oi_act)
                if oi_dir == "LONG": l_sc += 18; l_m.append(oi_act)
                if res:
                    if "空" in res: s_sc += 15; s_m.append("賽克斯共振")
                    if "多" in res: l_sc += 15; l_m.append("賽克斯共振")
                rows.append({"sym":sym,"price":p,"c1h":round(c1h,2),"c24h":round(c24h,2),"turn":round(turn,1),"logo":f"{lp}{sym.lower()}@2x.png","oi_act":oi_act,"oi_dir":oi_dir,"cycs":cycs,"res":res,"s_sc":min(s_sc,99),"s_msg":" + ".join(s_m) or "動能中性","l_sc":min(l_sc,99),"l_msg":" + ".join(l_m) or "動能中性"})
    except Exception: pass
    return rows
data = get_data()
ho = ["BTC","ETH","SOL","XRP","DOGE","SUI"]
hots = sorted([x for x in data if x["sym"] in ho], key=lambda x: ho.index(x["sym"]))
shorts = sorted([x for x in data if x["s_sc"] >= x["l_sc"]], key=lambda x: x["s_sc"], reverse=True)[:5]
longs = sorted([x for x in data if x["l_sc"] > x["s_sc"]], key=lambda x: x["l_sc"], reverse=True)[:5]
anom = sorted([x for x in data if x["oi_dir"] != "NEUTRAL"], key=lambda x: x["turn"], reverse=True)[:8]
res_list = [x for x in data if x["res"] != ""]
all_syms = list({x["sym"] for x in hots + shorts + longs + anom + res_list})
ws_url = "".join(["w","ss://","ws.","okx",".","com:8443/ws/v5/public"])
rest_url = "".join(["ht","tps://","www.","okx",".","com/api/v5/market/tickers?instType=SWAP"])
payload = json.dumps({"hots":hots,"shorts":shorts,"longs":longs,"anom":anom,"res":res_list,"syms":all_syms,"ws":ws_url,"rest":rest_url})

html = f"""<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1.0"><style>
body{{background:#070a10;color:#e2e8f0;font-family:sans-serif;margin:0;padding:4px;}}
.title{{font-size:21px;font-weight:900;color:#00f5d4;text-shadow:0 0 10px rgba(0,245,212,0.5);margin-bottom:6px;}}
.bar{{display:flex;gap:8px;align-items:center;margin-bottom:10px;font-size:12px;flex-wrap:wrap;}}
.clk{{font-family:monospace;color:#00f5d4;background:#0f172a;border:1px solid #1e293b;padding:4px 9px;border-radius:8px;font-weight:bold;}}
.tabs{{display:grid;grid-template-columns:repeat(5,1fr);gap:4px;margin-bottom:12px;position:sticky;top:0;background:#070a10;padding:5px 0;z-index:99;}}
.tab{{background:#0f172a;color:#94a3b8;border:1px solid #1e293b;border-radius:8px;padding:8px 2px;font-size:11px;font-weight:800;text-align:center;cursor:pointer;}}
.tab.active{{background:linear-gradient(135deg,#00f5d4,#00bbf9);color:#05080f;border:none;}}
.sec{{font-size:15px;font-weight:800;margin:8px 0;}}
.ghot{{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:8px;margin-bottom:12px;}}
.cbox{{background:#0f172a;border:1.5px solid #38bdf8;border-radius:12px;padding:11px;}}
.sbox{{background:#190a0f;border:2px solid #ff2a5f;border-radius:14px;padding:10px;margin-bottom:12px;}}
.lbox{{background:#091813;border:2px solid #00f59b;border-radius:14px;padding:10px;margin-bottom:12px;}}
.abox{{background:#0f172a;border:2px solid #38bdf8;border-radius:14px;padding:10px;margin-bottom:12px;}}
.rbox{{background:#1c1507;border:2px solid #facc15;border-radius:14px;padding:10px;margin-bottom:12px;}}
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
<div class="bar"><div class="clk">🕒 台灣：<span id="ck">--:--:--</span></div><div id="st" style="color:#00f59b;font-weight:bold;">⚡ 啟動實時報價...</div></div>
<div class="tabs">
  <div class="tab active" onclick="sw('hot',this)">🔥 熱門幣</div>
  <div class="tab" onclick="sw('rank',this)">🎯 推薦榜</div>
  <div class="tab" onclick="sw('anom',this)">📡 異常監控</div>
  <div class="tab" onclick="sw('res',this)">⚡ 共振買點</div>
  <div class="tab" onclick="sw('all',this)">🌐 全部</div>
</div>
<div id="p-hot"><div class="sec">🔥 熱門主流幣種（一幣一框 · 實時跳動）</div><div class="ghot" id="hc"></div></div>
<div id="p-res" class="hide"><div class="sec" style="color:#facc15;">⚡ 賽克斯指標 ＋ 獵手【雙重共振買點】</div><div class="rbox" id="rc"></div></div>
<div id="p-anom" class="hide"><div class="sec" style="color:#38bdf8;">📡 數據異常（主力開倉 / 撤資判別）</div><div class="abox" id="ac"></div></div>
<div id="p-rank" class="hide">
  <div class="sec" style="color:#ff5c85;">🔴 AI 推薦【做空】TOP 5</div><div class="sbox" id="sc"></div>
  <div class="sec" style="color:#00f59b;">🟢 AI 推薦【做多】TOP 5</div><div class="lbox" id="lc"></div>
</div>
<script>
const D={payload},LP={{}};
function sw(t,el){{document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));el.classList.add('active');
document.getElementById('p-hot').classList.toggle('hide',t!=='hot'&&t!=='all');
document.getElementById('p-rank').classList.toggle('hide',t!=='rank'&&t!=='all');
document.getElementById('p-anom').classList.toggle('hide',t!=='anom'&&t!=='all');
document.getElementById('p-res').classList.toggle('hide',t!=='res'&&t!=='all');}}
const fmt=p=>p<0.01?'$'+p.toFixed(6):(p<1?'$'+p.toFixed(5):(p<10?'$'+p.toFixed(4):'$'+p.toLocaleString('en-US',{{minimumFractionDigits:2,maximumFractionDigits:2}})));
setInterval(()=>{{document.getElementById('ck').innerText=new Date().toLocaleTimeString('zh-TW',{{timeZone:'Asia/Taipei',hour12:false}});}},1000);
let hh='';D.hots.forEach(c=>{{LP[c.sym]=c.price;const isS=c.s_sc>c.l_sc,bc=isS?'#ff2a5f':(c.l_sc>c.s_sc?'#00f59b':'#38bdf8'),tg=isS?`🔴偏空${{c.s_sc}}分`:(c.l_sc>c.s_sc?`🟢偏多${{c.l_sc}}分`:'⚪盤整');
hh+=`<div class="cbox" style="border-color:${{bc}}"><img src="${{c.logo}}" class="lg" onerror="this.style.display='none'"><b>${{c.sym}}/USDT</b>｜<span style="color:${{bc}};font-weight:bold">${{tg}}</span><div style="margin:5px 0"><span class="pv p-${{c.sym}}">${{fmt(c.price)}}</span> (${{c.c24h>=0?'+':''}}${{c.c24h}}%)</div><small>🎯止盈:<b class="tph-${{c.sym}}">${{fmt(isS?c.price*0.96:c.price*1.04)}}</b>｜🛡️停損:<b class="slh-${{c.sym}}">${{fmt(isS?c.price*1.02:c.price*0.98)}}</b></small></div>`;}});
document.getElementById('hc').innerHTML=hh;
let rh=D.res.length===0?'<div style="color:#94a3b8;padding:8px;">目前兩大指標尚未出現同向共振，請先參考推薦排行。</div>':'';
D.res.forEach(c=>{{LP[c.sym]=c.price;const isL=c.res.includes('做多');rh+=`<div class="itr"><img src="${{c.logo}}" class="lg" onerror="this.style.display='none'"><b>${{c.sym}}/USDT</b>｜<span style="color:#facc15;font-weight:900">${{c.res}}</span><div style="margin:4px 0">現價:<span class="pv p-${{c.sym}}">${{fmt(c.price)}}</span>｜賽克斯:<b>${{c.cycs}}</b></div><small>主力:<b>${{c.oi_act}}</b><br>🎯止盈:<b>${{fmt(isL?c.price*1.04:c.price*0.96)}}</b>｜🛡️停損:<b>${{fmt(isL?c.price*0.98:c.price*1.02)}}</b></small></div>`;}});
document.getElementById('rc').innerHTML=rh;
let ah='';D.anom.forEach(c=>{{LP[c.sym]=c.price;ah+=`<div class="ita"><img src="${{c.logo}}" class="lg" onerror="this.style.display='none'"><b>${{c.sym}}/USDT</b>｜<b>${{c.oi_act}}</b><div style="margin:4px 0">現價:<span class="pv p-${{c.sym}}">${{fmt(c.price)}}</span> (1H:${{c.c1h>=0?'+':''}}${{c.c1h}}%/換手:${{c.turn}}%)</div><small style="color:#94a3b8">賽克斯讀數:${{c.cycs}} ${{c.res?'｜'+c.res:''}}</small></div>`;}});
document.getElementById('ac').innerHTML=ah;
let sh='';D.shorts.forEach((c,i)=>{{LP[c.sym]=c.price;sh+=`<div class="its"><b>#${{i+1}}</b> <img src="${{c.logo}}" class="lg" onerror="this.style.display='none'"><b>${{c.sym}}/USDT</b>｜<span style="color:#ff5c85;font-weight:bold">勝率${{c.s_sc}}分</span><div style="margin:4px 0">現價:<span class="pv p-${{c.sym}}">${{fmt(c.price)}}</span> (${{c.c24h>=0?'+':''}}${{c.c24h}}%)</div><small>🎯止盈:<b>${{fmt(c.price*0.96)}}</b>｜🛡️停損:<b>${{fmt(c.price*1.02)}}</b><br>🔍${{c.s_msg}}</small></div>`;}});
document.getElementById('sc').innerHTML=sh;
let lh='';D.longs.forEach((c,i)=>{{LP[c.sym]=c.price;lh+=`<div class="itl"><b>#${{i+1}}</b> <img src="${{c.logo}}" class="lg" onerror="this.style.display='none'"><b>${{c.sym}}/USDT</b>｜<span style="color:#00f59b;font-weight:bold">勝率${{c.l_sc}}分</span><div style="margin:4px 0">現價:<span class="pv p-${{c.sym}}">${{fmt(c.price)}}</span> (${{c.c24h>=0?'+':''}}${{c.c24h}}%)</div><small>🎯止盈:<b>${{fmt(c.price*1.04)}}</b>｜🛡️停損:<b>${{fmt(c.price*0.98)}}</b><br>🔍${{c.l_msg}}</small></div>`;}});
document.getElementById('lc').innerHTML=lh;
function updateTick(s,np){{const op=LP[s];if(!op||np===op)return;LP[s]=np;const cl=np>op?'up':'dn';
document.querySelectorAll('.p-'+s).forEach(el=>{{el.innerText=fmt(np);el.classList.remove('up','dn');void el.offsetWidth;el.classList.add(cl);setTimeout(()=>el.classList.remove('up','dn'),400);}});}}
function connWS(){{const ws=new WebSocket(D.ws);ws.onopen=()=>{{document.getElementById('st').innerText='⚡ OKX 逐筆成交狂跳中';
D.syms.forEach(s=>ws.send(JSON.stringify({{op:'subscribe',args:[{{channel:'trades',instId:s+'-USDT-SWAP'}},{{channel:'bbo-tbt',instId:s+'-USDT-SWAP'}}]}})));}};
ws.onmessage=e=>{{const m=JSON.parse(e.data);if(m.data&&m.data){{const d=m.data,s=d.instId.replace('-USDT-SWAP',''),p=parseFloat(d.px||d.bidPx||d.last);if(p>0)updateTick(s,p);}}}};
ws.onclose=()=>setTimeout(connWS,2000);}}connWS();
setInterval(()=>{{fetch(D.rest).then(r=>r.json()).then(j=>{{if(j.data)j.data.forEach(d=>updateTick(d.instId.replace('-USDT-SWAP',''),parseFloat(d.last)));}}).catch(()=>{{}});}},1000);
</script></body></html>"""
components.html(html, height=1800, scrolling=True)
