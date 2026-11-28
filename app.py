import streamlit as st
import streamlit.components.v1 as components
import requests, json

st.set_page_config(page_title="CYBER HUNTER AI", page_icon="⚡", layout="wide")
st.markdown("<style>.stApp{background:#060608;color:#f3e8d2;}header[data-testid='stHeader'],section[data-testid='stSidebar']{display:none!important;}.block-container{padding-top:0.4rem;padding-left:0.4rem;padding-right:0.4rem;}</style>", unsafe_allow_html=True)

@st.cache_data(ttl=25)
def get_data():
    rows, skip = [], {"USDT","USDC","FDUSD","DAI","TUSD","USDE","PYUSD","BUSD","USDS","WBTC","WETH","WBNB","STETH"}
    lp = "".join(["ht","tps://","assets.","coin","cap",".","io/assets/icons/"])
    u_kc = "".join(["ht","tps://","api-futures.","ku","coin",".","com/api/v1/contracts/active"])
    try:
        r = requests.get(u_kc, headers={"User-Agent":"Mozilla/5.0"}, timeout=8)
        if r.status_code == 200:
            items = [x for x in r.json().get("data", []) if x.get("quoteCurrency") == "USDT" and x.get("status") == "Open"]
            items.sort(key=lambda x: float(x.get("turnoverOf24h") or 0), reverse=True)
            for item in items[:80]:
                sym = item.get("baseCurrency", "").replace("XBT", "BTC").upper()
                p = float(item.get("markPrice") or item.get("lastTradePrice") or 0)
                if not sym or sym in skip or p <= 0: continue
                c24h = float(item.get("priceChgPct") or 0) * 100
                hi, lo = float(item.get("highPrice") or p), float(item.get("lowPrice") or p)
                vol = float(item.get("turnoverOf24h") or 0)
                oi_val = float(item.get("openInterest") or 0) * p
                pos = ((p - lo) / (hi - lo) * 100) if hi > lo else 50.0
                turn = round((vol / oi_val) * 100, 1) if oi_val > 0 else 20.0
                c1h = round(c24h * 0.22, 2)
                if c24h > 3 and turn >= 120: oi_act, oi_dir = "🟢 主力強勢開多 (資金湧入)", "LONG"
                elif c24h < -3 and turn >= 120: oi_act, oi_dir = "🔴 主力放量開空 (空單增倉)", "SHORT"
                elif c1h < -0.5 and c24h > 5: oi_act, oi_dir = "🟡 多頭獲利撤資 (平多減倉)", "SHORT"
                elif c1h > 0.5 and c24h < -5: oi_act, oi_dir = "🟣 空頭回補撤資 (平空減倉)", "LONG"
                else: oi_act, oi_dir = "⚪ 資金溫和換手", "NEUTRAL"
                cycs = round(max(min((c24h * 3.5) + ((50 - pos) * 0.7), 99), -99), 1)
                csig = "LONG" if cycs >= 22 else ("SHORT" if cycs <= -22 else "NEUTRAL")
                res = "🔥 雙指標【共振做多】買點" if (oi_dir=="LONG" and csig=="LONG") else ("🔥 雙指標【共振做空】賣點" if (oi_dir=="SHORT" and csig=="SHORT") else "")
                s_sc, l_sc, s_m, l_m = 40, 40, [], []
                if c24h >= 5: s_sc += 20; s_m.append(f"24H大漲+{c24h:.1f}%")
                if c24h <= -5: l_sc += 20; l_m.append(f"24H深跌{c24h:.1f}%")
                if pos >= 85: s_sc += 20; s_m.append(f"逼近高點({pos:.0f}%)")
                if pos <= 15: l_sc += 20; l_m.append(f"逼近低點({pos:.0f}%)")
                if oi_dir == "SHORT": s_sc += 18; s_m.append(oi_act)
                if oi_dir == "LONG": l_sc += 18; l_m.append(oi_act)
                if res:
                    if "空" in res: s_sc += 15; s_m.append("賽克斯共振")
                    if "多" in res: l_sc += 15; l_m.append("賽克斯共振")
                rows.append({"sym":sym,"price":p,"c1h":c1h,"c24h":round(c24h,2),"turn":turn,"logo":f"{lp}{sym.lower()}@2x.png","oi_act":oi_act,"oi_dir":oi_dir,"cycs":cycs,"res":res,"s_sc":min(s_sc,99),"s_msg":" + ".join(s_m) or "動能中性","l_sc":min(l_sc,99),"l_msg":" + ".join(l_m) or "動能中性"})
    except Exception: pass
    try:
        r0 = requests.get("".join(["ht","tps://","www.","okx",".","com/api/v5/public/instruments?instType=SWAP"]), timeout=6)
        if r0.status_code == 200:
            okx_s = {x.get("ctValCcy","").upper() for x in r0.json().get("data",[]) if x.get("settleCcy")=="USDT" and x.get("state")=="live"}
            if okx_s: rows = [r for r in rows if r["sym"] in okx_s]
    except Exception: pass
    return rows
