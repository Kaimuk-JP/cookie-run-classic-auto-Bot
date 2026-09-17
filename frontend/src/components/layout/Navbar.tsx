import React from 'react';
import {
  Play,
  Square,
  RefreshCw,
  Clock,
  Settings,
  Sparkles,
  Heart,
  Bot,
  Bell,
} from 'lucide-react';
import { Device } from '../../types/bot';
import { CookieHeroIcon } from '../common/SweetIcons';
import candyKingdomBanner from '../../assets/candy_kingdom_banner.jpg';

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
  onOpenDiscord?: () => void;
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
  onOpenDiscord,
}) => {
  const isAnyRunning = runningCount > 0;

  return (
    <header className="relative overflow-hidden biscuit-panel sticky top-0 z-50 px-4 py-2.5 border-b-2 border-[#EEDBCE] shadow-md">
      {/* Background Banner Illustration on Header */}
      <div className="absolute inset-0 z-0 pointer-events-none">
        <img
          src={candyKingdomBanner}
          alt="Candy Kingdom"
          className="w-full h-full object-cover object-center opacity-30 mix-blend-multiply filter saturate-150"
        />
        <div className="absolute inset-0 bg-gradient-to-r from-[#FFFDF8] via-[#FFFDF8]/90 to-[#FFFDF8]/70"></div>
      </div>

      <div className="relative z-10 flex flex-wrap items-center justify-between gap-3">
        {/* Logo & Title with Cute Cookie Illustration Mascot */}
        <div className="flex items-center space-x-3">
        <div className="w-10 h-10 rounded-xl shadow-md overflow-hidden shrink-0 border-2 border-white flex items-center justify-center">
          <CookieHeroIcon className="w-full h-full object-cover" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="font-bold text-base sm:text-lg text-[#3D2012] font-heading tracking-tight flex items-center gap-1.5">
              <span>CookieRun</span>
              <span className="text-[#E11D48]">Bot</span>
            </h1>
          </div>
          <p className="text-xs text-[#8C6D58] hidden sm:block font-medium">
            ระบบฟาร์มอัตโนมัติ & หลายจอ
          </p>
        </div>
      </div>

      {/* Global Status Indicators */}
      <div className="flex items-center space-x-2.5 sm:space-x-3.5 bg-[#FFF9F0] px-3 sm:px-4 py-1.5 rounded-2xl border-2 border-[#F3E5D4] shadow-sm flex-wrap">
        <div className="flex items-center space-x-2">
          <span className="relative flex h-3 w-3">
            {isAnyRunning ? (
              <>
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500 shadow-sm"></span>
              </>
            ) : (
              <span className="relative inline-flex rounded-full h-3 w-3 bg-amber-400"></span>
            )}
          </span>
          <span className={`text-xs font-bold ${isAnyRunning ? 'text-emerald-700' : 'text-amber-800'}`}>
            {isAnyRunning ? `กำลังรัน ${runningCount} จอ` : 'พร้อมทำงาน'}
          </span>
        </div>

        <div className="h-4 w-px bg-[#EADBCE] hidden sm:block"></div>

        <div className="flex items-center space-x-1.5 text-xs text-[#8A3B04] font-bold">
          <Clock className="w-3.5 h-3.5 text-[#D97706]" />
          <span className="font-mono bg-white px-2 py-0.5 rounded-lg border border-[#F0DFCE] shadow-inner">{runtime}</span>
        </div>

        <div className="h-4 w-px bg-[#EADBCE] hidden sm:block"></div>

        {/* Emulator Selector Dropdown */}
        {devices.length > 0 && onSelectDevice && (
          <div className="relative">
            <select
              value={selectedSerial}
              onChange={(e) => onSelectDevice(e.target.value)}
              aria-label="เลือก Emulator"
              className="bg-white text-xs font-semibold text-[#452311] px-2.5 py-1 rounded-xl border-2 border-[#EEDBCE] hover:border-[#D4A373] focus:outline-none focus:ring-2 focus:ring-[#F59E0B] cursor-pointer shadow-sm"
            >
              {devices.map((d) => (
                <option key={d.serial} value={d.serial} className="bg-white text-[#452311]">
                  {d.is_running ? '● ' : '○ '}{d.name || d.serial}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Quick Action Buttons with 3D Tactile Candy Styling */}
      <div className="flex items-center space-x-1.5 sm:space-x-2">
        <button
          onClick={onScan}
          disabled={isScanning}
          className="candy-btn-soft px-2.5 sm:px-3 py-1.5 rounded-xl text-xs font-bold transition flex items-center space-x-1.5 disabled:opacity-50 cursor-pointer"
          title="สแกน Emulator"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-[#D97706] ${isScanning ? 'animate-spin' : ''}`} />
          <span className="hidden md:inline">สแกน</span>
        </button>

        {onOpenSettings && (
          <button
            onClick={onOpenSettings}
            className="candy-btn-soft px-2.5 sm:px-3 py-1.5 rounded-xl text-xs font-bold transition flex items-center space-x-1.5 cursor-pointer"
          >
            <Settings className="w-3.5 h-3.5 text-[#D97706]" />
            <span className="hidden sm:inline">ตั้งค่า</span>
          </button>
        )}

        {onOpenMacro && (
          <button
            onClick={onOpenMacro}
            className="candy-btn-soft px-2.5 sm:px-3 py-1.5 rounded-xl text-xs font-bold transition flex items-center space-x-1.5 cursor-pointer text-[#8A3B04]"
          >
            <Sparkles className="w-3.5 h-3.5 text-[#F59E0B]" />
            <span className="hidden sm:inline">มาโคร</span>
          </button>
        )}

        {onOpenTools && (
          <button
            onClick={onOpenTools}
            className="candy-btn-soft px-2.5 sm:px-3 py-1.5 rounded-xl text-xs font-bold transition flex items-center space-x-1.5 cursor-pointer text-[#E11D48]"
          >
            <Heart className="w-3.5 h-3.5 text-[#FF5C8A] fill-[#FF5C8A]" />
            <span className="hidden sm:inline">ปั๊มหัวใจ</span>
          </button>
        )}


        {/* Start All Button (Honey/Caramel 3D Candy Button) */}
        <button
          onClick={onStartAll}
          className="candy-btn-honey px-3.5 sm:px-4 py-1.5 rounded-xl text-xs font-bold transition flex items-center space-x-1.5 cursor-pointer"
          title="เริ่มทุกจอ"
        >
          <Play className="w-3.5 h-3.5 fill-current" />
          <span>เริ่มบอท</span>
        </button>

        {/* Stop All Button (Strawberry Red 3D Button) */}
        <button
          onClick={onStopAll}
          className="candy-btn-strawberry px-3 py-1.5 rounded-xl text-xs font-bold transition flex items-center justify-center cursor-pointer"
          title="หยุดทุกจอ"
        >
          <Square className="w-3.5 h-3.5 fill-current" />
        </button>
      </div>
      </div>
    </header>
  );
};
