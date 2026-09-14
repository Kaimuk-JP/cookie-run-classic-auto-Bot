import React from 'react';
import { Gem, Box, Shield, Coins, Heart, Trophy, UserMinus } from 'lucide-react';
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

  // Calculate totals across all devices for global view or active device
  const allDevices = devices.length > 0 ? devices : (device ? [device] : []);
  const totalCoins = allDevices.reduce((sum, d) => sum + (d.coin_stats?.session_earned ?? 0), 0);

  // Box statistics
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

  const roundsCount = isRunning
    ? (device?.session_rounds ?? 0)
    : (device?.rounds_played ?? 0);

  const formatCoins = (coins: number) => {
    if (coins >= 1000000) return `${(coins / 1000000).toFixed(1)}M`;
    if (coins >= 1000) return `${(coins / 1000).toFixed(1)}K`;
    return coins.toLocaleString();
  };

  return (
    <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
      {/* 1. Diamond Box */}
      <div
        onClick={onOpenStats}
        className="glass-card p-3 rounded-2xl flex flex-col items-center justify-center text-center border-purple-500/20 hover:border-purple-400/50 transition cursor-pointer group"
      >
        <div className="w-8 h-8 rounded-full bg-purple-500/20 text-purple-300 flex items-center justify-center mb-1.5 group-hover:scale-110 transition-transform">
          <Gem className="w-4 h-4 text-purple-300" />
        </div>
        <span className="text-[11px] text-purple-300 font-medium">Diamond Box</span>
        <span className="text-base font-bold text-white mt-0.5 font-mono">{rainbowCount}</span>
      </div>

      {/* 2. Gold Box */}
      <div
        onClick={onOpenStats}
        className="glass-card p-3 rounded-2xl flex flex-col items-center justify-center text-center border-amber-500/20 hover:border-amber-400/50 transition cursor-pointer group"
      >
        <div className="w-8 h-8 rounded-full bg-amber-500/20 text-amber-300 flex items-center justify-center mb-1.5 group-hover:scale-110 transition-transform">
          <Box className="w-4 h-4 text-amber-300" />
        </div>
        <span className="text-[11px] text-amber-300 font-medium">Gold Box</span>
        <span className="text-base font-bold text-white mt-0.5 font-mono">{goldCount}</span>
      </div>

      {/* 3. Silver Box */}
      <div
        onClick={onOpenStats}
        className="glass-card p-3 rounded-2xl flex flex-col items-center justify-center text-center border-slate-400/20 hover:border-slate-300/50 transition cursor-pointer group"
      >
        <div className="w-8 h-8 rounded-full bg-slate-500/20 text-slate-300 flex items-center justify-center mb-1.5 group-hover:scale-110 transition-transform">
          <Shield className="w-4 h-4 text-slate-300" />
        </div>
        <span className="text-[11px] text-slate-300 font-medium">Silver Box</span>
        <span className="text-base font-bold text-white mt-0.5 font-mono">{silverCount}</span>
      </div>

      {/* 4. Total Coins */}
      <div className="glass-card p-3 rounded-2xl flex flex-col items-center justify-center text-center border-yellow-500/20 hover:border-yellow-400/50 transition">
        <div className="w-8 h-8 rounded-full bg-yellow-500/20 text-yellow-300 flex items-center justify-center mb-1.5">
          <Coins className="w-4 h-4 text-yellow-300" />
        </div>
        <span className="text-[11px] text-yellow-300 font-medium">Total Coins</span>
        <span className="text-base font-bold text-white mt-0.5 font-mono">
          {formatCoins(totalCoins)}
        </span>
      </div>

      {/* 5. Hearts Run / Cleaner / Rounds */}
      <div className="glass-card col-span-2 sm:col-span-1 p-3 rounded-2xl flex flex-col items-center justify-center text-center border-pink-500/20 hover:border-pink-400/50 transition">
        <div className="w-8 h-8 rounded-full bg-pink-500/20 text-pink-300 flex items-center justify-center mb-1.5">
          {isCleaner ? (
            <UserMinus className="w-4 h-4 text-teal-300" />
          ) : isFarmer ? (
            <Heart className="w-4 h-4 text-pink-300 animate-pulse" />
          ) : (
            <Trophy className="w-4 h-4 text-pink-300" />
          )}
        </div>
        <span className="text-[11px] text-pink-300 font-medium">
          {isCleaner ? 'Cleaner' : isFarmer ? 'Hearts Run' : 'Total Rounds'}
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
