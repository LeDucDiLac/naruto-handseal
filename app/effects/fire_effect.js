// Fire Release: Great Fireball Jutsu effect
// Particle-based fireball expanding from center with glow blending

function createFireEffect(canvas) {
    const ctx = canvas.getContext('2d');
    const particles = [];
    const startTime = Date.now();
    const duration = 3000; // 3 seconds

    class FireParticle {
        constructor(x, y) {
            this.x = x;
            this.y = y;
            this.vx = (Math.random() - 0.5) * 8;
            this.vy = (Math.random() - 0.5) * 8 - 4;
            this.size = Math.random() * 30 + 10;
            this.life = 1.0;
            this.decay = Math.random() * 0.02 + 0.01;
            this.hue = Math.random() * 40 + 10; // Orange to red
        }

        update() {
            this.x += this.vx;
            this.y += this.vy;
            this.vy -= 0.1; // Rise upward
            this.life -= this.decay;
            this.size *= 0.99;
            this.vx *= 0.99;
        }

        draw(ctx) {
            if (this.life <= 0) return;
            const gradient = ctx.createRadialGradient(
                this.x, this.y, 0,
                this.x, this.y, this.size
            );
            gradient.addColorStop(0, `hsla(${this.hue}, 100%, 70%, ${this.life})`);
            gradient.addColorStop(0.4, `hsla(${this.hue - 10}, 100%, 50%, ${this.life * 0.8})`);
            gradient.addColorStop(1, `hsla(${this.hue - 20}, 100%, 30%, 0)`);
            ctx.fillStyle = gradient;
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    function animate() {
        const elapsed = Date.now() - startTime;
        if (elapsed > duration) {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            return;
        }

        ctx.globalCompositeOperation = 'source-over';
        ctx.fillStyle = 'rgba(0, 0, 0, 0.15)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.globalCompositeOperation = 'lighter';

        // Spawn phase (first 1.5 seconds)
        if (elapsed < 1500) {
            const intensity = Math.min(1, elapsed / 500);
            const spawnCount = Math.floor(15 * intensity);
            for (let i = 0; i < spawnCount; i++) {
                const cx = canvas.width / 2;
                const cy = canvas.height / 2;
                const angle = Math.random() * Math.PI * 2;
                const dist = Math.random() * 50 * intensity;
                particles.push(new FireParticle(
                    cx + Math.cos(angle) * dist,
                    cy + Math.sin(angle) * dist
                ));
            }
        }

        // Update and draw
        for (let i = particles.length - 1; i >= 0; i--) {
            particles[i].update();
            particles[i].draw(ctx);
            if (particles[i].life <= 0) particles.splice(i, 1);
        }

        // Central glow
        if (elapsed < 2000) {
            const glowIntensity = Math.min(1, elapsed / 800) * Math.max(0, 1 - (elapsed - 1500) / 500);
            if (glowIntensity > 0) {
                const glow = ctx.createRadialGradient(
                    canvas.width / 2, canvas.height / 2, 0,
                    canvas.width / 2, canvas.height / 2, 150
                );
                glow.addColorStop(0, `rgba(255, 200, 50, ${glowIntensity * 0.6})`);
                glow.addColorStop(0.5, `rgba(255, 100, 0, ${glowIntensity * 0.3})`);
                glow.addColorStop(1, 'rgba(255, 0, 0, 0)');
                ctx.fillStyle = glow;
                ctx.fillRect(0, 0, canvas.width, canvas.height);
            }
        }

        // Screen shake
        if (elapsed < 500) {
            const shake = Math.sin(elapsed * 0.5) * 5 * (1 - elapsed / 500);
            canvas.style.transform = `translate(${shake}px, ${shake * 0.5}px)`;
        } else {
            canvas.style.transform = '';
        }

        requestAnimationFrame(animate);
    }

    animate();
}
