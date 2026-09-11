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
    <header className="sticky top-0 z-40 bg-white/90 backdrop-blur-md border-b border-purple-100 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
        {/* Brand Logo & Title */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-brand-600 to-brand-500 flex items-center justify-center text-white shadow-md shadow-brand-500/30">
            <Bot className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold text-slate-900 leading-none font-sans">
                CookieRun AutoBot
              </h1>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-brand-100 text-brand-700">
                PRO 2.0
              </span>
            </div>
            <p className="text-[11px] text-slate-400 mt-0.5">
              ระบบควบคุมบอทอัตโนมัติหลายจอ (Multi-Device Control)
            </p>
          </div>
        </div>

        {/* Global Multi-Device Actions */}
        <div className="flex items-center gap-2.5">
          {/* Status Counter */}
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-purple-50/80 border border-purple-100 text-xs">
            <Smartphone className="w-4 h-4 text-brand-600" />
            <span className="text-slate-600 font-medium">พบ {devicesCount} จอ</span>
            {runningCount > 0 && (
              <span className="flex items-center gap-1 font-bold text-emerald-600">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                กำลังทำงาน {runningCount} จอ
              </span>
            )}
          </div>

          <button
            onClick={onScan}
            disabled={isScanning}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition active:scale-95 disabled:opacity-50"
            title="สแกน Emulator ทั้งหมดในเครื่อง"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isScanning ? 'animate-spin text-brand-600' : ''}`} />
            <span className="hidden md:inline">สแกนจอ</span>
          </button>

          <button
            onClick={onStartAll}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-sm shadow-emerald-600/30 transition active:scale-95"
            title="เริ่มบอททุกจอที่เชื่อมต่ออยู่"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>เริ่มทุกจอ</span>
          </button>

          <button
            onClick={onStopAll}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold shadow-sm shadow-rose-600/30 transition active:scale-95"
            title="หยุดบอททุกจอทันที"
          >
            <Square className="w-3.5 h-3.5 fill-current" />
            <span>หยุดทุกจอ</span>
          </button>
        </div>
      </div>
    </header>
  );
};
