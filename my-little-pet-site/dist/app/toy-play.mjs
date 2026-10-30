import {setupRoom} from './room-world.mjs?v=1.6-free-1';
export class ToyMotion {
  constructor(kind,random=Math.random){this.kind=kind;this.random=random;this.x=76;this.y=76;this.vx=24;this.vy=-8;this.age=0;this.impulse=0;this.turn=0;this.z=0;}
  bat(){this.impulse=0;const angle=this.random()*Math.PI*2,speed=this.kind==='butterfly'?34:this.kind==='ball'?30:19;this.vx=Math.cos(angle)*speed;this.vy=Math.sin(angle)*speed;}
  update(dt){dt=Math.max(0,Math.min(.05,dt));this.age+=dt;this.impulse+=dt;this.turn-=dt;
    if(this.turn<=0){this.turn=this.kind==='butterfly'?.3+this.random()*.5:.7+this.random();if(['mouse','butterfly','feather'].includes(this.kind))this.bat();}
    if(this.kind==='yarn'){this.vx*=Math.exp(-.8*dt);this.vy*=Math.exp(-.8*dt);this.z=0}
    else if(this.kind==='ball'){this.vx*=Math.exp(-.85*dt);this.vy*=Math.exp(-.85*dt);this.z=Math.abs(Math.sin(this.impulse*5))*5*Math.exp(-1.1*this.impulse);if(this.impulse>4)this.vx=this.vy=this.z=0;}
    else if(this.kind==='spring')this.z=Math.abs(Math.sin(this.age*7))*10;
    else if(this.kind==='mouse')this.z=Math.abs(Math.sin(this.age*14))*.7;
    else if(this.kind==='butterfly')this.z=8+Math.sin(this.age*9)*7;
    else this.z=6+Math.sin(this.age*5)*4;
    this.x+=this.vx*dt;this.y+=this.vy*dt;
    if(this.x<12||this.x>88){this.x=Math.max(12,Math.min(88,this.x));this.vx*=-1}
    if(this.y<58||this.y>88){this.y=Math.max(58,Math.min(88,this.y));this.vy*=-1}
  }
}

export function setupToyPlay(api){return setupRoom({...api,ToyMotion});}
