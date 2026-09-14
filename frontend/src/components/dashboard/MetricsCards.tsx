import React from 'react';
import { Coins, Heart, Trophy, UserMinus } from 'lucide-react';
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
  const isRunning = device?.is_running ?? false;
  const isFarmer = device?.active_mode === 'heart_farmer';
  const isCleaner = device?.active_mode === 'friend_cleaner';

  const allDevices = devices.length > 0 ? devices : (device ? [device] : []);
  const totalCoins = allDevices.reduce((sum, d) => sum + (d.coin_stats?.session_earned ?? 0), 0);

  const rainbowCount = allDevices.reduce(
    (sum, d) => sum + (d.session_box_counts?.rainbow ?? d.box_counts?.rainbow ?? 0),
    0
  );
  const goldCount = allDevices.reduce(
    (sum, d) => sum + (d.session_box_counts?.gold ?? d.box_counts?.gold ?? 0),
    0
  );
  const silverCount = allDevices.reduce(
    (sum, d) => sum + (d.session_box_counts?.silver ?? d.box_counts?.silver ?? 0),
    0
  );
  const woodCount = allDevices.reduce(
    (sum, d) => sum + (d.session_box_counts?.wood ?? d.box_counts?.wood ?? 0),
    0
  );

  const roundsCount = isRunning
    ? (device?.session_rounds ?? 0)
    : (device?.rounds_played ?? 0);

  const formatCoins = (coins: number) => {
    if (coins >= 1000000) return `${(coins / 1000000).toFixed(1)}M`;
    if (coins >= 1000) return `${(coins / 1000).toFixed(1)}K`;
    return coins.toLocaleString();
  };

  return (
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
        <span className="text-base font-extrabold text-[#3D2012] mt-0.5 font-mono">{rainbowCount}</span>
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
        <span className="text-base font-extrabold text-[#3D2012] mt-0.5 font-mono">{goldCount}</span>
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
        <span className="text-base font-extrabold text-[#3D2012] mt-0.5 font-mono">{silverCount}</span>
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
        <span className="text-base font-extrabold text-[#3D2012] mt-0.5 font-mono">{woodCount}</span>
      </div>

      {/* 5. Total Coins */}
      <div className="biscuit-card p-3 rounded-2xl flex flex-col items-center justify-center text-center shadow-sm hover:border-[#F59E0B]">
        <div className="w-10 h-10 rounded-full bg-gradient-to-b from-[#FFFBEB] to-[#FDE68A] border border-[#FCD34D] text-[#D97706] flex items-center justify-center mb-1.5 shadow-sm">
          <Coins className="w-5 h-5 text-[#D97706]" />
        </div>
        <span className="text-[11px] text-[#B45309] font-bold leading-tight">เหรียญรวม</span>
        <span className="text-base font-extrabold text-[#3D2012] mt-0.5 font-mono">
          {formatCoins(totalCoins)}
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
          {isCleaner ? 'ลบเพื่อน' : isFarmer ? 'หัวใจ' : 'รอบวิ่ง'}
        </span>
        <span className="text-base font-extrabold text-[#3D2012] mt-0.5 font-mono">
          {isCleaner
            ? (device?.cleaner_stats?.is_busy ? 'ทำอยู่' : 'พร้อม')
            : isFarmer
            ? device?.heart_stats?.success_count ?? 0
            : roundsCount}
        </span>
      </div>
    </div>
  );
};
