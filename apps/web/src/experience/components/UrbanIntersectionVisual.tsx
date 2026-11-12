import React, { useEffect, useRef } from 'react';

export const UrbanIntersectionVisual: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let width = (canvas.width = canvas.parentElement?.clientWidth || window.innerWidth);
    let height = (canvas.height = canvas.parentElement?.clientHeight || window.innerHeight);

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = canvas.parentElement?.clientWidth || window.innerWidth;
      height = canvas.height = canvas.parentElement?.clientHeight || window.innerHeight;
    };
    window.addEventListener('resize', handleResize);

    // Simulated traffic particles moving along arterial lanes
    interface Particle {
      x: number;
      y: number;
      speed: number;
      dir: 'NS' | 'SN' | 'EW' | 'WE';
      laneOffset: number;
      color: string;
      length: number;
    }

    const particles: Particle[] = [];
    const NUM_PARTICLES = 18;

    for (let i = 0; i < NUM_PARTICLES; i++) {
      const dirs: ('NS' | 'SN' | 'EW' | 'WE')[] = ['NS', 'SN', 'EW', 'WE'];
      const dir = dirs[Math.floor(Math.random() * dirs.length)];
      particles.push({
        x: Math.random() * width,
        y: Math.random() * height,
        speed: 0.8 + Math.random() * 1.4,
        dir,
        laneOffset: (Math.random() > 0.5 ? 1 : -1) * (18 + Math.random() * 22),
        color: Math.random() > 0.3 ? '#45C982' : '#E9A23B',
        length: 12 + Math.random() * 14,
      });
    }

    let angle = 0;

    const render = () => {
      ctx.clearRect(0, 0, width, height);

      const cx = width / 2;
      const cy = height / 2;
      const roadWidth = Math.min(width, height) * 0.28;

      // 1. Subtle Background Grid (Orthographic Engineering Plane)
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.03)';
      ctx.lineWidth = 1;
      const gridSize = 48;
      for (let x = 0; x < width; x += gridSize) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
      }
      for (let y = 0; y < height; y += gridSize) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
      }

      // 2. Road geometry (Dark charcoal asphalt #111A1D)
      ctx.fillStyle = '#111A1D';
      // Vertical road
      ctx.fillRect(cx - roadWidth / 2, 0, roadWidth, height);
      // Horizontal road
      ctx.fillRect(0, cy - roadWidth / 2, width, roadWidth);

      // Road curbs & lane borders
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.12)';
      ctx.lineWidth = 1.5;
      // Vertical curbs
      ctx.beginPath();
      ctx.moveTo(cx - roadWidth / 2, 0);
      ctx.lineTo(cx - roadWidth / 2, cy - roadWidth / 2);
      ctx.moveTo(cx + roadWidth / 2, 0);
      ctx.lineTo(cx + roadWidth / 2, cy - roadWidth / 2);
      ctx.moveTo(cx - roadWidth / 2, cy + roadWidth / 2);
      ctx.lineTo(cx - roadWidth / 2, height);
      ctx.moveTo(cx + roadWidth / 2, cy + roadWidth / 2);
      ctx.lineTo(cx + roadWidth / 2, height);

      // Horizontal curbs
      ctx.moveTo(0, cy - roadWidth / 2);
      ctx.lineTo(cx - roadWidth / 2, cy - roadWidth / 2);
      ctx.moveTo(0, cy + roadWidth / 2);
      ctx.lineTo(cx - roadWidth / 2, cy + roadWidth / 2);
      ctx.moveTo(cx + roadWidth / 2, cy - roadWidth / 2);
      ctx.lineTo(width, cy - roadWidth / 2);
      ctx.moveTo(cx + roadWidth / 2, cy + roadWidth / 2);
      ctx.lineTo(width, cy + roadWidth / 2);
      ctx.stroke();

      // 3. Lane Dividers (Dashed white/grey)
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.18)';
      ctx.setLineDash([8, 12]);
      ctx.lineWidth = 1;

      // Vertical lane dividers
      ctx.beginPath();
      ctx.moveTo(cx, 0);
      ctx.lineTo(cx, cy - roadWidth / 2);
      ctx.moveTo(cx, cy + roadWidth / 2);
      ctx.lineTo(cx, height);
      // Horizontal lane dividers
      ctx.moveTo(0, cy);
      ctx.lineTo(cx - roadWidth / 2, cy);
      ctx.moveTo(cx + roadWidth / 2, cy);
      ctx.lineTo(width, cy);
      ctx.stroke();
      ctx.setLineDash([]);

      // 4. Stop Lines & Crosswalks
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.28)';
      ctx.lineWidth = 2.5;
      ctx.beginPath();
      // North stop line
      ctx.moveTo(cx - roadWidth / 2, cy - roadWidth / 2 - 8);
      ctx.lineTo(cx + roadWidth / 2, cy - roadWidth / 2 - 8);
      // South stop line
      ctx.moveTo(cx - roadWidth / 2, cy + roadWidth / 2 + 8);
      ctx.lineTo(cx + roadWidth / 2, cy + roadWidth / 2 + 8);
      // West stop line
      ctx.moveTo(cx - roadWidth / 2 - 8, cy - roadWidth / 2);
      ctx.lineTo(cx - roadWidth / 2 - 8, cy + roadWidth / 2);
      // East stop line
      ctx.moveTo(cx + roadWidth / 2 + 8, cy - roadWidth / 2);
      ctx.lineTo(cx + roadWidth / 2 + 8, cy + roadWidth / 2);
      ctx.stroke();

      // 5. Active Roadside Camera FOV Frustums (CAM_J1 - CAM_J4)
      const corners = [
        { x: cx - roadWidth / 2 - 24, y: cy - roadWidth / 2 - 24, label: 'CAM_J1 [NW]', dir: [1, 1] },
        { x: cx + roadWidth / 2 + 24, y: cy - roadWidth / 2 - 24, label: 'CAM_J2 [NE]', dir: [-1, 1] },
        { x: cx + roadWidth / 2 + 24, y: cy + roadWidth / 2 + 24, label: 'CAM_J3 [SE]', dir: [-1, -1] },
        { x: cx - roadWidth / 2 - 24, y: cy + roadWidth / 2 + 24, label: 'CAM_J4 [SW]', dir: [1, -1] },
      ];

      angle += 0.008;

      corners.forEach((cam, idx) => {
        // Camera Pole marker
        ctx.fillStyle = '#45C982';
        ctx.beginPath();
        ctx.arc(cam.x, cam.y, 4, 0, Math.PI * 2);
        ctx.fill();

        // Pulsing radar ring
        const pulse = (Math.sin(angle * 2 + idx) + 1) * 0.5;
        ctx.strokeStyle = `rgba(69, 201, 130, ${0.15 + pulse * 0.25})`;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.arc(cam.x, cam.y, 10 + pulse * 8, 0, Math.PI * 2);
        ctx.stroke();

        // Vision FOV Cone targeting the intersection center
        const coneTargetX = cx + (cam.dir[0] * roadWidth * 0.2);
        const coneTargetY = cy + (cam.dir[1] * roadWidth * 0.2);
        const coneAngle = Math.atan2(coneTargetY - cam.y, coneTargetX - cam.x);
        const fovSpread = 0.45; // ~50 degree field of view
        const coneLength = roadWidth * 1.35;

        const grad = ctx.createRadialGradient(cam.x, cam.y, 10, cam.x, cam.y, coneLength);
        grad.addColorStop(0, 'rgba(69, 201, 130, 0.16)');
        grad.addColorStop(0.7, 'rgba(69, 201, 130, 0.04)');
        grad.addColorStop(1, 'rgba(69, 201, 130, 0.0)');

        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.moveTo(cam.x, cam.y);
        ctx.arc(cam.x, cam.y, coneLength, coneAngle - fovSpread, coneAngle + fovSpread);
        ctx.closePath();
        ctx.fill();

        // Edge scan lines
        ctx.strokeStyle = 'rgba(69, 201, 130, 0.25)';
        ctx.lineWidth = 1;
        ctx.stroke();

        // Label
        ctx.fillStyle = 'rgba(255, 255, 255, 0.65)';
        ctx.font = '10px "IBM Plex Mono", monospace';
        ctx.fillText(cam.label, cam.x - 28, cam.y - 12);
      });

      // 6. Intersection Central Signal Matrix
      const signalPulse = Math.sin(angle * 1.5) > 0;
      ctx.fillStyle = signalPulse ? 'rgba(69, 201, 130, 0.15)' : 'rgba(233, 162, 59, 0.15)';
      ctx.strokeStyle = signalPulse ? '#45C982' : '#E9A23B';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.rect(cx - 16, cy - 16, 32, 32);
      ctx.fill();
      ctx.stroke();

      // 7. Render dynamic traffic particles
      particles.forEach((p) => {
        if (p.dir === 'NS') {
          p.y += p.speed;
          p.x = cx + p.laneOffset;
          if (p.y > height + 20) p.y = -20;
        } else if (p.dir === 'SN') {
          p.y -= p.speed;
          p.x = cx + p.laneOffset;
          if (p.y < -20) p.y = height + 20;
        } else if (p.dir === 'WE') {
          p.x += p.speed;
          p.y = cy + p.laneOffset;
          if (p.x > width + 20) p.x = -20;
        } else if (p.dir === 'EW') {
          p.x -= p.speed;
          p.y = cy + p.laneOffset;
          if (p.x < -20) p.x = width + 20;
        }

        ctx.strokeStyle = p.color;
        ctx.lineWidth = 2.5;
        ctx.beginPath();
        if (p.dir === 'NS' || p.dir === 'SN') {
          const dy = p.dir === 'NS' ? -p.length : p.length;
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(p.x, p.y + dy);
        } else {
          const dx = p.dir === 'WE' ? -p.length : p.length;
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(p.x + dx, p.y);
        }
        ctx.stroke();
      });

      // 8. Dark Vignette Overlays (Soft gradient edges to #080D10)
      const vignette = ctx.createRadialGradient(cx, cy, Math.min(width, height) * 0.35, cx, cy, Math.max(width, height) * 0.75);
      vignette.addColorStop(0, 'rgba(8, 13, 16, 0.0)');
      vignette.addColorStop(0.65, 'rgba(8, 13, 16, 0.65)');
      vignette.addColorStop(1, '#080D10');
      ctx.fillStyle = vignette;
      ctx.fillRect(0, 0, width, height);

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none select-none z-0">
      <canvas ref={canvasRef} className="w-full h-full block opacity-85" />
    </div>
  );
};
