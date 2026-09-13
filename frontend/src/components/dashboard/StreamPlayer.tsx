import React, { useState, useRef, useEffect } from 'react';
import { Maximize2, Minimize2, MousePointer, RotateCw, Sparkles, Smartphone } from 'lucide-react';
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
  // Mobile check: Default to 30 FPS or Eco to prevent lag over mobile/tunnel
  const isMobile = typeof window !== 'undefined' && (window.innerWidth < 768 || /Mobi|Android|iPhone/i.test(navigator.userAgent));
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

    // Show visual ripple
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
    <div className="bg-white border border-purple-100 rounded-2xl sm:rounded-3xl p-3 sm:p-4 shadow-card space-y-2.5 sm:space-y-3">
      {/* Header bar of Stream Canvas */}
      <div className="flex items-center justify-between gap-2 pb-2 border-b border-purple-50">
        <div className="flex items-center gap-1.5 sm:gap-2 min-w-0">
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse shrink-0"></div>
          <h3 className="text-xs font-bold text-slate-800 truncate">
            หน้าจอถ่ายทอดสด
          </h3>
          <span className="text-[10px] text-slate-400 font-mono hidden md:inline truncate">
            (Interactive Live Screen)
          </span>
        </div>

        {/* FPS Mode Selector & Actions */}
        <div className="flex items-center gap-1.5 shrink-0">
          <div className="flex items-center gap-0.5 bg-slate-100 p-0.5 rounded-xl text-[10px] sm:text-[11px] font-bold">
            <button
              onClick={() => setFpsMode(60)}
              className={`px-2 sm:px-2.5 py-1 rounded-lg transition ${
                fpsMode === 60 ? 'bg-white text-brand-700 shadow-xs' : 'text-slate-500 hover:text-slate-800'
              }`}
              title="60 FPS (เหมาะสำหรับดูบน PC หรือ Wi-Fi บ้าน)"
            >
              60
            </button>
            <button
              onClick={() => setFpsMode(30)}
              className={`px-2 sm:px-2.5 py-1 rounded-lg transition ${
                fpsMode === 30 ? 'bg-white text-brand-700 shadow-xs' : 'text-slate-500 hover:text-slate-800'
              }`}
              title="30 FPS (แนะนำสำหรับมือถือและเน็ตทั่วไป)"
            >
              30
            </button>
            <button
              onClick={() => setFpsMode(5)}
              className={`px-2 sm:px-2.5 py-1 rounded-lg transition ${
                fpsMode === 5 ? 'bg-white text-emerald-700 shadow-xs' : 'text-slate-500 hover:text-slate-800'
              }`}
              title="Eco (15 FPS - ประหยัดเน็ตสูงสุด นิ่งไม่กระตุก)"
            >
              Eco
            </button>
          </div>

          <button
            onClick={() => {
              setStreamError(false);
              setStreamKey(Date.now());
            }}
            className="p-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-600 transition active:scale-95"
            title="รีเฟรชภาพสตรีม"
          >
            <RotateCw className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={toggleFullscreen}
            className="p-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-600 transition active:scale-95"
            title={isFullscreen ? "ออกจากเต็มจอ" : "ดูแบบเต็มจอ"}
          >
            {isFullscreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Screen Container */}
      <div
        ref={containerRef}
        className={`relative bg-slate-950 rounded-xl sm:rounded-2xl aspect-video overflow-hidden border border-purple-100 flex items-center justify-center shadow-inner group cursor-crosshair select-none touch-none ${
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
          <div className="text-center text-slate-400 text-xs p-4 sm:p-6 space-y-2">
            <p>ไม่สามารถโหลดภาพสดได้ หรือบอทยังไม่ได้เชื่อมต่อ</p>
            <button
              onClick={() => {
                setStreamError(false);
                setStreamKey(Date.now());
              }}
              className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-bold text-xs"
            >
              ลองใหม่อีกครั้ง
            </button>
          </div>
        )}

        {/* Stage Overlay Badge */}
        <div className="absolute top-2 sm:top-3 left-2 sm:left-3 pointer-events-none flex items-center gap-1.5 bg-black/65 backdrop-blur-md px-2 sm:px-2.5 py-1 rounded-lg sm:rounded-xl text-white text-[10px] sm:text-[11px] font-bold border border-white/10 shadow-xs">
          <span className={`w-2 h-2 rounded-full ${isRunning ? 'bg-emerald-400 animate-ping' : 'bg-slate-400'}`}></span>
          <span className="truncate max-w-[150px] sm:max-w-none">{translateStageToThai(stageName, isRunning)}</span>
        </div>

        {/* Last Tap Coordinate Badge */}
        {lastTap && (
          <div className="absolute top-2 sm:top-3 right-2 sm:right-3 pointer-events-none flex items-center gap-1 bg-brand-600/90 text-white text-[10px] sm:text-[11px] font-bold px-2 sm:px-2.5 py-1 rounded-lg sm:rounded-xl shadow-md animate-fade-in backdrop-blur-xs">
            <MousePointer className="w-3 h-3" />
            <span>แตะ ({lastTap.x}, {lastTap.y})</span>
          </div>
        )}

        {/* Click Ripple Indicator */}
        {clickRipple && (
          <div
            style={{ left: clickRipple.x, top: clickRipple.y }}
            className="absolute -translate-x-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-brand-400/50 border-2 border-brand-300 pointer-events-none animate-ping"
          ></div>
        )}

        {/* Mobile Fullscreen Overlay Exit button if in fullscreen */}
        {isFullscreen && (
          <button
            onClick={toggleFullscreen}
            className="absolute top-4 right-4 z-50 p-2 rounded-xl bg-black/70 text-white hover:bg-black/90 transition backdrop-blur-md"
          >
            <Minimize2 className="w-5 h-5" />
          </button>
        )}
      </div>
    </div>
  );
};
