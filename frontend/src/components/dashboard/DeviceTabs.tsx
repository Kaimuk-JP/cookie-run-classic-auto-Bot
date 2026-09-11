import React from 'react';
import { Smartphone, CheckCircle, Play } from 'lucide-react';
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
      <div className="bg-white border border-dashed border-purple-200 rounded-3xl p-6 text-center text-slate-400 text-xs">
        ไม่พบ Emulator ที่เปิดอยู่ กรุณาเปิดจำลองหน้าจอ (เช่น LDPlayer) แล้วกดปุ่ม &quot;สแกนจอ&quot;
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3 overflow-x-auto pb-1 custom-scrollbar">
      {devices.map((d) => {
        const isSelected = d.serial === selectedSerial;
        const isRunning = d.is_running;

        return (
          <button
            key={d.serial}
            onClick={() => onSelectDevice(d.serial)}
            className={`flex items-center gap-3 px-4 py-2.5 rounded-2xl border text-left transition shrink-0 cursor-pointer ${
              isSelected
                ? 'bg-gradient-to-r from-brand-50 to-purple-50/70 border-brand-500 shadow-sm ring-2 ring-brand-400/20'
                : 'bg-white border-purple-100 hover:border-purple-200 text-slate-700'
            }`}
          >
            <div
              className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${
                isSelected ? 'bg-brand-600 text-white shadow-xs' : 'bg-slate-100 text-slate-600'
              }`}
            >
              <Smartphone className="w-5 h-5" />
            </div>

            <div className="space-y-0.5 pr-2">
              <div className="flex items-center gap-2">
                <span className="font-bold text-xs text-slate-900">{d.name || d.serial}</span>
                {isRunning ? (
                  <span className="flex items-center gap-1 text-[10px] font-bold text-emerald-600 px-1.5 py-0.5 rounded-md bg-emerald-50 border border-emerald-200">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                    กำลังทำงาน
                  </span>
                ) : (
                  <span className="text-[10px] text-slate-400 font-medium px-1.5 py-0.5 rounded-md bg-slate-100">
                    หยุดพัก
                  </span>
                )}
              </div>
              <p className="text-[11px] text-slate-400 font-mono">
                {d.serial} • รอบที่ {d.rounds_played ?? 0}
              </p>
            </div>
          </button>
        );
      })}
    </div>
  );
};
