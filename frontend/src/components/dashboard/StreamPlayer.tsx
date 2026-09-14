import React, { useState, useRef, useEffect } from 'react';
import {
  Maximize2,
  Minimize2,
  MousePointer,
  RotateCw,
  Eye,
  Zap,
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

  const [actualFps, setActualFps] = useState<number>(fpsMode);
  const [realLatency, setRealLatency] = useState<number>(0);

  useEffect(() => {
    let isMounted = true;
    const updateStats = async () => {
      if (!deviceSerial) return;
      const t0 = performance.now();
      try {
        const res = await fetch(`/api/stream-stats?device=${encodeURIComponent(deviceSerial)}`);
        const roundTrip = Math.round(performance.now() - t0);
        if (!isMounted) return;
        setRealLatency(roundTrip);
        if (res.ok) {
          const data = await res.json();
          if (data && typeof data.fps === 'number' && data.fps > 0) {
            setActualFps(Math.round(data.fps));
          } else {
            setActualFps(fpsMode);
          }
        }
      } catch {
        if (isMounted) {
          setRealLatency(Math.max(1, Math.round(performance.now() - t0)));
          setActualFps(fpsMode);
        }
      }
    };

    updateStats();
    const interval = setInterval(updateStats, 2000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [deviceSerial, fpsMode]);

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

  return (
    <div className="glass-panel rounded-3xl p-3 sm:p-4 flex flex-col shadow-2xl relative overflow-hidden space-y-2.5 sm:space-y-3">
      {/* Header bar */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center space-x-2 min-w-0">
          <span className="px-2 sm:px-2.5 py-0.5 rounded-full bg-[#FFBEFB]/20 text-[#FFBEFB] text-[10px] sm:text-xs font-bold border border-[#FFBEFB]/40 flex items-center space-x-1 shrink-0">
            <span className="w-1.5 sm:w-2 h-1.5 sm:h-2 rounded-full bg-[#FFBEFB] animate-pulse"></span>
            <span>LIVE</span>
          </span>
          <h2 className="text-xs sm:text-sm font-semibold text-white truncate">
            หน้าจออีมูเลเตอร์ (Live Stream)
          </h2>
        </div>

        <div className="flex items-center space-x-1.5 sm:space-x-2 shrink-0">
          {/* FPS Mode Selector */}
          <div className="flex items-center space-x-0.5 sm:space-x-1 bg-[#23173a]/70 p-0.5 rounded-lg border border-[#DC95FF]/30 text-[10px] font-bold text-[#FFBEFB]">
            <button
              onClick={() => setFpsMode(60)}
              className={`px-1.5 sm:px-2 py-0.5 rounded transition ${fpsMode === 60 ? 'bg-[#8C56D4] text-white' : 'hover:text-white'
                }`}
            >
              60
            </button>
            <button
              onClick={() => setFpsMode(30)}
              className={`px-1.5 sm:px-2 py-0.5 rounded transition ${fpsMode === 30 ? 'bg-[#8C56D4] text-white' : 'hover:text-white'
                }`}
            >
              30
            </button>
            <button
              onClick={() => setFpsMode(5)}
              className={`px-1.5 sm:px-2 py-0.5 rounded transition ${fpsMode === 5 ? 'bg-[#DC95FF] text-[#160f29]' : 'hover:text-white'
                }`}
            >
              Eco
            </button>
          </div>

          <button
            onClick={() => {
              setStreamError(false);
              setStreamKey(Date.now());
            }}
            className="p-1 sm:p-1.5 rounded-lg bg-[#8C56D4]/30 hover:bg-[#8C56D4]/50 text-[#FFBEFB] transition"
            title="รีเฟรชภาพ"
          >
            <RotateCw className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={toggleFullscreen}
            className="p-1 sm:p-1.5 rounded-lg bg-[#8C56D4]/30 hover:bg-[#8C56D4]/50 text-[#FFBEFB] transition"
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
        className={`relative w-full aspect-video rounded-2xl overflow-hidden bg-slate-950 border border-[#DC95FF]/30 flex items-center justify-center shadow-inner group cursor-crosshair select-none touch-none ${isFullscreen ? 'w-full h-full rounded-none border-none' : ''
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
          <div className="text-center text-[#FFBEFB]/80 text-xs p-6 space-y-2">
            <p>ไม่สามารถโหลดภาพสดได้ หรือบอทยังไม่ได้เชื่อมต่อ</p>
            <button
              onClick={() => {
                setStreamError(false);
                setStreamKey(Date.now());
              }}
              className="px-3 py-1.5 rounded-xl bg-gradient-to-r from-[#8C56D4] to-[#DC95FF] hover:brightness-110 text-white font-bold text-xs shadow"
            >
              ลองใหม่อีกครั้ง
            </button>
          </div>
        )}

        {/* Running Overlay Animation Badge */}
        <div className="absolute top-2.5 sm:top-3 left-2.5 sm:left-3 bg-[#1d1233]/85 backdrop-blur-md px-2.5 sm:px-3 py-1 rounded-xl border border-[#DC95FF]/30 flex items-center space-x-1.5 sm:space-x-2 text-white text-[11px] sm:text-xs pointer-events-none">
          <Zap className={`w-3.5 h-3.5 text-[#FFF4BF] ${isRunning ? 'animate-bounce' : ''}`} />
          <span className="font-semibold truncate max-w-[160px] sm:max-w-[240px] text-[#FFF4BF]">
            {translateStageToThai(stageName, isRunning)}
          </span>
        </div>

        {/* Last Tap Coordinate Badge */}
        {lastTap && (
          <div className="absolute top-2.5 sm:top-3 right-2.5 sm:right-3 pointer-events-none flex items-center space-x-1 bg-[#8C56D4]/90 text-white text-[10px] font-bold px-2.5 py-1 rounded-xl shadow backdrop-blur-xs border border-[#DC95FF]/40">
            <MousePointer className="w-3 h-3 text-[#FFF4BF]" />
            <span>แตะ ({lastTap.x}, {lastTap.y})</span>
          </div>
        )}

        {/* Click Ripple Indicator */}
        {clickRipple && (
          <div
            style={{ left: clickRipple.x, top: clickRipple.y }}
            className="absolute -translate-x-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-[#DC95FF]/50 border-2 border-[#FFBEFB] pointer-events-none animate-ping"
          ></div>
        )}

        {/* Clean Bottom Telemetry Badge (FPS & Ping) without Jump/Slide buttons */}
        <div className="absolute bottom-2.5 left-2.5 sm:left-3 bg-[#120b20]/75 backdrop-blur-md px-2.5 sm:px-3 py-1 rounded-xl border border-[#DC95FF]/20 flex items-center space-x-3 text-[10px] sm:text-xs text-[#FFBEFB] pointer-events-none">
          <span className="flex items-center space-x-1">
            <Cpu className="w-3 h-3 text-[#DC95FF]" />
            <span>FPS: {actualFps}</span>
          </span>
          <span className="flex items-center space-x-1">
            <Wifi className="w-3 h-3 text-[#FFF4BF]" />
            <span>Ping: {realLatency > 0 ? `${realLatency}ms` : '<1ms'}</span>
          </span>
        </div>
      </div>
    </div>
  );
};
