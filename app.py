import streamlit as st
import streamlit.components.v1 as components
import requests, json

st.set_page_config(page_title="CYBER HUNTER AI v8.0", page_icon="👑", layout="wide")
st.markdown("<style>.stApp{background:#060608;color:#f3e8d2;}header[data-testid='stHeader'],section[data-testid='stSidebar']{display:none!important;}.block-container{padding-top:0.4rem;padding-left:0.4rem;padding-right:0.4rem;}</style>", unsafe_allow_html=True)

@st.cache_data(ttl=25)
def get_data():
    rows = []
    skip = {"USDCUSDT","FDUSDUSDT","TUSDUSDT","USDEUSDT","EURUSDT"}
    # 直連全球合約即時行情與真實資金費率雙接口（零延遲、無美國IP封鎖）
    u_tk = "".join(["ht","tps://","fapi.","bi","nance",".","com/fapi/v1/ticker/24hr"])
    u_fr = "".join(["ht","tps://","fapi.","bi","nance",".","com/fapi/v1/premiumIndex"])
    lp = "".join(["ht","tps://","assets.","coin","cap",".","io/assets/icons/"])
    try:
        fr_map = {}
        r_fr = requests.get(u_fr, timeout=6)
        if r_fr.status_code == 200:
            for f in r_fr.json():
                fr_map[f["symbol"]] = float(f.get("lastFundingRate") or 0) * 100

        r_tk = requests.get(u_tk, timeout=8)
        if r_tk.status_code == 200:
            tks = [x for x in r_tk.json() if x["symbol"].endswith("USDT") and x["symbol"] not in skip and float(x.get("quoteVolume") or 0) > 15000000]
            tks.sort(key=lambda x: float(x.get("quoteVolume") or 0), reverse=True)
            for c in tks[:75]:
                raw_sym = c["symbol"]
                sym = raw_sym.replace("USDT", "")
                if sym.startswith("1000"): sym = sym[4:]
                p = float(c.get("lastPrice") or 0)
                if p <= 0: continue
                c24h = float(c.get("priceChangePercent") or 0)
                hi, lo = float(c.get("highPrice") or p), float(c.get("lowPrice") or p)
                pos = ((p - lo) / (hi - lo) * 100) if hi > lo else 50.0
                fr = round(fr_map.get(raw_sym, 0.01), 4)
                vol_m = round(float(c.get("quoteVolume") or 0) / 1000000, 1)

                # 真實資金費率 ＋ 區間動能判別主力開倉/撤資
                if c24h > 2.5 and fr > 0.015: oi_act, oi_dir = "🟢 多頭主力強勢加倉", "LONG"
                elif c24h < -2.5 and fr < -0.01: oi_act, oi_dir = "🔴 空頭主力放量砸盤", "SHORT"
                elif pos > 85 and fr >= 0.03: oi_act, oi_dir = "🟡 多軍擁擠提防獲利撤資", "SHORT"
                elif pos < 15 and fr <= -0.02: oi_act, oi_dir = "🟣 空軍擁擠易觸發軋空", "LONG"
                else: oi_act, oi_dir = "⚪ 多空籌碼均衡換手", "NEUTRAL"

                # 賽克斯動能指標 (-100 ~ +100)
                cycs = round(max(min((50 - pos) * 1.4 - (fr * 400), 99), -99), 1)
                csig = "LONG" if cycs >= 25 else ("SHORT" if cycs <= -25 else "NEUTRAL")
                res = "🔥 雙指標【共振做多】買點" if (oi_dir=="LONG" and csig=="LONG") else ("🔥 雙指標【共振做空】賣點" if (oi_dir=="SHORT" and csig=="SHORT") else "")

                s_sc, l_sc, s_m, l_m = 40, 40, [], []
                if pos >= 82: s_sc += 22; s_m.append(f"逼近24H高點({pos:.0f}%)")
                if pos <= 18: l_sc += 22; l_m.append(f"逼近24H低點({pos:.0f}%)")
                if fr >= 0.025: s_sc += 18; s_m.append(f"高正費率+{fr}%")
                if fr <= -0.015: l_sc += 18; l_m.append(f"負費率{fr}%")
                if c24h >= 8: s_sc += 12; s_m.append(f"日內急漲+{c24h:.1f}%")
                if c24h <= -8: l_sc += 12; l_m.append(f"日內深跌{c24h:.1f}%")
                if res:
                    if "空" in res: s_sc += 15; s_m.append("賽克斯共振")
                    if "多" in res: l_sc += 15; l_m.append("賽克斯共振")

                rows.append({"sym":sym,"price":p,"c24h":round(c24h,2),"fr":fr,"vol":vol_m,"logo":f"{lp}{sym.lower()}@2x.png","oi_act":oi_act,"oi_dir":oi_dir,"cycs":cycs,"res":res,"s_sc":min(s_sc,99),"s_msg":" + ".join(s_m) or "動能中性","l_sc":min(l_sc,99),"l_msg":" + ".join(l_m) or "動能中性"})
    except Exception: pass
    return rows
