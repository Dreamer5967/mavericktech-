import React, { useEffect, useRef, useState } from 'react';
import { Play, Pause, Eye, Radar, Layers, Activity, ShieldCheck } from 'lucide-react';

interface Vehicle {
  id: number;
  type: 'car' | 'bus' | 'truck' | 'autonomous';
  x: number;
  y: number;
  speed: number;
  maxSpeed: number;
  dir: 'E' | 'W' | 'S' | 'N';
  color: string;
  length: number;
  width: number;
  height: number;
  braking: boolean;
  label: string;
  conf: number;
}

export const UrbanDigitalTwinVisual: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  // User interactive state toggles
  const [isPlaying, setIsPlaying] = useState<boolean>(true);
  const [showBoundingBoxes, setShowBoundingBoxes] = useState<boolean>(true);
  const [showRadarCones, setShowRadarCones] = useState<boolean>(true);
  const [trafficDensity, setTrafficDensity] = useState<'nominal' | 'rush'>('nominal');
  const [simTime, setSimTime] = useState<number>(0);
  const [activeVehiclesCount, setActiveVehiclesCount] = useState<number>(0);
  const [currentPhase, setCurrentPhase] = useState<'NS_GREEN' | 'EW_GREEN' | 'ALL_YELLOW'>('NS_GREEN');

  // References for animation loop
  const stateRef = useRef({
    isPlaying: true,
    showBoundingBoxes: true,
    showRadarCones: true,
    trafficDensity: 'nominal' as 'nominal' | 'rush',
  });

  // Keep stateRef synced
  useEffect(() => {
    stateRef.current.isPlaying = isPlaying;
    stateRef.current.showBoundingBoxes = showBoundingBoxes;
    stateRef.current.showRadarCones = showRadarCones;
    stateRef.current.trafficDensity = trafficDensity;
  }, [isPlaying, showBoundingBoxes, showRadarCones, trafficDensity]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d', { alpha: false });
    if (!ctx) return;

    let animId: number;
    let width = 0;
    let height = 0;

    // Handle high DPI display
    const handleResize = () => {
      if (!containerRef.current || !canvas) return;
      const rect = containerRef.current.getBoundingClientRect();
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = rect.width;
      height = Math.max(rect.width * 0.54, 460); // 16:9 proportional aspect ratio
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      ctx.scale(dpr, dpr);
    };

    handleResize();
    window.addEventListener('resize', handleResize);

    // Isometric 3D Projection Engine
    const cosAngle = Math.cos(Math.PI / 6); // cos(30 deg) ≈ 0.866
    const sinAngle = Math.sin(Math.PI / 6); // sin(30 deg) = 0.5

    function toIso(x: number, y: number, z: number, scale: number, originX: number, originY: number) {
      return {
        x: originX + (x - y) * cosAngle * scale,
        y: originY + (x + y) * sinAngle * scale - z * scale,
      };
    }

    // Static 3D City Buildings Definition
    interface Building {
      x: number;
      y: number;
      w: number;
      d: number;
      h: number;
      colorTop: string;
      colorLeft: string;
      colorRight: string;
      windows: boolean;
      windowColor?: string;
      roofType?: 'helipad' | 'antenna' | 'hvac';
    }

    const buildings: Building[] = [
      // North-West District (x: -260 to -50, y: -260 to -50)
      { x: -220, y: -210, w: 70, d: 65, h: 140, colorTop: '#1E282D', colorLeft: '#141D21', colorRight: '#0E1518', windows: true, windowColor: '#45C982', roofType: 'helipad' },
      { x: -130, y: -210, w: 60, d: 55, h: 95, colorTop: '#1A2327', colorLeft: '#12191C', colorRight: '#0B1012', windows: true, windowColor: '#E9A23B', roofType: 'hvac' },
      { x: -220, y: -130, w: 65, d: 65, h: 110, colorTop: '#1B2429', colorLeft: '#131A1D', colorRight: '#0C1114', windows: true, roofType: 'antenna' },
      { x: -135, y: -135, w: 75, d: 75, h: 165, colorTop: '#222D33', colorLeft: '#172024', colorRight: '#10171A', windows: true, windowColor: '#45C982', roofType: 'helipad' },

      // North-East District (x: 55 to 260, y: -260 to -50)
      { x: 65, y: -220, w: 80, d: 65, h: 130, colorTop: '#1F292F', colorLeft: '#151E22', colorRight: '#0E1619', windows: true, roofType: 'hvac' },
      { x: 160, y: -220, w: 65, d: 70, h: 105, colorTop: '#1A2328', colorLeft: '#121A1D', colorRight: '#0C1215', windows: true, roofType: 'antenna' },
      { x: 65, y: -135, w: 70, d: 75, h: 180, colorTop: '#243036', colorLeft: '#192328', colorRight: '#11191D', windows: true, windowColor: '#45C982', roofType: 'helipad' },
      { x: 155, y: -130, w: 75, d: 65, h: 90, colorTop: '#1B2429', colorLeft: '#131A1E', colorRight: '#0D1215', windows: true, roofType: 'hvac' },

      // South-West District (x: -260 to -50, y: 55 to 260)
      { x: -220, y: 65, w: 70, d: 75, h: 115, colorTop: '#1E282D', colorLeft: '#141D21', colorRight: '#0E1518', windows: true, roofType: 'antenna' },
      { x: -130, y: 65, w: 70, d: 70, h: 150, colorTop: '#212C32', colorLeft: '#161F24', colorRight: '#10171B', windows: true, windowColor: '#E9A23B', roofType: 'hvac' },
      { x: -220, y: 160, w: 75, d: 65, h: 85, colorTop: '#1A2328', colorLeft: '#12191C', colorRight: '#0C1113', windows: true, roofType: 'hvac' },
      { x: -130, y: 155, w: 65, d: 70, h: 125, colorTop: '#1E292E', colorLeft: '#151E22', colorRight: '#0E1619', windows: true, windowColor: '#45C982', roofType: 'helipad' },

      // South-East District (x: 55 to 260, y: 55 to 260)
      { x: 65, y: 65, w: 80, d: 80, h: 195, colorTop: '#253239', colorLeft: '#1A242A', colorRight: '#121B1F', windows: true, windowColor: '#45C982', roofType: 'antenna' },
      { x: 165, y: 65, w: 65, d: 70, h: 100, colorTop: '#1A2328', colorLeft: '#121A1D', colorRight: '#0C1215', windows: true, roofType: 'hvac' },
      { x: 65, y: 165, w: 75, d: 65, h: 120, colorTop: '#1E282D', colorLeft: '#141D21', colorRight: '#0E1518', windows: true, windowColor: '#E9A23B', roofType: 'hvac' },
      { x: 160, y: 155, w: 70, d: 75, h: 140, colorTop: '#202B31', colorLeft: '#162025', colorRight: '#10171B', windows: true, roofType: 'helipad' },
    ];

    // Camera Sensor Masts at the 4 intersection corners
    const cameraSensors = [
      { id: 'CAM_J1', x: -44, y: -44, targetAngle: Math.PI * 0.25, label: 'J1 / North Approach' },
      { id: 'CAM_J2', x: 44, y: -44, targetAngle: Math.PI * 0.75, label: 'J2 / East Approach' },
      { id: 'CAM_J3', x: 44, y: 44, targetAngle: Math.PI * 1.25, label: 'J3 / South Approach' },
      { id: 'CAM_J4', x: -44, y: 44, targetAngle: Math.PI * 1.75, label: 'J4 / West Approach' },
    ];

    // Vehicles Collection
    const vehicles: Vehicle[] = [];
    let vehicleIdCounter = 1;

    const vehicleColors = ['#F1EFE8', '#738088', '#45C982', '#00D1FF', '#E9A23B', '#3B82F6', '#D4D4D8'];

    const spawnVehicle = (dir: 'E' | 'W' | 'S' | 'N'): Vehicle => {
      const typeRand = Math.random();
      let type: Vehicle['type'] = 'car';
      let len = 18;
      let wid = 9;
      let hei = 8;
      let maxSpd = 1.3 + Math.random() * 0.5;
      let label = 'CAR';
      let conf = 0.94 + Math.random() * 0.05;

      if (typeRand < 0.15) {
        type = 'autonomous';
        label = 'AEGIS-AV';
        conf = 0.99;
      } else if (typeRand < 0.3) {
        type = 'bus';
        len = 34;
        wid = 11;
        hei = 13;
        maxSpd = 0.95;
        label = 'BUS';
        conf = 0.97;
      } else if (typeRand < 0.45) {
        type = 'truck';
        len = 28;
        wid = 11;
        hei = 14;
        maxSpd = 1.05;
        label = 'TRUCK';
        conf = 0.95;
      }

      const color = type === 'autonomous' ? '#45C982' : vehicleColors[Math.floor(Math.random() * vehicleColors.length)];

      let x = 0;
      let y = 0;
      const roadBound = 320;

      // Lane offsets: road is from -40 to 40. Outer lane is +/- 24, Inner lane is +/- 10
      const laneOffset = Math.random() > 0.5 ? 20 : 8;

      if (dir === 'E') {
        x = -roadBound - Math.random() * 60;
        y = laneOffset;
      } else if (dir === 'W') {
        x = roadBound + Math.random() * 60;
        y = -laneOffset;
      } else if (dir === 'S') {
        x = -laneOffset;
        y = -roadBound - Math.random() * 60;
      } else if (dir === 'N') {
        x = laneOffset;
        y = roadBound + Math.random() * 60;
      }

      return {
        id: vehicleIdCounter++,
        type,
        x,
        y,
        speed: maxSpd,
        maxSpeed: maxSpd,
        dir,
        color,
        length: len,
        width: wid,
        height: hei,
        braking: false,
        label,
        conf,
      };
    };

    // Populate initial vehicle set
    const directions: ('E' | 'W' | 'S' | 'N')[] = ['E', 'W', 'S', 'N'];
    const initialCount = 20;
    for (let i = 0; i < initialCount; i++) {
      const dir = directions[i % 4];
      const v = spawnVehicle(dir);
      // Scatter vehicles naturally along the road
      const advance = Math.random() * 500;
      if (dir === 'E') v.x += advance;
      else if (dir === 'W') v.x -= advance;
      else if (dir === 'S') v.y += advance;
      else if (dir === 'N') v.y -= advance;
      vehicles.push(v);
    }

    // Traffic Light Cycle Clock
    let cycleTime = 0;
    const CYCLE_DURATION = 14; // seconds

    let radarSweepAngle = 0;
    let tickCount = 0;

    // Main Render / Physics Loop
    let lastTimestamp = performance.now();

    const render = (now: number) => {
      const dt = Math.min((now - lastTimestamp) / 1000, 0.1);
      lastTimestamp = now;

      if (stateRef.current.isPlaying) {
        cycleTime = (cycleTime + dt) % CYCLE_DURATION;
        radarSweepAngle += dt * 2.2;
        tickCount += dt;
      }

      // Determine Traffic Light Phase:
      // 0 - 5.5s: NS Green, EW Red
      // 5.5 - 7.0s: NS Yellow, EW Red
      // 7.0 - 12.5s: EW Green, NS Red
      // 12.5 - 14.0s: EW Yellow, NS Red
      let nsState: 'GREEN' | 'YELLOW' | 'RED' = 'RED';
      let ewState: 'GREEN' | 'YELLOW' | 'RED' = 'RED';

      if (cycleTime < 5.5) {
        nsState = 'GREEN';
        ewState = 'RED';
      } else if (cycleTime < 7.0) {
        nsState = 'YELLOW';
        ewState = 'RED';
      } else if (cycleTime < 12.5) {
        nsState = 'RED';
        ewState = 'GREEN';
      } else {
        nsState = 'RED';
        ewState = 'YELLOW';
      }

      // Sync React state throttled
      if (Math.floor(now / 200) !== Math.floor((now - dt * 1000) / 200)) {
        setSimTime((prev) => +(prev + dt).toFixed(1));
        setActiveVehiclesCount(vehicles.length);
        setCurrentPhase(nsState === 'GREEN' ? 'NS_GREEN' : ewState === 'GREEN' ? 'EW_GREEN' : 'ALL_YELLOW');
      }

      // Clear Canvas Frame
      ctx.fillStyle = '#080D10';
      ctx.fillRect(0, 0, width, height);

      // Camera view coordinates
      const scale = Math.max(width / 780, 0.85);
      const originX = width * 0.5;
      const originY = height * 0.44;

      // 1. Draw Orthogonal Ground Grid Background
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.025)';
      ctx.lineWidth = 1;
      const gridSize = 32;
      for (let g = -340; g <= 340; g += gridSize) {
        const p1 = toIso(g, -340, 0, scale, originX, originY);
        const p2 = toIso(g, 340, 0, scale, originX, originY);
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        ctx.lineTo(p2.x, p2.y);
        ctx.stroke();

        const p3 = toIso(-340, g, 0, scale, originX, originY);
        const p4 = toIso(340, g, 0, scale, originX, originY);
        ctx.beginPath();
        ctx.moveTo(p3.x, p3.y);
        ctx.lineTo(p4.x, p4.y);
        ctx.stroke();
      }

      // 2. Draw Arterial Road Corridors
      // Road 1: EW Corridor (y: -40 to 40, x: -340 to 340)
      // Road 2: NS Corridor (x: -40 to 40, y: -340 to 340)
      const roadWidth = 40;

      const drawRoadSegment = (x1: number, y1: number, x2: number, y2: number) => {
        const c1 = toIso(x1, y1, 0, scale, originX, originY);
        const c2 = toIso(x2, y1, 0, scale, originX, originY);
        const c3 = toIso(x2, y2, 0, scale, originX, originY);
        const c4 = toIso(x1, y2, 0, scale, originX, originY);

        ctx.fillStyle = '#111A1E';
        ctx.beginPath();
        ctx.moveTo(c1.x, c1.y);
        ctx.lineTo(c2.x, c2.y);
        ctx.lineTo(c3.x, c3.y);
        ctx.lineTo(c4.x, c4.y);
        ctx.closePath();
        ctx.fill();

        ctx.strokeStyle = 'rgba(255, 255, 255, 0.12)';
        ctx.lineWidth = 1.5;
        ctx.stroke();
      };

      // Draw horizontal & vertical asphalt bands
      drawRoadSegment(-340, -roadWidth, 340, roadWidth);
      drawRoadSegment(-roadWidth, -340, roadWidth, 340);

      // Lane dividers & markings
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
      ctx.setLineDash([8, 8]);
      ctx.lineWidth = 1;

      // EW Lane dividers
      const ewDiv1 = toIso(-340, -14, 0, scale, originX, originY);
      const ewDiv2 = toIso(340, -14, 0, scale, originX, originY);
      ctx.beginPath();
      ctx.moveTo(ewDiv1.x, ewDiv1.y);
      ctx.lineTo(ewDiv2.x, ewDiv2.y);
      ctx.stroke();

      const ewDiv3 = toIso(-340, 14, 0, scale, originX, originY);
      const ewDiv4 = toIso(340, 14, 0, scale, originX, originY);
      ctx.beginPath();
      ctx.moveTo(ewDiv3.x, ewDiv3.y);
      ctx.lineTo(ewDiv4.x, ewDiv4.y);
      ctx.stroke();

      // NS Lane dividers
      const nsDiv1 = toIso(-14, -340, 0, scale, originX, originY);
      const nsDiv2 = toIso(-14, 340, 0, scale, originX, originY);
      ctx.beginPath();
      ctx.moveTo(nsDiv1.x, nsDiv1.y);
      ctx.lineTo(nsDiv2.x, nsDiv2.y);
      ctx.stroke();

      const nsDiv3 = toIso(14, -340, 0, scale, originX, originY);
      const nsDiv4 = toIso(14, 340, 0, scale, originX, originY);
      ctx.beginPath();
      ctx.moveTo(nsDiv3.x, nsDiv3.y);
      ctx.lineTo(nsDiv4.x, nsDiv4.y);
      ctx.stroke();

      ctx.setLineDash([]); // Reset line dash

      // Double yellow center divider lines
      ctx.strokeStyle = '#E9A23B';
      ctx.lineWidth = 1.2;

      const cew1 = toIso(-340, 0, 0, scale, originX, originY);
      const cew2 = toIso(-roadWidth, 0, 0, scale, originX, originY);
      ctx.beginPath();
      ctx.moveTo(cew1.x, cew1.y);
      ctx.lineTo(cew2.x, cew2.y);
      ctx.stroke();

      const cew3 = toIso(roadWidth, 0, 0, scale, originX, originY);
      const cew4 = toIso(340, 0, 0, scale, originX, originY);
      ctx.beginPath();
      ctx.moveTo(cew3.x, cew3.y);
      ctx.lineTo(cew4.x, cew4.y);
      ctx.stroke();

      const cns1 = toIso(0, -340, 0, scale, originX, originY);
      const cns2 = toIso(0, -roadWidth, 0, scale, originX, originY);
      ctx.beginPath();
      ctx.moveTo(cns1.x, cns1.y);
      ctx.lineTo(cns2.x, cns2.y);
      ctx.stroke();

      const cns3 = toIso(0, roadWidth, 0, scale, originX, originY);
      const cns4 = toIso(0, 340, 0, scale, originX, originY);
      ctx.beginPath();
      ctx.moveTo(cns3.x, cns3.y);
      ctx.lineTo(cns4.x, cns4.y);
      ctx.stroke();

      // Crosswalks and Stop Bars at the 4 approach mouths
      const drawStopBar = (x1: number, y1: number, x2: number, y2: number, isRed: boolean) => {
        const p1 = toIso(x1, y1, 0, scale, originX, originY);
        const p2 = toIso(x2, y2, 0, scale, originX, originY);
        ctx.strokeStyle = isRed ? 'rgba(239, 68, 68, 0.9)' : 'rgba(255, 255, 255, 0.7)';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        ctx.lineTo(p2.x, p2.y);
        ctx.stroke();
      };

      drawStopBar(-roadWidth, 0, -roadWidth, roadWidth, ewState !== 'GREEN');
      drawStopBar(roadWidth, -roadWidth, roadWidth, 0, ewState !== 'GREEN');
      drawStopBar(0, -roadWidth, -roadWidth, -roadWidth, nsState !== 'GREEN');
      drawStopBar(0, roadWidth, roadWidth, roadWidth, nsState !== 'GREEN');

      // 3. Draw 3D Isometric Buildings
      // Sort buildings by depth (x + y) to prevent occlusion bugs
      const sortedBuildings = [...buildings].sort((a, b) => a.x + a.y - (b.x + b.y));

      sortedBuildings.forEach((b) => {
        const { x, y, w, d, h } = b;

        // Bottom corners
        const p10 = toIso(x + w, y, 0, scale, originX, originY);
        const p11 = toIso(x + w, y + d, 0, scale, originX, originY);
        const p01 = toIso(x, y + d, 0, scale, originX, originY);

        // Top corners
        const t00 = toIso(x, y, h, scale, originX, originY);
        const t10 = toIso(x + w, y, h, scale, originX, originY);
        const t11 = toIso(x + w, y + d, h, scale, originX, originY);
        const t01 = toIso(x, y + d, h, scale, originX, originY);

        // Left Face (X+W, Y to Y+D)
        ctx.fillStyle = b.colorLeft;
        ctx.beginPath();
        ctx.moveTo(p10.x, p10.y);
        ctx.lineTo(p11.x, p11.y);
        ctx.lineTo(t11.x, t11.y);
        ctx.lineTo(t10.x, t10.y);
        ctx.closePath();
        ctx.fill();
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.08)';
        ctx.lineWidth = 1;
        ctx.stroke();

        // Right Face (X to X+W, Y+D)
        ctx.fillStyle = b.colorRight;
        ctx.beginPath();
        ctx.moveTo(p01.x, p01.y);
        ctx.lineTo(p11.x, p11.y);
        ctx.lineTo(t11.x, t11.y);
        ctx.lineTo(t01.x, t01.y);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();

        // Top Face (Roof)
        ctx.fillStyle = b.colorTop;
        ctx.beginPath();
        ctx.moveTo(t00.x, t00.y);
        ctx.lineTo(t10.x, t10.y);
        ctx.lineTo(t11.x, t11.y);
        ctx.lineTo(t01.x, t01.y);
        ctx.closePath();
        ctx.fill();
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.12)';
        ctx.stroke();

        // Roof features: Helipad or Communication Antenna
        if (b.roofType === 'helipad') {
          const centerRoof = toIso(x + w / 2, y + d / 2, h, scale, originX, originY);
          ctx.strokeStyle = '#45C982';
          ctx.lineWidth = 1.5;
          ctx.beginPath();
          ctx.arc(centerRoof.x, centerRoof.y, 8 * scale, 0, Math.PI * 2);
          ctx.stroke();

          ctx.fillStyle = '#45C982';
          ctx.font = `bold ${Math.round(8 * scale)}px sans-serif`;
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillText('H', centerRoof.x, centerRoof.y);
        } else if (b.roofType === 'antenna') {
          const antBase = toIso(x + w / 2, y + d / 2, h, scale, originX, originY);
          const antTop = toIso(x + w / 2, y + d / 2, h + 24, scale, originX, originY);
          ctx.strokeStyle = '#E9A23B';
          ctx.lineWidth = 1.5;
          ctx.beginPath();
          ctx.moveTo(antBase.x, antBase.y);
          ctx.lineTo(antTop.x, antTop.y);
          ctx.stroke();

          // Blinking beacon light
          const blink = (Math.sin(tickCount * 4) + 1) * 0.5;
          ctx.fillStyle = `rgba(233, 162, 59, ${blink})`;
          ctx.beginPath();
          ctx.arc(antTop.x, antTop.y, 3 * scale, 0, Math.PI * 2);
          ctx.fill();
        }

        // Illuminated architectural window matrices
        if (b.windows) {
          ctx.fillStyle = b.windowColor ? `${b.windowColor}22` : 'rgba(255, 255, 255, 0.15)';
          const windowRows = Math.floor(h / 14);
          for (let r = 1; r < windowRows; r += 2) {
            const zLevel = r * 12;
            const w1 = toIso(x + w, y + d * 0.25, zLevel, scale, originX, originY);
            const w2 = toIso(x + w, y + d * 0.75, zLevel, scale, originX, originY);
            ctx.beginPath();
            ctx.moveTo(w1.x, w1.y);
            ctx.lineTo(w2.x, w2.y);
            ctx.strokeStyle = b.windowColor ? `${b.windowColor}66` : 'rgba(255, 255, 255, 0.2)';
            ctx.lineWidth = 2;
            ctx.stroke();
          }
        }
      });

      // 4. Update & Render Vehicles
      // Spawn extra vehicles if in rush mode
      const targetVehicleCount = stateRef.current.trafficDensity === 'rush' ? 34 : 20;
      if (vehicles.length < targetVehicleCount && Math.random() < 0.08) {
        const randDir = directions[Math.floor(Math.random() * directions.length)];
        vehicles.push(spawnVehicle(randDir));
      }

      // Physics update per vehicle
      if (stateRef.current.isPlaying) {
        for (let i = vehicles.length - 1; i >= 0; i--) {
          const v = vehicles[i];

          // Stop distance checks at intersections
          let shouldStop = false;
          const stopLineDist = 48;

          if (v.dir === 'E') {
            const distToStop = -stopLineDist - v.x;
            if (ewState !== 'GREEN' && distToStop > 0 && distToStop < 90) {
              shouldStop = true;
            }
          } else if (v.dir === 'W') {
            const distToStop = v.x - stopLineDist;
            if (ewState !== 'GREEN' && distToStop > 0 && distToStop < 90) {
              shouldStop = true;
            }
          } else if (v.dir === 'S') {
            const distToStop = -stopLineDist - v.y;
            if (nsState !== 'GREEN' && distToStop > 0 && distToStop < 90) {
              shouldStop = true;
            }
          } else if (v.dir === 'N') {
            const distToStop = v.y - stopLineDist;
            if (nsState !== 'GREEN' && distToStop > 0 && distToStop < 90) {
              shouldStop = true;
            }
          }

          // Anti-collision check with the vehicle directly ahead in the same lane
          for (let j = 0; j < vehicles.length; j++) {
            if (i === j) continue;
            const other = vehicles[j];
            if (other.dir === v.dir && Math.abs(other.x - v.x) < 40 && Math.abs(other.y - v.y) < 40) {
              if (v.dir === 'E' && other.x > v.x && other.x - v.x < 36) shouldStop = true;
              if (v.dir === 'W' && other.x < v.x && v.x - other.x < 36) shouldStop = true;
              if (v.dir === 'S' && other.y > v.y && other.y - v.y < 36) shouldStop = true;
              if (v.dir === 'N' && other.y < v.y && v.y - other.y < 36) shouldStop = true;
            }
          }

          // Accelerate or decelerate smoothly
          if (shouldStop) {
            v.speed = Math.max(0, v.speed - dt * 4.5);
            v.braking = true;
          } else {
            v.speed = Math.min(v.maxSpeed, v.speed + dt * 2.5);
            v.braking = false;
          }

          // Update position
          if (v.dir === 'E') v.x += v.speed * 60 * dt;
          else if (v.dir === 'W') v.x -= v.speed * 60 * dt;
          else if (v.dir === 'S') v.y += v.speed * 60 * dt;
          else if (v.dir === 'N') v.y -= v.speed * 60 * dt;

          // Recycle vehicle once out of bounds
          const maxDist = 340;
          if (Math.abs(v.x) > maxDist || Math.abs(v.y) > maxDist) {
            vehicles.splice(i, 1);
          }
        }
      }

      // Render Vehicles (sorted by isometric depth)
      const sortedVehicles = [...vehicles].sort((a, b) => a.x + a.y - (b.x + b.y));

      sortedVehicles.forEach((v) => {
        const { x, y, length: len, width: wid, height: hei, color, dir } = v;

        // Bounding box orientations along axes
        let dx = dir === 'E' || dir === 'W' ? len / 2 : wid / 2;
        let dy = dir === 'E' || dir === 'W' ? wid / 2 : len / 2;

        const b00 = toIso(x - dx, y - dy, 0, scale, originX, originY);
        const b10 = toIso(x + dx, y - dy, 0, scale, originX, originY);
        const b11 = toIso(x + dx, y + dy, 0, scale, originX, originY);
        const b01 = toIso(x - dx, y + dy, 0, scale, originX, originY);

        const t00 = toIso(x - dx, y - dy, hei, scale, originX, originY);
        const t10 = toIso(x + dx, y - dy, hei, scale, originX, originY);
        const t11 = toIso(x + dx, y + dy, hei, scale, originX, originY);
        const t01 = toIso(x - dx, y + dy, hei, scale, originX, originY);

        // Vehicle Chassis Body
        ctx.fillStyle = color;
        // Top Roof
        ctx.beginPath();
        ctx.moveTo(t00.x, t00.y);
        ctx.lineTo(t10.x, t10.y);
        ctx.lineTo(t11.x, t11.y);
        ctx.lineTo(t01.x, t01.y);
        ctx.closePath();
        ctx.fill();

        // Left Face
        ctx.fillStyle = 'rgba(0, 0, 0, 0.25)';
        ctx.beginPath();
        ctx.moveTo(b10.x, b10.y);
        ctx.lineTo(b11.x, b11.y);
        ctx.lineTo(t11.x, t11.y);
        ctx.lineTo(t10.x, t10.y);
        ctx.closePath();
        ctx.fill();

        // Right Face
        ctx.fillStyle = 'rgba(0, 0, 0, 0.45)';
        ctx.beginPath();
        ctx.moveTo(b01.x, b01.y);
        ctx.lineTo(b11.x, b11.y);
        ctx.lineTo(t11.x, t11.y);
        ctx.lineTo(t01.x, t01.y);
        ctx.closePath();
        ctx.fill();

        // Vehicle Headlights casting beams on asphalt
        ctx.fillStyle = 'rgba(255, 255, 230, 0.25)';
        const frontPos = dir === 'E' ? { x: x + dx, y } : dir === 'W' ? { x: x - dx, y } : dir === 'S' ? { x, y: y + dy } : { x, y: y - dy };
        const beamPos = toIso(frontPos.x, frontPos.y, 2, scale, originX, originY);
        ctx.beginPath();
        ctx.arc(beamPos.x, beamPos.y, 4 * scale, 0, Math.PI * 2);
        ctx.fill();

        // Brake lights (Red glow when stopped/braking)
        const rearPos = dir === 'E' ? { x: x - dx, y } : dir === 'W' ? { x: x + dx, y } : dir === 'S' ? { x, y: y - dy } : { x, y: y + dy };
        const rearScreen = toIso(rearPos.x, rearPos.y, 3, scale, originX, originY);
        ctx.fillStyle = v.braking ? '#EF4444' : 'rgba(239, 68, 68, 0.6)';
        ctx.beginPath();
        ctx.arc(rearScreen.x, rearScreen.y, v.braking ? 3.5 * scale : 2 * scale, 0, Math.PI * 2);
        ctx.fill();

        // Autonomous Halo Indicator
        if (v.type === 'autonomous') {
          const haloCenter = toIso(x, y, hei + 4, scale, originX, originY);
          ctx.strokeStyle = '#45C982';
          ctx.lineWidth = 1.2;
          ctx.beginPath();
          ctx.arc(haloCenter.x, haloCenter.y, 6 * scale, 0, Math.PI * 2);
          ctx.stroke();
        }

        // AI Perception 3D Bounding Box (YOLO / Computer Vision Reticle)
        if (stateRef.current.showBoundingBoxes) {
          ctx.strokeStyle = v.type === 'autonomous' ? '#45C982' : '#00E5FF';
          ctx.lineWidth = 1;
          ctx.setLineDash([3, 3]);

          ctx.beginPath();
          // Bottom loop
          ctx.moveTo(b00.x, b00.y);
          ctx.lineTo(b10.x, b10.y);
          ctx.lineTo(b11.x, b11.y);
          ctx.lineTo(b01.x, b01.y);
          ctx.closePath();
          // Top loop
          ctx.moveTo(t00.x, t00.y);
          ctx.lineTo(t10.x, t10.y);
          ctx.lineTo(t11.x, t11.y);
          ctx.lineTo(t01.x, t01.y);
          ctx.closePath();
          // Vertical struts
          ctx.moveTo(b00.x, b00.y);
          ctx.lineTo(t00.x, t00.y);
          ctx.moveTo(b10.x, b10.y);
          ctx.lineTo(t10.x, t10.y);
          ctx.moveTo(b11.x, b11.y);
          ctx.lineTo(t11.x, t11.y);
          ctx.moveTo(b01.x, b01.y);
          ctx.lineTo(t01.x, t01.y);
          ctx.stroke();
          ctx.setLineDash([]);

          // AI Label Tag
          const tagPos = toIso(x, y, hei + 12, scale, originX, originY);
          ctx.fillStyle = 'rgba(8, 13, 16, 0.85)';
          ctx.fillRect(tagPos.x - 28, tagPos.y - 7, 56, 12);
          ctx.strokeStyle = v.type === 'autonomous' ? '#45C982' : '#00E5FF';
          ctx.lineWidth = 0.8;
          ctx.strokeRect(tagPos.x - 28, tagPos.y - 7, 56, 12);

          ctx.fillStyle = '#FFFFFF';
          ctx.font = 'bold 8px monospace';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillText(`${v.label} ${Math.round(v.conf * 100)}%`, tagPos.x, tagPos.y - 1);
        }
      });

      // 5. Draw Roadside Camera Sensors & Radar Cones
      cameraSensors.forEach((cam) => {
        const mastBase = toIso(cam.x, cam.y, 0, scale, originX, originY);
        const mastTop = toIso(cam.x, cam.y, 30, scale, originX, originY);

        // Mast pole
        ctx.strokeStyle = '#45C982';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(mastBase.x, mastBase.y);
        ctx.lineTo(mastTop.x, mastTop.y);
        ctx.stroke();

        // Camera Head Unit
        ctx.fillStyle = '#45C982';
        ctx.beginPath();
        ctx.arc(mastTop.x, mastTop.y, 3.5 * scale, 0, Math.PI * 2);
        ctx.fill();

        // Radar / Perception Field of View Cone
        if (stateRef.current.showRadarCones) {
          const coneLength = 110;
          const sweepSpread = 0.55; // 30-degree arc
          const currentSweep = cam.targetAngle + Math.sin(radarSweepAngle + cam.x) * sweepSpread;

          const arcPoint1 = toIso(
            cam.x + Math.cos(currentSweep - 0.4) * coneLength,
            cam.y + Math.sin(currentSweep - 0.4) * coneLength,
            0,
            scale,
            originX,
            originY
          );
          const arcPoint2 = toIso(
            cam.x + Math.cos(currentSweep + 0.4) * coneLength,
            cam.y + Math.sin(currentSweep + 0.4) * coneLength,
            0,
            scale,
            originX,
            originY
          );

          // Translucent gradient cone
          const coneGrad = ctx.createRadialGradient(mastTop.x, mastTop.y, 5, mastTop.x, mastTop.y, coneLength * scale * 1.2);
          coneGrad.addColorStop(0, 'rgba(69, 201, 130, 0.35)');
          coneGrad.addColorStop(0.7, 'rgba(69, 201, 130, 0.08)');
          coneGrad.addColorStop(1, 'transparent');

          ctx.fillStyle = coneGrad;
          ctx.beginPath();
          ctx.moveTo(mastTop.x, mastTop.y);
          ctx.lineTo(arcPoint1.x, arcPoint1.y);
          ctx.lineTo(arcPoint2.x, arcPoint2.y);
          ctx.closePath();
          ctx.fill();

          ctx.strokeStyle = 'rgba(69, 201, 130, 0.4)';
          ctx.lineWidth = 1;
          ctx.stroke();
        }

        // Camera ID Tag
        ctx.fillStyle = '#45C982';
        ctx.font = 'bold 9px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(cam.id, mastTop.x, mastTop.y - 8);
      });

      // 6. Draw Overhead Signal Heads
      const drawSignalHead = (x: number, y: number, state: 'GREEN' | 'YELLOW' | 'RED') => {
        const p = toIso(x, y, 32, scale, originX, originY);
        ctx.fillStyle = '#080D10';
        ctx.fillRect(p.x - 7, p.y - 12, 14, 24);
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
        ctx.strokeRect(p.x - 7, p.y - 12, 14, 24);

        // Light dots
        const dotColor = state === 'GREEN' ? '#45C982' : state === 'YELLOW' ? '#E9A23B' : '#EF4444';
        const glow = state === 'GREEN' ? 'rgba(69, 201, 130, 0.5)' : state === 'YELLOW' ? 'rgba(233, 162, 59, 0.5)' : 'rgba(239, 68, 68, 0.5)';

        ctx.fillStyle = glow;
        ctx.beginPath();
        ctx.arc(p.x, p.y, 8, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = dotColor;
        ctx.beginPath();
        ctx.arc(p.x, p.y, 4, 0, Math.PI * 2);
        ctx.fill();
      };

      drawSignalHead(-24, -42, ewState);
      drawSignalHead(24, 42, ewState);
      drawSignalHead(-42, 24, nsState);
      drawSignalHead(42, -24, nsState);

      // Loop frame
      animId = requestAnimationFrame(render);
    };

    animId = requestAnimationFrame(render);

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animId);
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className="relative w-full rounded-xl overflow-hidden border border-white/10 bg-[#080D10] shadow-2xl my-8 font-sans"
    >
      {/* 1. Canvas Viewport */}
      <canvas ref={canvasRef} className="block w-full h-auto cursor-grab active:cursor-grabbing" />

      {/* 2. Top HUD Overlay Bar */}
      <div className="absolute top-0 left-0 right-0 p-4 flex flex-wrap items-center justify-between gap-3 pointer-events-none bg-gradient-to-b from-[#080D10]/90 via-[#080D10]/50 to-transparent">
        <div className="flex items-center gap-2.5">
          <div className="px-2.5 py-1 rounded bg-[#080D10]/85 border border-[#45C982]/30 backdrop-blur-md flex items-center gap-2 pointer-events-auto">
            <span className="w-2 h-2 rounded-full bg-[#45C982] animate-pulse" />
            <span className="text-xs font-mono font-bold text-white uppercase tracking-wider">
              CARLA 0.9.15 + SUMO CO-SIMULATION
            </span>
          </div>

          <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#080D10]/70 border border-white/10 text-white/60 text-xs font-mono backdrop-blur-sm">
            <Layers className="w-3.5 h-3.5 text-[#45C982]" />
            <span>Sector 04 Arterial Grid</span>
          </div>
        </div>

        {/* Real-time Telemetry Tele-display */}
        <div className="flex items-center gap-2 font-mono text-xs pointer-events-auto">
          <div className="px-2.5 py-1 rounded bg-[#080D10]/85 border border-white/10 text-white/80 backdrop-blur-md flex items-center gap-2">
            <Activity className="w-3.5 h-3.5 text-[#45C982]" />
            <span>TICK: +{simTime.toFixed(1)}s</span>
            <span className="text-white/30">|</span>
            <span className="text-[#45C982] font-semibold">{activeVehiclesCount} VEHICLES</span>
            <span className="text-white/30">|</span>
            <span className={currentPhase === 'NS_GREEN' ? 'text-[#45C982]' : 'text-[#E9A23B]'}>
              PHASE: {currentPhase}
            </span>
          </div>
        </div>
      </div>

      {/* 3. Bottom Interactive Control Dock */}
      <div className="absolute bottom-0 left-0 right-0 p-3 sm:p-4 bg-gradient-to-t from-[#080D10]/95 via-[#080D10]/80 to-transparent flex flex-wrap items-center justify-between gap-3 border-t border-white/10">
        <div className="flex items-center gap-2">
          {/* Play / Pause Toggle */}
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            title={isPlaying ? 'Pause Simulation' : 'Resume Simulation'}
            className="px-3 py-1.5 rounded bg-white/10 hover:bg-white/15 text-white text-xs font-mono font-medium flex items-center gap-1.5 border border-white/15 transition-all cursor-pointer"
          >
            {isPlaying ? (
              <>
                <Pause className="w-3.5 h-3.5 text-[#E9A23B]" />
                <span>Pause</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 text-[#45C982]" />
                <span>Resume</span>
              </>
            )}
          </button>

          {/* Toggle Bounding Boxes */}
          <button
            onClick={() => setShowBoundingBoxes(!showBoundingBoxes)}
            className={`px-3 py-1.5 rounded text-xs font-mono transition-all flex items-center gap-1.5 border cursor-pointer ${
              showBoundingBoxes
                ? 'bg-[#45C982]/15 text-[#45C982] border-[#45C982]/40'
                : 'bg-white/5 text-white/50 border-white/10 hover:text-white'
            }`}
          >
            <Eye className="w-3.5 h-3.5" />
            <span>YOLO Boxes {showBoundingBoxes ? 'ON' : 'OFF'}</span>
          </button>

          {/* Toggle Radar Cones */}
          <button
            onClick={() => setShowRadarCones(!showRadarCones)}
            className={`px-3 py-1.5 rounded text-xs font-mono transition-all flex items-center gap-1.5 border cursor-pointer ${
              showRadarCones
                ? 'bg-[#45C982]/15 text-[#45C982] border-[#45C982]/40'
                : 'bg-white/5 text-white/50 border-white/10 hover:text-white'
            }`}
          >
            <Radar className="w-3.5 h-3.5" />
            <span>Sensor FOV {showRadarCones ? 'ON' : 'OFF'}</span>
          </button>
        </div>

        {/* Traffic Density Toggle */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-white/40 hidden sm:inline">Density:</span>
          <div className="inline-flex rounded border border-white/15 bg-white/5 p-0.5 text-xs font-mono">
            <button
              onClick={() => setTrafficDensity('nominal')}
              className={`px-2.5 py-1 rounded transition-colors cursor-pointer ${
                trafficDensity === 'nominal'
                  ? 'bg-white/20 text-white font-semibold'
                  : 'text-white/50 hover:text-white'
              }`}
            >
              Nominal
            </button>
            <button
              onClick={() => setTrafficDensity('rush')}
              className={`px-2.5 py-1 rounded transition-colors cursor-pointer ${
                trafficDensity === 'rush'
                  ? 'bg-[#E9A23B]/25 text-[#E9A23B] font-semibold'
                  : 'text-white/50 hover:text-white'
              }`}
            >
              Rush Hour
            </button>
          </div>

          <div className="hidden md:flex items-center gap-1.5 pl-2 text-xs font-mono text-white/40 border-l border-white/15">
            <ShieldCheck className="w-3.5 h-3.5 text-[#45C982]" />
            <span>60 FPS Synchronous</span>
          </div>
        </div>
      </div>
    </div>
  );
};
