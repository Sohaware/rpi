'use strict';
const SpritePrototype = (() => {
  let settings = {x:0,y:0,direction:90,size:100,backdrop:'white'};
  let state = {...settings,visible:true,speech:''};
  let pending = false;
  const held = new Set();
  const mouse = {x:0,y:0,down:false};
  const canvas = document.getElementById('spriteCanvas');
  const context = canvas.getContext('2d');
  const image = new Image();
  image.src = '/blocks/rocket.svg';
  image.onload = draw;
  const colours = {white:'#ffffff',sky:'#d9f1ff',field:'#e3f4dc'};
  async function request(command) {
    const response = await fetch('/blocks/stage.php', command ? {
      method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(command)
    } : {});
    const data = await response.json();
    if (!response.ok || !data.ok) throw Error(data.error || 'Stage request failed');
    state = data.state;
    document.getElementById('spriteStatus').textContent = 'Connected';
    draw();
    return state;
  }
  function draw() {
    context.fillStyle = colours[state.backdrop] || colours.white;
    context.fillRect(0,0,480,360);
    context.strokeStyle = '#b6c8cf'; context.lineWidth=1;
    context.beginPath();context.moveTo(240,0);context.lineTo(240,360);context.moveTo(0,180);context.lineTo(480,180);context.stroke();
    const x=240+state.x,y=180-state.y;
    if(state.visible && image.complete && image.naturalWidth) {
      const size=48*(state.size??100)/100;
      context.save();context.translate(x,y);context.rotate(state.direction*Math.PI/180);context.drawImage(image,-size/2,-size/2,size,size);context.restore();
    }
    if(state.visible && state.speech) {
      context.font='15px Arial';
      const words=state.speech.split(/\s+/),lines=[];let line='';
      for(const word of words) { const next=line?line+' '+word:word; if(context.measureText(next).width>210 && line){lines.push(line);line=word;}else line=next; }
      if(line)lines.push(line);
      const shown=lines.slice(0,6),height=shown.length*19+16;
      const left=Math.max(4,Math.min(240,x-100)),top=Math.max(4,Math.min(356-height,y-70-height));
      context.fillStyle='#fff';context.strokeStyle='#47616d';context.fillRect(left,top,236,height);context.strokeRect(left,top,236,height);
      context.fillStyle='#172e38';shown.forEach((text,i)=>context.fillText(text,left+8,top+21+i*19,220));
    }
    document.getElementById('spriteXReadout').textContent='x: '+state.x.toFixed(1);
    document.getElementById('spriteYReadout').textContent='y: '+state.y.toFixed(1);
  }
  function updateControls() {
    for(const key of ['x','y','direction','size','backdrop'])document.getElementById('sprite_'+key).value=settings[key];
  }
  async function configure() {
    try {await request({action:'configure',...settings});}catch(error){document.getElementById('spriteStatus').textContent=error.message;}
  }
  function definitions() {
    const number=(name)=>({type:'input_value',name,check:'Number'});
    const statement=(type,message0,args0=[])=>({type,message0,args0,previousStatement:null,nextStatement:null,colour:'#287db3'});
    Blockly.defineBlocksWithJsonArray([
      statement('sprite_move','move %1 steps',[number('STEPS')]),
      statement('sprite_turn','turn clockwise %1 degrees',[number('DEGREES')]),
      statement('sprite_point','point in direction %1',[number('DIRECTION')]),
      statement('sprite_change_x','change x by %1',[number('AMOUNT')]),
      statement('sprite_change_y','change y by %1',[number('AMOUNT')]),
      statement('sprite_set_size','set size to %1 percent',[number('SIZE')]),
      statement('sprite_change_size','change size by %1',[number('SIZE')]),
      statement('sprite_go','go to x %1 y %2',[number('X'),number('Y')]),
      statement('sprite_set_x','set x to %1',[number('X')]),
      statement('sprite_set_y','set y to %1',[number('Y')]),
      statement('sprite_glide','glide %1 seconds to x %2 y %3',[number('SECONDS'),number('X'),number('Y')]),
      statement('sprite_bounce','if on edge, bounce'),
      statement('sprite_go_mouse','go to mouse'),
      statement('sprite_say','say %1',[{type:'input_value',name:'TEXT'}]),
      statement('sprite_say_for','say %1 for %2 seconds',[{type:'input_value',name:'TEXT'},number('SECONDS')]),
      statement('sprite_show','show sprite'),statement('sprite_hide','hide sprite'),
      {type:'sprite_x',message0:'sprite x',output:'Number',colour:'#287db3'},
      {type:'sprite_y',message0:'sprite y',output:'Number',colour:'#287db3'},
      {type:'sprite_direction',message0:'direction',output:'Number',colour:'#287db3'},
      {type:'sprite_size',message0:'size (%)',output:'Number',colour:'#287db3'},
      {type:'sprite_mouse_x',message0:'mouse x',output:'Number',colour:'#287db3'},
      {type:'sprite_mouse_y',message0:'mouse y',output:'Number',colour:'#287db3'},
      {type:'sprite_mouse_down',message0:'mouse down?',output:'Boolean',colour:'#287db3'},
      {type:'sprite_edge',message0:'touching edge?',output:'Boolean',colour:'#287db3'},
      {type:'sprite_key',message0:'key %1 pressed?',args0:[{type:'field_dropdown',name:'KEY',options:[['up arrow','up'],['down arrow','down'],['left arrow','left'],['right arrow','right'],['space','space']]}],output:'Boolean',colour:'#287db3'}
    ]);
    for (const group of categories()) {
      for (const entry of group.contents) {
        const definition = Blockly.Blocks[entry.type];
        const originalInit = definition.init;
        definition.init = function() {
          originalInit.call(this);
          this.setColour(group.colour);
        };
      }
    }
  }
  const shadow=(name,num)=>({[name]:{shadow:{type:'math_number',fields:{NUM:num}}}});
  function categories() {
    return [{kind:'category',name:'Motion',colour:'#287db3',contents:[
      {kind:'block',type:'sprite_move',inputs:shadow('STEPS',10)},
      {kind:'block',type:'sprite_turn',inputs:shadow('DEGREES',15)},
      {kind:'block',type:'sprite_point',inputs:shadow('DIRECTION',90)},
      {kind:'block',type:'sprite_go',inputs:{...shadow('X',0),...shadow('Y',0)}},
      {kind:'block',type:'sprite_set_x',inputs:shadow('X',0)},
      {kind:'block',type:'sprite_set_y',inputs:shadow('Y',0)},
      {kind:'block',type:'sprite_glide',inputs:{...shadow('SECONDS',1),...shadow('X',100),...shadow('Y',0)}},
      {kind:'block',type:'sprite_bounce'},
      {kind:'block',type:'sprite_go_mouse'},
      {kind:'block',type:'sprite_change_x',inputs:shadow('AMOUNT',10)},
      {kind:'block',type:'sprite_change_y',inputs:shadow('AMOUNT',10)},
      ...['sprite_x','sprite_y','sprite_direction'].map(type=>({kind:'block',type}))
    ]},{kind:'category',name:'Looks',colour:'#b34d89',contents:[
      {kind:'block',type:'sprite_say',inputs:{TEXT:{shadow:{type:'text',fields:{TEXT:'Hello!'}}}}},
      {kind:'block',type:'sprite_say_for',inputs:{TEXT:{shadow:{type:'text',fields:{TEXT:'Hello!'}}},...shadow('SECONDS',2)}},
      {kind:'block',type:'sprite_set_size',inputs:shadow('SIZE',100)},
      {kind:'block',type:'sprite_change_size',inputs:shadow('SIZE',10)},
      ...['sprite_show','sprite_hide','sprite_size'].map(type=>({kind:'block',type}))
    ]},{kind:'category',name:'Sensing',colour:'#168579',contents:['sprite_key','sprite_mouse_x','sprite_mouse_y','sprite_mouse_down','sprite_edge'].map(type=>({kind:'block',type}))}];
  }
  function value(block) {
    if(block.type==='sprite_x')return '_stage.x()';
    if(block.type==='sprite_y')return '_stage.y()';
    if(block.type==='sprite_direction')return '_stage.direction()';
    if(block.type==='sprite_size')return '_stage.size()';
    if(block.type==='sprite_mouse_x')return '_stage.mouse_x()';
    if(block.type==='sprite_mouse_y')return '_stage.mouse_y()';
    if(block.type==='sprite_mouse_down')return '_stage.mouse_down()';
    if(block.type==='sprite_edge')return '_stage.touching_edge()';
    if(block.type==='sprite_key')return '_stage.key_pressed('+JSON.stringify(block.getFieldValue('KEY'))+')';
    return null;
  }
  function statement(block,toCode) {
    switch(block.type) {
      case 'sprite_move': return '_stage.move('+toCode(block,'STEPS','10')+')\n';
      case 'sprite_turn': return '_stage.turn('+toCode(block,'DEGREES','15')+')\n';
      case 'sprite_point': return '_stage.point_direction('+toCode(block,'DIRECTION','90')+')\n';
      case 'sprite_change_x': return '_stage.change_x('+toCode(block,'AMOUNT','10')+')\n';
      case 'sprite_change_y': return '_stage.change_y('+toCode(block,'AMOUNT','10')+')\n';
      case 'sprite_set_size': return '_stage.set_size('+toCode(block,'SIZE','100')+')\n';
      case 'sprite_change_size': return '_stage.change_size('+toCode(block,'SIZE','10')+')\n';
      case 'sprite_go': return '_stage.go('+toCode(block,'X','0')+', '+toCode(block,'Y','0')+')\n';
      case 'sprite_set_x': return '_stage.set_x('+toCode(block,'X','0')+')\n';
      case 'sprite_set_y': return '_stage.set_y('+toCode(block,'Y','0')+')\n';
      case 'sprite_glide': return '_stage.glide('+toCode(block,'SECONDS','1')+', '+toCode(block,'X','0')+', '+toCode(block,'Y','0')+')\n';
      case 'sprite_bounce': return '_stage.bounce()\n';
      case 'sprite_go_mouse': return '_stage.go_to_mouse()\n';
      case 'sprite_say_for': return '_stage.say_for('+toCode(block,'TEXT',"''")+', '+toCode(block,'SECONDS','2')+')\n';
      case 'sprite_say': return '_stage.say('+toCode(block,'TEXT',"''")+')\n';
      case 'sprite_show': return '_stage.show()\n';
      case 'sprite_hide': return '_stage.hide()\n';
      default: return null;
    }
  }
  function initialization() {
    return '_stage = SpriteStage(x='+settings.x+', y='+settings.y+', direction='+settings.direction+', size='+settings.size+', backdrop='+JSON.stringify(settings.backdrop)+')';
  }
  function initialize() {
    const tabs=['generalToolboxTab','spriteToolboxTab','hardwareToolboxTab'];
    const modes=['general','sprites','hardware'];
    for(const [index,id] of tabs.entries())document.getElementById(id).onkeydown=event=>{
      if(!['ArrowLeft','ArrowRight'].includes(event.key))return;
      event.preventDefault();
      const next=(index+(event.key==='ArrowRight'?1:2))%3;
      selectToolboxMode(modes[next]);
      document.getElementById(tabs[next]).focus();
    };
    Blockly.serialization.registry.register('codynick_stage',{
      priority:10,
      save:()=>({...settings}),
      load:data=>{
        if(data && ['x','y','direction'].every(key=>Number.isFinite(data[key])) && colours[data.backdrop]
           && Math.abs(data.x)<=240 && Math.abs(data.y)<=180 && Math.abs(data.direction)<=36000) settings={x:data.x,y:data.y,direction:data.direction,size:Number.isFinite(data.size)?Math.max(10,Math.min(300,data.size)):100,backdrop:data.backdrop};
        updateControls();
      },
      clear:()=>{settings={x:0,y:0,direction:90,size:100,backdrop:'white'};updateControls();}
    });
    for(const key of ['x','y','direction','size','backdrop'])document.getElementById('sprite_'+key).addEventListener('change',()=>{
      const element=document.getElementById('sprite_'+key),old=settings[key];
      const value=key==='backdrop'?element.value:Number(element.value);
      if(key!=='backdrop' && (!element.checkValidity() || !Number.isFinite(value))) {element.value=old;return;}
      settings[key]=value;configure();saveWorkspaceNow(true);updatePythonPreview(false);
    });
    document.getElementById('spriteReset').onclick=configure;
    document.getElementById('stageToggle').onclick=()=>{
      const main=document.querySelector('main.main');main.classList.toggle('stage-collapsed');
      document.getElementById('stageToggle').setAttribute('aria-expanded',String(!main.classList.contains('stage-collapsed')));
      Blockly.svgResize(workspace);
    };
    const keys={ArrowUp:'up',ArrowDown:'down',ArrowLeft:'left',ArrowRight:'right',' ':'space'};
    function pointer(event) {
      const bounds=canvas.getBoundingClientRect();
      mouse.x=Math.max(-240,Math.min(240,(event.clientX-bounds.left)/bounds.width*480-240));
      mouse.y=Math.max(-180,Math.min(180,180-(event.clientY-bounds.top)/bounds.height*360));
    }
    canvas.onpointermove=pointer;
    canvas.onpointerdown=event=>{canvas.focus();pointer(event);mouse.down=true;};
    canvas.onpointerleave=()=>{mouse.down=false;};
    canvas.onpointercancel=()=>{mouse.down=false;};
    window.addEventListener('pointerup',()=>{mouse.down=false;});
    canvas.onkeydown=event=>{if(keys[event.key]){event.preventDefault();held.add(keys[event.key]);}};
    canvas.onkeyup=event=>{if(keys[event.key]){event.preventDefault();held.delete(keys[event.key]);}};
    const release=()=>{held.clear();mouse.down=false;request({action:'keys',keys:[],mouse}).catch(()=>{});};
    canvas.onblur=release;window.addEventListener('blur',release);
    document.addEventListener('visibilitychange',()=>{if(document.hidden)release();});
    setInterval(async()=>{
      if(pending || document.hidden)return;pending=true;
      try {await request({action:'keys',keys:[...held],mouse});}
      catch(error){document.getElementById('spriteStatus').textContent=error.message;}
      finally {pending=false;}
    },100);
    updateControls();request().catch(error=>{document.getElementById('spriteStatus').textContent=error.message;});
  }
  return {definitions,categories,value,statement,initialization,initialize};
})();
