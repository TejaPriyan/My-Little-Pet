// Pet-led games use the same simulation for mouse, keyboard and spectator play.
export class PetPlayRound {
 constructor(kind,watch=false){this.kind=kind;this.watch=watch;this.x=20;this.y=72;this.target=[70,72];this.phase='ready';this.score=0;this.elapsed=0;this.jump=0;this.obstacle=100;this.checked=false;this.message=watch?'Sit back and watch your pet play.':kind==='fetch'?'Tap the grass to throw. Your pet brings the ball back.':'Tap or press Space to jump over the soft hurdles.'}
 throw(x,y){if(this.kind!=='fetch'||this.phase!=='ready'||x<42||x>90||y<45||y>80)return false;this.target=[x,y];this.phase='out';this.message='Fetch! Wait for your little friend to bring it back.';return true}
 leap(){if(this.kind!=='hurdles'||this.jump>0)return false;this.jump=.9;return true}
 step(dt){dt=Math.min(.1,Math.max(0,dt));this.elapsed+=dt;
  if(this.kind==='fetch'){
   if(this.watch&&this.phase==='ready')this.throw(65+Math.sin(this.elapsed)*18,62+Math.cos(this.elapsed)*12);
   if(this.phase!=='ready'){const [tx,ty]=this.phase==='out'?this.target:[20,72],dx=tx-this.x,dy=ty-this.y,dist=Math.hypot(dx,dy);if(dist<.6){if(this.phase==='out')this.phase='back';else{this.phase='ready';this.score+=4;this.message=this.watch?'Good fetch! Ready for another little run.':'Good fetch! Throw again, or press Space.'}}else{const step=Math.min(dist,dt*30);this.x+=dx/dist*step;this.y+=dy/dist*step}}
  }else{
   if(this.watch&&this.obstacle<42&&this.obstacle>35&&this.jump<=0)this.leap();
   this.jump=Math.max(0,this.jump-dt);this.obstacle-=(24+Math.min(8,this.elapsed/5))*dt;
   if(this.obstacle<=this.x+5&&!this.checked){this.checked=true;if(this.height>.45){this.score+=4;this.message='Lovely leap! A very proud little pet.'}else this.message='Soft landing! Try jumping a little earlier.'}
   if(this.obstacle<5){this.obstacle=100;this.checked=false}
  }
 }
 get height(){return this.jump?Math.sin(Math.PI*(1-this.jump/.9)):0}
}
