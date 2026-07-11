const assets=[
{id:'CP-SA-000014',type:'RTU',customer:'Broadway Bistro',location:'Roof • Zone 2',maker:'Trane',model:'YSC060E3',serial:'2419K4R7H',refrigerant:'R-410A',health:84,status:'Needs attention',notes:'Elevated compressor amperage. Verify airflow and capacitor on next visit.'},
{id:'CP-SA-000006',type:'Ice Machine',customer:'Riverwalk Hotel',location:'Main kitchen',maker:'Manitowoc',model:'IDT0750A',serial:'110728392',refrigerant:'R-410A',health:97,status:'Operational',notes:'Quarterly sanitation program active.'},
{id:'CP-SA-000003',type:'Walk-In Cooler',customer:'Alamo Market',location:'Receiving area',maker:'Heatcraft',model:'BZT060',serial:'HTC992801',refrigerant:'R-404A',health:72,status:'Monitor',notes:'Recurring low-temperature alarm and door gasket wear.'},
{id:'CP-SA-000021',type:'Reach-In',customer:'Southtown Cafe',location:'Prep line',maker:'True',model:'T-49-HC',serial:'10877654',refrigerant:'R-290',health:93,status:'Operational',notes:'No active concerns.'},
{id:'CP-SA-000019',type:'RTU',customer:'Stone Oak Offices',location:'Roof • Suite 400',maker:'Lennox',model:'ZGB060S4BM1Y',serial:'5624L02911',refrigerant:'R-410A',health:88,status:'Operational',notes:'Expansion valve history noted.'}
];
let currentPage='dashboard';
function healthClass(n){return n>=90?'good':n>=75?'warn':'bad'}
function renderPriority(){
document.getElementById('priorityList').innerHTML=assets.slice().sort((a,b)=>a.health-b.health).slice(0,4).map(a=>`<div class="asset-mini" onclick="openAsset('${a.id}')"><div><b>${a.id} • ${a.type}</b><span>${a.customer} — ${a.location}</span></div><span class="health ${healthClass(a.health)}">${a.health}%</span></div>`).join('')
}
function renderAssets(){
const q=document.getElementById('assetSearch')?.value.toLowerCase()||'',f=document.getElementById('assetFilter')?.value||'';
const filtered=assets.filter(a=>(!f||a.type===f)&&Object.values(a).join(' ').toLowerCase().includes(q));
document.getElementById('assetTable').innerHTML=`<div class="asset-row header"><div>Asset</div><div>Customer</div><div>Manufacturer</div><div>Status</div><div>Health</div></div>`+
filtered.map(a=>`<div class="asset-row" onclick="openAsset('${a.id}')"><div><b>${a.id}</b><span>${a.type} • ${a.location}</span></div><div><b>${a.customer}</b><span>${a.model}</span></div><div>${a.maker}</div><div>${a.status}</div><div><span class="health ${healthClass(a.health)}">${a.health}%</span></div></div>`).join('')
}
function openAsset(id){
const a=assets.find(x=>x.id.toLowerCase()===id.toLowerCase());if(!a){toast('Asset not found');return}
document.getElementById('assetDetail').innerHTML=`<div class="detail-hero"><div class="equipment-icon">❄</div><div><span class="eyebrow">${a.id}</span><h2>${a.type}</h2><p>${a.customer} • ${a.location}</p></div><span class="health ${healthClass(a.health)}">${a.health}% HEALTH</span></div>
<div class="detail-grid"><article class="panel"><h3>Equipment Information</h3><div class="kv"><div><span>Manufacturer</span><b>${a.maker}</b></div><div><span>Model</span><b>${a.model}</b></div><div><span>Serial</span><b>${a.serial}</b></div><div><span>Refrigerant</span><b>${a.refrigerant}</b></div><div><span>Status</span><b>${a.status}</b></div><div><span>Asset ID</span><b>${a.id}</b></div></div></article>
<article class="panel"><h3>Technician Intelligence</h3><p>${a.notes}</p><button class="primary">Start Work Order</button> <button class="secondary">Order Parts</button></article>
<article class="panel"><h3>Service Timeline</h3><div class="service-item"><b>Preventive Maintenance</b><span>Cooling inspection completed • 06/18/2026</span></div><div class="service-item"><b>Corrective Repair</b><span>Electrical component replaced • 03/02/2026</span></div></article>
<article class="panel"><h3>Documents & Photos</h3><p>Nameplate photo, wiring diagram, service manual, warranty file, and before/after photos.</p><button class="secondary">Upload Document</button></article></div>`;
showPage('detail')
}
function showPage(id){
document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));document.getElementById(id).classList.add('active');
document.querySelectorAll('nav button').forEach(b=>b.classList.toggle('active',b.dataset.page===id));
const titles={dashboard:['Operations Dashboard','Chill Pros asset intelligence and field operations'],assets:['Asset Registry','Search and manage installed equipment'],detail:['Asset Profile','Complete equipment record and service intelligence'],add:['Add Asset','Create a standardized Chill Pros equipment record'],scan:['QR Asset Scanner','Open equipment records directly from field tags'],workorders:['Work Orders','Job execution and Jobber synchronization'],pm:['Preventive Maintenance','Upcoming service and compliance tracking'],reports:['Reports & Analytics','Operational and asset portfolio intelligence']};
document.getElementById('pageTitle').textContent=titles[id][0];document.getElementById('pageSubtitle').textContent=titles[id][1];
currentPage=id;document.querySelector('.sidebar').classList.remove('open');window.scrollTo(0,0)
}
function manualLookup(){openAsset(document.getElementById('manualAsset').value.trim())}
function toast(msg){const t=document.getElementById('toast');t.textContent=msg;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2200)}
document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>showPage(b.dataset.page));
document.getElementById('mobileMenu').onclick=()=>document.querySelector('.sidebar').classList.toggle('open');
document.getElementById('assetSearch').oninput=renderAssets;document.getElementById('assetFilter').onchange=renderAssets;
document.getElementById('assetForm').onsubmit=e=>{e.preventDefault();const f=Object.fromEntries(new FormData(e.target));const next=String(Math.max(...assets.map(a=>+a.id.split('-').pop()))+1).padStart(6,'0');const a={id:`CP-SA-${next}`,type:f.type,customer:f.customer,location:f.equipmentLocation||f.location,maker:f.manufacturer,model:f.model,serial:f.serial,refrigerant:f.refrigerant||'Not recorded',health:100,status:'New asset',notes:f.notes||'Newly created asset. Initial condition assessment pending.'};assets.unshift(a);renderAssets();e.target.reset();toast(`${a.id} created`);openAsset(a.id)};
renderPriority();renderAssets();