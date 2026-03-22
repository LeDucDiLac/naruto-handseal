// Water Release: Water Dragon Jutsu effect
function createWaterEffect(canvas) {
    const ctx = canvas.getContext('2d'); const startTime = Date.now(); const duration = 3500; const particles = [];
    class WP { constructor(x,y,a,s){this.x=x;this.y=y;this.vx=Math.cos(a)*s;this.vy=Math.sin(a)*s;this.size=Math.random()*15+5;this.life=1;this.decay=Math.random()*0.01+0.005;this.hue=Math.random()*30+190;this.w=Math.random()*Math.PI*2;this.ws=Math.random()*0.1+0.05;} update(){this.w+=this.ws;this.x+=this.vx+Math.sin(this.w)*2;this.y+=this.vy+Math.cos(this.w);this.vy+=0.05;this.life-=this.decay;this.size*=0.995;} draw(ctx){if(this.life<=0)return;const g=ctx.createRadialGradient(this.x,this.y,0,this.x,this.y,this.size);g.addColorStop(0,`hsla(${this.hue},80%,70%,${this.life*0.7})`);g.addColorStop(1,`hsla(${this.hue+20},80%,30%,0)`);ctx.fillStyle=g;ctx.beginPath();ctx.arc(this.x,this.y,this.size,0,Math.PI*2);ctx.fill();}}
    function spawnDragon(t){const cx=canvas.width/2,cy=canvas.height/2,sa=t*0.005,sr=t*0.15,x=cx+Math.cos(sa)*sr,y=cy+Math.sin(sa)*sr;for(let i=0;i<5;i++)particles.push(new WP(x+(Math.random()-0.5)*20,y+(Math.random()-0.5)*20,sa+(Math.random()-0.5)*1.5,Math.random()*3+1));}
    function animate(){
        const el=Date.now()-startTime;if(el>duration){ctx.clearRect(0,0,canvas.width,canvas.height);canvas.style.transform='';return;}
        ctx.globalCompositeOperation='source-over';ctx.fillStyle='rgba(0,0,10,0.1)';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.globalCompositeOperation='lighter';
        if(el<duration-800)spawnDragon(el);
        for(let i=particles.length-1;i>=0;i--){particles[i].update();particles[i].draw(ctx);if(particles[i].life<=0)particles.splice(i,1);}
        const ti=Math.min(0.15,el/5000)*Math.max(0,1-(el-duration+800)/800);ctx.globalCompositeOperation='source-over';ctx.fillStyle=`rgba(0,50,150,${ti})`;ctx.fillRect(0,0,canvas.width,canvas.height);
        canvas.style.transform=`translate(${Math.sin(el*0.02)*2*Math.min(1,el/1000)}px,0)`;
        requestAnimationFrame(animate);
    }
    animate();
}
