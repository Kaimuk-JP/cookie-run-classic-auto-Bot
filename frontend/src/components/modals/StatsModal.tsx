import React, { useState } from 'react';
import {
  X,
  BarChart3,
  Coins,
  Sparkles,
  Trash2,
  TrendingUp,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  Activity,
  Layers,
  Zap,
  History,
} from 'lucide-react';
import { Device } from '../../types/bot';
import { botApi } from '../../api/botApi';
import { FarmingChart } from '../dashboard/FarmingChart';
import { toast, confirmModal } from '../../context/ToastContext';

interface StatsModalProps {
  isOpen: boolean;
  onClose: () => void;
  device?: Device;
  onReset?: () => void;
}

export const StatsModal: React.FC<StatsModalProps> = ({ isOpen, onClose, device, onReset }) => {
  const [activeTab, setActiveTab] = useState<'chart' | 'summary'>('chart');
  const [scope, setScope] = useState<'session' | 'all'>('session');
  const [isResetting, setIsResetting] = useState(false);

  if (!isOpen) return null;

  const handleResetStats = async () => {
    const ok = await confirmModal({
      title: 'รีเซ็ตสถิติสะสม',
      message: `คุณแน่ใจหรือไม่ว่าต้องการลบสถิติสะสม (เหรียญ, EXP, กล่องปริศนา, แคปซ่า) ทั้งหมดของจอ ${device?.serial || 'ทั้งหมด'}?`,
      confirmText: 'ลบสถิติทั้งหมด',
      type: 'danger',
    });
    if (!ok) return;

    setIsResetting(true);
    try {
      const res = await botApi.resetStats(device?.serial);
      toast.success(res.message || 'ลบสถิติทั้งหมดเรียบร้อยแล้ว');
      if (onReset) onReset();
      onClose();
    } catch (e: any) {
      toast.error('ลบสถิติไม่สำเร็จ: ' + e.message);
    } finally {
      setIsResetting(false);
    }
  };

  const isSession = scope === 'session';

  const boxes = isSession
    ? (device?.session_box_counts || { wood: 0, silver: 0, gold: 0, rainbow: 0, total: 0 })
    : (device?.box_counts || { wood: 0, silver: 0, gold: 0, rainbow: 0, total: 0 });

  const coins = isSession
    ? (device?.coin_stats?.session_earned ?? 0)
    : (device?.coin_stats?.lifetime_earned ?? device?.coin_stats?.session_earned ?? 0);

  const xp = isSession
    ? (device?.coin_stats?.session_xp_earned ?? 0)
    : (device?.coin_stats?.lifetime_xp_earned ?? device?.coin_stats?.session_xp_earned ?? 0);

  const chartHistory = isSession
    ? (device?.session_round_history || [])
    : (device?.round_history || []);

  const coinsPerHour = isSession
    ? (device?.coin_stats?.coins_per_hour ?? 0)
    : (device?.coin_stats?.lifetime_coins_per_hour ?? device?.coin_stats?.coins_per_hour ?? 0);

  const captcha = device?.captcha_stats || {
    total_attempts: 0,
    success_count: 0,
    fail_count: 0,
    last_attempt_time: null,
    last_result: null,
  };

  const captchaSuccessRate =
    captcha.total_attempts > 0
      ? Math.round((captcha.success_count / captcha.total_attempts) * 100)
      : 100;

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl max-w-2xl w-full max-h-[92vh] flex flex-col p-6 shadow-2xl border border-purple-100 animate-in fade-in zoom-in-95 duration-150">
        {/* Modal Header */}
        <div className="flex items-center justify-between pb-3 border-b border-purple-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center text-xl shadow-xs border border-amber-100">
              <BarChart3 className="w-5 h-5 text-amber-600" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">
                สถิติ & กราฟ
              </h3>
              <p className="text-xs text-slate-500">
                วิเคราะห์รอบปัจจุบันและสะสม • {device?.name || device?.serial || '-'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-slate-100 hover:bg-slate-200 flex items-center justify-center text-slate-600 font-bold transition cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Scope Selector: This Session vs All-Time */}
        <div className="flex flex-wrap items-center justify-between gap-2 pt-3 pb-2 border-b border-purple-50">
          <div className="flex items-center p-1 bg-slate-100/90 rounded-2xl gap-1">
            <button
              onClick={() => setScope('session')}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer ${
                scope === 'session'
                  ? 'bg-amber-500 text-white shadow-sm shadow-amber-200'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Zap className="w-3.5 h-3.5" />
              <span>⚡ รอบปัจจุบัน</span>
            </button>
            <button
              onClick={() => setScope('all')}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer ${
                scope === 'all'
                  ? 'bg-purple-600 text-white shadow-sm shadow-purple-200'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <History className="w-3.5 h-3.5" />
              <span>🏛️ สะสมทั้งหมด</span>
            </button>
          </div>

          {/* Session quick info indicator */}
          <div className="text-[11px] font-medium text-slate-500 flex items-center gap-2">
            {isSession ? (
              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-amber-50 text-amber-800 border border-amber-200 font-mono text-[11px]">
                <Clock className="w-3 h-3 text-amber-600" />
                เริ่ม: <strong>{device?.session_start_time || 'เพิ่งเริ่ม'}</strong>
                <span className="text-amber-400">|</span>
                วิ่ง: <strong>{device?.session_uptime || '00:00:00'}</strong>
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-purple-50 text-purple-800 border border-purple-200 font-mono text-[11px]">
                <Layers className="w-3 h-3 text-purple-600" />
                เวลารวม: <strong>{device?.total_uptime || device?.uptime || '00:00:00'}</strong>
              </span>
            )}
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-2 pt-2">
          <button
            onClick={() => setActiveTab('chart')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition cursor-pointer ${
              activeTab === 'chart'
                ? 'bg-purple-600 text-white shadow-md shadow-purple-200'
                : 'bg-slate-100 hover:bg-slate-200 text-slate-600'
            }`}
          >
            <TrendingUp className="w-4 h-4" />
            <span>กราฟรายรอบ</span>
          </button>
          <button
            onClick={() => setActiveTab('summary')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition cursor-pointer ${
              activeTab === 'summary'
                ? 'bg-purple-600 text-white shadow-md shadow-purple-200'
                : 'bg-slate-100 hover:bg-slate-200 text-slate-600'
            }`}
          >
            <Layers className="w-4 h-4" />
            <span>สรุปสถิติ & แคปซ่า</span>
            {captcha.total_attempts > 0 && (
              <span className="px-1.5 py-0.5 rounded-full text-[10px] bg-purple-200 text-purple-900">
                {captcha.total_attempts}
              </span>
            )}
          </button>
        </div>

        {/* Modal Scrollable Body */}
        <div className="flex-1 overflow-y-auto space-y-4 py-3 pr-1">
          {activeTab === 'chart' ? (
            /* TAB 1: Analytics & Charts */
            <FarmingChart
              history={chartHistory}
              coinsPerHour={coinsPerHour}
              scope={scope}
              sessionStartTime={device?.session_start_time}
              sessionUptime={device?.session_uptime}
              allHistory={device?.round_history || []}
              onSwitchToAll={() => setScope('all')}
            />
          ) : (
            /* TAB 2: Summary Stats & Captcha */
            <div className="space-y-4">
              {/* 4-Tier Mystery Box Cards with Real Images */}
              <div>
                <h4 className="text-xs font-bold text-slate-700 mb-2 flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-amber-500"></span>
                    {isSession ? 'กล่องปริศนาที่ได้รับในรอบนี้ (เซสชันปัจจุบัน)' : 'กล่องปริศนาสะสมทั้งหมด (All-Time)'}
                  </span>
                  <span className="text-[11px] font-mono text-slate-500 font-normal">
                    รวม {boxes.total ?? 0} กล่อง
                  </span>
                </h4>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center text-xs">
                  {/* Wood */}
                  <div className="p-3 rounded-2xl bg-amber-50 border border-amber-200 space-y-1 shadow-xs">
                    <img
                      src="/templates/BOX_WOOD.png"
                      alt="กล่องไม้"
                      className="w-11 h-11 mx-auto object-contain drop-shadow-sm"
                    />
                    <div className="font-bold text-amber-900">กล่องไม้</div>
                    <div className="text-xl font-bold font-mono text-amber-700">
                      {boxes.wood ?? 0}
                    </div>
                  </div>

                  {/* Silver */}
                  <div className="p-3 rounded-2xl bg-slate-100 border border-slate-200 space-y-1 shadow-xs">
                    <img
                      src="/templates/BOX_SILVER.png"
                      alt="กล่องเงิน"
                      className="w-11 h-11 mx-auto object-contain drop-shadow-sm"
                    />
                    <div className="font-bold text-slate-900">กล่องเงิน</div>
                    <div className="text-xl font-bold font-mono text-slate-700">
                      {boxes.silver ?? 0}
                    </div>
                  </div>

                  {/* Gold */}
                  <div className="p-3 rounded-2xl bg-yellow-50 border border-yellow-200 space-y-1 shadow-xs">
                    <img
                      src="/templates/BOX_GOLD.png"
                      alt="กล่องทอง"
                      className="w-11 h-11 mx-auto object-contain drop-shadow-sm"
                    />
                    <div className="font-bold text-yellow-900">กล่องทอง</div>
                    <div className="text-xl font-bold font-mono text-yellow-600">
                      {boxes.gold ?? 0}
                    </div>
                  </div>

                  {/* Rainbow */}
                  <div className="p-3 rounded-2xl bg-gradient-to-tr from-pink-50 to-purple-50 border border-pink-200 space-y-1 shadow-xs">
                    <img
                      src="/templates/BOX_RAINBOW.png"
                      alt="กล่องรุ้ง"
                      className="w-11 h-11 mx-auto object-contain drop-shadow-sm"
                    />
                    <div className="font-bold text-purple-900">กล่องรุ้ง</div>
                    <div className="text-xl font-bold font-mono text-purple-600">
                      {boxes.rainbow ?? 0}
                    </div>
                  </div>
                </div>
              </div>

              {/* Total Coins & EXP Accumulator */}
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-between shadow-xs">
                  <div>
                    <span className="text-slate-500 font-medium">
                      {isSession ? 'เหรียญรอบนี้ (เซสชันปัจจุบัน)' : 'เหรียญสะสมทั้งหมด (All-Time)'}
                    </span>
                    <div className="text-xl font-bold font-mono text-amber-600 mt-0.5">
                      +{coins.toLocaleString()} 🪙
                    </div>
                  </div>
                  <Coins className="w-8 h-8 text-amber-500" />
                </div>

                <div className="p-4 rounded-2xl bg-sky-500/10 border border-sky-500/20 flex items-center justify-between shadow-xs">
                  <div>
                    <span className="text-slate-500 font-medium">
                      {isSession ? 'EXP รอบนี้ (เซสชันปัจจุบัน)' : 'EXP สะสมทั้งหมด (All-Time)'}
                    </span>
                    <div className="text-xl font-bold font-mono text-sky-600 mt-0.5">
                      +{xp.toLocaleString()} EXP
                    </div>
                  </div>
                  <Sparkles className="w-8 h-8 text-sky-500" />
                </div>
              </div>

              {/* Anti-Bot Captcha Tracker Section */}
              <div className="p-4 rounded-2xl bg-linear-to-br from-indigo-50/70 via-purple-50/50 to-pink-50/30 border border-indigo-100 space-y-3 shadow-xs">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-xl bg-indigo-600 text-white flex items-center justify-center shadow-xs">
                      <ShieldCheck className="w-4 h-4" />
                    </div>
                    <div>
                      <h4 className="text-xs font-bold text-slate-900">
                        ระบบตรวจจับ & ปลดแคปซ่า (Anti-Bot Captcha Solver)
                      </h4>
                      <p className="text-[11px] text-slate-500">
                        บันทึกจำนวนครั้งที่เจอด่านแคปซ่าและผลการปลดล็อคอัตโนมัติ
                      </p>
                    </div>
                  </div>
                  <span
                    className={`px-2.5 py-1 rounded-full text-xs font-bold font-mono flex items-center gap-1 ${
                      captcha.total_attempts === 0
                        ? 'bg-slate-100 text-slate-600'
                        : captcha.fail_count === 0
                        ? 'bg-emerald-100 text-emerald-700'
                        : 'bg-amber-100 text-amber-700'
                    }`}
                  >
                    {captcha.total_attempts === 0
                      ? 'ยังไม่พบแคปซ่า'
                      : `สำเร็จ ${captchaSuccessRate}%`}
                  </span>
                </div>

                {/* 4 Captcha Metrics Cards */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-center">
                  <div className="p-2.5 rounded-xl bg-white/80 border border-slate-200/70 shadow-2xs">
                    <span className="text-[11px] text-slate-500 font-medium">เจอแคปซ่าทั้งหมด</span>
                    <div className="text-lg font-bold font-mono text-slate-800 mt-0.5">
                      {captcha.total_attempts} <span className="text-xs font-normal text-slate-400">ครั้ง</span>
                    </div>
                  </div>

                  <div className="p-2.5 rounded-xl bg-emerald-50/80 border border-emerald-200/70 shadow-2xs">
                    <div className="flex items-center justify-center gap-1 text-[11px] text-emerald-700 font-medium">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>แก้สำเร็จ</span>
                    </div>
                    <div className="text-lg font-bold font-mono text-emerald-600 mt-0.5">
                      {captcha.success_count} <span className="text-xs font-normal text-emerald-400">ครั้ง</span>
                    </div>
                  </div>

                  <div className="p-2.5 rounded-xl bg-rose-50/80 border border-rose-200/70 shadow-2xs">
                    <div className="flex items-center justify-center gap-1 text-[11px] text-rose-700 font-medium">
                      <XCircle className="w-3.5 h-3.5" />
                      <span>แก้ไม่สำเร็จ</span>
                    </div>
                    <div className="text-lg font-bold font-mono text-rose-600 mt-0.5">
                      {captcha.fail_count} <span className="text-xs font-normal text-rose-400">ครั้ง</span>
                    </div>
                  </div>

                  <div className="p-2.5 rounded-xl bg-purple-50/80 border border-purple-200/70 shadow-2xs">
                    <span className="text-[11px] text-purple-700 font-medium">อัตราสำเร็จ</span>
                    <div className="text-lg font-bold font-mono text-purple-600 mt-0.5">
                      {captchaSuccessRate}%
                    </div>
                  </div>
                </div>

                {/* Captcha details footer */}
                <div className="flex flex-wrap items-center justify-between text-[11px] text-slate-500 pt-1 border-t border-indigo-100/60">
                  <div className="flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5 text-slate-400" />
                    <span>
                      แก้ครั้งล่าสุด:{' '}
                      <strong className="text-slate-700">
                        {captcha.last_attempt_time ? captcha.last_attempt_time : 'ยังไม่มีประวัติ'}
                      </strong>
                    </span>
                  </div>

                  {captcha.last_result && (
                    <div className="flex items-center gap-1">
                      <span>ผลลัพธ์ล่าสุด:</span>
                      {captcha.last_result === 'success' ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-700">
                          <CheckCircle2 className="w-3 h-3" /> สำเร็จ
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-700">
                          <XCircle className="w-3 h-3" /> ไม่สำเร็จ
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="pt-3 flex items-center justify-between border-t border-purple-100">
          <button
            onClick={handleResetStats}
            disabled={isResetting}
            className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-rose-50 hover:bg-rose-100 text-rose-600 font-bold text-xs border border-rose-200 transition active:scale-95 disabled:opacity-50 cursor-pointer"
            title="ล้างสถิติทั้งหมด"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>{isResetting ? 'กำลังล้าง...' : 'ล้างสถิติ'}</span>
          </button>

          <button
            onClick={onClose}
            className="px-5 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs transition active:scale-95 cursor-pointer"
          >
            ปิด
          </button>
        </div>
      </div>
    </div>
  );
};

