export function setupComforts({getState,sync,persist}){
 const room=document.querySelector('#pet-room');
 const layer=document.createElement('div');layer.className='room-weather';layer.setAttribute('aria-hidden','true');room.append(layer);
 for(let i=0;i<18;i++){const drop=document.createElement('span');drop.style.left=(i*37%100)+'%';drop.style.animationDelay=-(i*.27)+'s';layer.append(drop)}
 const choices={'pet-size':'petSize','room-time':'roomTime','room-weather':'weather'};
 function render(){const s=getState();room.dataset.petSize=s.petSize||'medium';room.dataset.weather=s.weather||'clear';const hour=new Date().getHours();room.dataset.night=String(s.roomTime==='night'||((s.roomTime||'real')==='real'&&(hour<6||hour>=19)));room.dataset.still=String(s.paused||s.quiet);for(const [id,key] of Object.entries(choices)){const el=document.getElementById(id);if(document.activeElement!==el)el.value=s[key]||{petSize:'medium',roomTime:'real',weather:'clear'}[key];}}
 for(const [id,key] of Object.entries(choices))document.getElementById(id).onchange=e=>{sync();getState()[key]=e.target.value;persist();render()};
 document.querySelector('#room-fullscreen').onclick=async()=>{try{await document.documentElement.requestFullscreen?.();await screen.orientation.lock?.('landscape')}catch{}document.querySelector('[data-tab="room"]').click()};
 render();setInterval(render,1000);
}
