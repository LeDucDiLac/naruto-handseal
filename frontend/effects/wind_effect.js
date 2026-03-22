// Wind Release: Wind Scythe Jutsu effect
function createWindEffect(canvas) {
    const ctx = canvas.getContext('2d'); const startTime = Date.now(); const duration = 2000; const slashes = []; const lines = [];
    class Slash { constructor(){const cx=canvas.width/2,cy=canvas.height/2;this.angle=Math.random()*Math.PI*2;this.sd=20;this.ed=Math.random()*300+200;this.x1=cx+Math.cos(this.angle)*this.sd;this.y1=cy+Math.sin(this.angle)*this.sd;this.x2=cx+Math.cos(this.angle)*this.ed;this.y2=cy+Math.sin(this.angle)*this.ed;this.life=1;this.decay=Math.random()*0.04+0.02;this.thick=Math.random()*4+1;this.prog=0;this.spd=Math.random()*0.08+0.05;} update(){this.prog=Math.min(1,this.prog+this.spd);if(this.prog>=1)this.life-=this.decay;} draw(ctx){if(this.life<=0)return;const px=this.x1+(this.x2-this.x1)*this.prog,py=this.y1+(this.y2-this.y1)*this.prog;ctx.strokeStyle=`rgba(200,255,200,${this.life*0.8})`;ctx.lineWidth=this.thick;ctx.lineCap='round';ctx.beginPath();ctx.moveTo(this.x1,this.y1);ctx.lineTo(px,py);ctx.stroke();ctx.strokeStyle=`rgba(150,255,150,${this.life*0.3})`;ctx.lineWidth=this.thick*4;ctx.beginPath();ctx.moveTo(this.x1,this.y1);ctx.lineTo(px,py);ctx.stroke();}}
    class WLine { constructor(){this.y=Math.random()*canvas.height;this.x=-50;this.speed=Math.random()*15+8;this.len=Math.random()*100+50;this.life=1;this.thick=Math.random()*2+0.5;this.curve=(Math.random()-0.5)*0.02;} update(){this.x+=this.speed;this.y+=Math.sin(this.x*this.curve)*2;if(this.x>canvas.width+50)this.life=0;} draw(ctx){if(this.life<=0)return;ctx.strokeStyle=`rgba(180,255,200,0.4)`;ctx.lineWidth=this.thick;ctx.beginPath();ctx.moveTo(this.x-this.len,this.y);ctx.lineTo(this.x,this.y);ctx.stroke();}}
    let ls=0,lw=0;
    function animate(){
        const el=Date.now()-startTime;if(el>duration){ctx.clearRect(0,0,canvas.width,canvas.height);canvas.style.transform='';return;}
        ctx.globalCompositeOperation='source-over';ctx.fillStyle='rgba(0,0,0,0.2)';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.globalCompositeOperation='lighter';
        if(el-ls>100&&el<duration-500){slashes.push(new Slash());ls=el;}
        if(el-lw>30&&el<duration-300){lines.push(new WLine());lw=el;}
        for(let i=slashes.length-1;i>=0;i--){slashes[i].update();slashes[i].draw(ctx);if(slashes[i].life<=0)slashes.splice(i,1);}
        for(let i=lines.length-1;i>=0;i--){lines[i].update();lines[i].draw(ctx);if(lines[i].life<=0)lines.splice(i,1);}
        const si=Math.min(1,el/500)*Math.max(0,1-(el-duration+500)/500);
        canvas.style.transform=`skewX(${Math.sin(el*0.03)*3*si}deg)`;
        requestAnimationFrame(animate);
    }
    animate();
}
