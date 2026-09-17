import React from 'react';
import {
  Smartphone,
  Play,
  Square,
  Eye,
  Coins,
  Trophy,
  Heart,
  UserMinus,
  Layers,
} from 'lucide-react';
import { Device } from '../../types/bot';

interface DeviceBreakdownProps {
  devices: Device[];
  selectedSerial: string;
  onSelectDevice: (serial: string) => void;
  onStartDevice?: (serial: string) => void;
  onStopDevice?: (serial: string) => void;
}

export const DeviceBreakdown: React.FC<DeviceBreakdownProps> = ({
  devices,
  selectedSerial,
  onSelectDevice,
  onStartDevice,
  onStopDevice,
}) => {
  const formatCoins = (coins: number) => {
    if (coins >= 1000000) return `${(coins / 1000000).toFixed(1)}M`;
    if (coins >= 1000) return `${(coins / 1000).toFixed(1)}K`;
    return coins.toLocaleString();
  };

  if (devices.length === 0) {
    return null;
  }

  return (
    <div className="biscuit-panel rounded-3xl p-4 sm:p-5 shadow-md space-y-3.5">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-xl bg-[#FEF3C7] text-[#D97706] flex items-center justify-center shadow-xs">
            <Layers className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-bold text-sm text-[#3D2012] font-heading flex items-center gap-1.5">
              <span>สถิติแยกรายจอ</span>
              <span className="text-xs text-[#8C6D58] font-normal font-sans">
                (จอไหนได้อะไรเท่าไหร่)
              </span>
            </h3>
            <p className="text-[11px] text-[#8A3B04] font-medium">
              แสดงยอดที่ได้ของแต่ละ Emulator แบบเรียลไทม์
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-[11px] font-bold text-[#8A3B04] bg-[#FFF8EC] px-2.5 py-1 rounded-xl border border-[#EEDBCE] shadow-xs">
            เชื่อมต่อ {devices.length} จอ
          </span>
        </div>
      </div>

      {/* Devices Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {devices.map((d) => {
          const isSelected = d.serial === selectedSerial;
          const isRunning = d.is_running;
          const isFarmer = d.active_mode === 'heart_farmer';
          const isCleaner = d.active_mode === 'friend_cleaner';

          // Current active round or carried-over round
          const currentRoundNum = isRunning
            ? Math.max(1, d.session_rounds || 1)
            : d.rounds_played;

          // Coins
          const sessionCoins = d.coin_stats?.session_earned ?? 0;
          const lifetimeCoins = d.coin_stats?.lifetime_earned ?? 0;

          // Boxes
          const rainbow = isRunning
            ? (d.session_box_counts?.rainbow ?? 0)
            : (d.box_counts?.rainbow ?? 0);
          const gold = isRunning
            ? (d.session_box_counts?.gold ?? 0)
            : (d.box_counts?.gold ?? 0);
          const silver = isRunning
            ? (d.session_box_counts?.silver ?? 0)
            : (d.box_counts?.silver ?? 0);
          const wood = isRunning
            ? (d.session_box_counts?.wood ?? 0)
            : (d.box_counts?.wood ?? 0);
          const totalBoxes = isRunning
            ? (d.session_box_counts?.total ?? rainbow + gold + silver + wood)
            : (d.box_counts?.total ?? rainbow + gold + silver + wood);

          return (
            <div
              key={d.serial}
              className={`biscuit-card rounded-2xl p-3.5 transition-all duration-200 flex flex-col justify-between space-y-3 relative ${
                isSelected
                  ? 'ring-2 ring-[#F59E0B] bg-[#FFFDF5] shadow-md'
                  : 'hover:border-[#D4A373] hover:shadow-xs'
              }`}
            >
              {/* Card Top: Device Info & Running Badge */}
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center space-x-2.5 min-w-0">
                  <div
                    className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 border ${
                      isSelected
                        ? 'bg-[#F59E0B] text-white border-[#D97706] shadow-xs'
                        : 'bg-[#FFF8EC] text-[#8A3B04] border-[#EEDBCE]'
                    }`}
                  >
                    <Smartphone className="w-5 h-5" />
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className="font-bold text-xs text-[#3D2012] truncate max-w-[140px]">
                        {d.name || d.serial}
                      </span>
                      {isSelected && (
                        <span className="text-[10px] font-extrabold px-1.5 py-0.2 rounded-md bg-[#FEF3C7] text-[#B45309] border border-[#FDE68A]">
                          ดูกล้องจอนี้
                        </span>
                      )}
                    </div>
                    <span className="text-[10px] text-[#8C6D58] font-mono block truncate">
                      {d.serial}
                    </span>
                  </div>
                </div>

                {/* Status Badge */}
                <div className="shrink-0">
                  {isCleaner ? (
                    <span className="inline-flex items-center gap-1 text-[10px] font-bold text-teal-700 px-2 py-0.5 rounded-lg bg-teal-50 border border-teal-200">
                      <UserMinus className="w-3 h-3" />
                      ลบเพื่อน
                    </span>
                  ) : isFarmer ? (
                    <span className="inline-flex items-center gap-1 text-[10px] font-bold text-rose-700 px-2 py-0.5 rounded-lg bg-rose-50 border border-rose-200">
                      <Heart className="w-3 h-3 fill-rose-500 text-rose-500 animate-pulse" />
                      ปั๊มหัวใจ ({d.heart_stats?.success_count ?? 0})
                    </span>
                  ) : isRunning ? (
                    <span className="inline-flex items-center gap-1 text-[10px] font-bold text-emerald-700 px-2 py-0.5 rounded-lg bg-emerald-50 border border-emerald-200">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping"></span>
                      กำลังรันรอบที่ {currentRoundNum}
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-[10px] font-bold text-amber-800 px-2 py-0.5 rounded-lg bg-amber-50 border border-amber-200">
                      พร้อมทำงาน (ยอดยกมา)
                    </span>
                  )}
                </div>
              </div>

              {/* Stats Summary for this device (จอไหนได้อะไรเท่าไหร่) */}
              <div className="bg-[#FFF9F0] rounded-xl p-2.5 border border-[#F3E5D4] space-y-2 text-xs">
                {/* Rounds & Coins Row */}
                <div className="grid grid-cols-2 gap-2 border-b border-[#F0DFC9] pb-2">
                  <div className="flex items-center space-x-1.5">
                    <Trophy className="w-3.5 h-3.5 text-[#E11D48] shrink-0" />
                    <div>
                      <span className="text-[10px] text-[#8C6D58] block leading-tight">
                        {isRunning ? 'รอบปัจจุบัน' : 'รอบสะสม (ยอดยกมา)'}
                      </span>
                      <span className="font-extrabold text-[#3D2012] font-mono text-xs">
                        {isRunning ? `รอบที่ ${currentRoundNum}` : `${d.rounds_played} รอบ`}
                      </span>
                      {isRunning && (
                        <span className="text-[9px] text-[#8C6D58] block">
                          (สะสมรวม: {d.rounds_played})
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center space-x-1.5">
                    <Coins className="w-3.5 h-3.5 text-[#D97706] shrink-0" />
                    <div>
                      <span className="text-[10px] text-[#8C6D58] block leading-tight">
                        {isRunning ? 'เหรียญรอบนี้' : 'เหรียญสะสม (ยอดยกมา)'}
                      </span>
                      <span className="font-extrabold text-[#3D2012] font-mono text-xs">
                        {isRunning ? `+${formatCoins(sessionCoins)}` : formatCoins(lifetimeCoins)}
                      </span>
                      {isRunning && (
                        <span className="text-[9px] text-[#8C6D58] block">
                          (รวม: {formatCoins(lifetimeCoins)})
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Mystery Boxes Breakdown for this Device */}
                <div>
                  <div className="flex items-center justify-between text-[10px] text-[#8A3B04] font-bold mb-1">
                    <span>กล่องปริศนาที่ได้ {isRunning ? '(รอบนี้)' : '(ยอดยกมา)'}:</span>
                    <span className="font-mono">{totalBoxes} กล่อง</span>
                  </div>

                  <div className="grid grid-cols-4 gap-1.5 text-center">
                    {/* Rainbow Box */}
                    <div className="bg-white/90 p-1 rounded-lg border border-[#DDD6FE] flex flex-col items-center">
                      <img
                        src="/templates/BOX_RAINBOW.png"
                        alt="รุ้ง"
                        className="w-4 h-4 object-contain"
                      />
                      <span className="text-[9px] text-[#7C3AED] font-bold mt-0.5">รุ้ง</span>
                      <span className="text-xs font-black text-[#3D2012] font-mono">
                        {rainbow}
                      </span>
                      {isRunning && (
                        <span className="text-[8px] text-[#8C6D58] leading-none">
                          รวม {d.box_counts?.rainbow ?? 0}
                        </span>
                      )}
                    </div>

                    {/* Gold Box */}
                    <div className="bg-white/90 p-1 rounded-lg border border-[#FDE68A] flex flex-col items-center">
                      <img
                        src="/templates/BOX_GOLD.png"
                        alt="ทอง"
                        className="w-4 h-4 object-contain"
                      />
                      <span className="text-[9px] text-[#B45309] font-bold mt-0.5">ทอง</span>
                      <span className="text-xs font-black text-[#3D2012] font-mono">
                        {gold}
                      </span>
                      {isRunning && (
                        <span className="text-[8px] text-[#8C6D58] leading-none">
                          รวม {d.box_counts?.gold ?? 0}
                        </span>
                      )}
                    </div>

                    {/* Silver Box */}
                    <div className="bg-white/90 p-1 rounded-lg border border-[#CBD5E1] flex flex-col items-center">
                      <img
                        src="/templates/BOX_SILVER.png"
                        alt="เงิน"
                        className="w-4 h-4 object-contain"
                      />
                      <span className="text-[9px] text-[#475569] font-bold mt-0.5">เงิน</span>
                      <span className="text-xs font-black text-[#3D2012] font-mono">
                        {silver}
                      </span>
                      {isRunning && (
                        <span className="text-[8px] text-[#8C6D58] leading-none">
                          รวม {d.box_counts?.silver ?? 0}
                        </span>
                      )}
                    </div>

                    {/* Wood Box */}
                    <div className="bg-white/90 p-1 rounded-lg border border-[#FCD34D] flex flex-col items-center">
                      <img
                        src="/templates/BOX_WOOD.png"
                        alt="ไม้"
                        className="w-4 h-4 object-contain"
                      />
                      <span className="text-[9px] text-[#92400E] font-bold mt-0.5">ไม้</span>
                      <span className="text-xs font-black text-[#3D2012] font-mono">
                        {wood}
                      </span>
                      {isRunning && (
                        <span className="text-[8px] text-[#8C6D58] leading-none">
                          รวม {d.box_counts?.wood ?? 0}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Action Buttons for this Device */}
              <div className="flex items-center justify-between gap-2 pt-1 border-t border-[#F0DFC9]">
                <button
                  onClick={() => onSelectDevice(d.serial)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold transition flex items-center space-x-1 cursor-pointer ${
                    isSelected
                      ? 'bg-[#F59E0B] text-white shadow-xs'
                      : 'bg-white text-[#8A3B04] border border-[#EEDBCE] hover:bg-[#FFF8EC]'
                  }`}
                  title="สลับหน้าจอสตรีมสดมาที่จอนี้"
                >
                  <Eye className="w-3.5 h-3.5" />
                  <span>{isSelected ? 'กำลังดูกล้องจอนี้' : 'ดูกล้องจอนี้'}</span>
                </button>

                <div className="flex items-center space-x-1.5">
                  {isRunning ? (
                    <button
                      onClick={() => onStopDevice && onStopDevice(d.serial)}
                      className="candy-btn-strawberry px-2.5 py-1.5 rounded-xl text-xs font-bold transition flex items-center space-x-1 cursor-pointer"
                      title="หยุดบอทเฉพาะจอนี้"
                    >
                      <Square className="w-3 h-3 fill-current" />
                      <span>หยุดจอนี้</span>
                    </button>
                  ) : (
                    <button
                      onClick={() => onStartDevice && onStartDevice(d.serial)}
                      className="candy-btn-honey px-2.5 py-1.5 rounded-xl text-xs font-bold transition flex items-center space-x-1 cursor-pointer"
                      title="เริ่มบอทเฉพาะจอนี้"
                    >
                      <Play className="w-3 h-3 fill-current" />
                      <span>เริ่มจอนี้</span>
                    </button>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
