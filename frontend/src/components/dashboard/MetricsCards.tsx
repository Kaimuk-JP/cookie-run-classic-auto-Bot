import React from 'react';
import { Clock, Trophy, ArrowUpRight, Heart, UserMinus, Coins, Star } from 'lucide-react';
import { Device } from '../../types/bot';

interface MetricsCardsProps {
  device?: Device;
  devices?: Device[];
  onOpenStats: () => void;
}

export const MetricsCards: React.FC<MetricsCardsProps> = ({ device, devices = [], onOpenStats }) => {
  const isRunning = device?.is_running ?? false;
  const isFarmer = device?.active_mode === 'heart_farmer';
  const isCleaner = device?.active_mode === 'friend_cleaner';

  // Calculate totals across ALL devices
  const allDevices = devices && devices.length > 0 ? devices : (device ? [device] : []);
  const totalCoins = allDevices.reduce((sum, d) => sum + (d.coin_stats?.session_earned ?? 0), 0);
  const totalXp = allDevices.reduce((sum, d) => sum + (d.coin_stats?.session_xp_earned ?? 0), 0);
  const totalCoinsPerHour = allDevices.reduce((sum, d) => sum + (d.coin_stats?.coins_per_hour ?? 0), 0);

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
      {/* 1. Combined Gold & EXP across All Devices (Replaces สถานะปัจจุบัน) */}
      <div className="bg-gradient-to-br from-amber-50/80 via-white to-amber-50/40 border border-amber-200/90 rounded-2xl sm:rounded-3xl p-3.5 sm:p-4 shadow-card hover:shadow-md transition">
        <div className="flex items-center justify-between">
          <p className="text-xs font-bold text-amber-900/80">ผลรวมทุกจอ (All Devices)</p>
          <span className="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 border border-amber-200">
            <Coins className="w-2.5 h-2.5 text-amber-600" />
            รวม {allDevices.length} จอ
          </span>
        </div>

        {/* Total Gold Display */}
        <div className="mt-2 flex items-baseline gap-1.5">
          <Coins className="w-4 h-4 sm:w-5 sm:h-5 text-amber-500 shrink-0 self-center" />
          <h4 className="text-lg sm:text-2xl font-black text-amber-700 font-mono tracking-tight">
            +{totalCoins.toLocaleString()}
          </h4>
          <span className="text-[10px] sm:text-xs font-semibold text-amber-600">เหรียญ</span>
        </div>

        {/* Total EXP Display */}
        <div className="mt-1 flex items-center gap-1.5 text-xs text-indigo-600 font-semibold font-mono">
          <Star className="w-3.5 h-3.5 text-amber-400 fill-amber-400 shrink-0" />
          <span>+{totalXp.toLocaleString()} EXP</span>
          {totalCoinsPerHour > 0 && (
            <span className="text-[10px] text-slate-400 font-normal ml-auto hidden sm:inline">
              ~{(totalCoinsPerHour).toLocaleString()}/ชม.
            </span>
          )}
        </div>
      </div>

      {/* 2. Rounds Played / Hearts Sent / Friend Cleaner Status */}
      {isCleaner ? (
        <div className="bg-white border border-teal-100 rounded-2xl sm:rounded-3xl p-3.5 sm:p-4 shadow-card hover:shadow-md transition flex items-center justify-between">
          <div className="space-y-1">
            <p className="text-xs font-medium text-slate-400">รอบถัดไป / สถานะ</p>
            <h4 className="text-base sm:text-lg font-bold text-teal-700 font-mono truncate max-w-[150px]">
              {device?.cleaner_stats?.next_run ? `เวลา ${device.cleaner_stats.next_run}` : 'กำลังทำงาน'}
            </h4>
            <span className="text-[11px] font-semibold text-teal-600 flex items-center gap-0.5">
              {device?.cleaner_stats?.is_busy ? '⚡ กำลังทำงานบนจอนี้' : '⏳ รอรอบถัดไป'}
            </span>
          </div>
          <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-xl sm:rounded-2xl bg-teal-50 flex items-center justify-center shrink-0 shadow-xs border border-teal-200">
            <UserMinus className="w-5 h-5 sm:w-6 sm:h-6 text-teal-600" />
          </div>
        </div>
      ) : isFarmer ? (
        <div className="bg-white border border-pink-100 rounded-2xl sm:rounded-3xl p-3.5 sm:p-4 shadow-card hover:shadow-md transition flex items-center justify-between">
          <div className="space-y-1">
            <p className="text-xs font-medium text-slate-400">ส่งหัวใจสำเร็จ</p>
            <h4 className="text-xl sm:text-2xl font-bold text-pink-600 font-mono">
              {device?.heart_stats?.success_count ?? 0}{' '}
              <span className="text-xs font-semibold text-pink-400">ดวง</span>
            </h4>
            <span className="text-[11px] font-semibold text-pink-600 flex items-center gap-0.5">
              ↑ สำเร็จ {device?.heart_stats?.success_count ?? 0} / {device?.heart_stats?.rounds ?? 0} รอบ
            </span>
          </div>
          <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-xl sm:rounded-2xl bg-pink-50 flex items-center justify-center shrink-0 shadow-xs border border-pink-200">
            <Heart className="w-5 h-5 sm:w-6 sm:h-6 text-pink-500 fill-pink-500 animate-pulse" />
          </div>
        </div>
      ) : (
        <div className="bg-white border border-purple-100 rounded-2xl sm:rounded-3xl p-3.5 sm:p-4 shadow-card hover:shadow-md transition flex items-center justify-between">
          <div className="space-y-1">
            <p className="text-xs font-medium text-slate-400">รอบที่เล่นแล้ว</p>
            <h4 className="text-xl sm:text-2xl font-bold text-slate-800 font-mono">
              {isRunning
                ? (device?.session_rounds ?? 0)
                : (device?.rounds_played ?? 0)}
              <span className="text-xs font-normal text-slate-400 ml-1">รอบ</span>
            </h4>
            <span className="text-[11px] font-semibold text-emerald-600 flex items-center gap-0.5">
              {isRunning
                ? `↑ รอบเซสชันนี้ (สะสม ${device?.rounds_played ?? 0} รอบ)`
                : `↑ สะสมทั้งหมด ${device?.rounds_played ?? 0} รอบ`}
            </span>
          </div>
          <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-xl sm:rounded-2xl bg-amber-50 flex items-center justify-center shrink-0 shadow-xs border border-amber-100">
            <Trophy className="w-5 h-5 sm:w-6 sm:h-6 text-amber-600" />
          </div>
        </div>
      )}

      {/* 3. Mystery Boxes (Clickable to open StatsModal) */}
      <div
        onClick={onOpenStats}
        className="bg-white border border-purple-100 rounded-2xl sm:rounded-3xl p-3.5 sm:p-4 shadow-card hover:shadow-md hover:border-brand-300 transition cursor-pointer group flex items-center justify-between"
        title="คลิกเพื่อดูสถิติกล่องแยกเกรด ไม้/เงิน/ทอง/รุ้ง"
      >
        <div className="space-y-1">
          <div className="flex items-center gap-1">
            <p className="text-xs font-medium text-slate-400 group-hover:text-brand-600 transition">
              กล่องปริศนา
            </p>
            <ArrowUpRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-brand-600 transition" />
          </div>
          <h4 className="text-xl sm:text-2xl font-bold text-slate-800 font-mono">
            {isRunning
              ? (device?.session_mystery_boxes ?? device?.mystery_boxes ?? 0)
              : (device?.mystery_boxes ?? 0)}
            <span className="text-xs font-normal text-slate-400 ml-1">กล่อง</span>
          </h4>
          <span className="text-[11px] font-semibold text-purple-600">
            {isRunning
              ? `รอบนี้ (สะสม ${device?.mystery_boxes ?? 0}) >`
              : 'ดูสถิติสะสม >'}
          </span>
        </div>
        <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-xl sm:rounded-2xl bg-purple-50 flex items-center justify-center shrink-0 shadow-xs border border-purple-100 group-hover:scale-105 transition">
          <img src="/templates/BOX_WOOD.png" alt="กล่อง" className="w-7 h-7 sm:w-8 sm:h-8 object-contain drop-shadow-xs" />
        </div>
      </div>

      {/* 4. Total Uptime */}
      <div className="bg-white border border-purple-100 rounded-2xl sm:rounded-3xl p-3.5 sm:p-4 shadow-card hover:shadow-md transition flex items-center justify-between">
        <div className="space-y-1">
          <p className="text-xs font-medium text-slate-400">เวลาการทำงานบอท</p>
          <h4 className="text-lg sm:text-xl font-bold text-slate-800 font-mono">
            {isRunning
              ? (device?.session_uptime || device?.uptime || '00:00:00')
              : (device?.uptime || '00:00:00')}
          </h4>
          <span
            className={`text-[11px] font-semibold flex items-center gap-1 ${
              isFarmer ? 'text-pink-600' : isRunning ? 'text-emerald-600' : 'text-slate-500'
            }`}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                isFarmer ? 'bg-pink-500 animate-pulse' : isRunning ? 'bg-emerald-500 animate-pulse' : 'bg-slate-400'
              }`}
            ></span>
            {isFarmer
              ? 'กำลังปั้มหัวใจ'
              : isRunning
              ? (device?.session_start_time ? `เริ่ม ${device.session_start_time}` : 'กำลังทำงาน')
              : 'พร้อมทำงาน'}
          </span>
        </div>
        <div
          className={`w-10 h-10 sm:w-12 sm:h-12 rounded-xl sm:rounded-2xl flex items-center justify-center shrink-0 shadow-xs border ${
            isFarmer
              ? 'bg-pink-50 text-pink-600 border-pink-100'
              : 'bg-emerald-50 text-emerald-600 border-emerald-100'
          }`}
        >
          <Clock className="w-5 h-5 sm:w-6 sm:h-6" />
        </div>
      </div>
    </div>
  );
};
