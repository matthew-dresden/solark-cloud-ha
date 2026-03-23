if(typeof window.ApexCharts==="undefined"){
  const s=document.createElement("script");s.src="/local/community/apexcharts.min.js";document.head.appendChild(s);
}
const SC={PV:"#00E676",Battery:"#651FFF",SOC:"#00E5FF",Grid:"#FFD600",Load:"#FF1744",
  Export:"#4FC3F7",Import:"#FF8A65",Charge:"#CE93D8",Discharge:"#A5D6A7"};
const CH=560;

class SolarkEnergyCard extends HTMLElement{
  constructor(){super();this._hass=null;this._period="day";this._date=new Date();this._chart=null;this._started=false;}
  setConfig(c){this._config=c||{};}
  set hass(h){
    this._hass=h;
    if(!this._started){this._started=true;this._build();}
  }

  _dp(){
    const d=this._date,y=d.getFullYear(),m=String(d.getMonth()+1).padStart(2,"0"),dy=String(d.getDate()).padStart(2,"0");
    if(this._period==="total")return"all";if(this._period==="year")return`${y}`;if(this._period==="month")return`${y}-${m}`;return`${y}-${m}-${dy}`;
  }
  _dd(){
    const d=this._date;
    if(this._period==="day")return d.toLocaleDateString("en-US",{year:"numeric",month:"short",day:"numeric"});
    if(this._period==="month")return d.toLocaleDateString("en-US",{year:"numeric",month:"long"});
    if(this._period==="year")return""+d.getFullYear();return"All Time";
  }

  _build(){
    this.innerHTML=`<ha-card>
    <div style="padding:16px">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;flex-wrap:wrap;gap:8px">
        <div>
          <div style="font-size:15px;font-weight:600;color:#58a6ff">📈 Energy Generation</div>
          <div id="std" style="font-size:12px;color:#888">Day View — ${this._dd()}</div>
        </div>
        <div id="tabs" style="display:flex;gap:4px"></div>
        <div style="display:flex;align-items:center;gap:6px">
          <button class="xb" id="prev">‹</button>
          <span id="dd" class="xb" style="width:auto;padding:0 12px;min-width:100px;text-align:center;font-size:14px">${this._dd()}</span>
          <button class="xb" id="next">›</button>
          <button class="xb" id="cal">📅</button>
          <input type="date" id="di" style="position:absolute;opacity:0;width:0;height:0">
        </div>
      </div>
      <div id="chartarea" style="width:100%;height:${CH}px;min-height:${CH}px"></div>
      <div id="log" style="font-size:10px;color:#555;margin-top:4px"></div>
    </div>
    <style>
      .xb{background:transparent;border:1px solid #444;color:#aaa;width:30px;height:30px;border-radius:6px;cursor:pointer;font-size:16px;display:flex;align-items:center;justify-content:center}
      .xb:hover{background:#333;color:#fff}
      .xtb{padding:6px 14px;border-radius:6px;border:1px solid #444;background:transparent;color:#aaa;cursor:pointer;font-size:13px}
      .xtb:hover{background:#333;color:#fff}
      .xtb.on{background:#58a6ff;color:#fff;border-color:#58a6ff}
    </style>
    </ha-card>`;

    const tabs=this.querySelector("#tabs");
    for(const p of["day","month","year","total"]){
      const b=document.createElement("button");b.className="xtb"+(p==="day"?" on":"");
      b.dataset.p=p;b.textContent=p.charAt(0).toUpperCase()+p.slice(1);
      b.addEventListener("click",()=>this._tab(p));tabs.appendChild(b);
    }
    this.querySelector("#prev").addEventListener("click",()=>this._nav(-1));
    this.querySelector("#next").addEventListener("click",()=>this._nav(1));
    const cal=()=>{const i=this.querySelector("#di");if(i){const ds=this._dp();i.value=ds.length>=10?ds:ds+"-01";i.showPicker();}};
    this.querySelector("#cal").addEventListener("click",cal);
    this.querySelector("#dd").addEventListener("click",cal);
    this.querySelector("#di").addEventListener("change",e=>{if(e.target.value){this._date=new Date(e.target.value+"T12:00:00");this._ui();this._fetch();}});

    this._initApex();
  }

  async _initApex(){
    for(let i=0;i<100&&typeof window.ApexCharts==="undefined";i++)await new Promise(r=>setTimeout(r,100));
    await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
    this._fetch();
  }