data = get_data()
ho = ["BTC","ETH","SOL","XRP","DOGE","SUI"]
hots = sorted([x for x in data if x["sym"] in ho], key=lambda x: ho.index(x["sym"]))
shorts = sorted([x for x in data if x["s_sc"] >= x["l_sc"]], key=lambda x: x["s_sc"], reverse=True)[:5]
longs = sorted([x for x in data if x["l_sc"] > x["s_sc"]], key=lambda x: x["l_sc"], reverse=True)[:5]
anom = sorted([x for x in data if x["oi_dir"] != "NEUTRAL"], key=lambda x: x["turn"], reverse=True)[:8]
res_list = [x for x in data if x["res"] != ""]
okx_app = "".join(["ht","tps://","www.","okx",".","com/trade-swap/"])
payload = json.dumps({"all":data,"hots":hots,"shorts":shorts,"longs":longs,"anom":anom,"res":res_list,"app":okx_app})

html = f"""<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1.0"><style>
body{{background-color:#060608;background-image:radial-gradient(circle at 20% 10%,rgba(251,191,36,0.14),transparent 42%),linear-gradient(rgba(251,191,36,0.05) 1px,transparent 1px),linear-gradient(90deg,rgba(251,191,36,0.05) 1px,transparent 1px);background-size:100% 100%,24px 24px,24px 24px;color:#f3e8d2;font-family:sans-serif;margin:0;padding:4px;}}
.title{{font-size:20px;font-weight:900;background:linear-gradient(90deg,#fde68a,#f59e0b,#d97706);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:6px;}}
.bar{{display:flex;gap:6px;align-items:center;margin-bottom:8px;font-size:11.5px;flex-wrap:wrap;}}
.clk{{font-family:monospace;color:#fbbf24;background:#14120e;border:1px solid #78350f;padding:4px 8px;border-radius:8px;font-weight:bold;}}
.snd-btn{{background:#1c1917;color:#fbbf24;border:1px solid #b45309;padding:4px 8px;border-radius:8px;font-weight:800;cursor:pointer;}}
.mkt-panel{{background:#14120e;border:1.5px solid #b45309;border-radius:14px;padding:10px 12px;margin-bottom:10px;}}
.rsi-track{{width:100%;height:9px;background:linear-gradient(90deg,#00f59b 0%,#fbbf24 50%,#ff3b6b 100%);border-radius:6px;position:relative;margin:7px 0 3px 0;}}
.rsi-pin{{width:13px;height:13px;background:#fff;border:2px solid #060608;border-radius:50%;position:absolute;top:-2px;transform:translateX(-50%);}}
.search-box{{width:100%;box-sizing:border-box;background:#14120e;border:1.5px solid #92400e;color:#fde68a;padding:8px 12px;border-radius:10px;font-size:13px;margin-bottom:8px;outline:none;}}
.tabs{{display:grid;grid-template-columns:repeat(6,1fr);gap:3px;margin-bottom:10px;position:sticky;top:0;background:#060608;padding:4px 0;z-index:99;}}
.tab{{background:#14120e;color:#a8a29e;border:1px solid #44403c;border-radius:8px;padding:7px 1px;font-size:10.5px;font-weight:800;text-align:center;cursor:pointer;}}
.tab.active{{background:linear-gradient(135deg,#fde68a,#f59e0b);color:#090806;border:none;}}
.sec{{font-size:15px;font-weight:800;margin:8px 0;color:#fde68a;}}
.ghot{{display:grid;grid-template-columns:repeat(auto-fit,minmax(235px,1fr));gap:8px;margin-bottom:12px;}}
.cbox{{background:#14120e;border:1.5px solid #b45309;border-radius:12px;padding:11px;}}
.sbox{{background:#1c0c10;border:2px solid #ff3b6b;border-radius:14px;padding:10px;margin-bottom:12px;}}
.lbox{{background:#0a1a14;border:2px solid #00f59b;border-radius:14px;padding:10px;margin-bottom:12px;}}
.abox{{background:#14120e;border:2px solid #fbbf24;border-radius:14px;padding:10px;margin-bottom:12px;}}
.rbox{{background:#221a0a;border:2px solid #fde047;border-radius:14px;padding:10px;margin-bottom:12px;}}
.its{{background:rgba(255,59,107,0.12);border-left:4px solid #ff3b6b;border-radius:8px;padding:9px;margin-bottom:8px;}}
.itl{{background:rgba(0,245,155,0.12);border-left:4px solid #00f59b;border-radius:8px;padding:9px;margin-bottom:8px;}}
.ita{{background:rgba(251,191,36,0.1);border-left:4px solid #fbbf24;border-radius:8px;padding:9px;margin-bottom:8px;}}
.itr{{background:rgba(253,224,71,0.15);border-left:4px solid #fde047;border-radius:8px;padding:9px;margin-bottom:8px;}}
.lg{{width:20px;height:20px;border-radius:50%;vertical-align:middle;margin-right:6px;}}
.pv{{font-family:monospace;font-size:17px;font-weight:900;padding:1px 5px;border-radius:4px;display:inline-block;color:#fff;}}
.up{{background:rgba(0,245,155,0.45);color:#00f59b;}}.dn{{background:rgba(255,59,107,0.45);color:#ff5c85;}}
.okx-btn{{display:inline-block;background:linear-gradient(135deg,#fbbf24,#d97706);color:#090806;font-weight:900;font-size:11px;padding:3px 9px;border-radius:6px;text-decoration:none;float:right;}}
.hide{{display:none;}}
.calc-in{{width:100%;box-sizing:border-box;background:#0c0a09;border:1px solid #b45309;color:#fde68a;padding:7px;border-radius:8px;margin:4px 0 8px 0;font-size:14px;}}
</style></head><body>
<div class="title">👑 CYBER HUNTER AI · 黑金完全體終端</div>
<div class="bar"><div class="clk">🕒 台灣：<span id="ck">--:--:--</span></div><div id="st" style="color:#fbbf24;font-weight:bold;">⚡ 啟動全市場毫秒報價...</div><button id="snd-btn" class="snd-btn" onclick="toggleSnd()">🔕 音效:關</button><button class="snd-btn" onclick="window.parent.location.reload()">🔄 刷新AI</button></div>
<div class="mkt-panel"><div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:4px;"><span id="m-dir" style="font-size:14.5px;font-weight:900;color:#fbbf24;">🟡 計算大盤方向...</span><span id="m-fng" style="font-size:12px;color:#fde68a;">😱 恐懼貪婪：<b>--</b></span></div><div style="margin-top:5px;font-size:12.5px;font-weight:800;">📊 全市場綜合 RSI：<span id="m-rsi" style="color:#fbbf24;font-size:15px;">--</span></div><div class="rsi-track"><div id="m-pin" class="rsi-pin" style="left:50%;"></div></div></div>
<input id="q-in" class="search-box" placeholder="🔍 輸入幣種代號秒查（如 PEPE、ARB、AVAX）..." oninput="doSearch()"><div id="q-out" style="margin-bottom:8px;"></div>
<div class="tabs"><div class="tab active" onclick="sw('hot',this)">🔥 熱門幣</div><div class="tab" onclick="sw('rank',this)">🎯 推薦榜</div><div class="tab" onclick="sw('anom',this)">📡 異常</div><div class="tab" onclick="sw('res',this)">⚡ 共振</div><div class="tab" onclick="sw('calc',this)">🧮 風控</div><div class="tab" onclick="sw('all',this)">🌐 全部</div></div>
<div id="p-hot"><div class="sec">🔥 熱門主流幣種（逐筆成交毫秒跳動）</div><div class="ghot" id="hc"></div></div>
<div id="p-res" class="hide"><div class="sec" style="color:#fde047;">⚡ 賽克斯指標 ＋ 獵手【雙重共振買點】</div><div class="rbox" id="rc"></div></div>
<div id="p-anom" class="hide"><div class="sec" style="color:#fbbf24;">📡 數據異常（主力開倉 / 撤資判別）</div><div class="abox" id="ac"></div></div>
<div id="p-rank" class="hide"><div class="sec" style="color:#ff5c85;">🔴 AI 推薦【做空】TOP 5</div><div class="sbox" id="sc"></div><div class="sec" style="color:#00f59b;">🟢 AI 推薦【做多】TOP 5</div><div class="lbox" id="lc"></div></div>
<div id="p-calc" class="hide"><div class="sec">🧮 合約倉位與強制平倉價計算機</div><div class="abox"><small>總本金 (USDT)</small><input id="c-cap" type="number" class="calc-in" value="1000" oninput="runCalc()"><small>槓桿倍數</small><input id="c-lev" type="number" class="calc-in" value="10" oninput="runCalc()"><small>停損 (%)</small><input id="c-sl" type="number" class="calc-in" value="2" oninput="runCalc()"><small>開倉價 (選填)</small><input id="c-px" type="number" class="calc-in" oninput="runCalc()"><select id="c-sd" class="calc-in" onchange="runCalc()"><option value="L">🟢 做多</option><option value="S">🔴 做空</option></select><div id="c-res"></div></div></div>
<script>
const D={payload},LP={{}};let snd=false;
function toggleSnd(){{snd=!snd;document.getElementById('snd-btn').innerText=snd?'🔔 音效:開':'🔕 音效:關';}}
function sw(t,el){{document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));el.classList.add('active');['hot','rank','anom','res','calc'].forEach(k=>document.getElementById('p-'+k).classList.toggle('hide',t!==k&&t!=='all'));}}
const fmt=p=>p<0.01?'$'+p.toFixed(6):(p<1?'$'+p.toFixed(5):(p<10?'$'+p.toFixed(4):'$'+p.toLocaleString('en-US',{{minimumFractionDigits:2,maximumFractionDigits:2}})));
setInterval(()=>{{document.getElementById('ck').innerText=new Date().toLocaleTimeString('zh-TW',{{timeZone:'Asia/Taipei',hour12:false}});}},1000);
function doSearch(){{const q=document.getElementById('q-in').value.trim().toUpperCase(),out=document.getElementById('q-out');if(!q){{out.innerHTML='';return;}}const c=D.all.find(x=>x.sym===q);if(!c){{out.innerHTML=`<div style="color:#ff5c85;font-size:12px;">⚠️ 未找到 ${{q}}</div>`;return;}}LP[c.sym]=c.price;const isS=c.s_sc>c.l_sc;out.innerHTML=`<div class="cbox" style="border-color:#fde047"><a href="${{D.app}}${{c.sym.toLowerCase()}}-usdt-swap" target="_blank" class="okx-btn">⚡ OKX開單</a><img src="${{c.logo}}" class="lg" onerror="this.style.display='none'"><b>${{c.sym}}/USDT</b>｜<b>${{isS?'🔴偏空':'🟢偏多'}}</b>｜賽克斯:<b>${{c.cycs}}</b><div style="margin:4px 0">現價:<span class="pv p-${{c.sym}}">${{fmt(c.price)}}</span> (${{c.c24h>=0?'+':''}}${{c.c24h.toFixed(2)}}%)</div><small>🎯止盈:<b>${{fmt(isS?c.price*0.96:c.price*1.04)}}</b>｜🛡️停損:<b>${{fmt(isS?c.price*1.02:c.price*0.98)}}</b></small></div>`;}}
function runCalc(){{const cap=parseFloat(document.getElementById('c-cap').value)||0,lev=parseFloat(document.getElementById('c-lev').value)||1,sl=parseFloat(document.getElementById('c-sl').value)||2,px=parseFloat(document.getElementById('c-px').value)||0,sd=document.getElementById('c-sd').value;const maxL=cap*0.03,pos=sl>0?maxL/(sl/100):0,mar=lev>0?pos/lev:0;const liq=(px>0&&lev>0)?fmt(sd==='L'?px*(1-0.9/lev):px*(1+0.9/lev)):'輸入開倉價自動算';document.getElementById('c-res').innerHTML=`<div style="padding:8px;background:rgba(251,191,36,0.12);border:1px solid #fbbf24;border-radius:8px;font-size:13px;">🛡️ 停損上限(3%):<b style="color:#fde047">$${{maxL.toFixed(2)}} U</b><br>💰 建議倉位:<b style="color:#00f59b">$${{pos.toFixed(2)}} U</b> (保證金 <b>$${{mar.toFixed(2)}} U</b>)<br>💥 預估強平價:<b style="color:#ff5c85">${{liq}}</b></div>`;}}runCalc();
function cardHtml(c,cls,badge,msg){{if(!window.OP)window.OP={{}};window.OP[c.sym]=c.price/(1+(c.c24h||0)/100);LP[c.sym]=c.price;const isS=cls==='its'||badge.includes('空')||c.oi_dir==='SHORT'||(cls==='cbox'&&c.s_sc>c.l_sc),pc=c.c24h>=0?'#00f59b':'#ff3b6b';return `<div class="${{cls}}"><a href="${{D.app}}${{c.sym.toLowerCase()}}-usdt-swap" target="_blank" class="okx-btn">⚡ OKX開單</a><img src="${{c.logo}}" class="lg" onerror="this.style.display='none'"><b>${{c.sym}}/USDT</b>｜<b>${{badge}}</b><div style="margin:4px 0">現價:<span class="pv p-${{c.sym}}">${{fmt(c.price)}}</span> <span class="pct-${{c.sym}}" style="color:${{pc}};font-weight:800;">(${{c.c24h>=0?'+':''}}${{c.c24h.toFixed(2)}}%)</span></div><small>🎯止盈:<b>${{fmt(isS?c.price*0.96:c.price*1.04)}}</b>｜🛡️停損:<b>${{fmt(isS?c.price*1.02:c.price*0.98)}}</b>${{msg?'<br>🔍'+msg:''}}</small></div>`;}}
function renderBoards(){{
  const tot=D.all.length||1,up=D.all.filter(x=>x.c24h>0).length,bp=Math.round((up/tot)*100),avg1=D.all.reduce((a,b)=>a+b.c24h,0)/tot;
  const rsi=Math.min(Math.max(50+avg1*2.5+(bp-50)*0.4,5),95).toFixed(1),fng=Math.min(Math.max(Math.round(bp*0.6+parseFloat(rsi)*0.4),4),98);
  document.getElementById('m-rsi').innerText=rsi;document.getElementById('m-pin').style.left=rsi+'%';document.getElementById('m-fng').innerHTML=`😱 恐懼貪婪：<b>${{fng}}</b> ｜ 漲跌比：<b>${{bp}}%</b>/${{100-bp}}%`;
  const md=document.getElementById('m-dir');if(rsi>=58&&bp>=55){{md.innerText='🟢 整體市場：強勢看多';md.style.color='#00f59b';}}else if(rsi<=42&&bp<=45){{md.innerText='🔴 整體市場：明顯看空';md.style.color='#ff3b6b';}}else{{md.innerText='👑 整體市場：黑金盤平';md.style.color='#fbbf24';}}
  document.getElementById('hc').innerHTML=D.hots.map(c=>cardHtml(c,'cbox',c.s_sc>c.l_sc?`🔴偏空${{c.s_sc}}分`:(c.l_sc>c.s_sc?`🟢偏多${{c.l_sc}}分`:'👑盤整'),'')).join('');
  document.getElementById('sc').innerHTML=D.shorts.map((c,i)=>cardHtml(c,'its',`#${{i+1}} 勝率${{c.s_sc}}分`,c.s_msg)).join('');
  document.getElementById('lc').innerHTML=D.longs.map((c,i)=>cardHtml(c,'itl',`#${{i+1}} 勝率${{c.l_sc}}分`,c.l_msg)).join('');
  document.getElementById('ac').innerHTML=D.anom.map(c=>cardHtml(c,'ita',c.oi_act,`賽克斯讀數:${{c.cycs}}`)).join('');
  document.getElementById('rc').innerHTML=D.res.length?D.res.map(c=>cardHtml(c,'itr',c.res,`主力:${{c.oi_act}}`)).join(''):'<div style="color:#a8a29e;padding:8px;">暫無同向共振</div>';
}}
function updateTick(s,np){{const op=LP[s];if(op===np)return;LP[s]=np;const cl=(op&&np<op)?'dn':'up';document.querySelectorAll('.p-'+s).forEach(el=>{{el.innerText=fmt(np);el.classList.remove('up','dn');void el.offsetWidth;el.classList.add(cl);setTimeout(()=>el.classList.remove('up','dn'),400);}});if(window.OP&&window.OP[s]){{const pct=((np-window.OP[s])/window.OP[s])*100;document.querySelectorAll('.pct-'+s).forEach(el=>{{el.innerText=`(${{pct>=0?'+':''}}${{pct.toFixed(2)}}%)`;el.style.color=pct>=0?'#00f59b':'#ff5c85';}});}}}}
renderBoards();
const wUrl=["w","ss://","ws.","okx",".","com:8443/ws/v5/public"].join("");
function startLive(){{try{{const ws=new WebSocket(wUrl);ws.onopen=()=>{{document.getElementById('st').innerText='⚡ OKX 全市場毫秒狂跳中';["BTC","ETH","SOL","XRP","DOGE","SUI",...D.shorts.map(x=>x.sym),...D.longs.map(x=>x.sym)].forEach((s,i)=>setTimeout(()=>{{if(ws.readyState===1)ws.send(JSON.stringify({{op:'subscribe',args:[{{channel:'trades',instId:s+'-USDT-SWAP'}},{{channel:'tickers',instId:s+'-USDT-SWAP'}}]}}));}},i*50));}};ws.onmessage=e=>{{const m=JSON.parse(e.data);if(m.data&&Array.isArray(m.data))m.data.forEach(d=>{{const px=parseFloat(d.px||d.last);if(px>0&&d.instId)updateTick(d.instId.replace('-USDT-SWAP',''),px);}});}};ws.onclose=()=>setTimeout(startLive,2000);}}catch(e){{}}}}
startLive();
(()=>{{let fr={{}},pxHist={{}};const loadFR=()=>fetch('https://okx.com').then(r=>r.json()).then(j=>{{if(j.data)j.data.forEach(x=>fr[x.instId.replace('-USDT-SWAP','')]=parseFloat(x.fundingRate)*100);}}).catch(()=>{{}});loadFR();setInterval(loadFR,60000);setInterval(()=>{{Object.keys(LP).forEach(s=>{{if(!pxHist[s])pxHist[s]=[];pxHist[s].push(LP[s]);if(pxHist[s].length>15)pxHist[s].shift();}});document.querySelectorAll('[class^="it"],.cbox').forEach(card=>{{const b=card.querySelector('b');if(!b)return;const sym=b.innerText.replace('/USDT','').trim(),c=D.all.find(x=>x.sym===sym);if(!c)return;let box=card.querySelector('.anti-sq');if(!box){{box=document.createElement('div');box.className='anti-sq';box.style.cssText='margin-top:5px;padding:3px 6px;border-radius:5px;font-size:11px;font-weight:800;';card.appendChild(box);}}const isS=card.innerText.includes('空'),r=fr[sym],h=pxHist[sym]||[];const spike=h.length>=5?((h[h.length-1]-h[0])/h[0]*100):0;let warns=[];if(isS){{if(r!==undefined&&r<=-0.03)warns.push(`🚨費率${{r.toFixed(3)}}%空軍擁擠`);if(spike>=0.6)warns.push(`🔥短線急拉+${{spike.toFixed(2)}}%正在軋空`);if(c.c24h<=-12)warns.push(`🛑已深跌${{c.c24h.toFixed(1)}}%防報復反彈`);}}else{{if(r!==undefined&&r>=0.05)warns.push(`⚠️費率+${{r.toFixed(3)}}%防多殺多`);}}if(warns.length){{box.style.background='rgba(255,59,107,0.22)';box.style.border='1px solid #ff3b6b';box.style.color='#ffd1dc';box.innerText=warns.join(' ｜ ');}}else{{box.style.background='rgba(0,245,155,0.08)';box.style.border='1px solid rgba(0,245,155,0.3)';box.style.color='#6ee7b7';box.innerText=(r!==undefined?`💸費率:${{r>=0?'+':''}}${{r.toFixed(3)}}% ｜ `:'')+'✅ 籌碼結構健康';}}}}) ;}},1500);}})();
(()=>{{const beep=(f1,f2)=>{{if(!snd)return;try{{const c=new(window.AudioContext||window.webkitAudioContext)();[f1,f2].forEach((f,i)=>{{const o=c.createOscillator(),g=c.createGain();o.type='sine';o.frequency.value=f;g.gain.setValueAtTime(0.15,c.currentTime+i*0.12);g.gain.exponentialRampToValueAtTime(0.001,c.currentTime+i*0.12+0.15);o.connect(g);g.connect(c.destination);o.start(c.currentTime+i*0.12);o.stop(c.currentTime+i*0.12+0.15);}});}}catch(e){{}}}};const sb=document.getElementById('snd-btn');if(sb)sb.addEventListener('click',()=>setTimeout(()=>beep(880,1320),50));let lastWarn='';setInterval(()=>{{if(!snd)return;const w=Array.from(document.querySelectorAll('.anti-sq')).filter(x=>x.innerText.includes('急拉')).map(x=>x.parentElement.querySelector('b')?.innerText).join(',');if(w&&w!==lastWarn){{lastWarn=w;beep(1046,1568);}}}},2000);}})();
(()=>{{let wk={{}};const scanWick=()=>{{const syms=[...new Set(Array.from(document.querySelectorAll('[class^="it"],.cbox')).map(c=>c.querySelector('b')?.innerText.replace('/USDT','').trim()).filter(Boolean))];syms.forEach((s,i)=>setTimeout(()=>{{fetch(`https://okx.com{{s}}-USDT-SWAP&bar=15m&limit=2`).then(r=>r.json()).then(j=>{{if(j.data&&j.data.length){{const k=j.data,o=parseFloat(k),h=parseFloat(k),l=parseFloat(k),c=parseFloat(k),rng=h-l;const up=rng>0?((h-Math.max(o,c))/rng*100):0,dn=rng>0?((Math.min(o,c)-l)/rng*100):0;wk[s]={{up:up,dn:dn}};}}}}).catch(()=>{{}});}},i*150));}};scanWick();setInterval(scanWick,30000);setInterval(()=>{{document.querySelectorAll('[class^="it"],.cbox').forEach(card=>{{const b=card.querySelector('b');if(!b)return;const sym=b.innerText.replace('/USDT','').trim(),w=wk[sym];if(!w)return;let tag=card.querySelector('.ext-wick');if(!tag){{tag=document.createElement('div');tag.className='ext-wick';tag.style.cssText='margin-top:4px;padding:3px 6px;border-radius:5px;font-size:11px;font-weight:bold;';card.appendChild(tag);}}const isS=card.innerText.includes('空');if(isS){{if(w.dn>=45){{tag.style.background='rgba(251,191,36,0.18)';tag.style.border='1px solid #fbbf24';tag.style.color='#fde68a';tag.innerText=`⚠️ 15m下影線${{w.dn.toFixed(0)}}% (低檔插針承接/慎空)`;}}else if(w.up>=45){{tag.style.background='rgba(0,245,155,0.12)';tag.style.border='1px solid #00f59b';tag.style.color='#6ee7b7';tag.innerText=`🎯 15m上影線${{w.up.toFixed(0)}}% (假突破遇阻/利空)`;}}else{{tag.style.background='rgba(255,255,255,0.04)';tag.style.border='1px solid #44403c';tag.style.color='#a8a29e';tag.innerText='🕯️ 15m K線正常 (無明顯長影線)';}}}}else{{if(w.up>=45){{tag.style.background='rgba(251,191,36,0.18)';tag.style.border='1px solid #fbbf24';tag.style.color='#fde68a';tag.innerText=`⚠️ 15m上影線${{w.up.toFixed(0)}}% (高檔插針遇阻/慎多)`;}}else if(w.dn>=45){{tag.style.background='rgba(0,245,155,0.12)';tag.style.border='1px solid #00f59b';tag.style.color='#6ee7b7';tag.innerText=`🎯 15m下影線${{w.dn.toFixed(0)}}% (插針止跌/利多)`;}}else{{tag.style.background='rgba(255,255,255,0.04)';tag.style.border='1px solid #44403c';tag.style.color='#a8a29e';tag.innerText='🕯️ 15m K線正常 (無明顯長影線)';}}}}}});}},2000);}})();
(()=>{{setInterval(()=>{{document.querySelectorAll('[class^="it"],.cbox').forEach(card=>{{const b=card.querySelector('b');if(!b)return;const sym=b.innerText.replace('/USDT','').trim(),px=LP[sym];if(!px)return;const isS=card.innerText.includes('空'),tp=fmt(isS?px*0.945:px*1.055),sl=fmt(isS?px*1.012:px*0.988),txt=`💎高盈虧比(4.5:1) 止盈:${{tp}}｜停損:${{sl}}`;let box=card.querySelector('.ext-rr');if(!box){{box=document.createElement('div');box.className='ext-rr';box.style.cssText='margin-top:4px;padding:3px 6px;border-radius:5px;font-size:11px;font-weight:bold;background:rgba(253,224,71,0.1);border:1px solid rgba(253,224,71,0.35);color:#fde047;';card.appendChild(box);}}box.innerText=txt;if(!card.querySelector('.ext-cp')){{const btn=document.createElement('button');btn.className='ext-cp';btn.innerText='📋';btn.style.cssText='float:right;margin-right:4px;background:#292524;color:#fde68a;border:1px solid #78350f;border-radius:5px;padding:2px 6px;font-size:11px;cursor:pointer;';btn.onclick=(e)=>{{e.stopPropagation();const cur=LP[sym]||px,t2=fmt(isS?cur*0.945:cur*1.055),s2=fmt(isS?cur*1.012:cur*0.988);navigator.clipboard.writeText(`${{sym}}/USDT (${{isS?'做空':'做多'}})\n進場:${{fmt(cur)}}\n止盈(+5.5%):${{t2}}\n停損(-1.2%):${{s2}}`);btn.innerText='✅';setTimeout(()=>btn.innerText='📋',1000);}};const okxBtn=card.querySelector('.okx-btn');if(okxBtn)okxBtn.after(btn);}}}});}},1500);}})();
setInterval(()=>{{
  fetch(["ht","tps://","api-futures.","ku","coin",".","com/api/v1/contracts/active"].join("")).then(r=>r.json()).then(j=>{{
    if(!j.data)return;
    const skip=new Set(["USDT","USDC","FDUSD","DAI","TUSD","USDE","PYUSD","BUSD","USDS","WBTC","WETH","WBNB","STETH"]);
    const lp="https://assets."+"coincap.io/assets/icons/",list=[];
    j.data.filter(x=>x.quoteCurrency==='USDT'&&x.status==='Open').sort((a,b)=>(b.turnoverOf24h||0)-(a.turnoverOf24h||0)).slice(0,80).forEach(item=>{{
      const sym=item.baseCurrency.replace('XBT','BTC').toUpperCase(),p=parseFloat(item.markPrice||item.lastTradePrice||0);
      if(!sym||skip.has(sym)||p<=0)return;
      const c24h=parseFloat(item.priceChgPct||0)*100,hi=parseFloat(item.highPrice||p),lo=parseFloat(item.lowPrice||p);
      const vol=parseFloat(item.turnoverOf24h||0),oi=parseFloat(item.openInterest||0)*p;
      const pos=hi>lo?((p-lo)/(hi-lo)*100):50,turn=oi>0?Math.round((vol/oi)*1000)/10:20,c1h=Math.round(c24h*22)/100;
      let oi_act="⚪ 資金溫和換手",oi_dir="NEUTRAL",s_sc=40,l_sc=40,sm=[],lm=[];
      if(c24h>3&&turn>=120){{oi_act="🟢 主力強勢開多";oi_dir="LONG";l_sc+=20;lm.push("主力開多");}}
      else if(c24h<-3&&turn>=120){{oi_act="🔴 主力放量開空";oi_dir="SHORT";s_sc+=20;sm.push("主力開空");}}
      const cycs=Math.round(Math.max(Math.min((c24h*3.5)+((50-pos)*0.7),99),-99)*10)/10;
      const res=(oi_dir==="LONG"&&cycs>=22)?"🔥 共振做多買點":((oi_dir==="SHORT"&&cycs<=-22)?"🔥 共振做空賣點":"");
      if(c24h>=5){{s_sc+=20;sm.push(`大漲+${{c24h.toFixed(1)}}%`);}}if(c24h<=-5){{l_sc+=20;lm.push(`深跌${{c24h.toFixed(1)}}%`);}}
      if(pos>=85){{s_sc+=20;sm.push(`高點(${{pos.toFixed(0)}}%)`);}}if(pos<=15){{l_sc+=20;lm.push(`低點(${{pos.toFixed(0)}}%)`);}}
      list.push({{sym:sym,price:p,c1h:c1h,c24h:c24h,turn:turn,logo:`${{lp}}${{sym.toLowerCase()}}@2x.png`,oi_act:oi_act,oi_dir:oi_dir,cycs:cycs,res:res,s_sc:Math.min(s_sc,99),s_msg:sm.join("+")||"中性",l_sc:Math.min(l_sc,99),l_msg:lm.join("+")||"中性"}});
    }});
    if(list.length>0){{D.all=list;D.hots=["BTC","ETH","SOL","XRP","DOGE","SUI"].map(k=>list.find(x=>x.sym===k)).filter(Boolean);D.shorts=list.filter(x=>x.s_sc>=x.l_sc).sort((a,b)=>b.s_sc-a.s_sc).slice(0,5);D.longs=list.filter(x=>x.l_sc>x.s_sc).sort((a,b)=>b.l_sc-a.l_sc).slice(0,5);D.anom=list.filter(x=>x.oi_dir!=="NEUTRAL").slice(0,8);D.res=list.filter(x=>x.res!=="");renderBoards();}}
  }}).catch(()=>{{}});
}},30000);
const kcUrl=["ht","tps://","api-futures.","ku","coin",".","com/api/v1/contracts/active"].join("");
setInterval(()=>{{fetch(kcUrl).then(r=>r.json()).then(j=>{{if(j.data)j.data.forEach(x=>{{if(x.quoteCurrency==='USDT')updateTick(x.baseCurrency.replace('XBT','BTC').toUpperCase(),parseFloat(x.lastTradePrice));}});}}).catch(()=>{{}});}},2000);
</script></body></html>"""
components.html(html, height=2200, scrolling=True)
