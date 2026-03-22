// Wind Release: Wind Scythe Jutsu effect
// Swirling slash lines with distortion waves

function createWindEffect(canvas) {
    const ctx = canvas.getContext('2d');
    const startTime = Date.now();
    const duration = 2000;
    const slashes = [];
    const windLines = [];

    class WindSlash {
        constructor() {
            const cx = canvas.width / 2;
            const cy = canvas.height / 2;
            this.angle = Math.random() * Math.PI * 2;
            this.startDist = 20;
            this.endDist = Math.random() * 300 + 200;
            this.x1 = cx + Math.cos(this.angle) * this.startDist;
            this.y1 = cy + Math.sin(this.angle) * this.startDist;
            this.x2 = cx + Math.cos(this.angle) * this.endDist;
            this.y2 = cy + Math.sin(this.angle) * this.endDist;
            this.life = 1.0;
            this.decay = Math.random() * 0.04 + 0.02;
            this.thickness = Math.random() * 4 + 1;
            this.progress = 0;
            this.speed = Math.random() * 0.08 + 0.05;
        }

        update() {
            this.progress = Math.min(1, this.progress + this.speed);
            if (this.progress >= 1) this.life -= this.decay;
        }

        draw(ctx) {
            if (this.life <= 0) return;
            const px = this.x1 + (this.x2 - this.x1) * this.progress;
            const py = this.y1 + (this.y2 - this.y1) * this.progress;

            // Slash line
            ctx.strokeStyle = `rgba(200, 255, 200, ${this.life * 0.8})`;
            ctx.lineWidth = this.thickness;
            ctx.lineCap = 'round';
            ctx.beginPath();
            ctx.moveTo(this.x1, this.y1);
            ctx.lineTo(px, py);
            ctx.stroke();

            // Glow
            ctx.strokeStyle = `rgba(150, 255, 150, ${this.life * 0.3})`;
            ctx.lineWidth = this.thickness * 4;
            ctx.beginPath();
            ctx.moveTo(this.x1, this.y1);
            ctx.lineTo(px, py);
            ctx.stroke();
        }
    }

    class WindLine {
        constructor() {
            this.y = Math.random() * canvas.height;
            this.x = -50;
            this.speed = Math.random() * 15 + 8;
            this.length = Math.random() * 100 + 50;
            this.life = 1.0;
            this.thickness = Math.random() * 2 + 0.5;
            this.curve = (Math.random() - 0.5) * 0.02;
        }

        update() {
            this.x += this.speed;
            this.y += Math.sin(this.x * this.curve) * 2;
            if (this.x > canvas.width + 50) this.life = 0;
        }

        draw(ctx) {
            if (this.life <= 0) return;
            const alpha = Math.min(this.life, 0.4);
            ctx.strokeStyle = `rgba(180, 255, 200, ${alpha})`;
            ctx.lineWidth = this.thickness;
            ctx.beginPath();
            ctx.moveTo(this.x - this.length, this.y + Math.sin((this.x - this.length) * this.curve) * 20);
            for (let i = 0; i < this.length; i += 10) {
                const px = this.x - this.length + i;
                const py = this.y + Math.sin(px * this.curve) * 20;
                ctx.lineTo(px, py);
            }
            ctx.stroke();
        }
    }

    let lastSlash = 0;
    let lastWind = 0;

    function animate() {
        const elapsed = Date.now() - startTime;
        if (elapsed > duration) {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            canvas.style.transform = '';
            return;
        }

        ctx.globalCompositeOperation = 'source-over';
        ctx.fillStyle = 'rgba(0, 0, 0, 0.2)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.globalCompositeOperation = 'lighter';

        // Spawn slashes
        if (elapsed - lastSlash > 100 && elapsed < duration - 500) {
            slashes.push(new WindSlash());
            lastSlash = elapsed;
        }

        // Spawn wind lines
        if (elapsed - lastWind > 30 && elapsed < duration - 300) {
            windLines.push(new WindLine());
            lastWind = elapsed;
        }

        // Update and draw
        for (let i = slashes.length - 1; i >= 0; i--) {
            slashes[i].update();
            slashes[i].draw(ctx);
            if (slashes[i].life <= 0) slashes.splice(i, 1);
        }
        for (let i = windLines.length - 1; i >= 0; i--) {
            windLines[i].update();
            windLines[i].draw(ctx);
            if (windLines[i].life <= 0) windLines.splice(i, 1);
        }

        // Swirl in center
        const swirlIntensity = Math.min(1, elapsed / 500) * Math.max(0, 1 - (elapsed - duration + 500) / 500);
        if (swirlIntensity > 0) {
            ctx.save();
            ctx.translate(canvas.width / 2, canvas.height / 2);
            ctx.rotate(elapsed * 0.003);
            for (let i = 0; i < 6; i++) {
                const a = (i / 6) * Math.PI * 2;
                ctx.strokeStyle = `rgba(180, 255, 200, ${swirlIntensity * 0.2})`;
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.arc(0, 0, 80 + i * 15, a, a + Math.PI * 0.5);
                ctx.stroke();
            }
            ctx.restore();
        }

        // Screen distortion
        const distort = Math.sin(elapsed * 0.03) * 3 * swirlIntensity;
        canvas.style.transform = `skewX(${distort}deg)`;

        requestAnimationFrame(animate);
    }

    animate();
}