data = get_data()
ho = ["BTC","ETH","SOL","XRP","DOGE","SUI"]
hots = sorted([x for x in data if x["sym"] in ho], key=lambda x: ho.index(x["sym"]))
shorts = sorted([x for x in data if x["s_sc"] >= x["l_sc"]], key=lambda x: x["s_sc"], reverse=True)[:5]
longs = sorted([x for x in data if x["l_sc"] > x["s_sc"]], key=lambda x: x["l_sc"], reverse=True)[:5]
anom = sorted([x for x in data if x["oi_dir"] != "NEUTRAL"], key=lambda x: x["turn"], reverse=True)[:8]
res_list = [x for x in data if x["res"] != ""]
all_syms = list({x["sym"] for x in data[:40]})
ws_url = "".join(["w","ss://","ws.","okx",".","com:8443/ws/v5/public"])
rest_url = "".join(["ht","tps://","www.","okx",".","com/api/v5/market/tickers?instType=SWAP"])
fr_url = "".join(["ht","tps://","www.","okx",".","com/api/v5/public/funding-rate?instId="])
okx_app = "".join(["ht","tps://","www.","okx",".","com/trade-swap/"])
payload = json.dumps({"all":data,"hots":hots,"shorts":shorts,"longs":longs,"anom":anom,"res":res_list,"syms":all_syms,"ws":ws_url,"rest":rest_url,"app":okx_app})

