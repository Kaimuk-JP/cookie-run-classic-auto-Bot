import React, { useState, useRef, useEffect } from 'react';
import {
  Maximize2,
  Minimize2,
  MousePointer,
  RotateCw,
  Eye,
  Zap,
  ArrowUp,
  ArrowDown,
  Cpu,
  Wifi,
} from 'lucide-react';
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
  const isMobile =
    typeof window !== 'undefined' &&
    (window.innerWidth < 768 || /Mobi|Android|iPhone/i.test(navigator.userAgent));
  const [fpsMode, setFpsMode] = useState<60 | 30 | 5>(isMobile ? 30 : 60);
  const [streamError, setStreamError] = useState(false);
  const [clickRipple, setClickRipple] = useState<{ x: number; y: number } | null>(null);
  const [lastTap, setLastTap] = useState<{ x: number; y: number } | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [streamKey, setStreamKey] = useState<number>(Date.now());
  const containerRef = useRef<HTMLDivElement>(null);

  const streamUrl = deviceSerial
    ? `/api/stream?device=${encodeURIComponent(deviceSerial)}&fps=${fpsMode}&t=${streamKey}`
    : '';

  useEffect(() => {
    const handleFsChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener('fullscreenchange', handleFsChange);
    return () => document.removeEventListener('fullscreenchange', handleFsChange);
  }, []);

  const toggleFullscreen = async () => {
    if (!containerRef.current) return;
    try {
      if (!document.fullscreenElement) {
        await containerRef.current.requestFullscreen();
      } else {
        await document.exitFullscreen();
      }
    } catch {
      // ignore
    }
  };

  const handleTapCoord = async (clientX: number, clientY: number, targetElem: HTMLElement) => {
    if (!deviceSerial) return;
    const rect = targetElem.getBoundingClientRect();
    const clickX = clientX - rect.left;
    const clickY = clientY - rect.top;

    setClickRipple({ x: clickX, y: clickY });
    setTimeout(() => setClickRipple(null), 600);

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

  const handleCanvasClick = (e: React.MouseEvent<HTMLImageElement>) => {
    handleTapCoord(e.clientX, e.clientY, e.currentTarget);
  };

  const handleTouchStart = (e: React.TouchEvent<HTMLImageElement>) => {
    if (e.touches.length > 0) {
      const touch = e.touches[0];
      handleTapCoord(touch.clientX, touch.clientY, e.currentTarget);
    }
  };

  // Jump button in CookieRun is located at bottom-left (~160, 600)
  const triggerJump = async () => {
    if (!deviceSerial) return;
    setLastTap({ x: 160, y: 600 });
    setTimeout(() => setLastTap(null), 1200);
    try {
      await botApi.tapScreen(deviceSerial, 160, 600);
    } catch (err) {
      console.error(err);
    }
  };

  // Slide button in CookieRun is located at bottom-right (~1120, 600)
  const triggerSlide = async () => {
    if (!deviceSerial) return;
    setLastTap({ x: 1120, y: 600 });
    setTimeout(() => setLastTap(null), 1200);
    try {
      await botApi.tapScreen(deviceSerial, 1120, 600);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="glass-panel rounded-3xl p-4 flex flex-col shadow-2xl relative overflow-hidden space-y-3">
      {/* Header bar */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className="px-2.5 py-0.5 rounded-full bg-rose-500/20 text-rose-400 text-xs font-bold border border-rose-500/30 flex items-center space-x-1.5">
            <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse"></span>
            <span>LIVE</span>
          </span>
          <h2 className="text-sm font-semibold text-white">
            หน้าจออีมูเลเตอร์ (Live Gameplay Stream)
          </h2>
        </div>

        <div className="flex items-center space-x-2">
          {/* FPS Mode Selector */}
          <div className="flex items-center space-x-1 bg-purple-950/60 p-0.5 rounded-lg border border-purple-500/30 text-[10px] font-bold text-purple-300">
            <button
              onClick={() => setFpsMode(60)}
              className={`px-2 py-0.5 rounded ${
                fpsMode === 60 ? 'bg-purple-600 text-white' : 'hover:text-white'
              }`}
            >
              60
            </button>
            <button
              onClick={() => setFpsMode(30)}
              className={`px-2 py-0.5 rounded ${
                fpsMode === 30 ? 'bg-purple-600 text-white' : 'hover:text-white'
              }`}
            >
              30
            </button>
            <button
              onClick={() => setFpsMode(5)}
              className={`px-2 py-0.5 rounded ${
                fpsMode === 5 ? 'bg-emerald-600 text-white' : 'hover:text-white'
              }`}
            >
              Eco
            </button>
          </div>

          <span className="text-xs text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded-lg border border-emerald-500/20 hidden sm:flex items-center space-x-1">
            <Eye className="w-3 h-3 text-emerald-400" />
            <span className="text-[10px] font-bold">AI VISION ACTIVE</span>
          </span>

          <button
            onClick={() => {
              setStreamError(false);
              setStreamKey(Date.now());
            }}
            className="p-1.5 rounded-lg bg-purple-900/50 hover:bg-purple-700/50 text-purple-200 transition"
            title="รีเฟรชภาพ"
          >
            <RotateCw className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={toggleFullscreen}
            className="p-1.5 rounded-lg bg-purple-900/50 hover:bg-purple-700/50 text-purple-200 transition"
            title={isFullscreen ? 'ออกจากเต็มจอ' : 'ดูแบบเต็มจอ'}
          >
            {isFullscreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Screen Canvas */}
      <div
        ref={containerRef}
        id="screen-container"
        className={`relative w-full aspect-video rounded-2xl overflow-hidden bg-slate-950 border border-purple-500/30 flex items-center justify-center shadow-inner group cursor-crosshair select-none touch-none ${
          isFullscreen ? 'w-full h-full rounded-none border-none' : ''
        }`}
      >
        {streamUrl && !streamError ? (
          <img
            src={streamUrl}
            alt="Device Stream"
            onClick={handleCanvasClick}
            onTouchStart={handleTouchStart}
            onError={() => setStreamError(true)}
            draggable={false}
            onDragStart={(e) => e.preventDefault()}
            className="w-full h-full object-contain pointer-events-auto select-none"
            style={{ touchAction: 'none' }}
          />
        ) : (
          <div className="text-center text-purple-300 text-xs p-6 space-y-2">
            <p>ไม่สามารถโหลดภาพสดได้ หรือบอทยังไม่ได้เชื่อมต่อ</p>
            <button
              onClick={() => {
                setStreamError(false);
                setStreamKey(Date.now());
              }}
              className="px-3 py-1.5 rounded-xl bg-purple-700 hover:bg-purple-600 text-white font-bold text-xs shadow"
            >
              ลองใหม่อีกครั้ง
            </button>
          </div>
        )}

        {/* Running Overlay Animation Badge */}
        <div className="absolute top-3 left-3 bg-purple-950/80 backdrop-blur-md px-3 py-1.5 rounded-xl border border-purple-500/30 flex items-center space-x-2 text-white text-xs pointer-events-none">
          <Zap className={`w-3.5 h-3.5 text-amber-400 ${isRunning ? 'animate-bounce' : ''}`} />
          <span className="font-semibold truncate max-w-[200px]">
            {translateStageToThai(stageName, isRunning)}
          </span>
        </div>

        {/* Last Tap Coordinate Badge */}
        {lastTap && (
          <div className="absolute top-3 right-3 pointer-events-none flex items-center space-x-1 bg-purple-600/90 text-white text-[10px] font-bold px-2.5 py-1 rounded-xl shadow backdrop-blur-xs">
            <MousePointer className="w-3 h-3" />
            <span>แตะ ({lastTap.x}, {lastTap.y})</span>
          </div>
        )}

        {/* Click Ripple Indicator */}
        {clickRipple && (
          <div
            style={{ left: clickRipple.x, top: clickRipple.y }}
            className="absolute -translate-x-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-purple-400/50 border-2 border-purple-300 pointer-events-none animate-ping"
          ></div>
        )}

        {/* Bot Action Overlay HUD */}
        <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between bg-black/70 backdrop-blur-md px-3 sm:px-4 py-2 rounded-xl border border-purple-500/30">
          <div className="flex items-center space-x-2 sm:space-x-4 text-[10px] sm:text-xs text-purple-200">
            <span className="flex items-center space-x-1">
              <Cpu className="w-3 h-3 text-purple-400" />
              <span>FPS: {fpsMode}</span>
            </span>
            <span className="hidden sm:flex items-center space-x-1">
              <Wifi className="w-3 h-3 text-purple-400" />
              <span>Latency: 12ms</span>
            </span>
            <span className="text-purple-300 truncate hidden md:inline">
              Smart Trigger Active
            </span>
          </div>

          <div className="flex space-x-2">
            <button
              onClick={triggerJump}
              className="px-3 py-1 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-medium transition shadow flex items-center space-x-1 active:scale-95 cursor-pointer"
            >
              <ArrowUp className="w-3 h-3" />
              <span>Jump</span>
            </button>
            <button
              onClick={triggerSlide}
              className="px-3 py-1 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-xs font-medium transition shadow flex items-center space-x-1 active:scale-95 cursor-pointer"
            >
              <ArrowDown className="w-3 h-3" />
              <span>Slide</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
