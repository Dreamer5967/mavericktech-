import React from 'react';

interface FloatingObjectProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

/**
 * 3D Traffic Signal Head (Isometric Housing with 3 Light Lenses & Visor Hoods)
 */
export const Floating3DTrafficLight: React.FC<FloatingObjectProps & { activeLight?: 'red' | 'yellow' | 'green' }> = ({
  className = '',
  size = 'md',
  activeLight = 'green',
}) => {
  const scale = size === 'sm' ? 'scale-75' : size === 'lg' ? 'scale-110' : 'scale-90';

  return (
    <div className={`perspective-1000 select-none pointer-events-none ${className}`}>
      <div className={`transform-style-3d animate-float-3d ${scale}`}>
        {/* Shadow base on ground plane */}
        <div className="absolute -bottom-8 left-1/2 -translate-x-1/2 w-28 h-8 bg-slate-900/10 rounded-full blur-md" />

        {/* 3D Extruded Signal Housing */}
        <div
          className="relative w-24 h-64 rounded-2xl bg-gradient-to-br from-slate-900 via-slate-800 to-slate-950 p-3 shadow-2xl border-2 border-orange-500/40"
          style={{
            transform: 'rotateX(16deg) rotateY(-22deg) rotateZ(2deg)',
            transformStyle: 'preserve-3d',
            boxShadow: '16px 20px 35px -8px rgba(15, 23, 42, 0.35), 0 0 0 1px rgba(249, 115, 22, 0.2)',
          }}
        >
          {/* Top Mounting Bracket */}
          <div
            className="absolute -top-4 left-1/2 -translate-x-1/2 w-5 h-4 bg-slate-700 rounded-t border-t border-slate-600"
            style={{ transform: 'translateZ(-5px)' }}
          />

          {/* Side 3D extrusion illusion (right edge) */}
          <div
            className="absolute top-1 right-[-10px] w-[10px] h-[calc(100%-8px)] bg-slate-950/90 rounded-r-sm"
            style={{
              transform: 'rotateY(90deg) translateZ(-5px)',
              transformOrigin: 'left center',
            }}
          />

          {/* Yellow/Orange High-Visibility Backplate Border */}
          <div className="absolute inset-[-6px] rounded-3xl border border-orange-400/30 pointer-events-none -z-10 bg-slate-900/20 backdrop-blur-[1px]" />

          {/* Inner Signal Lamps Column */}
          <div className="flex flex-col justify-between h-full py-1">
            {/* 1. Red Signal Lamp */}
            <div className="relative flex flex-col items-center">
              {/* Visor Hood */}
              <div
                className="w-14 h-4 bg-slate-950 rounded-t-full border-t border-slate-700 shadow-sm"
                style={{ transform: 'translateZ(10px) rotateX(15deg)' }}
              />
              {/* Lens Housing */}
              <div className="w-14 h-14 rounded-full bg-slate-950 p-1.5 shadow-inner border border-slate-700/80">
                <div
                  className={`w-full h-full rounded-full transition-all duration-300 relative overflow-hidden flex items-center justify-center ${
                    activeLight === 'red'
                      ? 'bg-rose-500 shadow-[0_0_24px_rgba(244,63,94,0.9)] border border-rose-300'
                      : 'bg-rose-950/50 border border-rose-900/40 opacity-40'
                  }`}
                >
                  {/* Concentric Fresnel Lens Texture */}
                  <div className="absolute inset-1 rounded-full border border-white/20" />
                  <div className="absolute inset-2.5 rounded-full border border-white/15" />
                  <div className="w-3 h-3 rounded-full bg-white/40 blur-[1px]" />
                </div>
              </div>
            </div>

            {/* 2. Amber Signal Lamp */}
            <div className="relative flex flex-col items-center">
              {/* Visor Hood */}
              <div
                className="w-14 h-4 bg-slate-950 rounded-t-full border-t border-slate-700 shadow-sm"
                style={{ transform: 'translateZ(10px) rotateX(15deg)' }}
              />
              {/* Lens Housing */}
              <div className="w-14 h-14 rounded-full bg-slate-950 p-1.5 shadow-inner border border-slate-700/80">
                <div
                  className={`w-full h-full rounded-full transition-all duration-300 relative overflow-hidden flex items-center justify-center ${
                    activeLight === 'yellow'
                      ? 'bg-amber-400 shadow-[0_0_24px_rgba(251,191,36,0.9)] border border-amber-200'
                      : 'bg-amber-950/50 border border-amber-900/40 opacity-40'
                  }`}
                >
                  <div className="absolute inset-1 rounded-full border border-white/20" />
                  <div className="absolute inset-2.5 rounded-full border border-white/15" />
                  <div className="w-3 h-3 rounded-full bg-white/40 blur-[1px]" />
                </div>
              </div>
            </div>

            {/* 3. Green Signal Lamp */}
            <div className="relative flex flex-col items-center">
              {/* Visor Hood */}
              <div
                className="w-14 h-4 bg-slate-950 rounded-t-full border-t border-slate-700 shadow-sm"
                style={{ transform: 'translateZ(10px) rotateX(15deg)' }}
              />
              {/* Lens Housing */}
              <div className="w-14 h-14 rounded-full bg-slate-950 p-1.5 shadow-inner border border-slate-700/80">
                <div
                  className={`w-full h-full rounded-full transition-all duration-300 relative overflow-hidden flex items-center justify-center ${
                    activeLight === 'green'
                      ? 'bg-emerald-500 shadow-[0_0_28px_rgba(16,185,129,0.95)] border border-emerald-300'
                      : 'bg-emerald-950/50 border border-emerald-900/40 opacity-40'
                  }`}
                >
                  <div className="absolute inset-1 rounded-full border border-white/20" />
                  <div className="absolute inset-2.5 rounded-full border border-white/15" />
                  <div className="w-3 h-3 rounded-full bg-white/40 blur-[1px]" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

/**
 * 3D Floating Signal Lens (Concentric Fresnel glass with safety orange rim)
 */
export const Floating3DSignalLens: React.FC<FloatingObjectProps & { color?: 'orange' | 'emerald' | 'amber' }> = ({
  className = '',
  color = 'orange',
}) => {
  const colorMap = {
    orange: {
      rim: 'border-orange-500/60',
      core: 'bg-gradient-to-tr from-orange-600 to-amber-400',
      shadow: 'shadow-[0_0_25px_rgba(249,115,22,0.45)]',
      glow: 'bg-orange-500/10',
    },
    emerald: {
      rim: 'border-emerald-500/60',
      core: 'bg-gradient-to-tr from-emerald-600 to-teal-300',
      shadow: 'shadow-[0_0_25px_rgba(16,185,129,0.45)]',
      glow: 'bg-emerald-500/10',
    },
    amber: {
      rim: 'border-amber-500/60',
      core: 'bg-gradient-to-tr from-amber-500 to-yellow-300',
      shadow: 'shadow-[0_0_25px_rgba(245,158,11,0.45)]',
      glow: 'bg-amber-500/10',
    },
  }[color];

  return (
    <div className={`perspective-1000 select-none pointer-events-none ${className}`}>
      <div className="transform-style-3d animate-float-3d-lens">
        <div
          className={`relative w-28 h-28 rounded-full bg-white p-2 border-2 ${colorMap.rim} shadow-2xl ${colorMap.shadow}`}
          style={{
            transform: 'rotateX(26deg) rotateY(-18deg)',
            transformStyle: 'preserve-3d',
          }}
        >
          {/* Beveled metallic ring */}
          <div className="w-full h-full rounded-full bg-slate-900 p-2 shadow-inner flex items-center justify-center relative overflow-hidden">
            {/* Concentric rings */}
            <div className="absolute inset-1 rounded-full border border-white/20" />
            <div className="absolute inset-2.5 rounded-full border border-white/20" />
            <div className="absolute inset-4 rounded-full border border-white/20" />
            {/* Glowing Core */}
            <div className={`w-10 h-10 rounded-full ${colorMap.core} shadow-lg relative flex items-center justify-center`}>
              <div className="w-4 h-4 rounded-full bg-white/60 blur-[1px]" />
            </div>
          </div>

          {/* Outer floating orbital indicator ring */}
          <div
            className="absolute -inset-2.5 rounded-full border border-dashed border-slate-300/60 animate-spin"
            style={{ animationDuration: '24s' }}
          />
        </div>
      </div>
    </div>
  );
};

/**
 * 3D Traffic Intersection Diamond Beacon
 */
export const Floating3DIntersectionBeacon: React.FC<FloatingObjectProps> = ({ className = '' }) => {
  return (
    <div className={`perspective-1000 select-none pointer-events-none ${className}`}>
      <div className="transform-style-3d animate-float-3d-reverse">
        <div
          className="relative w-32 h-32 rounded-2xl bg-white p-3.5 border-2 border-slate-200 shadow-2xl shadow-slate-300/40"
          style={{
            transform: 'rotateX(45deg) rotateZ(45deg)',
            transformStyle: 'preserve-3d',
          }}
        >
          {/* Intersection Grid Lines */}
          <div className="w-full h-full rounded-lg bg-slate-900 p-2 relative flex items-center justify-center">
            {/* Cross lanes */}
            <div className="absolute w-full h-5 bg-slate-800" />
            <div className="absolute h-full w-5 bg-slate-800" />

            {/* 4 Corner Traffic Light Pips */}
            <div className="absolute top-1 left-1 w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.8)]" />
            <div className="absolute top-1 right-1 w-2.5 h-2.5 rounded-full bg-rose-500 shadow-[0_0_6px_rgba(244,63,94,0.8)]" />
            <div className="absolute bottom-1 left-1 w-2.5 h-2.5 rounded-full bg-rose-500 shadow-[0_0_6px_rgba(244,63,94,0.8)]" />
            <div className="absolute bottom-1 right-1 w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.8)]" />

            {/* Center Junction Controller Hub */}
            <div className="w-4 h-4 rounded-full bg-orange-500 shadow-[0_0_10px_rgba(249,115,22,0.9)] relative z-10 flex items-center justify-center">
              <div className="w-1.5 h-1.5 rounded-full bg-white" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

/**
 * 3D Traffic Detection Sensor Node
 */
export const Floating3DSensorNode: React.FC<FloatingObjectProps> = ({ className = '' }) => {
  return (
    <div className={`perspective-1000 select-none pointer-events-none ${className}`}>
      <div className="transform-style-3d animate-float-3d">
        <div
          className="relative w-28 h-20 rounded-xl bg-white border border-slate-200 shadow-xl shadow-slate-300/50 p-2.5 flex items-center gap-2.5"
          style={{
            transform: 'rotateX(14deg) rotateY(-18deg) rotateZ(3deg)',
            transformStyle: 'preserve-3d',
          }}
        >
          {/* Sensor Lens */}
          <div className="w-10 h-10 rounded-lg bg-slate-900 border border-slate-700 flex items-center justify-center flex-shrink-0 shadow-inner">
            <div className="w-6 h-6 rounded-full bg-orange-500/20 border border-orange-400/80 flex items-center justify-center">
              <div className="w-2.5 h-2.5 rounded-full bg-orange-500 shadow-[0_0_8px_rgba(249,115,22,0.9)] animate-pulse" />
            </div>
          </div>

          {/* Telemetry Indicator */}
          <div className="flex-grow font-mono text-[9px] text-slate-500 leading-tight">
            <div className="text-slate-800 font-bold uppercase tracking-wider">RADAR · J3</div>
            <div className="text-emerald-600 font-semibold mt-0.5">30 FPS STREAM</div>
            <div className="text-slate-400">YOLOv10 INGEST</div>
          </div>
        </div>
      </div>
    </div>
  );
};