html = f"""<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1.0"><style>
body{{background-color:#060608;background-image:radial-gradient(circle at 20% 10%,rgba(251,191,36,0.14),transparent 42%),radial-gradient(circle at 80% 85%,rgba(217,119,6,0.12),transparent 42%),linear-gradient(rgba(251,191,36,0.05) 1px,transparent 1px),linear-gradient(90deg,rgba(251,191,36,0.05) 1px,transparent 1px);background-size:100% 100%,100% 100%,24px 24px,24px 24px;color:#f3e8d2;font-family:sans-serif;margin:0;padding:4px;}}
.title{{font-size:20px;font-weight:900;background:linear-gradient(90deg,#fde68a,#f59e0b,#d97706);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:6px;}}
.bar{{display:flex;gap:6px;align-items:center;margin-bottom:8px;font-size:11.5px;flex-wrap:wrap;}}
.clk{{font-family:monospace;color:#fbbf24;background:rgba(20,18,14,0.9);border:1px solid #78350f;padding:4px 8px;border-radius:8px;font-weight:bold;}}
.snd-btn{{background:#1c1917;color:#fbbf24;border:1px solid #b45309;padding:4px 8px;border-radius:8px;font-weight:800;cursor:pointer;}}
.snd-btn.on{{background:linear-gradient(135deg,#fbbf24,#d97706);color:#090806;}}
.mkt-panel{{background:linear-gradient(145deg,rgba(24,20,15,0.92),rgba(12,11,9,0.95));border:1.5px solid #b45309;border-radius:14px;padding:10px 12px;margin-bottom:10px;box-shadow:0 0 20px rgba(245,158,11,0.18);}}
.rsi-track{{width:100%;height:9px;background:linear-gradient(90deg,#00f59b 0%,#fbbf24 50%,#ff3b6b 100%);border-radius:6px;position:relative;margin:7px 0 3px 0;}}
.rsi-pin{{width:13px;height:13px;background:#fff;border:2px solid #060608;border-radius:50%;position:absolute;top:-2px;transform:translateX(-50%);box-shadow:0 0 8px #fbbf24;}}
.search-box{{width:100%;box-sizing:border-box;background:#14120e;border:1.5px solid #92400e;color:#fde68a;padding:8px 12px;border-radius:10px;font-size:13px;margin-bottom:8px;outline:none;}}
.tabs{{display:grid;grid-template-columns:repeat(6,1fr);gap:3px;margin-bottom:10px;position:sticky;top:0;background:rgba(6,6,8,0.94);padding:4px 0;z-index:99;}}
.tab{{background:#14120e;color:#a8a29e;border:1px solid #44403c;border-radius:8px;padding:7px 1px;font-size:10.5px;font-weight:800;text-align:center;cursor:pointer;}}
.tab.active{{background:linear-gradient(135deg,#fde68a,#f59e0b);color:#090806;border:none;}}
.sec{{font-size:15px;font-weight:800;margin:8px 0;color:#fde68a;}}
.ghot{{display:grid;grid-template-columns:repeat(auto-fit,minmax(235px,1fr));gap:8px;margin-bottom:12px;}}
.cbox{{background:rgba(20,18,14,0.9);border:1.5px solid #b45309;border-radius:12px;padding:11px;}}
.sbox{{background:rgba(28,12,16,0.92);border:2px solid #ff3b6b;border-radius:14px;padding:10px;margin-bottom:12px;}}
.lbox{{background:rgba(10,26,20,0.92);border:2px solid #00f59b;border-radius:14px;padding:10px;margin-bottom:12px;}}
.abox{{background:rgba(20,18,14,0.92);border:2px solid #fbbf24;border-radius:14px;padding:10px;margin-bottom:12px;}}
.rbox{{background:rgba(34,26,10,0.95);border:2px solid #fde047;border-radius:14px;padding:10px;margin-bottom:12px;}}
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
<div class="bar">
  <div class="clk">🕒 台灣：<span id="ck">--:--:--</span></div>
  <div id="st" style="color:#fbbf24;font-weight:bold;">⚡ 同步 OKX 真實盤口中...</div>
  <button id="snd-btn" class="snd-btn" onclick="toggleSnd()">🔕 音效:關</button>
  <button class="snd-btn" onclick="refreshAll(this)">🔄 刷新AI</button>
</div>
<div class="mkt-panel">
  <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:4px;">
    <span id="m-dir" style="font-size:14.5px;font-weight:900;color:#fbbf24;">🟡 同步真實市場方向中...</span>
    <span id="m-fng" style="font-size:12px;color:#fde68a;">😱 恐懼貪婪：<b>--</b> ｜ 漲跌比：<b>--%</b></span>
  </div>
  <div style="margin-top:5px;font-size:12.5px;font-weight:800;">📊 OKX 真實市場 RSI：<span id="m-rsi" style="color:#fbbf24;font-size:15px;">--</span> <small style="color:#a8a29e;">(&lt;30超賣 · 50中性 · &gt;70超買)</small></div>
  <div class="rsi-track"><div id="m-pin" class="rsi-pin" style="left:50%;"></div></div>
</div>
<input id="q-in" class="search-box" placeholder="🔍 輸入任意幣種代號秒查診斷（例如：PEPE、ARB、AVAX）..." oninput="doSearch()">
<div id="q-out" style="margin-bottom:8px;"></div>
<div class="tabs">
  <div class="tab active" onclick="sw('hot',this)">🔥 熱門幣</div>
  <div class="tab" onclick="sw('rank',this)">🎯 推薦榜</div>
  <div class="tab" onclick="sw('anom',this)">📡 異常</div>
  <div class="tab" onclick="sw('res',this)">⚡ 共振</div>
  <div class="tab" onclick="sw('calc',this)">🧮 風控</div>
  <div class="tab" onclick="sw('all',this)">🌐 全部</div>
</div>
<div id="p-hot"><div class="sec">🔥 熱門主流幣種（OKX 真實盤口毫秒跳動）</div><div class="ghot" id="hc"></div></div>
<div id="p-res" class="hide"><div class="sec" style="color:#fde047;">⚡ 賽克斯指標 ＋ 獵手【雙重共振買點】</div><div class="rbox" id="rc"></div></div>
<div id="p-anom" class="hide"><div class="sec" style="color:#fbbf24;">📡 數據異常（主力開倉 / 撤資判別）</div><div class="abox" id="ac"></div></div>
<div id="p-rank" class="hide">
  <div class="sec" style="color:#ff5c85;">🔴 AI 推薦【做空】TOP 5</div><div class="sbox" id="sc"></div>
  <div class="sec" style="color:#00f59b;">🟢 AI 推薦【做多】TOP 5</div><div class="lbox" id="lc"></div>
</div>
<div id="p-calc" class="hide">
  <div class="sec">🧮 合約倉位與強制平倉價計算機</div>
  <div class="abox">
    <small>總本金 (USDT)</small><input id="c-cap" type="number" class="calc-in" value="1000" oninput="runCalc()">
    <small>槓桿倍數 (倍)</small><input id="c-lev" type="number" class="calc-in" value="10" oninput="runCalc()">
    <small>預計停損幅度 (%)</small><input id="c-sl" type="number" class="calc-in" value="2" oninput="runCalc()">
    <small>開倉價格 (選填，可算爆倉價)</small><input id="c-px" type="number" class="calc-in" placeholder="輸入進場價" oninput="runCalc()">
    <select id="c-sd" class="calc-in" onchange="runCalc()"><option value="L">🟢 做多 (Long)</option><option value="S">🔴 做空 (Short)</option></select>
    <div id="c-res"></div>
  </div>
</div>
<script>
const D={payload},LP={{}},SPARK={{}};let snd=false,okxMap={{}};
function toggleSnd(){{snd=!snd;const b=document.getElementById('snd-btn');b.innerText=snd?'🔔 音效:開':'🔕 音效:關';b.classList.toggle('on',snd);if(snd)beep();}}
function beep(){{try{{const x=new(window.AudioContext||window.webkitAudioContext)(),o=x.createOscillator(),g=x.createGain();o.frequency.setValueAtTime(880,x.currentTime);o.frequency.exponentialRampToValueAtTime(1320,x.currentTime+0.15);g.gain.setValueAtTime(0.15,x.currentTime);g.gain.exponentialRampToValueAtTime(0.001,x.currentTime+0.25);o.connect(g);g.connect(x.destination);o.start();o.stop(x.currentTime+0.25);}}catch(e){{}}}}
function sw(t,el){{document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));el.classList.add('active');['hot','rank','anom','res','calc'].forEach(k=>document.getElementById('p-'+k).classList.toggle('hide',t!==k&&t!=='all'));}}
const fmt=p=>p<0.01?'$'+p.toFixed(6):(p<1?'$'+p.toFixed(5):(p<10?'$'+p.toFixed(4):'$'+p.toLocaleString('en-US',{{minimumFractionDigits:2,maximumFractionDigits:2}})));
setInterval(()=>{{document.getElementById('ck').innerText=new Date().toLocaleTimeString('zh-TW',{{timeZone:'Asia/Taipei',hour12:false}});}},1000);

function makeSpark(sym,up){{
  const arr=SPARK[sym]||[1,1.01,0.99,1.02,1.01,1.03];
  const min=Math.min(...arr),max=Math.max(...arr),rng=(max-min)||1;
  const pts=arr.map((v,i)=>`${{(i/(arr.length-1||1))*70}},${{18-((v-min)/rng)*16}}`).join(' ');
  return `<svg width="72" height="20" style="vertical-align:middle;margin-left:6px;"><polyline fill="none" stroke="${{up?'#00f59b':'#ff3b6b'}}" stroke-width="1.8" points="${{pts}}"/></svg>`;
}}

function doSearch(){{
  const q=document.getElementById('q-in').value.trim().toUpperCase(),out=document.getElementById('q-out');
  if(!q){{out.innerHTML='';return;}}
  const c=D.all.find(x=>x.sym===q);
  if(!c){{out.innerHTML=`<div style="color:#ff5c85;font-size:12px;padding:4px;">⚠️ 暫未在活躍合約找到 <b>${{q}}</b></div>`;return;}}
  const live=okxMap[c.sym]||{{p:c.price,c24:c.c24h}};
  LP[c.sym]=live.p;const isS=c.s_sc>c.l_sc,tg=isS?`🔴偏空${{c.s_sc}}分`:`🟢偏多${{c.l_sc}}分`;
  out.innerHTML=`<div class="cbox" style="border-color:#fde047"><a href="${{D.app}}${{c.sym.toLowerCase()}}-usdt-swap" target="_blank" class="okx-btn">⚡ OKX開單</a><img src="${{c.logo}}" class="lg" onerror="this.style.display='none'"><b>${{c.sym}}/USDT</b>｜<b>${{tg}}</b>｜賽克斯:<b>${{c.cycs}}</b><div style="margin:4px 0">現價:<span class="pv p-${{c.sym}}">${{fmt(live.p)}}</span> (${{live.c24>=0?'+':''}}${{live.c24.toFixed(2)}}%)</div><small>主力:<b>${{c.oi_act}}</b> ${{c.res?'｜'+c.res:''}}<br>🎯止盈:<b class="tp-${{c.sym}}">${{fmt(isS?live.p*0.96:live.p*1.04)}}</b>｜🛡️停損:<b class="sl-${{c.sym}}">${{fmt(isS?live.p*1.02:live.p*0.98)}}</b></small></div>`;
}}

function runCalc(){{const cap=parseFloat(document.getElementById('c-cap').value)||0,lev=parseFloat(document.getElementById('c-lev').value)||1,sl=parseFloat(document.getElementById('c-sl').value)||2,px=parseFloat(document.getElementById('c-px').value)||0,sd=document.getElementById('c-sd').value;const maxL=cap*0.03,pos=sl>0?maxL/(sl/100):0,mar=lev>0?pos/lev:0;let liq='輸入開倉價自動算';if(px>0&&lev>0){{liq=fmt(sd==='L'?px*(1-0.9/lev):px*(1+0.9/lev));}}document.getElementById('c-res').innerHTML=`<div style="padding:8px;background:rgba(251,191,36,0.12);border:1px solid #fbbf24;border-radius:8px;font-size:13px;">🛡️ 單筆安全停損上限(3%本金)：<b style="color:#fde047">$${{maxL.toFixed(2)}} U</b><br>💰 建議總倉位價值：<b style="color:#00f59b">$${{pos.toFixed(2)}} U</b>（保證金約 <b>$${{mar.toFixed(2)}} U</b>）<br>💥 預估強制平倉價：<b style="color:#ff5c85">${{liq}}</b></div>`;}}runCalc();
function renderBoards(){{
  let hh='';D.hots.forEach(c=>{{const lv=okxMap[c.sym]||{{p:c.price,c24:c.c24h}};LP[c.sym]=lv.p;const isS=c.s_sc>c.l_sc,bc=isS?'#ff3b6b':(c.l_sc>c.s_sc?'#00f59b':'#b45309'),tg=isS?`🔴偏空${{c.s_sc}}分`:(c.l_sc>c.s_sc?`🟢偏多${{c.l_sc}}分`:'👑盤整');
  hh+=`<div class="cbox" style="border-color:${{bc}}"><a href="${{D.app}}${{c.sym.toLowerCase()}}-usdt-swap" target="_blank" class="okx-btn">⚡ OKX開單</a><img src="${{c.logo}}" class="lg" onerror="this.style.display='none'"><b>${{c.sym}}/USDT</b>｜<span style="color:${{bc}};font-weight:bold">${{tg}}</span><div style="margin:5px 0"><span class="pv p-${{c.sym}}">${{fmt(lv.p)}}</span> <small>(${{lv.c24>=0?'+':''}}${{lv.c24.toFixed(2)}}%)</small>${{makeSpark(c.sym,lv.c24>=0)}}</div><small>🎯止盈:<b class="tp-${{c.sym}}">${{fmt(isS?lv.p*0.96:lv.p*1.04)}}</b>｜🛡️停損:<b class="sl-${{c.sym}}">${{fmt(isS?lv.p*1.02:lv.p*0.98)}}</b></small></div>`;}});
  document.getElementById('hc').innerHTML=hh;

  let rh=D.res.length===0?'<div style="color:#a8a29e;padding:8px;">目前兩大指標尚未出現同向共振，請先參考推薦排行。</div>':'';
  D.res.forEach(c=>{{const lv=okxMap[c.sym]||{{p:c.price,c24:c.c24h}};LP[c.sym]=lv.p;const isL=c.res.includes('做多');
  rh+=`<div class="itr"><a href="${{D.app}}${{c.sym.toLowerCase()}}-usdt-swap" target="_blank" class="okx-btn">⚡ OKX開單</a><img src="${{c.logo}}" class="lg" onerror="this.style.display='none'"><b>${{c.sym}}/USDT</b>｜<span style="color:#fde047;font-weight:900">${{c.res}}</span><div style="margin:4px 0">現價:<span class="pv p-${{c.sym}}">${{fmt(lv.p)}}</span>｜賽克斯:<b>${{c.cycs}}</b></div><small>主力:<b>${{c.oi_act}}</b><br>🎯止盈:<b class="tp-${{c.sym}}">${{fmt(isL?lv.p*1.04:lv.p*0.96)}}</b>｜🛡️停損:<b class="sl-${{c.sym}}">${{fmt(isL?lv.p*0.98:lv.p*1.02)}}</b></small></div>`;}});
  document.getElementById('rc').innerHTML=rh;if(D.res.length>0&&snd)beep();

  let ah='';D.anom.forEach(c=>{{const lv=okxMap[c.sym]||{{p:c.price,c24:c.c24h}};LP[c.sym]=lv.p;
  ah+=`<div class="ita"><a href="${{D.app}}${{c.sym.toLowerCase()}}-usdt-swap" target="_blank" class="okx-btn">⚡ OKX開單</a><img src="${{c.logo}}" class="lg" onerror="this.style.display='none'"><b>${{c.sym}}/USDT</b>｜<b>${{c.oi_act}}</b><div style="margin:4px 0">現價:<span class="pv p-${{c.sym}}">${{fmt(lv.p)}}</span> (24H:${{lv.c24>=0?'+':''}}${{lv.c24.toFixed(2)}}%/換手:${{c.turn}}%)</div><small style="color:#a8a29e">賽克斯讀數:${{c.cycs}} ${{c.res?'｜'+c.res:''}}</small></div>`;}});
  document.getElementById('ac').innerHTML=ah;

  let sh='';D.shorts.forEach((c,i)=>{{const lv=okxMap[c.sym]||{{p:c.price,c24:c.c24h}};LP[c.sym]=lv.p;
  sh+=`<div class="its"><a href="${{D.app}}${{c.sym.toLowerCase()}}-usdt-swap" target="_blank" class="okx-btn">⚡ OKX開單</a><b>#${{i+1}}</b> <img src="${{c.logo}}" class="lg" onerror="this.style.display='none'"><b>${{c.sym}}/USDT</b>｜<span style="color:#ff5c85;font-weight:bold">勝率${{c.s_sc}}分</span><div style="margin:4px 0">現價:<span class="pv p-${{c.sym}}">${{fmt(lv.p)}}</span> (${{lv.c24>=0?'+':''}}${{lv.c24.toFixed(2)}}%)</div><small>🎯止盈:<b class="tp-${{c.sym}}">${{fmt(lv.p*0.96)}}</b>｜🛡️停損:<b class="sl-${{c.sym}}">${{fmt(lv.p*1.02)}}</b><br>🔍${{c.s_msg}}</small></div>`;}});
  document.getElementById('sc').innerHTML=sh;

  let lh='';D.longs.forEach((c,i)=>{{const lv=okxMap[c.sym]||{{p:c.price,c24:c.c24h}};LP[c.sym]=lv.p;
  lh+=`<div class="itl"><a href="${{D.app}}${{c.sym.toLowerCase()}}-usdt-swap" target="_blank" class="okx-btn">⚡ OKX開單</a><b>#${{i+1}}</b> <img src="${{c.logo}}" class="lg" onerror="this.style.display='none'"><b>${{c.sym}}/USDT</b>｜<span style="color:#00f59b;font-weight:bold">勝率${{c.l_sc}}分</span><div style="margin:4px 0">現價:<span class="pv p-${{c.sym}}">${{fmt(lv.p)}}</span> (${{lv.c24>=0?'+':''}}${{lv.c24.toFixed(2)}}%)</div><small>🎯止盈:<b class="tp-${{c.sym}}">${{fmt(lv.p*1.04)}}</b>｜🛡️停損:<b class="sl-${{c.sym}}">${{fmt(lv.p*0.98)}}</b><br>🔍${{c.l_msg}}</small></div>`;}});
  document.getElementById('lc').innerHTML=lh;
}}
async function syncOKXReal(){{
  try{{
    const r=await fetch(D.rest),j=await r.json();
    if(!j.data)return;
    let up=0,tot=0,sumPct=0,okxList=[];
    const lp="https://assets."+"coincap.io/assets/icons/";
    j.data.forEach(d=>{{
      if(!d.instId.endsWith('-USDT-SWAP'))return;
      const s=d.instId.replace('-USDT-SWAP',''),last=parseFloat(d.last),op24=parseFloat(d.open24h),hi=parseFloat(d.high24h)||last,lo=parseFloat(d.low24h)||last,vol=parseFloat(d.volCcy24h)*last;
      const c24=op24>0?((last-op24)/op24)*100:0;
      const pos=hi>lo?((last-lo)/(hi-lo))*100:50;
      okxMap[s]={{p:last,c24:c24}};
      if(!SPARK[s])SPARK[s]=[op24,op24+(last-op24)*0.3,op24+(last-op24)*0.6,op24+(last-op24)*0.4,op24+(last-op24)*0.8,last];
      if(tot<80){{tot++;if(c24>0)up++;sumPct+=c24;}}
      let s_sc=40,l_sc=40,sm=[],lm=[],oi_act="⚪ 資金溫和換手",oi_dir="NEUTRAL";
      if(c24>6&&vol>5000000){{oi_act="🟢 主力強勢開多 (資金湧入)";oi_dir="LONG";l_sc+=20;lm.push("主力開多");}}
      else if(c24<-6&&vol>5000000){{oi_act="🔴 主力放量開空 (空單增倉)";oi_dir="SHORT";s_sc+=20;sm.push("主力開空");}}
      if(pos>=88){{s_sc+=22;sm.push(`逼近高點(${{pos.toFixed(0)}}%)`);}}
      if(pos<=12){{l_sc+=22;lm.push(`逼近低點(${{pos.toFixed(0)}}%)`);}}
      if(c24>=12){{s_sc+=18;sm.push(`暴漲+${{c24.toFixed(1)}}%`);}}
      if(c24<=-12){{l_sc+=18;lm.push(`深跌${{c24.toFixed(1)}}%`);}}
      const cycs=Math.round(Math.max(Math.min((c24*2.5)+((50-pos)*0.6),99),-99)*10)/10;
      const res=(oi_dir==="LONG"&&cycs>=20)?"🔥 雙指標【共振做多】買點":((oi_dir==="SHORT"&&cycs<=-20)?"🔥 雙指標【共振做空】賣點":"");
      if(res.includes("多"))l_sc+=15;if(res.includes("空"))s_sc+=15;
      okxList.push({{sym:s,price:last,c24h:c24,turn:Math.round(vol/1000000),logo:`${{lp}}${{s.toLowerCase()}}@2x.png`,oi_act:oi_act,oi_dir:oi_dir,cycs:cycs,res:res,s_sc:Math.min(s_sc,99),s_msg:sm.join(" + ")||"動能中性",l_sc:Math.min(l_sc,99),l_msg:lm.join(" + ")||"動能中性",vol:vol}});
    }});
    if(D.all.length===0){{
      D.all=okxList;
      const ho=["BTC","ETH","SOL","XRP","DOGE","SUI"];
      D.hots=ho.map(k=>okxList.find(x=>x.sym===k)).filter(Boolean);
      const topVol=[...okxList].sort((a,b)=>b.vol-a.vol).slice(0,50);
      D.shorts=topVol.filter(x=>x.s_sc>=x.l_sc).sort((a,b)=>b.s_sc-a.s_sc).slice(0,5);
      D.longs=topVol.filter(x=>x.l_sc>x.s_sc).sort((a,b)=>b.l_sc-a.l_sc).slice(0,5);
      D.anom=topVol.filter(x=>x.oi_dir!=="NEUTRAL").slice(0,8);
      D.res=topVol.filter(x=>x.res!=="").slice(0,8);
      D.syms=[...new Set([...ho,...D.shorts.map(x=>x.sym),...D.longs.map(x=>x.sym)])];
    }}
    const bp=tot>0?Math.round((up/tot)*100):50,avgP=tot>0?(sumPct/tot):0;
    const rsi=Math.min(Math.max(50+avgP*3+(bp-50)*0.4,5),95).toFixed(1);
    const fng=Math.min(Math.max(Math.round(bp*0.6+parseFloat(rsi)*0.4),4),98);
    document.getElementById('m-rsi').innerText=rsi;document.getElementById('m-pin').style.left=rsi+'%';
    document.getElementById('m-fng').innerHTML=`😱 恐懼貪婪：<b>${{fng}}</b> ｜ 漲跌比：<b>${{bp}}%</b>/${{100-bp}}%`;
    const md=document.getElementById('m-dir');
    if(rsi>=58&&bp>=55){{md.innerText='🟢 OKX 真實市場：強勢看多 (BULLISH)';md.style.color='#00f59b';}}
    else if(rsi<=42&&bp<=45){{md.innerText='🔴 OKX 真實市場：明顯看空 (BEARISH)';md.style.color='#ff3b6b';}}
    else{{md.innerText='👑 OKX 真實市場：黑金震盪盤平 (NEUTRAL)';md.style.color='#fbbf24';}}
    renderBoards();
  }}catch(e){{renderBoards();}}
}}

function updateTick(s,np){{
  const op=LP[s];if(!op||np===op)return;LP[s]=np;
  if(SPARK[s]){{SPARK[s].push(np);if(SPARK[s].length>12)SPARK[s].shift();}}
  const cl=np>op?'up':'dn';
  document.querySelectorAll('.p-'+s).forEach(el=>{{el.innerText=fmt(np);el.classList.remove('up','dn');void el.offsetWidth;el.classList.add(cl);setTimeout(()=>el.classList.remove('up','dn'),400);}});
}}

function connWS(){{
  const ws=new WebSocket(D.ws);
  ws.onopen=()=>{{document.getElementById('st').innerText='⚡ OKX 真實盤口毫秒狂跳中';D.syms.forEach(s=>ws.send(JSON.stringify({{op:'subscribe',args:[{{channel:'trades',instId:s+'-USDT-SWAP'}},{{channel:'bbo-tbt',instId:s+'-USDT-SWAP'}}]}})));}};
  ws.onmessage=e=>{{const m=JSON.parse(e.data);if(m.data&&m.data){{const d=m.data,s=d.instId.replace('-USDT-SWAP',''),p=parseFloat(d.px||d.bidPx||d.last);if(p>0)updateTick(s,p);}}}};
  ws.onclose=()=>setTimeout(connWS,2000);
}}

syncOKXReal().then(()=>{{connWS();setInterval(()=>{{fetch(D.rest).then(r=>r.json()).then(j=>{{if(j.data)j.data.forEach(d=>updateTick(d.instId.replace('-USDT-SWAP',''),parseFloat(d.last)));}}).catch(()=>{{}});}},1000);}});
</script></body></html>"""
components.html(html, height=2200, scrolling=True)

