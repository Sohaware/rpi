'use strict';
const NamedDesigns = (()=>{
  let baseline=null,busy=false;
  const input=()=>document.getElementById('designName');
  const fingerprint=()=>JSON.stringify(currentWorkspaceJson());
  async function request(action,data) {
    const url='/blocks/designs.php?action='+action;
    const response=await fetch(url,data?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)}:{});
    const result=await response.json();
    if(!response.ok||!result.ok) {const error=Error(result.error||'Design request failed');error.exists=result.exists;throw error;}
    return result;
  }
  function confirmReplace() {
    const dirty=baseline===null?workspace.getAllBlocks(false).length>0:fingerprint()!==baseline;
    return !dirty||confirm('Replace the current design? Changes not saved to a named design will be lost.');
  }
  function dialogButtons() {
    const disabled=busy||!document.getElementById('designList').value;
    document.getElementById('designLoadConfirm').disabled=disabled;
    document.getElementById('designDelete').disabled=disabled;
  }
  async function save() {
    if(busy)return;
    const name=input().value.trim();
    if(!name){input().focus();toast('Enter a design name first.',true);return;}
    input().value=name;
    const snapshot=currentWorkspaceJson();
    busy=true;
    try {
      let result;
      try {result=await request('save',{name,workspace:snapshot});}
      catch(error) {
        if(!error.exists||!confirm('Overwrite the saved design "'+name+'"?')) {if(error.exists)return;throw error;}
        result=await request('save',{name,workspace:snapshot,overwrite:true});
      }
      baseline=JSON.stringify(snapshot);
      await saveWorkspaceNow(true);
      toast('Design saved: '+result.name);
    }catch(error){toast(error.message,true);}
    finally{busy=false;}
  }
  async function open() {
    if(busy)return;
    const dialog=document.getElementById('designDialog'),list=document.getElementById('designList');
    list.replaceChildren();dialogButtons();
    dialog.showModal();
    document.getElementById('designListStatus').textContent='Loading...';
    try {
      const result=await request('list');
      for(const item of result.designs) {
        const option=document.createElement('option');option.value=item.name;option.textContent=item.name;
        list.appendChild(option);
      }
      document.getElementById('designListStatus').textContent=result.designs.length?'':'No saved designs.';
      if(result.designs.length)list.selectedIndex=0;
      dialogButtons();
    }catch(error){document.getElementById('designListStatus').textContent=error.message;}
  }
  async function load() {
    const name=document.getElementById('designList').value;
    if(!name||busy)return;
    busy=true;dialogButtons();
    try {
      const result=await request('load&name='+encodeURIComponent(name));
      if(!confirmReplace())return;
      const previous=currentWorkspaceJson();
      try {
        Blockly.serialization.workspaces.load(result.workspace,workspace);
        input().value=result.name;
      }catch(error){Blockly.serialization.workspaces.load(previous,workspace);throw error;}
      baseline=fingerprint();
      document.getElementById('designDialog').close();
      updatePythonPreview(true);
      await saveWorkspaceNow(true);
      toast('Design loaded: '+result.name);
    }catch(error){toast(error.message,true);}
    finally{busy=false;dialogButtons();}
  }
  async function remove() {
    const list=document.getElementById('designList'),name=list.value;
    if(!name||busy||!confirm('Delete the saved design "'+name+'" from this device? This cannot be undone. The open workspace will not change.'))return;
    busy=true;dialogButtons();
    try {
      await request('delete',{name,confirmed:true});
      const option=[...list.options].find(item=>item.value===name);
      const selected=option?.index??0;
      option?.remove();
      if(list.options.length)list.selectedIndex=Math.min(selected,list.options.length-1);
      document.getElementById('designListStatus').textContent=list.options.length?'':'No saved designs.';
      if(input().value.trim()===name)baseline=null;
      toast('Design deleted: '+name);
    }catch(error){toast(error.message,true);}
    finally{busy=false;dialogButtons();}
  }
  function initialize() {
    Blockly.serialization.registry.register('codynick_design',{
      priority:5,save:()=>({name:input().value}),
      load:data=>{input().value=typeof data?.name==='string'?data.name:'';baseline=null;},
      clear:()=>{input().value='';baseline=null;}
    });
    input().oninput=()=>scheduleSave();
    document.getElementById('designList').onchange=dialogButtons;
  }
  return {initialize,save,open,load,remove,confirmReplace};
})();
