// Chidori / Lightning Release effect
// Jagged lightning bolts with electric blue glow and screen flash

function createLightningEffect(canvas) {
    const ctx = canvas.getContext('2d');
    const startTime = Date.now();
    const duration = 2500;
    const bolts = [];

    class LightningBolt {
        constructor(x1, y1, x2, y2, generations) {
            this.points = [];
            this.life = 1.0;
            this.decay = Math.random() * 0.03 + 0.02;
            this.thickness = Math.random() * 3 + 1;
            this._generate(x1, y1, x2, y2, generations);
        }

        _generate(x1, y1, x2, y2, gen) {
            if (gen <= 0) {
                this.points.push({ x: x1, y: y1 });
                this.points.push({ x: x2, y: y2 });
                return;
            }
            const midX = (x1 + x2) / 2 + (Math.random() - 0.5) * Math.abs(x2 - x1) * 0.4;
            const midY = (y1 + y2) / 2 + (Math.random() - 0.5) * Math.abs(y2 - y1) * 0.4;
            this._generate(x1, y1, midX, midY, gen - 1);
            this._generate(midX, midY, x2, y2, gen - 1);
        }

        update() { this.life -= this.decay; }

        draw(ctx) {
            if (this.life <= 0 || this.points.length < 2) return;

            // Glow layer
            ctx.strokeStyle = `rgba(100, 180, 255, ${this.life * 0.3})`;
            ctx.lineWidth = this.thickness * 6;
            ctx.lineCap = 'round';
            ctx.lineJoin = 'round';
            ctx.beginPath();
            ctx.moveTo(this.points[0].x, this.points[0].y);
            for (let i = 1; i < this.points.length; i++) {
                ctx.lineTo(this.points[i].x, this.points[i].y);
            }
            ctx.stroke();

            // Core bolt
            ctx.strokeStyle = `rgba(200, 230, 255, ${this.life})`;
            ctx.lineWidth = this.thickness;
            ctx.beginPath();
            ctx.moveTo(this.points[0].x, this.points[0].y);
            for (let i = 1; i < this.points.length; i++) {
                ctx.lineTo(this.points[i].x, this.points[i].y);
            }
            ctx.stroke();

            // White core
            ctx.strokeStyle = `rgba(255, 255, 255, ${this.life * 0.8})`;
            ctx.lineWidth = this.thickness * 0.4;
            ctx.beginPath();
            ctx.moveTo(this.points[0].x, this.points[0].y);
            for (let i = 1; i < this.points.length; i++) {
                ctx.lineTo(this.points[i].x, this.points[i].y);
            }
            ctx.stroke();
        }
    }

    function spawnBolts() {
        const cx = canvas.width / 2;
        const cy = canvas.height / 2;
        for (let i = 0; i < 3; i++) {
            const angle = Math.random() * Math.PI * 2;
            const dist = Math.random() * 300 + 100;
            bolts.push(new LightningBolt(
                cx + (Math.random() - 0.5) * 60,
                cy + (Math.random() - 0.5) * 60,
                cx + Math.cos(angle) * dist,
                cy + Math.sin(angle) * dist,
                5
            ));
        }
    }

    let lastSpawn = 0;

    function animate() {
        const elapsed = Date.now() - startTime;
        if (elapsed > duration) {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            canvas.style.transform = '';
            return;
        }

        ctx.globalCompositeOperation = 'source-over';
        ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.globalCompositeOperation = 'lighter';

        // Spawn bolts periodically
        if (elapsed - lastSpawn > 80 && elapsed < duration - 500) {
            spawnBolts();
            lastSpawn = elapsed;
        }

        // Flash effect at start
        if (elapsed < 200) {
            const flashIntensity = (1 - elapsed / 200) * 0.8;
            ctx.globalCompositeOperation = 'source-over';
            ctx.fillStyle = `rgba(150, 200, 255, ${flashIntensity})`;
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.globalCompositeOperation = 'lighter';
        }

        // Update and draw bolts
        for (let i = bolts.length - 1; i >= 0; i--) {
            bolts[i].update();
            bolts[i].draw(ctx);
            if (bolts[i].life <= 0) bolts.splice(i, 1);
        }

        // Center glow (chakra concentration)
        const glowPhase = Math.sin(elapsed * 0.01) * 0.3 + 0.7;
        const glow = ctx.createRadialGradient(
            canvas.width / 2, canvas.height / 2, 0,
            canvas.width / 2, canvas.height / 2, 120
        );
        glow.addColorStop(0, `rgba(150, 220, 255, ${0.4 * glowPhase})`);
        glow.addColorStop(0.5, `rgba(50, 100, 255, ${0.2 * glowPhase})`);
        glow.addColorStop(1, 'rgba(0, 0, 100, 0)');
        ctx.fillStyle = glow;
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Screen shake
        const shakeIntensity = Math.min(1, elapsed / 300) * Math.max(0, 1 - (elapsed - duration + 500) / 500);
        const shake = (Math.random() - 0.5) * 6 * shakeIntensity;
        canvas.style.transform = `translate(${shake}px, ${shake}px)`;

        requestAnimationFrame(animate);
    }

    animate();
}
