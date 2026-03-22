// Shadow Clone Jutsu effect
function createCloneEffect(canvas) {
    const ctx = canvas.getContext('2d'); const startTime = Date.now(); const duration = 2500; const smoke = [];
    class Smoke { constructor(x,y,isC){this.x=x;this.y=y;this.vx=(Math.random()-0.5)*6;this.vy=(Math.random()-0.5)*6-2;this.size=Math.random()*40+20;this.maxSize=this.size*3;this.life=1;this.decay=Math.random()*0.015+0.008;this.isC=isC;} update(){this.x+=this.vx;this.y+=this.vy;this.vy-=0.02;this.vx*=0.98;this.life-=this.decay;this.size=Math.min(this.maxSize,this.size+1);} draw(ctx){if(this.life<=0)return;const g=ctx.createRadialGradient(this.x,this.y,0,this.x,this.y,this.size);const c=this.isC?[200,200,255]:[220,220,220];g.addColorStop(0,`rgba(${c},${this.life*0.5})`);g.addColorStop(1,`rgba(${c},0)`);ctx.fillStyle=g;ctx.beginPath();ctx.arc(this.x,this.y,this.size,0,Math.PI*2);ctx.fill();}}
    const clones=[];for(let i=0;i<4;i++){const a=(i/4)*Math.PI*2+Math.PI/4;clones.push({x:canvas.width/2+Math.cos(a)*180,y:canvas.height/2+Math.sin(a)*120,t:300+i*150,alpha:0});}
    function animate(){
        const el=Date.now()-startTime;if(el>duration){ctx.clearRect(0,0,canvas.width,canvas.height);return;}
        ctx.globalCompositeOperation='source-over';ctx.fillStyle='rgba(0,0,0,0.12)';ctx.fillRect(0,0,canvas.width,canvas.height);
        if(el<600)for(let i=0;i<5;i++)smoke.push(new Smoke(canvas.width/2+(Math.random()-0.5)*40,canvas.height/2+(Math.random()-0.5)*40,false));
        for(const c of clones){if(el>c.t&&el<c.t+400)for(let i=0;i<3;i++)smoke.push(new Smoke(c.x+(Math.random()-0.5)*30,c.y+(Math.random()-0.5)*30,true));
        if(el>c.t+200){const fi=Math.min(1,(el-c.t-200)/400),fo=el>duration-600?Math.max(0,1-(el-(duration-600))/600):1;c.alpha=fi*fo;ctx.save();ctx.globalAlpha=c.alpha*0.6;const g=ctx.createRadialGradient(c.x,c.y,0,c.x,c.y,60);g.addColorStop(0,'rgba(100,150,255,0.5)');g.addColorStop(1,'rgba(30,60,150,0)');ctx.fillStyle=g;ctx.fillRect(c.x-60,c.y-80,120,160);ctx.restore();}}
        for(let i=smoke.length-1;i>=0;i--){smoke[i].update();smoke[i].draw(ctx);if(smoke[i].life<=0)smoke.splice(i,1);}
        if(el<1000&&el>100){const ta=Math.min(1,(el-100)/200)*Math.max(0,1-(el-600)/400);ctx.save();ctx.globalAlpha=ta;ctx.font='bold 48px "Outfit",sans-serif';ctx.textAlign='center';ctx.fillStyle='#fff';ctx.shadowColor='rgba(100,150,255,0.8)';ctx.shadowBlur=20;ctx.fillText('POOF!',canvas.width/2,canvas.height/2-80);ctx.restore();}
        requestAnimationFrame(animate);
    }
    animate();
}
