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
    <div className="biscuit-panel rounded-3xl p-5 shadow-md space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="font-bold text-sm text-[#3D2012] font-heading flex items-center space-x-2">
          <Sliders className="w-4 h-4 text-[#D97706]" />
          <span>แผงควบคุม</span>
        </h3>
        <span className="text-[11px] text-[#8A3B04] font-mono bg-[#FFF8EC] px-2.5 py-0.5 rounded-xl border border-[#EEDBCE] truncate max-w-[140px] font-bold shadow-xs">
          {deviceSerial || '127.0.0.1:5555'}
        </span>
      </div>

      {/* Main Start / Stop Buttons Grid (3D Candy Tactile Buttons) */}
      <div className="grid grid-cols-2 gap-3">
        <button
          onClick={onStart}
          className={`candy-btn-honey py-3 px-4 rounded-2xl text-xs font-bold transition flex items-center justify-center space-x-2 cursor-pointer ${
            isRunning ? 'ring-4 ring-[#FDE68A]' : ''
          }`}
        >
          <Play className="w-4 h-4 fill-current text-white" />
          <span>เริ่มบอท</span>
        </button>

        <button
          onClick={onStop}
          className="candy-btn-strawberry py-3 px-4 rounded-2xl text-xs font-bold transition flex items-center justify-center space-x-2 cursor-pointer"
        >
          <Square className="w-4 h-4 fill-current text-white" />
          <span>หยุดบอท</span>
        </button>
      </div>

      {/* Utility Buttons Grid (4 columns in Biscuit Cards) */}
      <div className="grid grid-cols-4 gap-2.5">
        <button
          onClick={handleClearRam}
          disabled={loadingAction === 'ram'}
          className="biscuit-card p-2.5 rounded-2xl flex flex-col items-center justify-center text-[#452311] hover:border-[#F59E0B] hover:bg-[#FFFDF0] transition disabled:opacity-50 cursor-pointer shadow-xs"
          title="ล้าง RAM"
        >
          <div className="w-8 h-8 rounded-xl bg-[#FEF3C7] text-[#D97706] flex items-center justify-center mb-1">
            <Zap className="w-4 h-4 fill-current" />
          </div>
          <span className="text-[10px] font-bold text-[#8A3B04]">ล้าง RAM</span>
        </button>

        <button
          onClick={handleResetApp}
          disabled={loadingAction === 'reset'}
          className="biscuit-card p-2.5 rounded-2xl flex flex-col items-center justify-center text-[#452311] hover:border-[#8B5CF6] hover:bg-[#FAF5FF] transition disabled:opacity-50 cursor-pointer shadow-xs"
          title="รีสตาร์ทเกม"
        >
          <div className="w-8 h-8 rounded-xl bg-[#EDE9FE] text-[#7C3AED] flex items-center justify-center mb-1">
            <RotateCcw className="w-4 h-4" />
          </div>
          <span className="text-[10px] font-bold text-[#6D28D9]">รีเกม</span>
        </button>

        <button
          onClick={handleTestAdb}
          disabled={loadingAction === 'adb'}
          className="biscuit-card p-2.5 rounded-2xl flex flex-col items-center justify-center text-[#452311] hover:border-[#10B981] hover:bg-[#F0FDF4] transition disabled:opacity-50 cursor-pointer shadow-xs"
          title="เช็คการเชื่อมต่อ ADB"
        >
          <div className="w-8 h-8 rounded-xl bg-[#D1FAE5] text-[#059669] flex items-center justify-center mb-1">
            <Plug className="w-4 h-4" />
          </div>
          <span className="text-[10px] font-bold text-[#047857]">เช็ค ADB</span>
        </button>

        <button
          onClick={handleCaptureScreen}
          className="biscuit-card p-2.5 rounded-2xl flex flex-col items-center justify-center text-[#452311] hover:border-[#0EA5E9] hover:bg-[#F0F9FF] transition cursor-pointer shadow-xs"
          title="แคปภาพหน้าจอ"
        >
          <div className="w-8 h-8 rounded-xl bg-[#E0F2FE] text-[#0284C7] flex items-center justify-center mb-1">
            <Camera className="w-4 h-4" />
          </div>
          <span className="text-[10px] font-bold text-[#0369A1]">แคปจอ</span>
        </button>
      </div>
    </div>
  );
};
