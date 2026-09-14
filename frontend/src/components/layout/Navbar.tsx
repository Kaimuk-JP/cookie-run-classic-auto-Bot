import React from 'react';
import {
  Play,
  Square,
  RefreshCw,
  Smartphone,
  Clock,
  Settings,
  Sparkles,
  Heart,
  Bot,
} from 'lucide-react';
import { Device } from '../../types/bot';

interface NavbarProps {
  devicesCount: number;
  runningCount: number;
  onScan: () => void;
  onStartAll: () => void;
  onStopAll: () => void;
  isScanning?: boolean;
  devices?: Device[];
  selectedSerial?: string;
  onSelectDevice?: (serial: string) => void;
  runtime?: string;
  onOpenSettings?: () => void;
  onOpenMacro?: () => void;
  onOpenTools?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  devicesCount,
  runningCount,
  onScan,
  onStartAll,
  onStopAll,
  isScanning = false,
  devices = [],
  selectedSerial = '',
  onSelectDevice,
  runtime = '00:00:00',
  onOpenSettings,
  onOpenMacro,
  onOpenTools,
}) => {
  const isAnyRunning = runningCount > 0;

  return (
    <header className="glass-panel sticky top-0 z-50 px-4 py-3 border-b border-purple-500/20 flex flex-wrap items-center justify-between gap-4">
      {/* Logo & Title */}
      <div className="flex items-center space-x-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-purple-500/30 shrink-0">
          <Bot className="w-5 h-5 text-white" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="font-bold text-base sm:text-lg text-white font-sans">
              CookieRun Bot{' '}
              <span className="text-[10px] sm:text-xs px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30">
                PRO UX v3.0
              </span>
            </h1>
          </div>
          <p className="text-xs text-purple-300/80 hidden sm:block">
            ระบบฟาร์มอัตโนมัติ & ควบคุมหลายจออัจฉริยะ
          </p>
        </div>
      </div>

      {/* Global Status Indicators */}
      <div className="flex items-center space-x-3 sm:space-x-4 bg-purple-950/40 px-3 sm:px-4 py-2 rounded-xl border border-purple-500/20 flex-wrap">
        <div className="flex items-center space-x-2">
          <span className="relative flex h-3 w-3">
            {isAnyRunning ? (
              <>
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
              </>
            ) : (
              <span className="relative inline-flex rounded-full h-3 w-3 bg-slate-500"></span>
            )}
          </span>
          <span className={`text-xs font-medium ${isAnyRunning ? 'text-emerald-300' : 'text-slate-400'}`}>
            {isAnyRunning ? `ทำงาน ${runningCount} จอ` : 'พร้อมทำงาน (Idle)'}
          </span>
        </div>

        <div className="h-4 w-px bg-purple-500/30 hidden sm:block"></div>

        <div className="flex items-center space-x-1.5 text-xs text-purple-200">
          <Clock className="w-3.5 h-3.5 text-purple-400" />
          <span className="font-mono text-purple-200">{runtime}</span>
        </div>

        <div className="h-4 w-px bg-purple-500/30 hidden sm:block"></div>

        {/* Emulator Selector Dropdown */}
        {devices.length > 0 && onSelectDevice && (
          <div className="relative">
            <select
              value={selectedSerial}
              onChange={(e) => onSelectDevice(e.target.value)}
              aria-label="เลือก Emulator"
              className="bg-purple-900/60 text-xs text-purple-200 px-2.5 py-1 rounded-lg border border-purple-500/40 focus:outline-none focus:ring-2 focus:ring-purple-400 cursor-pointer"
            >
              {devices.map((d) => (
                <option key={d.serial} value={d.serial} className="bg-slate-900 text-white">
                  📱 {d.name || d.serial} {d.is_running ? '🟢' : '⚪'}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Quick Action Buttons */}
      <div className="flex items-center space-x-1.5 sm:space-x-2">
        <button
          onClick={onScan}
          disabled={isScanning}
          className="px-2.5 sm:px-3 py-2 rounded-xl bg-purple-800/40 hover:bg-purple-700/60 text-purple-200 text-xs font-medium border border-purple-500/30 transition flex items-center space-x-1.5 active:scale-95 disabled:opacity-50"
          title="สแกน Emulator ทั้งหมด"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isScanning ? 'animate-spin text-purple-400' : ''}`} />
          <span className="hidden md:inline">สแกน</span>
        </button>

        {onOpenSettings && (
          <button
            onClick={onOpenSettings}
            className="px-2.5 sm:px-3 py-2 rounded-xl bg-purple-800/40 hover:bg-purple-700/60 text-purple-200 text-xs font-medium border border-purple-500/30 transition flex items-center space-x-1.5 active:scale-95"
          >
            <Settings className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">ตั้งค่าบอท</span>
          </button>
        )}

        {onOpenMacro && (
          <button
            onClick={onOpenMacro}
            className="px-2.5 sm:px-3 py-2 rounded-xl bg-purple-800/40 hover:bg-purple-700/60 text-purple-200 text-xs font-medium border border-purple-500/30 transition flex items-center space-x-1.5 active:scale-95"
          >
            <Sparkles className="w-3.5 h-3.5 text-purple-300" />
            <span className="hidden sm:inline">มาโคร</span>
          </button>
        )}

        {onOpenTools && (
          <button
            onClick={onOpenTools}
            className="px-2.5 sm:px-3 py-2 rounded-xl bg-pink-900/40 hover:bg-pink-800/60 text-pink-200 text-xs font-medium border border-pink-500/30 transition flex items-center space-x-1.5 active:scale-95"
          >
            <Heart className="w-3.5 h-3.5 text-pink-400" />
            <span className="hidden sm:inline">ปั๊มหัวใจ</span>
          </button>
        )}

        {/* Start All Button */}
        <button
          onClick={onStartAll}
          className="px-3 sm:px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-semibold shadow-lg shadow-emerald-900/40 transition flex items-center space-x-1.5 active:scale-95 cursor-pointer"
          title="เริ่มบอททุกจอ"
        >
          <Play className="w-3.5 h-3.5 fill-current" />
          <span>เริ่มรันบอท</span>
        </button>

        {/* Stop All Button */}
        <button
          onClick={onStopAll}
          className="px-3 py-2 rounded-xl bg-gradient-to-r from-rose-600 to-red-600 hover:from-rose-500 hover:to-red-500 text-white text-xs font-semibold shadow-lg shadow-rose-900/40 transition active:scale-95 cursor-pointer"
          title="หยุดบอททุกจอทันที"
        >
          <Square className="w-3.5 h-3.5 fill-current" />
        </button>
      </div>
    </header>
  );
};
