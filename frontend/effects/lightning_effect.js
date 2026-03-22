// Chidori / Lightning Release effect
function createLightningEffect(canvas) {
    const ctx = canvas.getContext('2d'); const startTime = Date.now(); const duration = 2500; const bolts = [];
    class LightningBolt {
        constructor(x1, y1, x2, y2, gen) { this.points = []; this.life = 1.0; this.decay = Math.random()*0.03+0.02; this.thickness = Math.random()*3+1; this._gen(x1,y1,x2,y2,gen); }
        _gen(x1,y1,x2,y2,g) { if(g<=0){this.points.push({x:x1,y:y1},{x:x2,y:y2});return;} const mx=(x1+x2)/2+(Math.random()-0.5)*Math.abs(x2-x1)*0.4, my=(y1+y2)/2+(Math.random()-0.5)*Math.abs(y2-y1)*0.4; this._gen(x1,y1,mx,my,g-1); this._gen(mx,my,x2,y2,g-1); }
        update(){this.life-=this.decay;}
        draw(ctx){ if(this.life<=0||this.points.length<2)return; [['rgba(100,180,255,'+this.life*0.3+')',this.thickness*6],['rgba(200,230,255,'+this.life+')',this.thickness],['rgba(255,255,255,'+this.life*0.8+')',this.thickness*0.4]].forEach(([c,w])=>{ ctx.strokeStyle=c;ctx.lineWidth=w;ctx.lineCap='round';ctx.lineJoin='round';ctx.beginPath();ctx.moveTo(this.points[0].x,this.points[0].y);for(let i=1;i<this.points.length;i++)ctx.lineTo(this.points[i].x,this.points[i].y);ctx.stroke();}); }
    }
    function spawn(){const cx=canvas.width/2,cy=canvas.height/2;for(let i=0;i<3;i++){const a=Math.random()*Math.PI*2,d=Math.random()*300+100;bolts.push(new LightningBolt(cx+(Math.random()-0.5)*60,cy+(Math.random()-0.5)*60,cx+Math.cos(a)*d,cy+Math.sin(a)*d,5));}}
    let lastSpawn=0;
    function animate(){
        const elapsed=Date.now()-startTime; if(elapsed>duration){ctx.clearRect(0,0,canvas.width,canvas.height);canvas.style.transform='';return;}
        ctx.globalCompositeOperation='source-over';ctx.fillStyle='rgba(0,0,0,0.3)';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.globalCompositeOperation='lighter';
        if(elapsed-lastSpawn>80&&elapsed<duration-500){spawn();lastSpawn=elapsed;}
        if(elapsed<200){ctx.globalCompositeOperation='source-over';ctx.fillStyle=`rgba(150,200,255,${(1-elapsed/200)*0.8})`;ctx.fillRect(0,0,canvas.width,canvas.height);ctx.globalCompositeOperation='lighter';}
        for(let i=bolts.length-1;i>=0;i--){bolts[i].update();bolts[i].draw(ctx);if(bolts[i].life<=0)bolts.splice(i,1);}
        const gp=Math.sin(elapsed*0.01)*0.3+0.7,glow=ctx.createRadialGradient(canvas.width/2,canvas.height/2,0,canvas.width/2,canvas.height/2,120);
        glow.addColorStop(0,`rgba(150,220,255,${0.4*gp})`);glow.addColorStop(0.5,`rgba(50,100,255,${0.2*gp})`);glow.addColorStop(1,'rgba(0,0,100,0)');ctx.fillStyle=glow;ctx.fillRect(0,0,canvas.width,canvas.height);
        const si=Math.min(1,elapsed/300)*Math.max(0,1-(elapsed-duration+500)/500);canvas.style.transform=`translate(${(Math.random()-0.5)*6*si}px,${(Math.random()-0.5)*6*si}px)`;
        requestAnimationFrame(animate);
    }
    animate();
}
