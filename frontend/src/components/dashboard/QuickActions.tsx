import React, { useState } from 'react';
import {
  Play,
  Square,
  Sparkles,
  RotateCcw,
  Wifi,
  Camera,
  Settings,
  Bell,
  Heart,
} from 'lucide-react';
import { botApi } from '../../api/botApi';

interface QuickActionsProps {
  deviceSerial: string;
  isRunning: boolean;
  onStart: () => void;
  onStop: () => void;
  onOpenSettings: () => void;
  onOpenDiscord: () => void;
  onOpenTools: () => void;
}

export const QuickActions: React.FC<QuickActionsProps> = ({
  deviceSerial,
  isRunning,
  onStart,
  onStop,
  onOpenSettings,
  onOpenDiscord,
  onOpenTools,
}) => {
  const [loadingAction, setLoadingAction] = useState<string | null>(null);

  const handleClearRam = async () => {
    setLoadingAction('ram');
    try {
      const res = await botApi.clearRam();
      alert(res.message || 'เคลียร์ RAM เรียบร้อย');
    } catch (e: any) {
      alert('เคลียร์ RAM ไม่สำเร็จ: ' + e.message);
    } finally {
      setLoadingAction(null);
    }
  };

  const handleResetApp = async () => {
    if (!deviceSerial) return alert('กรุณาเลือกจอก่อน');
    if (!confirm('ต้องการบังคับปิดและเปิดเกม CookieRun ใหม่หรือไม่?')) return;
    setLoadingAction('reset');
    try {
      const res = await botApi.resetApp(deviceSerial);
      alert(res.message || 'รีสตาร์ทเกมเรียบร้อย');
    } catch (e: any) {
      alert('รีสตาร์ทเกมไม่สำเร็จ: ' + e.message);
    } finally {
      setLoadingAction(null);
    }
  };

  const handleTestAdb = async () => {
    if (!deviceSerial) return alert('กรุณาเลือกจอก่อน');
    setLoadingAction('adb');
    try {
      const res = await botApi.testConnection(deviceSerial);
      alert(res.message || 'ADB ทำงานปกติ');
    } catch (e: any) {
      alert('ตรวจสอบ ADB ไม่สำเร็จ: ' + e.message);
    } finally {
      setLoadingAction(null);
    }
  };

  const handleCaptureScreen = () => {
    if (!deviceSerial) return alert('กรุณาเลือกจอก่อน');
    window.open(`/api/screen?device=${encodeURIComponent(deviceSerial)}&download=1`, '_blank');
  };

  return (
    <div className="bg-white border border-purple-100 rounded-3xl p-4 shadow-card space-y-3">
      <div className="flex items-center justify-between pb-2 border-b border-purple-50">
        <h3 className="text-xs font-bold text-slate-800">แผงควบคุมและเครื่องมือด่วน</h3>
        <span className="text-[11px] text-slate-400 font-mono truncate max-w-[140px]">
          {deviceSerial || '-'}
        </span>
      </div>

      {/* Main Start / Stop Button */}
      {isRunning ? (
        <button
          onClick={onStop}
          className="w-full py-3.5 rounded-2xl bg-rose-600 hover:bg-rose-700 text-white font-bold text-sm shadow-md shadow-rose-600/30 transition flex items-center justify-center gap-2 active:scale-98 animate-pulse cursor-pointer"
        >
          <Square className="w-4 h-4 fill-current" />
          <span>⏹️ หยุดบอท</span>
        </button>
      ) : (
        <button
          onClick={onStart}
          className="w-full py-3.5 rounded-2xl bg-gradient-to-r from-brand-600 to-brand-500 hover:from-brand-700 hover:to-brand-600 text-white font-bold text-sm shadow-btn transition flex items-center justify-center gap-2 active:scale-98 cursor-pointer"
        >
          <Play className="w-4 h-4 fill-current" />
          <span>▶️ เริ่มบอท (Start Bot)</span>
        </button>
      )}

      {/* 4 Tool Action Buttons */}
      <div className="grid grid-cols-2 gap-2 text-xs font-semibold">
        <button
          onClick={handleClearRam}
          disabled={loadingAction === 'ram'}
          className="flex items-center justify-center gap-1.5 py-2.5 px-3 rounded-xl border border-purple-100 hover:border-purple-200 bg-purple-50/50 hover:bg-purple-50 text-brand-700 transition active:scale-95 disabled:opacity-50"
          title="เคลียร์ RAM 3 ระดับ (Python + Windows + Android)"
        >
          <Sparkles className="w-3.5 h-3.5 text-brand-600" />
          <span>🧹 เคลียร์ RAM</span>
        </button>

        <button
          onClick={handleResetApp}
          disabled={loadingAction === 'reset'}
          className="flex items-center justify-center gap-1.5 py-2.5 px-3 rounded-xl border border-slate-200 hover:border-slate-300 bg-slate-50 hover:bg-slate-100 text-slate-700 transition active:scale-95 disabled:opacity-50"
          title="Force close และเปิดเกม CookieRun ใหม่"
        >
          <RotateCcw className="w-3.5 h-3.5 text-slate-600" />
          <span>🔄 รีสตาร์ทเกม</span>
        </button>

        <button
          onClick={handleTestAdb}
          disabled={loadingAction === 'adb'}
          className="flex items-center justify-center gap-1.5 py-2.5 px-3 rounded-xl border border-slate-200 hover:border-slate-300 bg-slate-50 hover:bg-slate-100 text-slate-700 transition active:scale-95 disabled:opacity-50"
          title="ทดสอบสัญญาณการเชื่อมต่อ ADB"
        >
          <Wifi className="w-3.5 h-3.5 text-emerald-600" />
          <span>🔌 เช็ค ADB</span>
        </button>

        <button
          onClick={handleCaptureScreen}
          className="flex items-center justify-center gap-1.5 py-2.5 px-3 rounded-xl border border-slate-200 hover:border-slate-300 bg-slate-50 hover:bg-slate-100 text-slate-700 transition active:scale-95"
          title="บันทึกภาพหน้าจอปัจจุบันและดาวน์โหลด"
        >
          <Camera className="w-3.5 h-3.5 text-indigo-600" />
          <span>📸 แคปหน้าจอ</span>
        </button>
      </div>

      {/* Settings, Discord, Heart Farmer modal launcher shortcuts */}
      <div className="pt-2 border-t border-purple-50 grid grid-cols-3 gap-2 text-xs">
        <button
          onClick={onOpenSettings}
          className="flex flex-col items-center gap-1 py-2 px-1 rounded-xl hover:bg-slate-50 text-slate-600 transition"
        >
          <Settings className="w-4 h-4 text-brand-600" />
          <span className="text-[11px] font-medium">ตั้งค่าบอท</span>
        </button>

        <button
          onClick={onOpenDiscord}
          className="flex flex-col items-center gap-1 py-2 px-1 rounded-xl hover:bg-slate-50 text-slate-600 transition"
        >
          <Bell className="w-4 h-4 text-indigo-600" />
          <span className="text-[11px] font-medium">Discord</span>
        </button>

        <button
          onClick={onOpenTools}
          className="flex flex-col items-center gap-1 py-2 px-1 rounded-xl hover:bg-slate-50 text-slate-600 transition"
        >
          <Heart className="w-4 h-4 text-pink-600" />
          <span className="text-[11px] font-medium">ปั๊มหัวใจ/เพื่อน</span>
        </button>
      </div>
    </div>
  );
};
