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
        className="glass-card p-3 rounded-2xl flex flex-col items-center justify-center text-center border-[#DC95FF]/30 hover:border-[#DC95FF]/60 transition cursor-pointer group shadow-sm"
        title="คลิกเพื่อดูสถิติกล่องละเอียด"
      >
        <div className="w-9 h-9 rounded-full bg-[#DC95FF]/15 flex items-center justify-center mb-1.5 group-hover:scale-110 transition-transform">
          <img
            src="/templates/BOX_RAINBOW.png"
            alt="Legendary Box"
            className="w-7 h-7 object-contain drop-shadow-md"
          />
        </div>
        <span className="text-[11px] text-[#DC95FF] font-medium leading-tight">Legendary Box</span>
        <span className="text-base font-bold text-white mt-0.5 font-mono">{rainbowCount}</span>
      </div>

      {/* 2. Gold Box (BOX_GOLD.png) */}
      <div
        onClick={onOpenStats}
        className="glass-card p-3 rounded-2xl flex flex-col items-center justify-center text-center border-[#FFF4BF]/30 hover:border-[#FFF4BF]/60 transition cursor-pointer group shadow-sm"
        title="คลิกเพื่อดูสถิติกล่องละเอียด"
      >
        <div className="w-9 h-9 rounded-full bg-[#FFF4BF]/15 flex items-center justify-center mb-1.5 group-hover:scale-110 transition-transform">
          <img
            src="/templates/BOX_GOLD.png"
            alt="Gold Box"
            className="w-7 h-7 object-contain drop-shadow-md"
          />
        </div>
        <span className="text-[11px] text-[#FFF4BF] font-medium leading-tight">Gold Box</span>
        <span className="text-base font-bold text-white mt-0.5 font-mono">{goldCount}</span>
      </div>

      {/* 3. Silver Box (BOX_SILVER.png) */}
      <div
        onClick={onOpenStats}
        className="glass-card p-3 rounded-2xl flex flex-col items-center justify-center text-center border-[#DC95FF]/20 hover:border-[#FFBEFB]/50 transition cursor-pointer group shadow-sm"
        title="คลิกเพื่อดูสถิติกล่องละเอียด"
      >
        <div className="w-9 h-9 rounded-full bg-[#8C56D4]/20 flex items-center justify-center mb-1.5 group-hover:scale-110 transition-transform">
          <img
            src="/templates/BOX_SILVER.png"
            alt="Silver Box"
            className="w-7 h-7 object-contain drop-shadow-md"
          />
        </div>
        <span className="text-[11px] text-[#FFBEFB]/90 font-medium leading-tight">Silver Box</span>
        <span className="text-base font-bold text-white mt-0.5 font-mono">{silverCount}</span>
      </div>

      {/* 4. Wood Box (BOX_WOOD.png) */}
      <div
        onClick={onOpenStats}
        className="glass-card p-3 rounded-2xl flex flex-col items-center justify-center text-center border-amber-600/30 hover:border-amber-500/60 transition cursor-pointer group shadow-sm"
        title="คลิกเพื่อดูสถิติกล่องละเอียด"
      >
        <div className="w-9 h-9 rounded-full bg-amber-600/15 flex items-center justify-center mb-1.5 group-hover:scale-110 transition-transform">
          <img
            src="/templates/BOX_WOOD.png"
            alt="Wood Box"
            className="w-7 h-7 object-contain drop-shadow-md"
          />
        </div>
        <span className="text-[11px] text-amber-300 font-medium leading-tight">Wood Box</span>
        <span className="text-base font-bold text-white mt-0.5 font-mono">{woodCount}</span>
      </div>

      {/* 5. Total Coins */}
      <div className="glass-card p-3 rounded-2xl flex flex-col items-center justify-center text-center border-[#FFF4BF]/30 hover:border-[#FFF4BF]/60 transition shadow-sm">
        <div className="w-9 h-9 rounded-full bg-[#FFF4BF]/20 text-[#FFF4BF] flex items-center justify-center mb-1.5">
          <Coins className="w-5 h-5 text-[#FFF4BF]" />
        </div>
        <span className="text-[11px] text-[#FFF4BF] font-medium leading-tight">Total Coins</span>
        <span className="text-base font-bold text-white mt-0.5 font-mono">
          {formatCoins(totalCoins)}
        </span>
      </div>

      {/* 6. Hearts Run / Cleaner / Rounds */}
      <div className="glass-card p-3 rounded-2xl flex flex-col items-center justify-center text-center border-[#FFBEFB]/30 hover:border-[#FFBEFB]/60 transition shadow-sm">
        <div className="w-9 h-9 rounded-full bg-[#FFBEFB]/20 text-[#FFBEFB] flex items-center justify-center mb-1.5">
          {isCleaner ? (
            <UserMinus className="w-5 h-5 text-[#FFBEFB]" />
          ) : isFarmer ? (
            <Heart className="w-5 h-5 text-[#FFBEFB] animate-pulse" />
          ) : (
            <Trophy className="w-5 h-5 text-[#FFBEFB]" />
          )}
        </div>
        <span className="text-[11px] text-[#FFBEFB] font-medium leading-tight">
          {isCleaner ? 'Cleaner' : isFarmer ? 'Hearts' : 'Rounds'}
        </span>
        <span className="text-base font-bold text-white mt-0.5 font-mono">
          {isCleaner
            ? (device?.cleaner_stats?.is_busy ? 'Busy' : 'Idle')
            : isFarmer
            ? device?.heart_stats?.success_count ?? 0
            : roundsCount}
        </span>
      </div>
    </div>
  );
};
