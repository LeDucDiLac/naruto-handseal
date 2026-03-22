// Shadow Clone Jutsu effect
// Smoke poof animation with afterimage duplicates

function createCloneEffect(canvas) {
    const ctx = canvas.getContext('2d');
    const startTime = Date.now();
    const duration = 2500;
    const smokeParticles = [];

    class SmokeParticle {
        constructor(x, y, isClone) {
            this.x = x;
            this.y = y;
            this.vx = (Math.random() - 0.5) * 6;
            this.vy = (Math.random() - 0.5) * 6 - 2;
            this.size = Math.random() * 40 + 20;
            this.maxSize = this.size * 3;
            this.life = 1.0;
            this.decay = Math.random() * 0.015 + 0.008;
            this.rotation = Math.random() * Math.PI * 2;
            this.rotSpeed = (Math.random() - 0.5) * 0.1;
            this.isClone = isClone;
        }

        update() {
            this.x += this.vx;
            this.y += this.vy;
            this.vy -= 0.02;
            this.vx *= 0.98;
            this.life -= this.decay;
            this.size = Math.min(this.maxSize, this.size + 1);
            this.rotation += this.rotSpeed;
        }

        draw(ctx) {
            if (this.life <= 0) return;

            ctx.save();
            ctx.translate(this.x, this.y);
            ctx.rotate(this.rotation);

            const gradient = ctx.createRadialGradient(0, 0, 0, 0, 0, this.size);
            if (this.isClone) {
                gradient.addColorStop(0, `rgba(200, 200, 255, ${this.life * 0.6})`);
                gradient.addColorStop(0.5, `rgba(150, 150, 200, ${this.life * 0.3})`);
                gradient.addColorStop(1, `rgba(100, 100, 150, 0)`);
            } else {
                gradient.addColorStop(0, `rgba(220, 220, 220, ${this.life * 0.5})`);
                gradient.addColorStop(0.5, `rgba(180, 180, 180, ${this.life * 0.3})`);
                gradient.addColorStop(1, `rgba(150, 150, 150, 0)`);
            }

            ctx.fillStyle = gradient;
            ctx.beginPath();
            ctx.arc(0, 0, this.size, 0, Math.PI * 2);
            ctx.fill();
            ctx.restore();
        }
    }

    // Create clone positions (like shadow clones appearing)
    const clonePositions = [];
    const numClones = 4;
    for (let i = 0; i < numClones; i++) {
        const angle = (i / numClones) * Math.PI * 2 + Math.PI / 4;
        clonePositions.push({
            x: canvas.width / 2 + Math.cos(angle) * 180,
            y: canvas.height / 2 + Math.sin(angle) * 120,
            spawnTime: 300 + i * 150,
            alpha: 0,
        });
    }

    function animate() {
        const elapsed = Date.now() - startTime;
        if (elapsed > duration) {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            return;
        }

        ctx.globalCompositeOperation = 'source-over';
        ctx.fillStyle = 'rgba(0, 0, 0, 0.12)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Initial poof at center
        if (elapsed < 600) {
            for (let i = 0; i < 5; i++) {
                smokeParticles.push(new SmokeParticle(
                    canvas.width / 2 + (Math.random() - 0.5) * 40,
                    canvas.height / 2 + (Math.random() - 0.5) * 40,
                    false
                ));
            }
        }

        // Clone appearance poofs
        for (const clone of clonePositions) {
            if (elapsed > clone.spawnTime && elapsed < clone.spawnTime + 400) {
                for (let i = 0; i < 3; i++) {
                    smokeParticles.push(new SmokeParticle(
                        clone.x + (Math.random() - 0.5) * 30,
                        clone.y + (Math.random() - 0.5) * 30,
                        true
                    ));
                }
            }

            // Draw clone silhouette
            if (elapsed > clone.spawnTime + 200) {
                const fadeIn = Math.min(1, (elapsed - clone.spawnTime - 200) / 400);
                const fadeOut = elapsed > duration - 600 
                    ? Math.max(0, 1 - (elapsed - (duration - 600)) / 600) 
                    : 1;
                clone.alpha = fadeIn * fadeOut;

                ctx.save();
                ctx.globalAlpha = clone.alpha * 0.6;

                // Draw simple clone figure
                const gradient = ctx.createRadialGradient(
                    clone.x, clone.y, 0,
                    clone.x, clone.y, 60
                );
                gradient.addColorStop(0, 'rgba(100, 150, 255, 0.5)');
                gradient.addColorStop(0.7, 'rgba(50, 100, 200, 0.3)');
                gradient.addColorStop(1, 'rgba(30, 60, 150, 0)');
                ctx.fillStyle = gradient;
                ctx.fillRect(clone.x - 60, clone.y - 80, 120, 160);

                ctx.restore();
            }
        }

        // Update and draw smoke
        for (let i = smokeParticles.length - 1; i >= 0; i--) {
            smokeParticles[i].update();
            smokeParticles[i].draw(ctx);
            if (smokeParticles[i].life <= 0) smokeParticles.splice(i, 1);
        }

        // "Poof!" text
        if (elapsed < 1000 && elapsed > 100) {
            const textAlpha = Math.min(1, (elapsed - 100) / 200) * Math.max(0, 1 - (elapsed - 600) / 400);
            ctx.save();
            ctx.globalAlpha = textAlpha;
            ctx.font = 'bold 48px "Outfit", sans-serif';
            ctx.textAlign = 'center';
            ctx.fillStyle = '#fff';
            ctx.shadowColor = 'rgba(100, 150, 255, 0.8)';
            ctx.shadowBlur = 20;
            ctx.fillText('POOF!', canvas.width / 2, canvas.height / 2 - 80);
            ctx.restore();
        }

        requestAnimationFrame(animate);
    }

    animate();
}
