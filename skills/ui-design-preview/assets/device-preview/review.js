"use strict";
// 页面 ID 代表同一功能场景；每个设备在自己的逻辑视口内独立布局。
const pages=[['chat','主界面'],['drawer','左侧抽屉'],['conversation','对话详情'],['work','工作'],['discover','能力目录'],['tasks','任务'],['me','我的空间'],['settings','设置分类'],['general','常规设置'],['appearance','外观设置'],['model','模型连接'],['model-providers','选择服务商'],['model-detail','供应商配置'],['model-fetch','获取模型'],['model-editor','新建连接'],['skills-import','导入技能'],['agents-import','导入智能体'],['plugins-import','导入插件'],['agents','子智能体'],['plugins','插件'],['mcp','MCP 服务器'],['skills','技能'],['memory','记忆'],['commands','命令'],['hooks','钩子'],['usage','使用统计'],['search','全局搜索'],['detail','能力详情']];
const params=new URLSearchParams(location.search);
const validPage=value=>pages.some(([id])=>id===value);
const validTheme=value=>value==='light'||value==='dark';
const initialPage=validPage(params.get('page'))?params.get('page'):params.get('section')==='models'?'model-detail':'chat';
const initialTheme=validTheme(params.get('theme'))?params.get('theme'):'light';
let synced=params.get('sync')!=='0';
let lastDevice=['phone','pad'].includes(params.get('last'))?params.get('last'):'phone';
const targets=[{id:'phone',title:'Phone',w:390,h:884},{id:'pad',title:'Pad',w:768,h:1024}].map(d=>({...d,
 page:!synced&&validPage(params.get(d.id))?params.get(d.id):initialPage,
 theme:!synced&&validTheme(params.get(d.id+'Theme'))?params.get(d.id+'Theme'):initialTheme,
 ready:false,error:'',view:null
}));
const pageControl=document.getElementById('review-page');
const themeControl=document.getElementById('review-theme');
const syncControl=document.getElementById('review-sync');
const options=()=>pages.map(([id,name])=>`<option value="${id}">${name}</option>`).join('');
pageControl.innerHTML=options();
document.getElementById('devices').innerHTML=targets.map(d=>`<section class="panel ${d.id}"><div class="panel-header"><div><strong>${d.title}</strong><small>${d.w} × ${d.h} · 独立布局</small></div><div class="controls"><select aria-label="${d.title} 页面" data-device="${d.id}">${options()}</select><select aria-label="${d.title} 主题" data-device-theme="${d.id}"><option value="light">浅色</option><option value="dark">深色</option></select></div></div><div class="viewport"><iframe id="${d.id}" title="${d.title}交互原型" name="${d.id}" width="${d.w}" height="${d.h}"></iframe></div></section>`).join('');
function activeTarget(){return targets.find(d=>d.id===lastDevice)||targets[0]}
function updateControls(){
 const active=activeTarget();pageControl.value=active.page;themeControl.value=active.theme;syncControl.checked=synced;
 const i=pages.findIndex(([id])=>id===active.page);
 document.getElementById('review-position').textContent=`${i+1} / ${pages.length}`;
 document.getElementById('review-prev').disabled=i===0;
 document.getElementById('review-next').disabled=i===pages.length-1;
 targets.forEach(d=>{document.querySelector(`[data-device="${d.id}"]`).value=d.page;document.querySelector(`[data-device-theme="${d.id}"]`).value=d.theme});
 const status=document.getElementById('review-status'),failed=targets.filter(d=>d.error),loading=targets.filter(d=>!d.ready);
 status.classList.toggle('error',failed.length>0);
 status.textContent=failed.length?failed.map(d=>`${d.title} 预览失败：${d.error}`).join('；'):loading.length?`正在加载 ${loading.map(d=>d.title).join(' / ')}，完成后应用最新选择…`:synced?'联动已开启 · 点击任一端的导航、弹窗或选项卡均可同步':'独立对照 · 顶部控制仍可一次切换两端';
}
function saveLocation(){
 const url=new URL(location.href),active=activeTarget();url.searchParams.set('page',active.page);url.searchParams.set('theme',active.theme);url.searchParams.set('sync',synced?'1':'0');url.searchParams.set('last',lastDevice);
 targets.forEach(d=>{if(synced){url.searchParams.delete(d.id);url.searchParams.delete(d.id+'Theme')}else{url.searchParams.set(d.id,d.page);url.searchParams.set(d.id+'Theme',d.theme)}});
 history.replaceState(null,'',url);
}
function applyTarget(d,route=true){
 if(!d.ready)return;
 try{
  // 同源、由本页创建的本地子文档；不读取任意URL或广播业务事件。
  const w=document.getElementById(d.id).contentWindow;
  if(typeof w.previewRoute!=='function'||typeof w.dispatch!=='function')throw new Error('缺少预览适配器，请检查入口后重新载入');
  if(route){if(d.view && typeof w.applyPreviewView==='function')w.applyPreviewView(d.view);else w.previewRoute(d.page);}
  w.dispatch('theme-'+d.theme,null);d.error='';
 }catch(error){d.error=error.message}
}
function choose(kind,value,device){
 if(kind==='page'&&!validPage(value)||kind==='theme'&&!validTheme(value))return;
 if(device)lastDevice=device;
 targets.filter(d=>!device||synced||d.id===device).forEach(d=>{d[kind]=value;if(kind==='page')d.view=null;else if(d.view)d.view.theme=value;applyTarget(d,kind==='page')});
 updateControls();saveLocation();
}
pageControl.addEventListener('change',()=>choose('page',pageControl.value));
themeControl.addEventListener('change',()=>choose('theme',themeControl.value));
syncControl.addEventListener('change',()=>{
 synced=syncControl.checked;
 if(synced){const active=activeTarget();targets.forEach(d=>{d.page=active.page;d.theme=active.theme;d.view=active.view?structuredClone(active.view):null;if(d!==active)applyTarget(d)})}
 updateControls();saveLocation();
});
document.getElementById('review-prev').addEventListener('click',()=>{const i=pages.findIndex(([id])=>id===activeTarget().page);if(i>0)choose('page',pages[i-1][0])});
document.getElementById('review-next').addEventListener('click',()=>{const i=pages.findIndex(([id])=>id===activeTarget().page);if(i<pages.length-1)choose('page',pages[i+1][0])});
document.addEventListener('change',e=>{if(e.target.dataset.device)choose('page',e.target.value,e.target.dataset.device);if(e.target.dataset.deviceTheme)choose('theme',e.target.value,e.target.dataset.deviceTheme)});
function fit(){targets.forEach(d=>{const f=document.getElementById(d.id),v=f.parentElement,scale=v.clientWidth/d.w;f.style.transform=`scale(${scale})`;v.style.height=`${d.h*scale}px`})}
new ResizeObserver(fit).observe(document.getElementById('devices'));
function receiveView(source,view){
 if(!view||!validPage(view.page)||!validTheme(view.theme))return;
 lastDevice=source.id;source.page=view.page;source.theme=view.theme;source.view=view;
 if(synced)targets.filter(d=>d!==source).forEach(d=>{d.page=view.page;d.theme=view.theme;d.view=structuredClone(view);applyTarget(d)});
 updateControls();saveLocation();
}
// 先注册load再指定src；重载和慢设备都读取当前状态，避免回放旧选择。
targets.forEach(d=>{const frame=document.getElementById(d.id);frame.addEventListener('load',()=>{d.ready=true;frame.contentWindow.onPreviewChange=view=>receiveView(d,view);applyTarget(d);updateControls()});frame.src='./index.html?v=medium-buttons-1#chat'});
updateControls();fit();saveLocation();