  async _fetch(){
    const ct=this.querySelector("#chartarea"),log=this.querySelector("#log");
    if(!ct)return;
    // Show loading but keep container height
    ct.style.height=CH+"px";
    ct.style.minHeight=CH+"px";
    ct.innerHTML=`<div style="color:#555;text-align:center;padding:${CH/2-20}px 0">Loading...</div>`;
    try{
      let tk="";try{tk=this._hass.auth.data.access_token}catch(_){}
      if(!tk)try{tk=JSON.parse(localStorage.getItem("hassTokens")).access_token}catch(_){}
      if(!tk){if(log)log.textContent="No token";return;}
      const r=await fetch("/api/services/solark_cloud/fetch_energy?return_response",{
        method:"POST",headers:{"Authorization":"Bearer "+tk,"Content-Type":"application/json"},
        body:JSON.stringify({period:this._period,date:this._dp()})});
      if(!r.ok){if(log)log.textContent=`HTTP ${r.status}`;return;}
      const raw=await r.json(),data=raw.service_response||raw;
      if(!data.series||Object.keys(data.series).length===0){
        ct.innerHTML=`<div style="color:#555;text-align:center;padding:${CH/2-20}px 0">No data</div>`;return;}
      await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
      this._renderChart(ct,data,log);
    }catch(e){if(log)log.textContent="Error: "+e.message;}
  }

  _renderChart(ct,data,log){
    if(this._chart){try{this._chart.destroy()}catch(_){}this._chart=null;}
    ct.style.height=CH+"px";
    ct.style.minHeight=CH+"px";
    ct.innerHTML="";

    const isDay=this._period==="day";
    const isBar=!isDay;
    const unit=isDay?"W":"kWh";
    const series=data.series;

    const catSet=new Set();
    for(const recs of Object.values(series))if(recs)for(const r of recs)catSet.add(r.time);
    const categories=[...catSet].sort();

    const chartSeries=[],chartColors=[],strokeWidths=[];
    for(const[label,recs] of Object.entries(series)){
      if(!recs||recs.length===0)continue;
      const vm=new Map(recs.map(r=>[r.time,r.value]));
      const s={name:label,data:categories.map(c=>vm.get(c)??0)};
      if(isDay) s.type=label==="SOC"?"line":"area";
      chartSeries.push(s);
      chartColors.push(SC[label]||"#888");
      strokeWidths.push(label==="SOC"?2.5:1.5);
    }
    if(chartSeries.length===0)return;

    const opts={
      chart:{type:isBar?"bar":"line",height:CH,background:"transparent",foreColor:"#ccc",toolbar:{show:true},zoom:{enabled:true}},
      series:chartSeries,
      colors:chartColors,
      xaxis:{categories,labels:{style:{colors:"#888",fontSize:"10px"},rotate:-45,hideOverlappingLabels:true},tickAmount:isDay?24:undefined},
      yaxis:{title:{text:unit,style:{color:"#ccc"}},labels:{style:{colors:"#ccc"},formatter:function(v){return v!=null?Math.round(v).toLocaleString():""}},decimalsInFloat:0},
      tooltip:{shared:true,intersect:false,theme:"dark",y:{formatter:function(v){return v!=null?Math.round(v).toLocaleString()+" "+unit:""}}},
      legend:{show:true,position:"bottom",labels:{colors:"#ccc"},fontSize:"12px"},
      grid:{borderColor:"#333",strokeDashArray:3},
      theme:{mode:"dark"},
      dataLabels:{enabled:false},
    };

    if(isBar){
      opts.plotOptions={bar:{columnWidth:"60%",borderRadius:3}};
      opts.stroke={width:0};
      opts.fill={opacity:0.85};
    }else{
      opts.stroke={curve:"smooth",width:strokeWidths};
      opts.fill={type:"gradient",gradient:{shadeIntensity:1,opacityFrom:0.6,opacityTo:0.1,stops:[0,90,100]}};
    }

    this._chart=new ApexCharts(ct,opts);
    this._chart.render();
    if(log)log.textContent=chartSeries.length+" series, "+categories.length+" pts";
  }

  _nav(dir){const d=new Date(this._date);if(this._period==="day")d.setDate(d.getDate()+dir);else if(this._period==="month")d.setMonth(d.getMonth()+dir);else d.setFullYear(d.getFullYear()+dir);this._date=d;this._ui();this._fetch();}
  _tab(p){this._period=p;this.querySelectorAll(".xtb").forEach(t=>t.classList.toggle("on",t.dataset.p===p));this._ui();this._fetch();}
  _ui(){const dd=this.querySelector("#dd"),td=this.querySelector("#std");if(dd)dd.textContent=this._dd();if(td)td.textContent=`${this._period.charAt(0).toUpperCase()+this._period.slice(1)} View — ${this._dd()}`;}
  getCardSize(){return 8;}
  static getStubConfig(){return{};}
}
customElements.define("solark-energy-card",SolarkEnergyCard);
window.customCards=window.customCards||[];
window.customCards.push({type:"solark-energy-card",name:"SolArk Energy Generation",description:"By Dresdencraft"});
