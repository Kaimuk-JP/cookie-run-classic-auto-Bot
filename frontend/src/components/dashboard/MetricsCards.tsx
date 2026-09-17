import React, { useState } from 'react';
import { Coins, Heart, Trophy, UserMinus, Sparkles, Layers } from 'lucide-react';
import { Device } from '../../types/bot';

interface MetricsCardsProps {
  device?: Device;
  devices?: Device[];
  onOpenStats: () => void;
}

export const MetricsCards: React.FC<MetricsCardsProps> = ({
  device,
  devices = [],
  onOpenStats,
}) => {
  // Target device or first available
  const activeDev = device || (devices.length > 0 ? devices[0] : undefined);

  // Scope: 'device' (only active device) or 'all' (sum all devices)
  const [scope, setScope] = useState<'device' | 'all'>('device');
  const isAll = scope === 'all' && devices.length > 1;

  // Running status
  const isRunning = isAll
    ? devices.some((d) => d.is_running)
    : (activeDev?.is_running ?? false);
  const isFarmer = !isAll && activeDev?.active_mode === 'heart_farmer';
  const isCleaner = !isAll && activeDev?.active_mode === 'friend_cleaner';

  // View Mode: 'auto' (shows session if running, lifetime if idle), or manual 'session' or 'lifetime'
  const [viewMode, setViewMode] = useState<'auto' | 'session' | 'lifetime'>('auto');

  // Determine whether to show session (current active run) or lifetime (ยอดยกมา)
  const showSession = viewMode === 'auto' ? isRunning : viewMode === 'session';

  // Boxes:
  const rainbowCount = showSession
    ? (isAll
        ? devices.reduce((s, d) => s + (d.session_box_counts?.rainbow ?? 0), 0)
        : (activeDev?.session_box_counts?.rainbow ?? 0))
    : (isAll
        ? devices.reduce((s, d) => s + (d.box_counts?.rainbow ?? 0), 0)
        : (activeDev?.box_counts?.rainbow ?? 0));
  const rainbowLifetime = isAll
    ? devices.reduce((s, d) => s + (d.box_counts?.rainbow ?? 0), 0)
    : (activeDev?.box_counts?.rainbow ?? 0);

  const goldCount = showSession
    ? (isAll
        ? devices.reduce((s, d) => s + (d.session_box_counts?.gold ?? 0), 0)
        : (activeDev?.session_box_counts?.gold ?? 0))
    : (isAll
        ? devices.reduce((s, d) => s + (d.box_counts?.gold ?? 0), 0)
        : (activeDev?.box_counts?.gold ?? 0));
  const goldLifetime = isAll
    ? devices.reduce((s, d) => s + (d.box_counts?.gold ?? 0), 0)
    : (activeDev?.box_counts?.gold ?? 0);

  const silverCount = showSession
    ? (isAll
        ? devices.reduce((s, d) => s + (d.session_box_counts?.silver ?? 0), 0)
        : (activeDev?.session_box_counts?.silver ?? 0))
    : (isAll
        ? devices.reduce((s, d) => s + (d.box_counts?.silver ?? 0), 0)
        : (activeDev?.box_counts?.silver ?? 0));
  const silverLifetime = isAll
    ? devices.reduce((s, d) => s + (d.box_counts?.silver ?? 0), 0)
    : (activeDev?.box_counts?.silver ?? 0);

  const woodCount = showSession
    ? (isAll
        ? devices.reduce((s, d) => s + (d.session_box_counts?.wood ?? 0), 0)
        : (activeDev?.session_box_counts?.wood ?? 0))
    : (isAll
        ? devices.reduce((s, d) => s + (d.box_counts?.wood ?? 0), 0)
        : (activeDev?.box_counts?.wood ?? 0));
  const woodLifetime = isAll
    ? devices.reduce((s, d) => s + (d.box_counts?.wood ?? 0), 0)
    : (activeDev?.box_counts?.wood ?? 0);

  // Coins:
  const totalCoins = showSession
    ? (isAll
        ? devices.reduce((s, d) => s + (d.coin_stats?.session_earned ?? 0), 0)
        : (activeDev?.coin_stats?.session_earned ?? 0))
    : (isAll
        ? devices.reduce((s, d) => s + (d.coin_stats?.lifetime_earned ?? 0), 0)
        : (activeDev?.coin_stats?.lifetime_earned ?? 0));
  const coinsLifetime = isAll
    ? devices.reduce((s, d) => s + (d.coin_stats?.lifetime_earned ?? 0), 0)
    : (activeDev?.coin_stats?.lifetime_earned ?? 0);

  // Rounds:
  // "หากเริ่มแล้วให้แสดงรอบที่กำลังเริ่มอยู่"
  const currentActiveRound = isAll
    ? devices.reduce((s, d) => s + Math.max(d.session_rounds || 0, d.is_running ? 1 : 0), 0)
    : Math.max(1, activeDev?.session_rounds || 1);

  const roundsCount = showSession
    ? currentActiveRound
    : (isAll
        ? devices.reduce((s, d) => s + (d.rounds_played ?? 0), 0)
        : (activeDev?.rounds_played ?? 0));

  const formatCoins = (coins: number) => {
    if (coins >= 1000000) return `${(coins / 1000000).toFixed(1)}M`;
    if (coins >= 1000) return `${(coins / 1000).toFixed(1)}K`;
    return coins.toLocaleString();
  };

  return (
    <div className="space-y-2">
      {/* Sub-header status & toggle pills */}
      <div className="flex flex-wrap items-center justify-between gap-2 px-1 text-xs">
        <div className="flex items-center space-x-2 flex-wrap gap-y-1">
          {showSession ? (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-[#ECFDF5] text-[#047857] border border-[#A7F3D0] font-bold text-[11px] shadow-2xs">
              <span className="w-2 h-2 rounded-full bg-[#10B981] animate-ping"></span>
              ⚡ {isAll ? `รอบที่กำลังรันอยู่ (รวมทุกจอ)` : `รอบที่กำลังเริ่มอยู่ (รอบที่ ${currentActiveRound})`}
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-[#FFFBEB] text-[#B45309] border border-[#FDE68A] font-bold text-[11px] shadow-2xs">
              📦 แสดงยอดยกมา (สะสมเดิม)
            </span>
          )}

          {!isAll && activeDev && (
            <span className="text-[#8C6D58] font-medium hidden sm:inline">
              • {activeDev.name || activeDev.serial}
            </span>
          )}
          {isAll && (
            <span className="text-[#8C6D58] font-medium hidden sm:inline">
              • รวมทั้งหมด {devices.length} จอ
            </span>
          )}
        </div>

        {/* Controls: Scope Toggle & View Mode Toggle */}
        <div className="flex items-center space-x-1.5 flex-wrap gap-y-1">
          {/* Device Scope Switcher (if > 1 device) */}
          {devices.length > 1 && (
            <div className="flex items-center space-x-0.5 bg-[#FFF8EC] p-0.5 rounded-xl border border-[#EEDBCE] text-[10px] font-bold shadow-2xs">
              <button
                onClick={() => setScope('device')}
                className={`px-2 py-0.5 rounded-lg transition cursor-pointer ${
                  scope === 'device'
                    ? 'bg-[#F59E0B] text-white shadow-2xs'
                    : 'text-[#8A3B04] hover:text-[#452311]'
                }`}
                title="แสดงสถิติเฉพาะจอนี้"
              >
                จอนี้
              </button>
              <button
                onClick={() => setScope('all')}
                className={`px-2 py-0.5 rounded-lg transition cursor-pointer ${
                  scope === 'all'
                    ? 'bg-[#F59E0B] text-white shadow-2xs'
                    : 'text-[#8A3B04] hover:text-[#452311]'
                }`}
                title="แสดงสถิติรวมทุกจอ"
              >
                รวมทุกจอ
              </button>
            </div>
          )}

          {/* View Mode Toggle Buttons */}
          <div className="flex items-center space-x-0.5 bg-[#FFF8EC] p-0.5 rounded-xl border border-[#EEDBCE] text-[10px] font-bold shadow-2xs">
            <button
              onClick={() => setViewMode('session')}
              className={`px-2 py-0.5 rounded-lg transition cursor-pointer ${
                showSession
                  ? 'bg-[#F59E0B] text-white shadow-2xs'
                  : 'text-[#8A3B04] hover:text-[#452311]'
              }`}
              title="แสดงผลเฉพาะรอบที่กำลังรันอยู่"
            >
              รอบปัจจุบัน
            </button>
            <button
              onClick={() => setViewMode('lifetime')}
              className={`px-2 py-0.5 rounded-lg transition cursor-pointer ${
                !showSession
                  ? 'bg-[#F59E0B] text-white shadow-2xs'
                  : 'text-[#8A3B04] hover:text-[#452311]'
              }`}
              title="แสดงยอดยกมาทั้งหมด"
            >
              ยอดยกมา
            </button>
            {viewMode !== 'auto' && (
              <button
                onClick={() => setViewMode('auto')}
                className="px-1.5 py-0.5 rounded-lg text-[#8C6D58] hover:text-[#452311] transition cursor-pointer"
                title="สลับอัตโนมัติ (กำลังรัน=รอบปัจจุบัน, หยุด=ยอดยกมา)"
              >
                (ออโต้)
              </button>
            )}
          </div>
        </div>
      </div>

      {/* 6 Metric Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5 sm:gap-3">
        {/* 1. Legendary Box (BOX_RAINBOW.png) */}
        <div
          onClick={onOpenStats}
          className="biscuit-card p-3 rounded-2xl flex flex-col items-center justify-center text-center cursor-pointer group shadow-sm hover:border-[#C084FC] hover:bg-[#FAF5FF]"
          title="ดูสถิติกล่อง"
        >
          <div className="w-10 h-10 rounded-full bg-gradient-to-b from-[#FAF5FF] to-[#EDE9FE] border border-[#DDD6FE] flex items-center justify-center mb-1.5 group-hover:scale-110 transition-transform shadow-sm">
            <img
              src="/templates/BOX_RAINBOW.png"
              alt="กล่องรุ้ง"
              className="w-7 h-7 object-contain drop-shadow"
            />
          </div>
          <span className="text-[11px] text-[#7C3AED] font-bold leading-tight">กล่องรุ้ง</span>
          <span className="text-base font-extrabold text-[#3D2012] mt-0.5 font-mono">
            {rainbowCount}
          </span>
          <span className="text-[9px] text-[#8C6D58] mt-0.5 leading-none">
            {showSession ? `(ยกมา: ${rainbowLifetime})` : 'ยอดยกมา'}
          </span>
        </div>

        {/* 2. Gold Box (BOX_GOLD.png) */}
        <div
          onClick={onOpenStats}
          className="biscuit-card p-3 rounded-2xl flex flex-col items-center justify-center text-center cursor-pointer group shadow-sm hover:border-[#FBBF24] hover:bg-[#FFFDF0]"
          title="ดูสถิติกล่อง"
        >
          <div className="w-10 h-10 rounded-full bg-gradient-to-b from-[#FEFCE8] to-[#FEF3C7] border border-[#FDE68A] flex items-center justify-center mb-1.5 group-hover:scale-110 transition-transform shadow-sm">
            <img
              src="/templates/BOX_GOLD.png"
              alt="กล่องทอง"
              className="w-7 h-7 object-contain drop-shadow"
            />
          </div>
          <span className="text-[11px] text-[#B45309] font-bold leading-tight">กล่องทอง</span>
          <span className="text-base font-extrabold text-[#3D2012] mt-0.5 font-mono">
            {goldCount}
          </span>
          <span className="text-[9px] text-[#8C6D58] mt-0.5 leading-none">
            {showSession ? `(ยกมา: ${goldLifetime})` : 'ยอดยกมา'}
          </span>
        </div>

        {/* 3. Silver Box (BOX_SILVER.png) */}
        <div
          onClick={onOpenStats}
          className="biscuit-card p-3 rounded-2xl flex flex-col items-center justify-center text-center cursor-pointer group shadow-sm hover:border-[#94A3B8] hover:bg-[#F8FAFC]"
          title="ดูสถิติกล่อง"
        >
          <div className="w-10 h-10 rounded-full bg-gradient-to-b from-[#F8FAFC] to-[#E2E8F0] border border-[#CBD5E1] flex items-center justify-center mb-1.5 group-hover:scale-110 transition-transform shadow-sm">
            <img
              src="/templates/BOX_SILVER.png"
              alt="กล่องเงิน"
              className="w-7 h-7 object-contain drop-shadow"
            />
          </div>
          <span className="text-[11px] text-[#475569] font-bold leading-tight">กล่องเงิน</span>
          <span className="text-base font-extrabold text-[#3D2012] mt-0.5 font-mono">
            {silverCount}
          </span>
          <span className="text-[9px] text-[#8C6D58] mt-0.5 leading-none">
            {showSession ? `(ยกมา: ${silverLifetime})` : 'ยอดยกมา'}
          </span>
        </div>

        {/* 4. Wood Box (BOX_WOOD.png) */}
        <div
          onClick={onOpenStats}
          className="biscuit-card p-3 rounded-2xl flex flex-col items-center justify-center text-center cursor-pointer group shadow-sm hover:border-[#D97706] hover:bg-[#FFFBEB]"
          title="ดูสถิติกล่อง"
        >
          <div className="w-10 h-10 rounded-full bg-gradient-to-b from-[#FEF3C7] to-[#FDE68A] border border-[#FCD34D] flex items-center justify-center mb-1.5 group-hover:scale-110 transition-transform shadow-sm">
            <img
              src="/templates/BOX_WOOD.png"
              alt="กล่องไม้"
              className="w-7 h-7 object-contain drop-shadow"
            />
          </div>
          <span className="text-[11px] text-[#92400E] font-bold leading-tight">กล่องไม้</span>
          <span className="text-base font-extrabold text-[#3D2012] mt-0.5 font-mono">
            {woodCount}
          </span>
          <span className="text-[9px] text-[#8C6D58] mt-0.5 leading-none">
            {showSession ? `(ยกมา: ${woodLifetime})` : 'ยอดยกมา'}
          </span>
        </div>

        {/* 5. Total Coins */}
        <div className="biscuit-card p-3 rounded-2xl flex flex-col items-center justify-center text-center shadow-sm hover:border-[#F59E0B]">
          <div className="w-10 h-10 rounded-full bg-gradient-to-b from-[#FFFBEB] to-[#FDE68A] border border-[#FCD34D] text-[#D97706] flex items-center justify-center mb-1.5 shadow-sm">
            <Coins className="w-5 h-5 text-[#D97706]" />
          </div>
          <span className="text-[11px] text-[#B45309] font-bold leading-tight">
            {showSession ? 'เหรียญรอบนี้' : 'เหรียญสะสม'}
          </span>
          <span className="text-base font-extrabold text-[#3D2012] mt-0.5 font-mono">
            {showSession ? `+${formatCoins(totalCoins)}` : formatCoins(totalCoins)}
          </span>
          <span className="text-[9px] text-[#8C6D58] mt-0.5 leading-none">
            {showSession ? `(ยกมา: ${formatCoins(coinsLifetime)})` : 'ยอดยกมา'}
          </span>
        </div>

        {/* 6. Hearts Run / Cleaner / Rounds */}
        <div className="biscuit-card p-3 rounded-2xl flex flex-col items-center justify-center text-center shadow-sm hover:border-[#F43F5E]">
          <div className="w-10 h-10 rounded-full bg-gradient-to-b from-[#FFF1F2] to-[#FFE4E6] border border-[#FECDD3] text-[#E11D48] flex items-center justify-center mb-1.5 shadow-sm">
            {isCleaner ? (
              <UserMinus className="w-5 h-5 text-[#E11D48]" />
            ) : isFarmer ? (
              <Heart className="w-5 h-5 text-[#E11D48] animate-pulse fill-[#E11D48]" />
            ) : (
              <Trophy className="w-5 h-5 text-[#E11D48]" />
            )}
          </div>
          <span className="text-[11px] text-[#BE123C] font-bold leading-tight">
            {isCleaner
              ? 'ลบเพื่อน'
              : isFarmer
              ? 'หัวใจ'
              : showSession
              ? 'รอบที่กำลังวิ่ง'
              : 'รอบสะสม'}
          </span>
          <span className="text-base font-extrabold text-[#3D2012] mt-0.5 font-mono">
            {isCleaner
              ? activeDev?.cleaner_stats?.is_busy
                ? 'ทำอยู่'
                : 'พร้อม'
              : isFarmer
              ? activeDev?.heart_stats?.success_count ?? 0
              : showSession
              ? `รอบที่ ${roundsCount}`
              : `${roundsCount} รอบ`}
          </span>
          <span className="text-[9px] text-[#8C6D58] mt-0.5 leading-none">
            {isCleaner || isFarmer
              ? 'โหมดพิเศษ'
              : showSession
              ? `(สะสม: ${isAll ? devices.reduce((s, d) => s + (d.rounds_played ?? 0), 0) : activeDev?.rounds_played ?? 0})`
              : 'ยอดยกมา'}
          </span>
        </div>
      </div>
    </div>
  );
};
