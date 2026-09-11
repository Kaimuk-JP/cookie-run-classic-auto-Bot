import React from 'react';
import { PlayCircle, Clock, Trophy, Gift, ArrowUpRight } from 'lucide-react';
import { Device } from '../../types/bot';

import { translateStageToThai } from '../../utils/translations';

interface MetricsCardsProps {
  device?: Device;
  onOpenStats: () => void;
}

export const MetricsCards: React.FC<MetricsCardsProps> = ({ device, onOpenStats }) => {
  const isRunning = device?.is_running ?? false;
  const stageText = translateStageToThai(device?.current_stage, isRunning);

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {/* 1. Status & Stage */}
      <div className="bg-white border border-purple-100 rounded-3xl p-4 shadow-card hover:shadow-md transition">
        <div className="flex items-center justify-between">
          <p className="text-xs font-medium text-slate-400">สถานะปัจจุบัน</p>
          <span
            className={`inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full ${
              isRunning ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-600'
            }`}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                isRunning ? 'bg-emerald-500 animate-pulse' : 'bg-slate-400'
              }`}
            ></span>
            {isRunning ? 'กำลังทำงาน' : 'หยุดพัก'}
          </span>
        </div>
        <h4 className="text-lg sm:text-xl font-bold text-slate-800 mt-2 truncate font-sans" title={stageText}>
          {stageText}
        </h4>
        <p className="text-[11px] text-slate-500 mt-0.5 truncate">
          {device?.name || device?.serial || 'ยังไม่ได้เลือกจอ'}
        </p>
      </div>

      {/* 2. Rounds Played */}
      <div className="bg-white border border-purple-100 rounded-3xl p-4 shadow-card hover:shadow-md transition flex items-center justify-between">
        <div className="space-y-1">
          <p className="text-xs font-medium text-slate-400">รอบที่เล่นแล้ว</p>
          <h4 className="text-xl sm:text-2xl font-bold text-slate-800 font-mono">
            {device?.rounds_played ?? 0}
          </h4>
          <span className="text-[11px] font-semibold text-emerald-600 flex items-center gap-0.5">
            ↑ สะสมในเซสชัน
          </span>
        </div>
        <div className="w-12 h-12 rounded-2xl bg-amber-50 flex items-center justify-center shrink-0 shadow-xs border border-amber-100">
          <Trophy className="w-6 h-6 text-amber-600" />
        </div>
      </div>

      {/* 3. Mystery Boxes (Clickable to open StatsModal) */}
      <div
        onClick={onOpenStats}
        className="bg-white border border-purple-100 rounded-3xl p-4 shadow-card hover:shadow-md hover:border-brand-300 transition cursor-pointer group flex items-center justify-between"
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
            {device?.mystery_boxes ?? 0}
          </h4>
          <span className="text-[11px] font-semibold text-purple-600">
            ดูสถิติสะสม &gt;
          </span>
        </div>
        <div className="w-12 h-12 rounded-2xl bg-purple-50 flex items-center justify-center shrink-0 shadow-xs border border-purple-100 group-hover:scale-105 transition">
          <img src="/templates/BOX_WOOD.png" alt="กล่อง" className="w-8 h-8 object-contain drop-shadow-xs" />
        </div>
      </div>

      {/* 4. Total Uptime */}
      <div className="bg-white border border-purple-100 rounded-3xl p-4 shadow-card hover:shadow-md transition flex items-center justify-between">
        <div className="space-y-1">
          <p className="text-xs font-medium text-slate-400">เวลาการทำงานบอท</p>
          <h4 className="text-lg sm:text-xl font-bold text-slate-800 font-mono">
            {device?.uptime || '00:00:00'}
          </h4>
          <span
            className={`text-[11px] font-semibold flex items-center gap-1 ${
              isRunning ? 'text-emerald-600' : 'text-slate-500'
            }`}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                isRunning ? 'bg-emerald-500 animate-pulse' : 'bg-slate-400'
              }`}
            ></span>
            {isRunning ? 'กำลังทำงาน' : 'พร้อมทำงาน'}
          </span>
        </div>
        <div className="w-12 h-12 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0 shadow-xs border border-emerald-100">
          <Clock className="w-6 h-6" />
        </div>
      </div>
    </div>
  );
};
