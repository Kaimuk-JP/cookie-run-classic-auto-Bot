import React, { useState } from 'react';
import {
  Play,
  Square,
  Zap,
  RotateCcw,
  Plug,
  Camera,
  Sliders,
} from 'lucide-react';
import { botApi } from '../../api/botApi';
import { toast, confirmModal } from '../../context/ToastContext';

interface QuickActionsProps {
  deviceSerial: string;
  isRunning: boolean;
  onStart: () => void;
  onStop: () => void;
  onOpenSettings: () => void;
  onOpenMacro: () => void;
  onOpenDiscord: () => void;
  onOpenTools: () => void;
}

export const QuickActions: React.FC<QuickActionsProps> = ({
  deviceSerial,
  isRunning,
  onStart,
  onStop,
}) => {
  const [loadingAction, setLoadingAction] = useState<string | null>(null);

  const handleClearRam = async () => {
    setLoadingAction('ram');
    try {
      const res = await botApi.clearRam();
      toast.success(res.message || 'เคลียร์ RAM สำเร็จ');
    } catch (e: any) {
      toast.error('เคลียร์ RAM ไม่สำเร็จ: ' + e.message);
    } finally {
      setLoadingAction(null);
    }
  };

  const handleResetApp = async () => {
    if (!deviceSerial) return toast.warning('กรุณาเลือกจอก่อน');
    const ok = await confirmModal({
      title: 'รีสตาร์ทเกม CookieRun',
      message: 'ต้องการบังคับปิดและเปิดเกม CookieRun ใหม่ทันทีหรือไม่?',
      confirmText: 'รีสตาร์ทเกม',
      type: 'warning',
    });
    if (!ok) return;

    setLoadingAction('reset');
    try {
      const res = await botApi.resetApp(deviceSerial);
      toast.success(res.message || 'รีสตาร์ทเกมแล้ว');
    } catch (e: any) {
      toast.error('รีสตาร์ทเกมไม่สำเร็จ: ' + e.message);
    } finally {
      setLoadingAction(null);
    }
  };

  const handleTestAdb = async () => {
    if (!deviceSerial) return toast.warning('กรุณาเลือกจอก่อน');
    setLoadingAction('adb');
    try {
      const res = await botApi.testConnection(deviceSerial);
      toast.success(res.message || 'เชื่อมต่อ ADB สำเร็จ');
    } catch (e: any) {
      toast.error('ตรวจสอบ ADB ไม่สำเร็จ: ' + e.message);
    } finally {
      setLoadingAction(null);
    }
  };

  const handleCaptureScreen = () => {
    if (!deviceSerial) return toast.warning('กรุณาเลือกจอก่อน');
    window.open(`/api/screen?device=${encodeURIComponent(deviceSerial)}&download=1`, '_blank');
    toast.success('บันทึกภาพหน้าจอเรียบร้อย');
  };

  return (
    <div className="glass-panel rounded-3xl p-5 shadow-xl space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-sm text-white flex items-center space-x-2">
          <Sliders className="w-4 h-4 text-purple-400" />
          <span>แผงควบคุมหลัก (Control Center)</span>
        </h3>
        <span className="text-[11px] text-purple-300 font-mono bg-purple-950/60 px-2 py-0.5 rounded border border-purple-500/20 truncate max-w-[140px]">
          {deviceSerial || '127.0.0.1:5555'}
        </span>
      </div>

      {/* Main Start / Stop Buttons Grid */}
      <div className="grid grid-cols-2 gap-3">
        <button
          onClick={onStart}
          className={`py-3 px-4 rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-bold shadow-lg shadow-emerald-900/40 transition flex items-center justify-center space-x-2 active:scale-95 cursor-pointer ${
            isRunning ? 'opacity-80 ring-2 ring-emerald-400' : ''
          }`}
        >
          <Play className="w-4 h-4 fill-current" />
          <span>เริ่มทำงานบอท</span>
        </button>

        <button
          onClick={onStop}
          className="py-3 px-4 rounded-2xl bg-gradient-to-r from-rose-600 to-red-600 hover:from-rose-500 hover:to-red-500 text-white text-xs font-bold shadow-lg shadow-rose-900/40 transition flex items-center justify-center space-x-2 active:scale-95 cursor-pointer"
        >
          <Square className="w-4 h-4 fill-current" />
          <span>หยุดการทำงาน</span>
        </button>
      </div>

      {/* Utility Buttons Grid (4 columns) */}
      <div className="grid grid-cols-4 gap-2">
        <button
          onClick={handleClearRam}
          disabled={loadingAction === 'ram'}
          className="glass-card p-2.5 rounded-xl flex flex-col items-center justify-center hover:bg-purple-800/40 transition text-purple-200 active:scale-95 disabled:opacity-50 cursor-pointer"
          title="เคลียร์ RAM 3 ระดับ"
        >
          <Zap className="w-4 h-4 text-amber-400 mb-1" />
          <span className="text-[10px]">เคลียร์ RAM</span>
        </button>

        <button
          onClick={handleResetApp}
          disabled={loadingAction === 'reset'}
          className="glass-card p-2.5 rounded-xl flex flex-col items-center justify-center hover:bg-purple-800/40 transition text-purple-200 active:scale-95 disabled:opacity-50 cursor-pointer"
          title="Force close & รีสตาร์ทเกม CookieRun"
        >
          <RotateCcw className="w-4 h-4 text-purple-400 mb-1" />
          <span className="text-[10px]">รีสตาร์ทเกม</span>
        </button>

        <button
          onClick={handleTestAdb}
          disabled={loadingAction === 'adb'}
          className="glass-card p-2.5 rounded-xl flex flex-col items-center justify-center hover:bg-purple-800/40 transition text-purple-200 active:scale-95 disabled:opacity-50 cursor-pointer"
          title="ทดสอบสัญญาณการเชื่อมต่อ ADB"
        >
          <Plug className="w-4 h-4 text-emerald-400 mb-1" />
          <span className="text-[10px]">เช็ค ADB</span>
        </button>

        <button
          onClick={handleCaptureScreen}
          className="glass-card p-2.5 rounded-xl flex flex-col items-center justify-center hover:bg-purple-800/40 transition text-purple-200 active:scale-95 cursor-pointer"
          title="บันทึกภาพหน้าจอปัจจุบันและดาวน์โหลด"
        >
          <Camera className="w-4 h-4 text-sky-400 mb-1" />
          <span className="text-[10px]">แคปภาพจอ</span>
        </button>
      </div>
    </div>
  );
};
