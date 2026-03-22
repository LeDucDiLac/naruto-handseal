// Water Release: Water Dragon Jutsu effect
// Blue particle wave with swirling dragon motion

function createWaterEffect(canvas) {
    const ctx = canvas.getContext('2d');
    const startTime = Date.now();
    const duration = 3500;
    const particles = [];

    class WaterParticle {
        constructor(x, y, angle, speed) {
            this.x = x;
            this.y = y;
            this.vx = Math.cos(angle) * speed;
            this.vy = Math.sin(angle) * speed;
            this.size = Math.random() * 15 + 5;
            this.life = 1.0;
            this.decay = Math.random() * 0.01 + 0.005;
            this.hue = Math.random() * 30 + 190; // Blue range
            this.wobble = Math.random() * Math.PI * 2;
            this.wobbleSpeed = Math.random() * 0.1 + 0.05;
        }

        update() {
            this.wobble += this.wobbleSpeed;
            this.x += this.vx + Math.sin(this.wobble) * 2;
            this.y += this.vy + Math.cos(this.wobble) * 1;
            this.vy += 0.05; // Gravity
            this.life -= this.decay;
            this.size *= 0.995;
        }

        draw(ctx) {
            if (this.life <= 0) return;
            const gradient = ctx.createRadialGradient(
                this.x, this.y, 0,
                this.x, this.y, this.size
            );
            gradient.addColorStop(0, `hsla(${this.hue}, 80%, 70%, ${this.life * 0.7})`);
            gradient.addColorStop(0.5, `hsla(${this.hue}, 90%, 50%, ${this.life * 0.4})`);
            gradient.addColorStop(1, `hsla(${this.hue + 20}, 80%, 30%, 0)`);
            ctx.fillStyle = gradient;
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    function spawnDragonSegment(t) {
        // Dragon spirals from center outward
        const cx = canvas.width / 2;
        const cy = canvas.height / 2;
        const spiralAngle = t * 0.005;
        const spiralRadius = t * 0.15;
        const x = cx + Math.cos(spiralAngle) * spiralRadius;
        const y = cy + Math.sin(spiralAngle) * spiralRadius;

        for (let i = 0; i < 5; i++) {
            const angle = spiralAngle + (Math.random() - 0.5) * 1.5;
            const speed = Math.random() * 3 + 1;
            particles.push(new WaterParticle(
                x + (Math.random() - 0.5) * 20,
                y + (Math.random() - 0.5) * 20,
                angle, speed
            ));
        }
    }

    function animate() {
        const elapsed = Date.now() - startTime;
        if (elapsed > duration) {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            canvas.style.transform = '';
            return;
        }

        ctx.globalCompositeOperation = 'source-over';
        ctx.fillStyle = 'rgba(0, 0, 10, 0.1)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.globalCompositeOperation = 'lighter';

        // Spawn dragon particles
        if (elapsed < duration - 800) {
            spawnDragonSegment(elapsed);
        }

        // Splash particles from edges
        if (elapsed > 500 && elapsed < 2500) {
            for (let i = 0; i < 2; i++) {
                const edge = Math.floor(Math.random() * 4);
                let x, y, angle;
                switch (edge) {
                    case 0: x = Math.random() * canvas.width; y = 0; angle = Math.PI / 2; break;
                    case 1: x = canvas.width; y = Math.random() * canvas.height; angle = Math.PI; break;
                    case 2: x = Math.random() * canvas.width; y = canvas.height; angle = -Math.PI / 2; break;
                    default: x = 0; y = Math.random() * canvas.height; angle = 0; break;
                }
                particles.push(new WaterParticle(x, y, angle + (Math.random() - 0.5) * 0.5, Math.random() * 4 + 2));
            }
        }

        // Update and draw particles
        for (let i = particles.length - 1; i >= 0; i--) {
            particles[i].update();
            particles[i].draw(ctx);
            if (particles[i].life <= 0) particles.splice(i, 1);
        }

        // Water overlay tint
        const tintIntensity = Math.min(0.15, elapsed / 5000) * Math.max(0, 1 - (elapsed - duration + 800) / 800);
        ctx.globalCompositeOperation = 'source-over';
        ctx.fillStyle = `rgba(0, 50, 150, ${tintIntensity})`;
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Subtle ripple shake
        const ripple = Math.sin(elapsed * 0.02) * 2 * Math.min(1, elapsed / 1000);
        canvas.style.transform = `translate(${ripple}px, ${ripple * 0.5}px)`;

        requestAnimationFrame(animate);
    }

    animate();
}
