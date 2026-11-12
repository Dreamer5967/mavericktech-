import React, { useEffect, useRef, useState } from 'react';
import { SnapshotResponse, JunctionData } from '../../types/api';
import { Play, Pause, Eye, Radar, Activity, ShieldCheck } from 'lucide-react';

interface LiveDigitalTwinCommandBannerProps {
  snapshot?: SnapshotResponse;
}

interface Vehicle {
  id: number;
  type: 'sedan' | 'autonomous' | 'van' | 'bus' | 'emergency';
  lane: 'N_S' | 'S_N' | 'W_E' | 'E_W';
  subLane: 0 | 1; // 0 = inner/left, 1 = outer/right
  dist: number; // progress in pixels along the corridor
  speed: number;
  maxSpeed: number;
  accel: number;
  color: string;
  length: number;
  width: number;
  turning: 'straight' | 'left' | 'right';
  turnProgress: number; // 0 to 1 during intersection turn
  braking: boolean;
  label: string;
}

export const LiveDigitalTwinCommandBanner: React.FC<LiveDigitalTwinCommandBannerProps> = ({ snapshot }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  // User interactive state toggles
  const [isPlaying, setIsPlaying] = useState<boolean>(true);
  const [showReticles, setShowReticles] = useState<boolean>(true);
  const [showRadar, setShowRadar] = useState<boolean>(true);
  const [trafficDensity, setTrafficDensity] = useState<'nominal' | 'rush'>('nominal');
  const [vehicleCount, setVehicleCount] = useState<number>(18);
  const [phaseDisplay, setPhaseDisplay] = useState<'NS_GREEN' | 'NS_YELLOW' | 'EW_GREEN' | 'EW_YELLOW'>('NS_GREEN');
  const [phaseCountdown, setPhaseCountdown] = useState<number>(14);

  // Mutable refs for high-frequency RAF loop
  const stateRef = useRef({
    isPlaying: true,
    showReticles: true,
    showRadar: true,
    trafficDensity: 'nominal' as 'nominal' | 'rush',
    snapshot,
  });

  useEffect(() => {
    stateRef.current.isPlaying = isPlaying;
    stateRef.current.showReticles = showReticles;
    stateRef.current.showRadar = showRadar;
    stateRef.current.trafficDensity = trafficDensity;
    stateRef.current.snapshot = snapshot;
  }, [isPlaying, showReticles, showRadar, trafficDensity, snapshot]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d', { alpha: true });
    if (!ctx) return;

    let animId: number;
    let width = 0;
    let height = 0;

    // Responsive Canvas Resizing with high DPI support
    const handleResize = () => {
      if (!containerRef.current || !canvas) return;
      const rect = containerRef.current.getBoundingClientRect();
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = rect.width;
      height = Math.max(Math.min(rect.width * 0.32, 320), 220); // Sleek widescreen banner aspect
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      ctx.scale(dpr, dpr);
    };

    handleResize();
    window.addEventListener('resize', handleResize);

    // 2.5D Isometric-Angle Math
    // Center intersection at (cx, cy)
    // Horizontal corridor (East-West) and Vertical corridor (North-South)
    let nextVehId = 1;
    const vehicles: Vehicle[] = [];

    // Colors matching design palette
    const colors = {
      autonomous: '#45C982', // Neon Emerald
      sedanWhite: '#E8ECEF',
      sedanSilver: '#94A3B8',
      vanAmber: '#E9A23B',
      busCyan: '#38BDF8',
      emergencyRed: '#EF4444',
    };

    function spawnVehicle(lane?: 'N_S' | 'S_N' | 'W_E' | 'E_W'): Vehicle {
      const lanes: ('N_S' | 'S_N' | 'W_E' | 'E_W')[] = ['N_S', 'S_N', 'W_E', 'E_W'];
      const chosenLane = lane || lanes[Math.floor(Math.random() * lanes.length)];
      const subLane = (Math.random() > 0.45 ? 1 : 0) as 0 | 1;

      const rand = Math.random();
      let type: Vehicle['type'] = 'sedan';
      let color = colors.sedanWhite;
      let length = 14;
      let width = 7;
      let maxSpeed = 1.6 + Math.random() * 0.5;
      let label = `SEDAN_${Math.floor(Math.random() * 899 + 100)}`;

      if (rand < 0.28) {
        type = 'autonomous';
        color = colors.autonomous;
        length = 13;
        width = 6.5;
        maxSpeed = 1.8;
        label = `AV_POD_${Math.floor(Math.random() * 89 + 10)}`;
      } else if (rand < 0.48) {
        type = 'van';
        color = colors.vanAmber;
        length = 18;
        width = 7.5;
        maxSpeed = 1.4;
        label = `LOGISTICS_${Math.floor(Math.random() * 89 + 10)}`;
      } else if (rand < 0.6) {
        type = 'bus';
        color = colors.busCyan;
        length = 26;
        width = 8;
        maxSpeed = 1.2;
        label = `TRANSIT_${Math.floor(Math.random() * 89 + 10)}`;
      } else if (rand < 0.65) {
        type = 'emergency';
        color = colors.emergencyRed;
        length = 16;
        width = 7;
        maxSpeed = 2.2;
        label = `EMS_RESP_${Math.floor(Math.random() * 89 + 10)}`;
      }

      // Turning behavior: inner lanes might turn left, outer lanes might turn right
      let turning: Vehicle['turning'] = 'straight';
      if (subLane === 0 && Math.random() < 0.25) {
        turning = 'left';
      } else if (subLane === 1 && Math.random() < 0.2) {
        turning = 'right';
      }

      return {
        id: nextVehId++,
        type,
        lane: chosenLane,
        subLane,
        dist: -Math.random() * 120 - 40, // Spawn offscreen before stop line
        speed: maxSpeed * 0.8,
        maxSpeed,
        accel: 0.05,
        color,
        length,
        width,
        turning,
        turnProgress: 0,
        braking: false,
        label,
      };
    }

    // Populate initial vehicle fleet
    for (let i = 0; i < 22; i++) {
      const v = spawnVehicle();
      v.dist = Math.random() * 450 - 50;
      vehicles.push(v);
    }

    // Signal Cycle Engine (synced with actual snapshot if available)
    let phaseTimer = 0;
    const PHASE_GREEN = 14;
    const PHASE_YELLOW = 3;
    const TOTAL_CYCLE = (PHASE_GREEN + PHASE_YELLOW) * 2;

    let lastTime = performance.now();
    let frameCounter = 0;

    // Simulation render loop
    const render = (time: number) => {
      animId = requestAnimationFrame(render);
      const dt = Math.min((time - lastTime) / 1000, 0.1);
      lastTime = time;
      frameCounter++;

      if (width === 0 || height === 0) return;

      // Clear Canvas
      ctx.clearRect(0, 0, width, height);

      // Deep Obsidian Tactical Canvas Base
      ctx.fillStyle = '#080D10';
      ctx.fillRect(0, 0, width, height);

      // Determine Traffic Phase (Fallback to synthetic loop, or respect snapshot if present)
      phaseTimer = (phaseTimer + (stateRef.current.isPlaying ? dt : 0)) % TOTAL_CYCLE;
      let activePhase: 'NS_GREEN' | 'NS_YELLOW' | 'EW_GREEN' | 'EW_YELLOW' = 'NS_GREEN';
      let remaining = 0;

      if (phaseTimer < PHASE_GREEN) {
        activePhase = 'NS_GREEN';
        remaining = Math.ceil(PHASE_GREEN - phaseTimer);
      } else if (phaseTimer < PHASE_GREEN + PHASE_YELLOW) {
        activePhase = 'NS_YELLOW';
        remaining = Math.ceil(PHASE_GREEN + PHASE_YELLOW - phaseTimer);
      } else if (phaseTimer < PHASE_GREEN * 2 + PHASE_YELLOW) {
        activePhase = 'EW_GREEN';
        remaining = Math.ceil(PHASE_GREEN * 2 + PHASE_YELLOW - phaseTimer);
      } else {
        activePhase = 'EW_YELLOW';
        remaining = Math.ceil(TOTAL_CYCLE - phaseTimer);
      }

      if (frameCounter % 15 === 0) {
        setPhaseDisplay(activePhase);
        setPhaseCountdown(remaining);
        setVehicleCount(vehicles.length);
      }

      // Check if any junction has an active incident/fault in snapshot
      const currentSnapshot = stateRef.current.snapshot;
      const incidentJunction = currentSnapshot?.junctions?.find(
        (j: JunctionData) => j.camera_status === 'MISSING' || j.data_quality === 'DEGRADED'
      );

      // Geometry coordinates
      const cx = width / 2;
      const cy = height / 2;
      const roadWidth = Math.min(width * 0.14, 96); // Width of 4-lane arterial
      const halfRoad = roadWidth / 2;
      const laneWidth = roadWidth / 4;

      // -------------------------------------------------------------
      // 1. Draw Tactical Grid Background
      // -------------------------------------------------------------
      ctx.save();
      ctx.strokeStyle = 'rgba(69, 201, 130, 0.04)';
      ctx.lineWidth = 1;
      const gridSize = 32;
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
      ctx.restore();

      // -------------------------------------------------------------
      // 2. Draw Asphalt Corridors (East-West & North-South)
      // -------------------------------------------------------------
      ctx.save();
      // East-West Corridor
      ctx.fillStyle = '#0f171c';
      ctx.fillRect(0, cy - halfRoad, width, roadWidth);

      // North-South Corridor
      ctx.fillRect(cx - halfRoad, 0, roadWidth, height);

      // Road Borders (curbs)
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.12)';
      ctx.lineWidth = 1.5;

      // North-West curb
      ctx.beginPath();
      ctx.moveTo(0, cy - halfRoad);
      ctx.lineTo(cx - halfRoad, cy - halfRoad);
      ctx.lineTo(cx - halfRoad, 0);
      ctx.stroke();

      // North-East curb
      ctx.beginPath();
      ctx.moveTo(width, cy - halfRoad);
      ctx.lineTo(cx + halfRoad, cy - halfRoad);
      ctx.lineTo(cx + halfRoad, 0);
      ctx.stroke();

      // South-West curb
      ctx.beginPath();
      ctx.moveTo(0, cy + halfRoad);
      ctx.lineTo(cx - halfRoad, cy + halfRoad);
      ctx.lineTo(cx - halfRoad, height);
      ctx.stroke();

      // South-East curb
      ctx.beginPath();
      ctx.moveTo(width, cy + halfRoad);
      ctx.lineTo(cx + halfRoad, cy + halfRoad);
      ctx.lineTo(cx + halfRoad, height);
      ctx.stroke();

      // Center Dividers (Double Yellow / Solid Amber lines)
      ctx.strokeStyle = '#E9A23B';
      ctx.lineWidth = 1.2;

      // West divider
      ctx.beginPath();
      ctx.moveTo(0, cy - 1);
      ctx.lineTo(cx - halfRoad - 12, cy - 1);
      ctx.moveTo(0, cy + 1);
      ctx.lineTo(cx - halfRoad - 12, cy + 1);
      ctx.stroke();

      // East divider
      ctx.beginPath();
      ctx.moveTo(cx + halfRoad + 12, cy - 1);
      ctx.lineTo(width, cy - 1);
      ctx.moveTo(cx + halfRoad + 12, cy + 1);
      ctx.lineTo(width, cy + 1);
      ctx.stroke();

      // North divider
      ctx.beginPath();
      ctx.moveTo(cx - 1, 0);
      ctx.lineTo(cx - 1, cy - halfRoad - 12);
      ctx.moveTo(cx + 1, 0);
      ctx.lineTo(cx + 1, cy - halfRoad - 12);
      ctx.stroke();

      // South divider
      ctx.beginPath();
      ctx.moveTo(cx - 1, cy + halfRoad + 12);
      ctx.lineTo(cx - 1, height);
      ctx.moveTo(cx + 1, cy + halfRoad + 12);
      ctx.lineTo(cx + 1, height);
      ctx.stroke();

      // Dashed White Lane Dividers
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.25)';
      ctx.lineWidth = 1;
      ctx.setLineDash([8, 8]);

      // West lanes
      ctx.beginPath();
      ctx.moveTo(0, cy - halfRoad + laneWidth);
      ctx.lineTo(cx - halfRoad - 8, cy - halfRoad + laneWidth);
      ctx.moveTo(0, cy + halfRoad - laneWidth);
      ctx.lineTo(cx - halfRoad - 8, cy + halfRoad - laneWidth);
      ctx.stroke();

      // East lanes
      ctx.beginPath();
      ctx.moveTo(cx + halfRoad + 8, cy - halfRoad + laneWidth);
      ctx.lineTo(width, cy - halfRoad + laneWidth);
      ctx.moveTo(cx + halfRoad + 8, cy + halfRoad - laneWidth);
      ctx.lineTo(width, cy + halfRoad - laneWidth);
      ctx.stroke();

      // North lanes
      ctx.beginPath();
      ctx.moveTo(cx - halfRoad + laneWidth, 0);
      ctx.lineTo(cx - halfRoad + laneWidth, cy - halfRoad - 8);
      ctx.moveTo(cx + halfRoad - laneWidth, 0);
      ctx.lineTo(cx + halfRoad - laneWidth, cy - halfRoad - 8);
      ctx.stroke();

      // South lanes
      ctx.beginPath();
      ctx.moveTo(cx - halfRoad + laneWidth, cy + halfRoad + 8);
      ctx.lineTo(cx - halfRoad + laneWidth, height);
      ctx.moveTo(cx + halfRoad - laneWidth, cy + halfRoad + 8);
      ctx.lineTo(cx + halfRoad - laneWidth, height);
      ctx.stroke();
      ctx.setLineDash([]); // Reset dash

      // -------------------------------------------------------------
      // 3. Stop Bars & Zebra Crosswalks
      // -------------------------------------------------------------
      ctx.fillStyle = 'rgba(255, 255, 255, 0.45)';
      // Crosswalks around junction box
      const zebraWidth = 10;
      const stripeW = 3;

      // West Crosswalk
      for (let y = cy - halfRoad + 2; y < cy + halfRoad - 2; y += 7) {
        ctx.fillRect(cx - halfRoad - zebraWidth, y, stripeW, 4);
      }
      // East Crosswalk
      for (let y = cy - halfRoad + 2; y < cy + halfRoad - 2; y += 7) {
        ctx.fillRect(cx + halfRoad + zebraWidth - stripeW, y, stripeW, 4);
      }
      // North Crosswalk
      for (let x = cx - halfRoad + 2; x < cx + halfRoad - 2; x += 7) {
        ctx.fillRect(x, cy - halfRoad - zebraWidth, 4, stripeW);
      }
      // South Crosswalk
      for (let x = cx - halfRoad + 2; x < cx + halfRoad - 2; x += 7) {
        ctx.fillRect(x, cy + halfRoad + zebraWidth - stripeW, 4, stripeW);
      }

      // Stop Lines (Solid White)
      ctx.strokeStyle = '#FFFFFF';
      ctx.lineWidth = 2.5;

      // West Stop Line (Eastbound approach: cy to cy + halfRoad)
      ctx.beginPath();
      ctx.moveTo(cx - halfRoad - zebraWidth - 2, cy);
      ctx.lineTo(cx - halfRoad - zebraWidth - 2, cy + halfRoad);
      ctx.stroke();

      // East Stop Line (Westbound approach: cy - halfRoad to cy)
      ctx.beginPath();
      ctx.moveTo(cx + halfRoad + zebraWidth + 2, cy - halfRoad);
      ctx.lineTo(cx + halfRoad + zebraWidth + 2, cy);
      ctx.stroke();

      // North Stop Line (Southbound approach: cx to cx + halfRoad)
      ctx.beginPath();
      ctx.moveTo(cx, cy - halfRoad - zebraWidth - 2);
      ctx.lineTo(cx + halfRoad, cy - halfRoad - zebraWidth - 2);
      ctx.stroke();

      // South Stop Line (Northbound approach: cx - halfRoad to cx)
      ctx.beginPath();
      ctx.moveTo(cx - halfRoad, cy + halfRoad + zebraWidth + 2);
      ctx.lineTo(cx, cy + halfRoad + zebraWidth + 2);
      ctx.stroke();

      ctx.restore();

      // -------------------------------------------------------------
      // 4. Traffic Signal Heads & Glowing Beacons
      // -------------------------------------------------------------
      const nsLightColor =
        activePhase === 'NS_GREEN'
          ? '#45C982'
          : activePhase === 'NS_YELLOW'
          ? '#E9A23B'
          : '#EF4444';

      const ewLightColor =
        activePhase === 'EW_GREEN'
          ? '#45C982'
          : activePhase === 'EW_YELLOW'
          ? '#E9A23B'
          : '#EF4444';

      const drawSignalHead = (x: number, y: number, color: string, dir: string) => {
        ctx.save();
        // Signal Mast Base
        ctx.fillStyle = '#1e293b';
        ctx.beginPath();
        ctx.arc(x, y, 6, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = '#475569';
        ctx.lineWidth = 1;
        ctx.stroke();

        // Glowing Lamp
        ctx.fillStyle = color;
        ctx.shadowColor = color;
        ctx.shadowBlur = 10;
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fill();

        // Direction Indicator
        ctx.shadowBlur = 0;
        ctx.fillStyle = 'rgba(255, 255, 255, 0.6)';
        ctx.font = '8px monospace';
        ctx.fillText(dir, x + 8, y + 3);
        ctx.restore();
      };

      // Draw 4 corner signal gantries
      drawSignalHead(cx - halfRoad - 8, cy + halfRoad + 16, nsLightColor, 'S->N');
      drawSignalHead(cx + halfRoad + 8, cy - halfRoad - 16, nsLightColor, 'N->S');
      drawSignalHead(cx - halfRoad - 16, cy - halfRoad - 8, ewLightColor, 'W->E');
      drawSignalHead(cx + halfRoad + 16, cy + halfRoad + 8, ewLightColor, 'E->W');

      // -------------------------------------------------------------
      // 5. Radar / Vision Cones from Camera Masts (CAM_J1 - CAM_J4)
      // -------------------------------------------------------------
      if (stateRef.current.showRadar) {
        ctx.save();

        const drawCameraCone = (
          x: number,
          y: number,
          baseAngle: number,
          label: string,
          hasIncident: boolean
        ) => {
          const coneLength = Math.min(width * 0.16, 95);
          const coneSpread = 0.55;

          const coneGrad = ctx.createRadialGradient(x, y, 5, x, y, coneLength);
          if (hasIncident) {
            coneGrad.addColorStop(0, 'rgba(239, 68, 68, 0.35)');
            coneGrad.addColorStop(0.8, 'rgba(239, 68, 68, 0.08)');
            coneGrad.addColorStop(1, 'rgba(239, 68, 68, 0)');
          } else {
            coneGrad.addColorStop(0, 'rgba(69, 201, 130, 0.25)');
            coneGrad.addColorStop(0.8, 'rgba(69, 201, 130, 0.05)');
            coneGrad.addColorStop(1, 'rgba(69, 201, 130, 0)');
          }

          ctx.fillStyle = coneGrad;
          ctx.beginPath();
          ctx.moveTo(x, y);
          ctx.arc(x, y, coneLength, baseAngle - coneSpread, baseAngle + coneSpread);
          ctx.closePath();
          ctx.fill();

          // Sweeping radar scanline ray
          const rayAngle = baseAngle - coneSpread + ((Math.sin(time * 0.0025 + x) + 1) * 0.5) * (coneSpread * 2);
          ctx.strokeStyle = hasIncident ? 'rgba(239, 68, 68, 0.6)' : 'rgba(69, 201, 130, 0.6)';
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.moveTo(x, y);
          ctx.lineTo(x + Math.cos(rayAngle) * coneLength, y + Math.sin(rayAngle) * coneLength);
          ctx.stroke();

          // Camera Mast Post
          ctx.fillStyle = hasIncident ? '#EF4444' : '#45C982';
          ctx.shadowColor = hasIncident ? '#EF4444' : '#45C982';
          ctx.shadowBlur = 8;
          ctx.beginPath();
          ctx.arc(x, y, 3.5, 0, Math.PI * 2);
          ctx.fill();

          // Mast Label
          ctx.shadowBlur = 0;
          ctx.fillStyle = hasIncident ? '#F87171' : 'rgba(255, 255, 255, 0.6)';
          ctx.font = '9px monospace';
          ctx.fillText(label, x - 14, y - 8);

          if (hasIncident) {
            // Pulsing warning ring around faulted camera
            const pulse = (Math.sin(time * 0.008) + 1) * 8 + 8;
            ctx.strokeStyle = 'rgba(239, 68, 68, 0.7)';
            ctx.lineWidth = 1.5;
            ctx.beginPath();
            ctx.arc(x, y, pulse, 0, Math.PI * 2);
            ctx.stroke();
          }
        };

        const isJ1Fault = incidentJunction?.junction_id === 'J1';
        const isJ2Fault = incidentJunction?.junction_id === 'J2';
        const isJ3Fault = incidentJunction?.junction_id === 'J3';
        const isJ4Fault = incidentJunction?.junction_id === 'J4';

        drawCameraCone(cx - halfRoad - 20, cy - halfRoad - 20, Math.PI * 0.25, 'CAM_J1', isJ1Fault);
        drawCameraCone(cx + halfRoad + 20, cy - halfRoad - 20, Math.PI * 0.75, 'CAM_J2', isJ2Fault);
        drawCameraCone(cx - halfRoad - 20, cy + halfRoad + 20, -Math.PI * 0.25, 'CAM_J3', isJ3Fault);
        drawCameraCone(cx + halfRoad + 20, cy + halfRoad + 20, -Math.PI * 0.75, 'CAM_J4', isJ4Fault);

        ctx.restore();
      }

      // -------------------------------------------------------------
      // 6. Vehicle Physics & Motion Simulation
      // -------------------------------------------------------------
      const stopDistanceW = cx - halfRoad - zebraWidth - 8;
      const stopDistanceE = cx + halfRoad + zebraWidth + 8;
      const stopDistanceN = cy - halfRoad - zebraWidth - 8;
      const stopDistanceS = cy + halfRoad + zebraWidth + 8;

      const densityMultiplier = stateRef.current.trafficDensity === 'rush' ? 1.6 : 1.0;

      // Spawn new vehicles if count drops or for continuous flow
      if (vehicles.length < 24 * densityMultiplier && Math.random() < 0.06 * densityMultiplier) {
        vehicles.push(spawnVehicle());
      }

      // Sort vehicles by lane and distance for queueing
      vehicles.sort((a, b) => b.dist - a.dist);

      for (let i = vehicles.length - 1; i >= 0; i--) {
        const v = vehicles[i];

        if (!stateRef.current.isPlaying) {
          // paused
        } else {
          // Check vehicle ahead in same lane & sublane
          let distToLeader = 9999;
          for (let j = 0; j < vehicles.length; j++) {
            if (i === j) continue;
            const other = vehicles[j];
            if (other.lane === v.lane && other.subLane === v.subLane && other.dist > v.dist) {
              const d = other.dist - v.dist - other.length;
              if (d < distToLeader) {
                distToLeader = d;
              }
            }
          }

          // Check traffic light status for this lane
          let lightRed = false;
          let stopLineDist = 0;

          if (v.lane === 'W_E') {
            stopLineDist = stopDistanceW;
            lightRed = activePhase !== 'EW_GREEN';
          } else if (v.lane === 'E_W') {
            stopLineDist = width - stopDistanceE;
            lightRed = activePhase !== 'EW_GREEN';
          } else if (v.lane === 'N_S') {
            stopLineDist = stopDistanceN;
            lightRed = activePhase !== 'NS_GREEN';
          } else if (v.lane === 'S_N') {
            stopLineDist = height - stopDistanceS;
            lightRed = activePhase !== 'NS_GREEN';
          }

          // Distance to stop bar
          const distToStop = stopLineDist - v.dist;
          const approachingRed = lightRed && distToStop > 0 && distToStop < 90;

          // Target Speed Calculation
          let targetSpeed = v.maxSpeed;

          if (approachingRed) {
            // Smoothly decelerate to a stop before the stop bar
            targetSpeed = 0;
            v.braking = true;
          } else if (distToLeader < 28) {
            // Decelerate behind car in front
            targetSpeed = 0;
            v.braking = true;
          } else if (distToLeader < 55) {
            targetSpeed = v.maxSpeed * 0.4;
            v.braking = true;
          } else {
            v.braking = false;
          }

          // Speed smoothing
          if (v.speed < targetSpeed) {
            v.speed = Math.min(v.speed + v.accel, targetSpeed);
          } else if (v.speed > targetSpeed) {
            v.speed = Math.max(v.speed - v.accel * 2.2, targetSpeed);
          }

          // Move vehicle forward
          v.dist += v.speed;
        }

        // Calculate (x, y) and heading angle based on lane & distance
        let vx = 0;
        let vy = 0;
        let heading = 0; // In radians

        if (v.lane === 'W_E') {
          // Driving Eastbound (cy to cy + halfRoad)
          const laneOffset = v.subLane === 0 ? laneWidth * 0.5 : laneWidth * 1.5;
          vy = cy + laneOffset;
          vx = v.dist;
          heading = 0; // Facing East

          // Turning logic in intersection
          if (v.turning === 'left' && vx > cx - laneOffset && vx < cx + halfRoad) {
            heading = -Math.PI / 2 * ((vx - (cx - laneOffset)) / roadWidth);
            vy -= ((vx - (cx - laneOffset)) * 0.6);
          }
        } else if (v.lane === 'E_W') {
          // Driving Westbound (cy - halfRoad to cy)
          const laneOffset = v.subLane === 0 ? laneWidth * 0.5 : laneWidth * 1.5;
          vy = cy - laneOffset;
          vx = width - v.dist;
          heading = Math.PI; // Facing West

          if (v.turning === 'left' && vx < cx + laneOffset && vx > cx - halfRoad) {
            heading = Math.PI + Math.PI / 2 * (((cx + laneOffset) - vx) / roadWidth);
            vy += (((cx + laneOffset) - vx) * 0.6);
          }
        } else if (v.lane === 'N_S') {
          // Driving Southbound (cx to cx + halfRoad)
          const laneOffset = v.subLane === 0 ? laneWidth * 0.5 : laneWidth * 1.5;
          vx = cx + laneOffset;
          vy = v.dist;
          heading = Math.PI / 2; // Facing South
        } else if (v.lane === 'S_N') {
          // Driving Northbound (cx - halfRoad to cx)
          const laneOffset = v.subLane === 0 ? laneWidth * 0.5 : laneWidth * 1.5;
          vx = cx - laneOffset;
          vy = height - v.dist;
          heading = -Math.PI / 2; // Facing North
        }

        // Despawn off-screen vehicles
        const maxDist = Math.max(width, height) + 80;
        if (v.dist > maxDist) {
          vehicles.splice(i, 1);
          continue;
        }

        // -------------------------------------------------------------
        // 7. Render Individual Vehicle
        // -------------------------------------------------------------
        ctx.save();
        ctx.translate(vx, vy);
        ctx.rotate(heading);

        // Headlight Beams (casting onto asphalt ahead)
        const lightGrad = ctx.createRadialGradient(
          v.length * 0.5,
          0,
          2,
          v.length * 0.5 + 24,
          0,
          28
        );
        lightGrad.addColorStop(0, 'rgba(255, 255, 230, 0.45)');
        lightGrad.addColorStop(0.6, 'rgba(255, 255, 210, 0.12)');
        lightGrad.addColorStop(1, 'rgba(255, 255, 200, 0)');

        ctx.fillStyle = lightGrad;
        ctx.beginPath();
        ctx.moveTo(v.length * 0.5, -v.width * 0.35);
        ctx.lineTo(v.length * 0.5 + 26, -v.width * 1.2);
        ctx.lineTo(v.length * 0.5 + 26, v.width * 1.2);
        ctx.lineTo(v.length * 0.5, v.width * 0.35);
        ctx.closePath();
        ctx.fill();

        // Vehicle Chassis Shadow
        ctx.fillStyle = 'rgba(0, 0, 0, 0.65)';
        ctx.fillRect(-v.length * 0.5 + 1, -v.width * 0.5 + 1, v.length, v.width);

        // Vehicle Body
        ctx.fillStyle = v.color;
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
        ctx.lineWidth = 0.8;

        // Rounded chassis rectangle
        ctx.beginPath();
        const r = 2;
        ctx.roundRect(-v.length * 0.5, -v.width * 0.5, v.length, v.width, [r, r, r, r]);
        ctx.fill();
        ctx.stroke();

        // Windshield / Cabin Glass
        ctx.fillStyle = '#0f172a';
        ctx.fillRect(-v.length * 0.15, -v.width * 0.35, v.length * 0.45, v.width * 0.7);

        // Emergency Flashing Strobe (if emergency vehicle)
        if (v.type === 'emergency') {
          const strobe = Math.sin(time * 0.02) > 0;
          ctx.fillStyle = strobe ? '#EF4444' : '#38BDF8';
          ctx.shadowColor = strobe ? '#EF4444' : '#38BDF8';
          ctx.shadowBlur = 8;
          ctx.beginPath();
          ctx.arc(0, 0, 2.5, 0, Math.PI * 2);
          ctx.fill();
          ctx.shadowBlur = 0;
        }

        // Autonomous Lidar Dome (if autonomous pod)
        if (v.type === 'autonomous') {
          ctx.fillStyle = '#45C982';
          ctx.shadowColor = '#45C982';
          ctx.shadowBlur = 6;
          ctx.beginPath();
          ctx.arc(0, 0, 1.8, 0, Math.PI * 2);
          ctx.fill();
          ctx.shadowBlur = 0;
        }

        // Taillights (Red) - Brighten when braking
        ctx.fillStyle = v.braking ? '#FF2222' : '#B91C1C';
        ctx.shadowColor = v.braking ? '#FF2222' : '#991B1B';
        ctx.shadowBlur = v.braking ? 8 : 2;

        ctx.fillRect(-v.length * 0.5 - 0.5, -v.width * 0.45, 1.2, 2);
        ctx.fillRect(-v.length * 0.5 - 0.5, v.width * 0.45 - 2, 1.2, 2);
        ctx.shadowBlur = 0;

        // 3D YOLO Bounding Box Reticle
        if (stateRef.current.showReticles) {
          ctx.strokeStyle = v.type === 'autonomous' ? 'rgba(69, 201, 130, 0.75)' : 'rgba(56, 189, 248, 0.5)';
          ctx.lineWidth = 0.8;
          ctx.strokeRect(-v.length * 0.6, -v.width * 0.7, v.length * 1.2, v.width * 1.4);

          // Micro detection tag
          ctx.fillStyle = v.type === 'autonomous' ? '#45C982' : '#38BDF8';
          ctx.font = '7px monospace';
          ctx.fillText(`[${v.label.slice(0, 7)}]`, -v.length * 0.6, -v.width * 0.8);
        }

        ctx.restore();
      }

      // -------------------------------------------------------------
      // 8. Incident Banner Reticle Overlay (if incident is active!)
      // -------------------------------------------------------------
      if (incidentJunction) {
        ctx.save();
        ctx.fillStyle = 'rgba(239, 68, 68, 0.12)';
        ctx.strokeStyle = '#EF4444';
        ctx.lineWidth = 1.5;
        ctx.setLineDash([6, 4]);

        // Draw alert frame around the faulted intersection quadrant
        ctx.strokeRect(cx - halfRoad - 24, cy - halfRoad - 24, roadWidth + 48, roadWidth + 48);
        ctx.fillRect(cx - halfRoad - 24, cy - halfRoad - 24, roadWidth + 48, roadWidth + 48);
        ctx.setLineDash([]);

        // Holographic warning tag
        ctx.fillStyle = '#EF4444';
        ctx.font = 'bold 10px monospace';
        const alertText = `[!] INCIDENT ENGAGED: ${incidentJunction.junction_id} SENSOR FAULT DETECTED`;
        ctx.fillText(alertText, cx - 140, cy - halfRoad - 32);
        ctx.restore();
      }

      // -------------------------------------------------------------
      // 9. Seamless Vignette Gradient (Edges fade smoothly into #080D10)
      // -------------------------------------------------------------
      ctx.save();
      // Top Edge Fade
      const topGrad = ctx.createLinearGradient(0, 0, 0, 48);
      topGrad.addColorStop(0, '#080D10');
      topGrad.addColorStop(1, 'rgba(8, 13, 16, 0)');
      ctx.fillStyle = topGrad;
      ctx.fillRect(0, 0, width, 48);

      // Bottom Edge Fade
      const btmGrad = ctx.createLinearGradient(0, height - 48, 0, height);
      btmGrad.addColorStop(0, 'rgba(8, 13, 16, 0)');
      btmGrad.addColorStop(1, '#080D10');
      ctx.fillStyle = btmGrad;
      ctx.fillRect(0, height - 48, width, 48);

      // Left Edge Fade
      const leftGrad = ctx.createLinearGradient(0, 0, 64, 0);
      leftGrad.addColorStop(0, '#080D10');
      leftGrad.addColorStop(1, 'rgba(8, 13, 16, 0)');
      ctx.fillStyle = leftGrad;
      ctx.fillRect(0, 0, 64, height);

      // Right Edge Fade
      const rightGrad = ctx.createLinearGradient(width - 64, 0, width, 0);
      rightGrad.addColorStop(0, 'rgba(8, 13, 16, 0)');
      rightGrad.addColorStop(1, '#080D10');
      ctx.fillStyle = rightGrad;
      ctx.fillRect(width - 64, 0, 64, height);
      ctx.restore();
    };

    animId = requestAnimationFrame(render);

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className="relative w-full bg-[#080D10] overflow-hidden select-none -mb-2"
      style={{
        minHeight: '230px',
      }}
    >
      {/* Canvas Viewport */}
      <canvas ref={canvasRef} className="block w-full" />

      {/* Embedded HUD Telemetry Header */}
      <div className="absolute top-3 left-4 right-4 flex items-center justify-between pointer-events-none z-10 text-xs font-mono">
        <div className="flex items-center gap-3 bg-[#080D10]/80 backdrop-blur-md px-3 py-1.5 rounded-full border border-white/10 shadow-lg pointer-events-auto">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#45C982] opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-[#45C982]" />
          </span>
          <span className="font-semibold text-white tracking-wide">ILLUSTRATIVE VISUALIZATION</span>
          <span className="text-white/40">|</span>
          <span className="text-[#45C982]">NOT CONNECTED TO LIVE SIMULATION</span>
          <span className="hidden md:inline text-white/40">|</span>
          <span className="hidden md:inline text-white/70">UI PREVIEW</span>
        </div>

        {/* Tactical Control Pills */}
        <div className="flex items-center gap-2 pointer-events-auto">
          {/* Phase Badge */}
          <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#080D10]/85 border border-white/10 text-[11px] text-white/80">
            <Activity className="w-3 h-3 text-[#45C982]" />
            <span>CONCEPT:</span>
            <span
              className={`font-semibold ${
                phaseDisplay.includes('GREEN')
                  ? 'text-[#45C982]'
                  : phaseDisplay.includes('YELLOW')
                  ? 'text-[#E9A23B]'
                  : 'text-rose-400'
              }`}
            >
              {phaseDisplay} ({phaseCountdown}s)
            </span>
          </div>

          {/* Density Toggle */}
          <button
            onClick={() => setTrafficDensity((prev) => (prev === 'nominal' ? 'rush' : 'nominal'))}
            className={`px-2.5 py-1 rounded border text-[11px] transition-all cursor-pointer ${
              trafficDensity === 'rush'
                ? 'border-[#E9A23B]/60 bg-[#E9A23B]/10 text-[#E9A23B]'
                : 'border-white/10 bg-[#080D10]/80 text-white/60 hover:text-white'
            }`}
            title="Adjust illustrative animation density"
          >
            {trafficDensity === 'rush' ? 'RUSH HOUR (1.6x)' : 'NOMINAL FLOW'}
          </button>

          {/* Reticles Toggle */}
          <button
            onClick={() => setShowReticles(!showReticles)}
            className={`px-2 py-1 rounded border text-[11px] transition-all cursor-pointer ${
              showReticles
                ? 'border-[#45C982]/60 bg-[#45C982]/10 text-[#45C982]'
                : 'border-white/10 bg-[#080D10]/80 text-white/40 hover:text-white'
            }`}
            title="Toggle Object Reticles"
          >
            <Eye className="w-3 h-3" />
          </button>

          {/* Radar Cones Toggle */}
          <button
            onClick={() => setShowRadar(!showRadar)}
            className={`px-2 py-1 rounded border text-[11px] transition-all cursor-pointer ${
              showRadar
                ? 'border-[#45C982]/60 bg-[#45C982]/10 text-[#45C982]'
                : 'border-white/10 bg-[#080D10]/80 text-white/40 hover:text-white'
            }`}
            title="Toggle Sensor Cones"
          >
            <Radar className="w-3 h-3" />
          </button>

          {/* Play / Pause Toggle */}
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            className="p-1 rounded border border-white/10 bg-[#080D10]/80 text-white/70 hover:text-white hover:border-white/30 transition-all cursor-pointer"
            title={isPlaying ? 'Pause illustrative animation' : 'Resume illustrative animation'}
          >
            {isPlaying ? <Pause className="w-3 h-3" /> : <Play className="w-3 h-3 text-[#45C982]" />}
          </button>
        </div>
      </div>

      {/* Embedded HUD Telemetry Footer (Subtle Bottom Micro-Strip) */}
      <div className="absolute bottom-1.5 left-6 right-6 flex items-center justify-between pointer-events-none z-10 text-[10px] font-mono text-white/40">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-[#45C982]" />
            ILLUSTRATIVE VEHICLES: <strong className="text-white/80">{vehicleCount}</strong>
          </span>
          <span className="hidden sm:inline">NODES: J1 (CORE) &bull; J2 (ARTERIAL) &bull; J3 (WEST) &bull; J4 (SOUTH)</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1">
            <ShieldCheck className="w-3 h-3 text-[#45C982]" />
            DETERMINISTIC PHASE GUARD ACTIVE
          </span>
          <span className="hidden md:inline">FEED REVISION #{snapshot?.state_revision ?? '—'}</span>
        </div>
      </div>
    </div>
  );
};
