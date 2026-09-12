import React from 'react';
import { PlayCircle, Clock, Trophy, Gift, ArrowUpRight, Heart, UserMinus } from 'lucide-react';
import { Device } from '../../types/bot';

import { translateStageToThai } from '../../utils/translations';

interface MetricsCardsProps {
  device?: Device;
  onOpenStats: () => void;
}

export const MetricsCards: React.FC<MetricsCardsProps> = ({ device, onOpenStats }) => {
  const isRunning = device?.is_running ?? false;
  const isFarmer = device?.active_mode === 'heart_farmer';
  const isCleaner = device?.active_mode === 'friend_cleaner';

  const stageText = isCleaner
    ? (device?.cleaner_stats?.is_busy ? 'กำลังลบเพื่อนเวล 1 🧹' : 'ระบบลบเพื่อนเลเวล 1')
    : isFarmer
    ? `กำลังปั้มหัวใจ (รอบที่ ${device?.heart_stats?.rounds || 1})`
    : translateStageToThai(device?.current_stage, isRunning);

  const actionDetail = isCleaner
    ? (device?.cleaner_stats?.current_step || 'กำลังเตรียมการลบเพื่อน...')
    : isFarmer
    ? (device?.heart_stats?.current_step || 'กำลังวนลูปปั้มหัวใจ...')
    : isRunning
    ? `กำลังฟาร์มเหรียญ • รอบที่ ${device?.rounds_played || 0}`
    : `จอ: ${device?.name || device?.serial || 'จอจำลอง'} • พร้อมเริ่มงาน`;

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {/* 1. Status & Stage */}
      <div className="bg-white border border-purple-100 rounded-3xl p-4 shadow-card hover:shadow-md transition">
        <div className="flex items-center justify-between">
          <p className="text-xs font-medium text-slate-400">สถานะปัจจุบัน</p>
          <span
            className={`inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full ${
              isCleaner
                ? 'bg-teal-100 text-teal-800 border border-teal-200'
                : isFarmer
                ? 'bg-pink-100 text-pink-700 border border-pink-200'
                : isRunning
                ? 'bg-emerald-100 text-emerald-700'
                : 'bg-slate-100 text-slate-600'
            }`}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                isCleaner
                  ? 'bg-teal-500 animate-pulse'
                  : isFarmer
                  ? 'bg-pink-500 animate-pulse'
                  : isRunning
                  ? 'bg-emerald-500 animate-pulse'
                  : 'bg-slate-400'
              }`}
            ></span>
            {isCleaner ? 'ลบเพื่อนเวล 1 🧹' : isFarmer ? 'กำลังปั้มหัวใจ ❤️' : isRunning ? 'กำลังทำงาน' : 'หยุดพัก'}
          </span>
        </div>
        <h4 className="text-lg sm:text-xl font-bold text-slate-800 mt-2 truncate font-sans" title={stageText}>
          {stageText}
        </h4>
        <p className="text-[11px] text-slate-500 mt-0.5 truncate" title={actionDetail}>
          {isCleaner ? (
            <span className="text-teal-700 font-medium">⚡ {actionDetail}</span>
          ) : isFarmer ? (
            <span className="text-pink-600 font-medium">⚡ {actionDetail}</span>
          ) : (
            actionDetail
          )}
        </p>
      </div>

      {/* 2. Rounds Played / Hearts Sent / Friend Cleaner Status */}
      {isCleaner ? (
        <div className="bg-white border border-teal-100 rounded-3xl p-4 shadow-card hover:shadow-md transition flex items-center justify-between">
          <div className="space-y-1">
            <p className="text-xs font-medium text-slate-400">รอบถัดไป / สถานะ</p>
            <h4 className="text-base sm:text-lg font-bold text-teal-700 font-mono truncate max-w-[150px]">
              {device?.cleaner_stats?.next_run ? `เวลา ${device.cleaner_stats.next_run}` : 'กำลังทำงาน'}
            </h4>
            <span className="text-[11px] font-semibold text-teal-600 flex items-center gap-0.5">
              {device?.cleaner_stats?.is_busy ? '⚡ กำลังทำงานบนจอนี้' : '⏳ รอรอบถัดไป'}
            </span>
          </div>
          <div className="w-12 h-12 rounded-2xl bg-teal-50 flex items-center justify-center shrink-0 shadow-xs border border-teal-200">
            <UserMinus className="w-6 h-6 text-teal-600" />
          </div>
        </div>
      ) : isFarmer ? (
        <div className="bg-white border border-pink-100 rounded-3xl p-4 shadow-card hover:shadow-md transition flex items-center justify-between">
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
          <div className="w-12 h-12 rounded-2xl bg-pink-50 flex items-center justify-center shrink-0 shadow-xs border border-pink-200">
            <Heart className="w-6 h-6 text-pink-500 fill-pink-500 animate-pulse" />
          </div>
        </div>
      ) : (
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
      )}

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
              isFarmer ? 'text-pink-600' : isRunning ? 'text-emerald-600' : 'text-slate-500'
            }`}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                isFarmer ? 'bg-pink-500 animate-pulse' : isRunning ? 'bg-emerald-500 animate-pulse' : 'bg-slate-400'
              }`}
            ></span>
            {isFarmer ? 'กำลังปั้มหัวใจ' : isRunning ? 'กำลังทำงาน' : 'พร้อมทำงาน'}
          </span>
        </div>
        <div
          className={`w-12 h-12 rounded-2xl flex items-center justify-center shrink-0 shadow-xs border ${
            isFarmer
              ? 'bg-pink-50 text-pink-600 border-pink-100'
              : 'bg-emerald-50 text-emerald-600 border-emerald-100'
          }`}
        >
          <Clock className="w-6 h-6" />
        </div>
      </div>
    </div>
  );
};

