import React from 'react';
import { Smartphone, CheckCircle, Play, Sparkles } from 'lucide-react';
import { Device } from '../../types/bot';

interface DeviceTabsProps {
  devices: Device[];
  selectedSerial: string;
  onSelectDevice: (serial: string) => void;
}

export const DeviceTabs: React.FC<DeviceTabsProps> = ({
  devices,
  selectedSerial,
  onSelectDevice,
}) => {
  if (devices.length === 0) {
    return (
      <div className="glass-panel border border-dashed border-purple-200 rounded-2xl sm:rounded-3xl p-6 text-center text-slate-400 text-xs shadow-glass">
        ไม่พบ Emulator กรุณาเปิดโปรแกรมแล้วกด &quot;สแกน&quot;
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2.5 overflow-x-auto pb-1.5 custom-scrollbar">
      {devices.map((d) => {
        const isSelected = d.serial === selectedSerial;
        const isRunning = d.is_running;

        return (
          <button
            key={d.serial}
            onClick={() => onSelectDevice(d.serial)}
            className={`flex items-center gap-3 px-3.5 sm:px-4 py-2 sm:py-2.5 rounded-2xl text-left transition-all duration-200 shrink-0 cursor-pointer ${
              isSelected
                ? 'bg-white/95 border-2 border-brand-500 shadow-glass ring-2 ring-brand-400/20 scale-101'
                : 'glass-panel hover:bg-white/90 border-purple-100 hover:border-purple-200 text-slate-700 hover:shadow-xs'
            }`}
          >
            <div
              className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 transition-transform ${
                isSelected
                  ? 'bg-gradient-to-tr from-brand-600 to-indigo-600 text-white shadow-xs'
                  : 'bg-brand-50/80 text-brand-700'
              }`}
            >
              <Smartphone className="w-5 h-5" />
            </div>

            <div className="space-y-0.5 pr-1">
              <div className="flex items-center gap-2">
                <span className="font-bold text-xs text-slate-900 font-display">
                  {d.name || d.serial}
                </span>
                {d.active_mode === 'friend_cleaner' ? (
                  <span className="flex items-center gap-1 text-[10px] font-bold text-teal-700 px-1.5 py-0.5 rounded-md bg-teal-50 border border-teal-200">
                    <span className="w-1.5 h-1.5 rounded-full bg-teal-500 animate-pulse"></span>
                    ลบเพื่อน
                  </span>
                ) : d.active_mode === 'heart_farmer' ? (
                  <span className="flex items-center gap-1 text-[10px] font-bold text-pink-600 px-1.5 py-0.5 rounded-md bg-pink-50 border border-pink-200">
                    <span className="w-1.5 h-1.5 rounded-full bg-pink-500 animate-pulse"></span>
                    ปั๊มหัวใจ
                  </span>
                ) : isRunning ? (
                  <span className="flex items-center gap-1 text-[10px] font-bold text-emerald-600 px-1.5 py-0.5 rounded-md bg-emerald-50 border border-emerald-200">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                    กำลังรัน
                  </span>
                ) : (
                  <span className="text-[10px] text-slate-400 font-medium px-1.5 py-0.5 rounded-md bg-slate-100">
                    พร้อม
                  </span>
                )}
              </div>
              <p
                className="text-[11px] text-slate-400 font-mono truncate max-w-[180px]"
                title={
                  d.active_mode === 'friend_cleaner' && d.cleaner_stats?.current_step
                    ? d.cleaner_stats.current_step
                    : d.active_mode === 'heart_farmer' && d.heart_stats
                    ? `ส่งแล้ว ${d.heart_stats.success_count ?? 0} ❤️`
                    : `${d.serial} • รอบที่ ${d.rounds_played ?? 0}`
                }
              >
                {d.active_mode === 'friend_cleaner' && d.cleaner_stats?.current_step
                  ? d.cleaner_stats.current_step
                  : d.active_mode === 'heart_farmer' && d.heart_stats
                  ? `ส่งแล้ว ${d.heart_stats.success_count ?? 0} ❤️`
                  : `${d.serial} • รอบที่ ${d.rounds_played ?? 0}`}
              </p>
            </div>
          </button>
        );
      })}
    </div>
  );
};
