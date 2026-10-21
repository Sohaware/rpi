'use strict';
history.replaceState(null, '', '/');
const $ = id => document.getElementById(id);
const mainPanelUrl = new URL(window.location.href);
mainPanelUrl.port = '';
mainPanelUrl.pathname = '/';
mainPanelUrl.search = '';
mainPanelUrl.hash = '';
$('mainPanel').href = mainPanelUrl.href;
const newGadgets={
  joystick:{title:'Stand-Alone joystick',body:'<div class="photo-device"><img class="joystick-photo" src="/joystick.png" alt="Stand-Alone joystick"><div class="standalone-stick"></div><output id="standaloneState">Neutral</output></div>'},
  ultrasonic:{title:'Ultrasonic sensor',body:'<div class="photo-device"><img src="/ultrasonic.png" alt="Stand-Alone ultrasonic sensor"><div class="sensor-controls"><label for="distanceValue">Distance (cm)</label><input id="distanceValue" type="number" min="2" max="400" step="0.1" value="50"><input id="distanceSlider" type="range" min="2" max="400" step="0.1" value="50" aria-label="Simulated distance"></div></div>'},
  soil:{title:'Soil-moisture sensor',body:'<div class="photo-device"><img class="soil-photo" src="/soil.png" alt="Soil-moisture sensor"><div class="sensor-controls"><label for="soilValue">Soil moisture (%)</label><input id="soilValue" type="number" min="0" max="100" step="1" value="50"><input id="soilSlider" type="range" min="0" max="100" step="1" value="50" aria-label="Simulated soil reading"></div></div>'},
  wifi:{title:'Wi-Fi / IoT',body:'<div class="photo-device wifi-device"><img src="/wifi.png" alt="Wi-Fi and IoT gadget"><p class="sim-label">SIMULATED NETWORK</p><div class="network-controls"><label><input id="wifiLink" type="checkbox" checked> Wi-Fi available</label><label><input id="cloudLink" type="checkbox" checked> Cloud available</label></div><dl class="wifi-status"><dt>Wi-Fi</dt><dd id="wifiState">Disconnected</dd><dt>IoT</dt><dd id="iotState">Disconnected</dd><dt>SSID</dt><dd id="wifiSSID">Not configured</dd></dl><div class="cloud-editor"><label>Type<select id="cloudType"><option value="0">Int</option><option value="1">Float</option><option value="2">Bool</option><option value="3">String</option></select></label><label>Index<input id="cloudIndex" type="number" min="0" max="3" value="0"></label><label class="cloud-value">Value<input id="cloudValue" maxlength="40" value="0"></label><button id="cloudApply">Set value</button></div><pre id="cloudValues" aria-label="Simulated cloud variables"></pre></div>'}
};
for(const [kind,data] of Object.entries(newGadgets)) {
  const item=document.createElement('section');item.className='stage-item';item.id='gadget-'+kind;item.dataset.kind=kind;item.hidden=true;
  item.innerHTML=`<button class="handle" aria-label="Move ${data.title}" title="Move ${data.title}">${data.title}<span aria-hidden="true">&#10021;</span></button>${data.body}`;
  $('stage').append(item);
}
for(const [state,symbol] of [['UP','\u2191'],['LEFT','\u2190'],['CLICK','\u25cf'],['RIGHT','\u2192'],['DOWN','\u2193']]) {
  const button=document.createElement('button');button.dataset.state=state;button.dataset.controller='joystick';button.textContent=symbol;button.title='Stand-Alone joystick '+state.toLowerCase();button.setAttribute('aria-label',button.title);
  document.querySelector('.standalone-stick').append(button);
}
for(const image of document.images) {
  let retries=0;
  const retry=()=>{if(retries++<3)setTimeout(()=>{const url=new URL(image.src);url.searchParams.set('retry',retries);image.src=url.href;},400);};
  image.addEventListener('error',retry);
  if(image.complete&&!image.naturalWidth)retry();
}
const order = [15,14,13,12,8,9,10,11,7,6,5,4,0,1,2,3];
const leds = new Map();
for (const id of order) {
  const el = document.createElement('div'); el.className = 'led'; el.textContent = id;
  el.title = `LED ${id}`; el.dataset.led = id; $('leds').append(el); leds.set(id, el);
}
const digitMap = {0:'abcdef',1:'bc',2:'abdeg',3:'abcdg',4:'bcfg',5:'acdfg',6:'acdefg',7:'abc',8:'abcdefg',9:'abcdfg','-':'g',' ':''};
const digits = [];
for (let i=0; i<4; i++) {
  const digit = document.createElement('div'); digit.className='digit';
  for (const segment of 'abcdefgp') {
    const el=document.createElement('i'); el.className='segment '+segment; digit.append(el);
  }
  $('sevenDigits').append(digit); digits.push(digit);
}
function displayNumber(text) {
  const values=[];
  for (const ch of text) {
    if (ch==='.' && values.length) values[values.length-1].dot=true;
    else values.push({char:ch,dot:false});
  }
  while(values.length<4) values.unshift({char:' ',dot:false});
  values.slice(0,4).forEach((value,index)=>{
    const enabled=(digitMap[value.char] || '')+(value.dot?'p':'');
    for(const segment of digits[index].children) segment.classList.toggle('on',enabled.includes(segment.classList[1]));
  });
  $('sevenDigits').setAttribute('aria-label','Seven-segment display: '+(text || 'blank'));
  $('displayValue').textContent=text || 'Blank';
}
let audio, muted = true, active = '', standaloneActive='', lastNote = 0, online = false, oscillator, lastInput = 0;
async function command(body) {
  const reply = await fetch('/command', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
  if (!reply.ok) { const data=await reply.json(); throw new Error(data.error || 'Simulator request failed'); }
  return reply.json();
}
function stopTone() { if (oscillator) { try {oscillator.stop();} catch {} oscillator = null; } }
$('sound').onclick = async () => {
  try {
    audio ||= new (window.AudioContext || window.webkitAudioContext)(); await audio.resume();
    muted = !muted; $('sound').textContent = muted ? 'Enable sound' : 'Mute sound';
    $('soundStatus').textContent = muted ? 'Muted' : 'Sound enabled';
    if (muted) stopTone();
  } catch { $('soundStatus').textContent = 'Sound is unavailable in this browser.'; }
};
function tone(note) {
  if (!audio || muted) return;
  stopTone(); const osc = audio.createOscillator(), gain = audio.createGain();
  oscillator = osc; osc.type = 'square'; osc.frequency.value = note.frequency;
  gain.gain.setValueAtTime(.025, audio.currentTime); gain.gain.exponentialRampToValueAtTime(.0001, audio.currentTime + note.duration/1000);
  osc.connect(gain); gain.connect(audio.destination); osc.start(); osc.stop(audio.currentTime + note.duration/1000);
  osc.onended = () => { osc.disconnect(); gain.disconnect(); if (oscillator === osc) oscillator = null; };
}
function input(value,device='cjp') {
  if(device==='cjp')active=value;else standaloneActive=value;
  for (const b of document.querySelectorAll('[data-state]')) if((b.dataset.controller||'cjp')===device)b.classList.toggle('active', b.dataset.state === value);
  return command({action:'input', device, states:value ? [value] : []}).catch(()=>{});
}
for (const button of document.querySelectorAll('[data-state]')) {
  const device=button.dataset.controller||'cjp';
  button.onpointerdown = e => {e.preventDefault(); button.setPointerCapture(e.pointerId); input(button.dataset.state,device);};
  button.onpointerup = button.onpointercancel = button.onlostpointercapture = () => input('',device);
  button.onkeydown = e => {if (['Enter',' '].includes(e.key)) {e.preventDefault(); input(button.dataset.state,device);}};
  button.onkeyup = e => {if (['Enter',' '].includes(e.key)) input('',device);};
}
function releaseInputs(){input('');if(scene?.gadgets.joystick)input('','joystick');stopTone();}
window.addEventListener('blur',releaseInputs);
document.addEventListener('visibilitychange', () => {if (document.hidden)releaseInputs();});
const labels={cjp:'CodyJoy Pro',seven:'Seven-segment',temperature:'Temperature sensor',matrix:'LED matrix',...Object.fromEntries(Object.entries(newGadgets).map(([key,value])=>[key,value.title]))};
const defaults={seven:{x:440,y:40},temperature:{x:440,y:360},matrix:{x:760,y:360},joystick:{x:40,y:640},ultrasonic:{x:400,y:720},soil:{x:740,y:720},wifi:{x:1050,y:760}};
let scene=null, selected='cjp', dragging=null, pending=0, pythonConnected=false, z=1, temperatureTimer, stageZoom=1, initialFit=false;
function zoom(value){stageZoom=value;$('stage').style.zoom=value;$('stageViewport').scrollTo(0,0);}
function fitStage(){
  if(!scene) return;
  const viewport=$('stageViewport'); let right=380,bottom=600;
  for(const [key,pos] of Object.entries(scene.gadgets)) {
    const item=$('gadget-'+key);right=Math.max(right,pos.x+item.offsetWidth+24);bottom=Math.max(bottom,pos.y+item.offsetHeight+24);
  }
  zoom(Math.max(.2,Math.min(1,(viewport.clientWidth-16)/right,(viewport.clientHeight-16)/bottom)));
}
$('fit').onclick=fitStage;$('actual').onclick=()=>zoom(1);
function showError(message) { $('error').textContent=message; $('error').hidden=!message; }
function select(kind) {
  selected=kind; $('selected').textContent=labels[kind];
  for(const item of document.querySelectorAll('.stage-item')) item.classList.toggle('selected',item.dataset.kind===kind);
  $('remove').disabled=kind==='cjp'||pythonConnected;
}
function renderScene(value) {
  scene=structuredClone(value);
  for(const item of document.querySelectorAll('.stage-item')) {
    const pos=scene.gadgets[item.dataset.kind]; item.hidden=!pos;
    if(pos) {item.style.left=pos.x+'px';item.style.top=pos.y+'px';}
  }
  for(const button of document.querySelectorAll('[data-add]')) button.disabled=pythonConnected||!!scene.gadgets[button.dataset.add];
  if(!scene.gadgets[selected]) select('cjp');
  if(![$('temperatureValue'),$('temperatureSlider')].includes(document.activeElement)) {
    $('temperatureValue').value=scene.temperature; $('temperatureSlider').value=scene.temperature;
  }
  for(const [prefix,key] of [['distance','distance'],['soil','soil']]) {
    if(![$(prefix+'Value'),$(prefix+'Slider')].includes(document.activeElement)) {
      $(prefix+'Value').value=value[key];$(prefix+'Slider').value=value[key];
    }
  }
  $('wifiLink').checked=scene.wifi_link;$('cloudLink').checked=scene.cloud_link;
  select(selected);
}
let saveQueue=Promise.resolve();
function saveScene() {
  const value=structuredClone(scene); pending++; $('saved').textContent='Saving...';
  saveQueue=saveQueue.catch(()=>{}).then(()=>command({action:'scene',scene:value})).then(()=>{
    $('saved').textContent='Saved'; showError('');
  }).catch(error=>{showError(error.message);$('saved').textContent='Not saved';}).finally(()=>{pending--;});
  return saveQueue;
}
function place(kind,x,y) {
  const item=$('gadget-'+kind); item.hidden=false;
  const pos={x:Math.round(Math.max(0,Math.min(1400-item.offsetWidth,x))/8)*8,
    y:Math.round(Math.max(0,Math.min(1500-item.offsetHeight,y))/8)*8};
  scene.gadgets[kind]=pos; item.style.left=pos.x+'px';item.style.top=pos.y+'px';
}
async function addGadget(kind,pos) {
  if(!scene||scene.gadgets[kind]||pythonConnected) return;
  place(kind,(pos||defaults[kind]).x,(pos||defaults[kind]).y); select(kind); await saveScene();
  renderScene(scene);
  if(innerWidth>640) fitStage(); else $('gadget-'+kind).scrollIntoView({block:'nearest',inline:'nearest'});
}
for(const button of document.querySelectorAll('[data-add]')) {
  button.onclick=()=>addGadget(button.dataset.add);
  button.ondragstart=event=>{
    if(button.disabled) return event.preventDefault();
    event.dataTransfer.setData('text/plain',button.dataset.add);event.dataTransfer.effectAllowed='copy';
  };
}
$('stage').ondragover=event=>{event.preventDefault();event.dataTransfer.dropEffect='copy';$('stage').classList.add('drag-over');};
$('stage').ondragleave=()=>$('stage').classList.remove('drag-over');
$('stage').ondrop=event=>{
  event.preventDefault();$('stage').classList.remove('drag-over');
  const kind=event.dataTransfer.getData('text/plain'), rect=$('stage').getBoundingClientRect();
  if(defaults[kind]) addGadget(kind,{x:(event.clientX-rect.left)/stageZoom,y:(event.clientY-rect.top)/stageZoom});
};
$('remove').onclick=async()=>{
  if(selected==='cjp'||pythonConnected||!scene) return;
  delete scene.gadgets[selected]; renderScene(scene); await saveScene();
};
for(const item of document.querySelectorAll('.stage-item')) {
  const handle=item.querySelector('.handle');
  item.onpointerdown=()=>{select(item.dataset.kind);item.style.zIndex=++z;};
  handle.onpointerdown=event=>{
    if(!scene) return;event.preventDefault();handle.setPointerCapture(event.pointerId);
    const kind=item.dataset.kind;
    dragging={kind,x:event.clientX,y:event.clientY,position:{...scene.gadgets[kind]}};
  };
  handle.onpointermove=event=>{
    if(!dragging||dragging.kind!==item.dataset.kind) return;
    place(dragging.kind,dragging.position.x+(event.clientX-dragging.x)/stageZoom,dragging.position.y+(event.clientY-dragging.y)/stageZoom);
  };
  handle.onpointerup=handle.onpointercancel=()=>{if(dragging){dragging=null;saveScene();}};
  handle.onkeydown=event=>{
    const delta={ArrowLeft:[-8,0],ArrowRight:[8,0],ArrowUp:[0,-8],ArrowDown:[0,8]}[event.key];
    if(delta&&scene){event.preventDefault();const p=scene.gadgets[item.dataset.kind];place(item.dataset.kind,p.x+delta[0],p.y+delta[1]);saveScene();}
  };
}
function setTemperature(event) {
  const value=Number(event.target.value);
  if(!scene||event.target.value===''||!Number.isFinite(value)||value < -55||value > 125) return;
  scene.temperature=Math.round(value*10)/10;
  $('temperatureValue').value=scene.temperature; $('temperatureSlider').value=scene.temperature;
  clearTimeout(temperatureTimer); temperatureTimer=setTimeout(()=>{temperatureTimer=null;saveScene();},150);
}
$('temperatureValue').oninput=$('temperatureSlider').oninput=setTemperature;
for(const [prefix,key,min,max] of [['distance','distance',2,400],['soil','soil',0,100]]) {
  const update=event=>{
    const value=Number(event.target.value);
    if(!scene||event.target.value===''||!Number.isFinite(value)||value<min||value>max)return;
    scene[key]=Math.round(value*10)/10;$(prefix+'Value').value=scene[key];$(prefix+'Slider').value=scene[key];
    clearTimeout(temperatureTimer);temperatureTimer=setTimeout(()=>{temperatureTimer=null;saveScene();},150);
  };
  $(prefix+'Value').oninput=$(prefix+'Slider').oninput=update;
}
for(const [id,key] of [['wifiLink','wifi_link'],['cloudLink','cloud_link']]) $(id).onchange=()=>{if(scene){scene[key]=$(id).checked;saveScene();}};
$('cloudApply').onclick=async()=>{
  try {await command({action:'wifi_slot',type:$('cloudType').value,index:Number($('cloudIndex').value),value:$('cloudValue').value});showError('');}
  catch(error){showError(error.message);}
};

const matrixPixels=[];
for(let i=0;i<64;i++){const el=document.createElement('div');el.className='matrix-pixel';$('matrixPixels').append(el);matrixPixels.push(el);}
let matrix={mode:'pixels',pixels:Array(64).fill(0)}, matrixRevision=-1, matrixStarted=0, raster=null;
function matrixUpdate(value) {
  if(value.revision===matrixRevision) return;
  matrix=value;matrixRevision=value.revision;matrixStarted=performance.now();
  $('matrixText').textContent=value.mode==='text'?value.text:'';
  if(value.mode==='text') {
    // Each byte is one column; bit 0 is the top row. No font scaling or antialiasing.
    const columns=Array(8).fill(0);
    for(const character of value.text) {
      const glyph=MATRIX_FONT5X7[character.charCodeAt(0)-32] || MATRIX_FONT5X7[31];
      columns.push(...glyph,0);
    }
    columns.push(...Array(8).fill(0));
    raster={width:columns.length,columns};
  }
}
function animateMatrix(now) {
  if(!$('gadget-matrix').hidden) {
    let pixels=matrix.pixels;
    if(matrix.mode==='text'&&raster) {
      const offset=Math.floor((now-matrixStarted)/[240,160,100][matrix.speed])%raster.width;
      pixels=Array.from({length:64},(_,i)=>(raster.columns[(i%8+offset)%raster.width]>>Math.floor(i/8))&1);
    }
    matrixPixels.forEach((el,i)=>el.classList.toggle('on',!!pixels[i]));
  }
  requestAnimationFrame(animateMatrix);
}
requestAnimationFrame(animateMatrix);
select('cjp');
async function poll() {
  try {
    const reply = await fetch('/state', {cache:'no-store', signal:AbortSignal.timeout(2000)});
    if (!reply.ok) throw new Error(); const state = await reply.json();
    $('connection').textContent = 'Service online'; $('python').textContent = state.connected ? 'Connected' : 'Waiting';
    pythonConnected=state.connected;
    if(!dragging&&!pending&&!temperatureTimer) {renderScene(state.scene);$('saved').textContent='Saved';}
    if(!initialFit&&scene){initialFit=true;if(innerWidth>640)fitStage();}
    for(const button of document.querySelectorAll('[data-add]')) button.disabled=state.connected||!!scene?.gadgets[button.dataset.add];
    $('remove').disabled=selected==='cjp'||state.connected;
    if(state.error) showError(state.error);
    matrixUpdate(state.matrix);
    $('direction').textContent = state.states.join(' + ') || 'Neutral';
    $('standaloneState').textContent=state.joystick_states.join(' + ')||'Neutral';
    $('wifiState').textContent=state.wifi.wifi===3?'Connected':'Disconnected';$('iotState').textContent=state.wifi.iot===1?'Connected':'Disconnected';
    $('wifiSSID').textContent=state.wifi.ssid||'Not configured';
    $('cloudValues').textContent=state.wifi.slots.map(slot=>`${slot.type}[${slot.index}] = ${slot.value}`).join('\n')||'No values';
    displayNumber(state.seven_segment || '');
    if(!state.scene.gadgets.seven) $('displayValue').textContent='Not added';
    state.leds.forEach((color,id) => {const el=leds.get(id); el.style.background=color; el.style.boxShadow=color === '#000000' ? 'none' : `0 0 12px ${color}`; el.style.color=color === '#000000' ? '#9ba89f' : '#101b15';});
    if (!state.connected) {stopTone(); $('note').textContent='Silent';}
    for (const note of state.notes) {
      if (note.id > lastNote) {
        // Do not replay old notes when opening/reconnecting the browser.
        if (online && state.now-note.at < 1) tone(note);
        lastNote = note.id;
      }
    }
    const recent=state.notes.at(-1);
    $('note').textContent=recent && state.now < recent.at+recent.duration/1000 ? `${recent.frequency} Hz` : 'Silent';
    online = true;
    if ((active||standaloneActive) && Date.now()-lastInput>250) {lastInput=Date.now();if(active)await input(active);if(standaloneActive)await input(standaloneActive,'joystick');}
  } catch {online=false; stopTone(); $('connection').textContent='Service disconnected'; $('python').textContent='Unknown';}
  setTimeout(poll, 50);
}
poll();
