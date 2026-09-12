import React, { useState, useRef, useEffect } from 'react';
import { Play, Pause, Zap, RefreshCw, Maximize2, MousePointer } from 'lucide-react';
import { botApi } from '../../api/botApi';
import { translateStageToThai } from '../../utils/translations';

interface StreamPlayerProps {
  deviceSerial: string;
  stageName: string;
  isRunning: boolean;
}

export const StreamPlayer: React.FC<StreamPlayerProps> = ({
  deviceSerial,
  stageName,
  isRunning,
}) => {
  const [fpsMode, setFpsMode] = useState<60 | 30 | 5>(60);
  const [streamError, setStreamError] = useState(false);
  const [clickRipple, setClickRipple] = useState<{ x: number; y: number } | null>(null);
  const [lastTap, setLastTap] = useState<{ x: number; y: number } | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const streamUrl = deviceSerial
    ? `/api/stream?device=${encodeURIComponent(deviceSerial)}&fps=${fpsMode}&t=${Date.now()}`
    : '';

  const handleCanvasClick = async (e: React.MouseEvent<HTMLImageElement>) => {
    if (!deviceSerial) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;

    // Show ripple effect
    setClickRipple({ x: clickX, y: clickY });
    setTimeout(() => setClickRipple(null), 600);

    // Map to 1280x720 internal coordinate space
    const targetX = Math.round((clickX / rect.width) * 1280);
    const targetY = Math.round((clickY / rect.height) * 720);

    setLastTap({ x: targetX, y: targetY });
    setTimeout(() => setLastTap(null), 1500);

    try {
      await botApi.tapScreen(deviceSerial, targetX, targetY);
    } catch (err) {
      console.error('Tap failed:', err);
    }
  };

  return (
    <div className="bg-white border border-purple-100 rounded-3xl p-4 shadow-card space-y-3">
      {/* Header bar of Stream Canvas */}
      <div className="flex items-center justify-between pb-2 border-b border-purple-50">
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></div>
          <h3 className="text-xs font-bold text-slate-800">
            หน้าจอถ่ายทอดสด (Interactive Live Screen)
          </h3>
          <span className="text-[10px] text-slate-400 font-mono hidden sm:inline">
            คลิกบนจอเพื่อแตะสั่งการ
          </span>
        </div>

        {/* FPS Mode Selector */}
        <div className="flex items-center gap-1 bg-slate-100 p-0.5 rounded-xl text-[11px] font-bold">
          <button
            onClick={() => setFpsMode(60)}
            className={`px-2.5 py-1 rounded-lg transition ${
              fpsMode === 60 ? 'bg-white text-brand-700 shadow-xs' : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            60 FPS
          </button>
          <button
            onClick={() => setFpsMode(30)}
            className={`px-2.5 py-1 rounded-lg transition ${
              fpsMode === 30 ? 'bg-white text-brand-700 shadow-xs' : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            30 FPS
          </button>
          <button
            onClick={() => setFpsMode(5)}
            className={`px-2.5 py-1 rounded-lg transition ${
              fpsMode === 5 ? 'bg-white text-emerald-700 shadow-xs' : 'text-slate-500 hover:text-slate-800'
            }`}
            title="ประหยัดทรัพยากรเครื่อง"
          >
            Eco
          </button>
        </div>
      </div>

      {/* Screen Container */}
      <div
        ref={containerRef}
        className="relative bg-slate-950 rounded-2xl aspect-video overflow-hidden border border-purple-100 flex items-center justify-center shadow-inner group cursor-crosshair select-none"
      >
        {streamUrl && !streamError ? (
          <img
            src={streamUrl}
            alt="Device Stream"
            onClick={handleCanvasClick}
            onError={() => setStreamError(true)}
            draggable={false}
            onDragStart={(e) => e.preventDefault()}
            className="w-full h-full object-contain pointer-events-auto select-none"
          />
        ) : (
          <div className="text-center text-slate-400 text-xs p-6 space-y-2">
            <p>ไม่สามารถโหลดภาพสดได้ หรือบอทยังไม่ได้เชื่อมต่อ</p>
            <button
              onClick={() => setStreamError(false)}
              className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-bold text-xs"
            >
              ลองใหม่
            </button>
          </div>
        )}

        {/* Stage Overlay Badge */}
        <div className="absolute top-3 left-3 pointer-events-none flex items-center gap-1.5 bg-black/60 backdrop-blur-md px-2.5 py-1 rounded-xl text-white text-[11px] font-bold border border-white/10 shadow-xs">
          <span className={`w-2 h-2 rounded-full ${isRunning ? 'bg-emerald-400 animate-ping' : 'bg-slate-400'}`}></span>
          <span>{translateStageToThai(stageName, isRunning)}</span>
        </div>

        {/* Last Tap Coordinate Badge */}
        {lastTap && (
          <div className="absolute top-3 right-3 pointer-events-none flex items-center gap-1 bg-brand-600/90 text-white text-[11px] font-bold px-2.5 py-1 rounded-xl shadow-md animate-fade-in backdrop-blur-xs">
            <MousePointer className="w-3 h-3" />
            <span>แตะที่ ({lastTap.x}, {lastTap.y})</span>
          </div>
        )}

        {/* Click Ripple Indicator */}
        {clickRipple && (
          <div
            style={{ left: clickRipple.x, top: clickRipple.y }}
            className="absolute -translate-x-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-brand-400/40 border-2 border-brand-300 pointer-events-none animate-ping"
          ></div>
        )}

        {/* Interactive Click Helper Icon Hint */}
        <div className="absolute bottom-3 right-3 pointer-events-none bg-black/50 backdrop-blur-xs px-2 py-0.5 rounded-lg text-white/80 text-[10px] font-medium flex items-center gap-1 opacity-0 group-hover:opacity-100 transition">
          <MousePointer className="w-3 h-3" />
          <span>แตะเพื่อส่งคำสั่งกดจอ</span>
        </div>
      </div>
    </div>
  );
};
