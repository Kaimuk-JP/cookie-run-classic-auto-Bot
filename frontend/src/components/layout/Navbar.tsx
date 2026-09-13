import React from 'react';
import { Play, Square, RefreshCw, Smartphone, Bot } from 'lucide-react';

interface NavbarProps {
  devicesCount: number;
  runningCount: number;
  onScan: () => void;
  onStartAll: () => void;
  onStopAll: () => void;
  isScanning?: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  devicesCount,
  runningCount,
  onScan,
  onStartAll,
  onStopAll,
  isScanning = false,
}) => {
  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-purple-100 shadow-xs">
      <div className="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8 h-14 sm:h-16 flex items-center justify-between gap-2 sm:gap-4">
        {/* Brand Logo & Title */}
        <div className="flex items-center gap-2 sm:gap-3 min-w-0">
          <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-xl sm:rounded-2xl bg-gradient-to-tr from-brand-600 to-brand-500 flex items-center justify-center text-white shadow-md shadow-brand-500/30 shrink-0">
            <Bot className="w-4 h-4 sm:w-6 sm:h-6" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-1.5">
              <h1 className="text-sm sm:text-base font-bold text-slate-900 leading-none truncate font-sans">
                CookieRun Bot
              </h1>
              <span className="px-1.5 py-0.5 rounded-full text-[9px] sm:text-[10px] font-bold bg-brand-100 text-brand-700 shrink-0">
                PRO
              </span>
            </div>
            <p className="text-[10px] sm:text-[11px] text-slate-400 mt-0.5 hidden sm:block truncate">
              ระบบควบคุมบอทอัตโนมัติ (Multi-Device)
            </p>
          </div>
        </div>

        {/* Global Multi-Device Actions */}
        <div className="flex items-center gap-1.5 sm:gap-2.5 shrink-0">
          {/* Status Counter */}
          <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-purple-50/80 border border-purple-100 text-xs">
            <Smartphone className="w-3.5 h-3.5 text-brand-600" />
            <span className="text-slate-600 font-medium">{devicesCount} จอ</span>
            {runningCount > 0 && (
              <span className="flex items-center gap-1 font-bold text-emerald-600">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                ทำงาน {runningCount}
              </span>
            )}
          </div>

          <button
            onClick={onScan}
            disabled={isScanning}
            className="flex items-center gap-1 px-2.5 sm:px-3 py-1.5 sm:py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition active:scale-95 disabled:opacity-50"
            title="สแกน Emulator ทั้งหมดในเครื่อง"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isScanning ? 'animate-spin text-brand-600' : ''}`} />
            <span className="hidden sm:inline">สแกน</span>
          </button>

          <button
            onClick={onStartAll}
            className="flex items-center gap-1 px-2.5 sm:px-3.5 py-1.5 sm:py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-xs transition active:scale-95"
            title="เริ่มบอททุกจอที่เชื่อมต่ออยู่"
          >
            <Play className="w-3 h-3 sm:w-3.5 sm:h-3.5 fill-current" />
            <span className="text-[11px] sm:text-xs">เริ่มทุกจอ</span>
          </button>

          <button
            onClick={onStopAll}
            className="flex items-center gap-1 px-2.5 sm:px-3.5 py-1.5 sm:py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold shadow-xs transition active:scale-95"
            title="หยุดบอททุกจอทันที"
          >
            <Square className="w-3 h-3 sm:w-3.5 sm:h-3.5 fill-current" />
            <span className="text-[11px] sm:text-xs">หยุดทุกจอ</span>
          </button>
        </div>
      </div>
    </header>
  );
};
