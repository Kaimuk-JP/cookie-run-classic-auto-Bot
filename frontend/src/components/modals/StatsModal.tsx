import React, { useState } from 'react';
import { X, BarChart3, Coins, Sparkles, Trash2 } from 'lucide-react';
import { Device } from '../../types/bot';
import { botApi } from '../../api/botApi';

interface StatsModalProps {
  isOpen: boolean;
  onClose: () => void;
  device?: Device;
  onReset?: () => void;
}

export const StatsModal: React.FC<StatsModalProps> = ({ isOpen, onClose, device, onReset }) => {
  const [isResetting, setIsResetting] = useState(false);

  if (!isOpen) return null;

  const handleResetStats = async () => {
    if (!confirm(`คุณแน่ใจหรือไม่ว่าต้องการลบสถิติสะสม (เหรียญ, EXP, กล่องปริศนา) ทั้งหมดของจอ ${device?.serial || 'ทั้งหมด'}?`)) {
      return;
    }

    setIsResetting(true);
    try {
      const res = await botApi.resetStats(device?.serial);
      alert(res.message || 'ลบสถิติทั้งหมดเรียบร้อยแล้ว');
      if (onReset) onReset();
      onClose();
    } catch (e: any) {
      alert('ลบสถิติไม่สำเร็จ: ' + e.message);
    } finally {
      setIsResetting(false);
    }
  };

  const boxes = device?.box_counts || { wood: 0, silver: 0, gold: 0, rainbow: 0, total: 0 };
  const coins = device?.coin_stats?.session_earned ?? 0;
  const xp = device?.coin_stats?.session_xp_earned ?? 0;

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl max-w-xl w-full p-6 space-y-4 shadow-2xl border border-purple-100 animate-in fade-in zoom-in-95 duration-150">
        {/* Modal Header */}
        <div className="flex items-center justify-between pb-3 border-b border-purple-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center text-xl shadow-xs border border-amber-100">
              <BarChart3 className="w-5 h-5 text-amber-600" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">
                สถิติสะสม (Accumulated Stats)
              </h3>
              <p className="text-xs text-slate-500">
                ยอดเหรียญ EXP และกล่องปริศนาแยกเกรด • {device?.name || device?.serial || '-'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-slate-100 hover:bg-slate-200 flex items-center justify-center text-slate-600 font-bold transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* 4-Tier Mystery Box Cards with Real Images */}
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

        {/* Total Coins & EXP Accumulator */}
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-between shadow-xs">
            <div>
              <span className="text-slate-500 font-medium">เหรียญสะสมทั้งหมด</span>
              <div className="text-xl font-bold font-mono text-amber-600 mt-0.5">
                +{coins.toLocaleString()} 🪙
              </div>
            </div>
            <Coins className="w-8 h-8 text-amber-500" />
          </div>

          <div className="p-4 rounded-2xl bg-sky-500/10 border border-sky-500/20 flex items-center justify-between shadow-xs">
            <div>
              <span className="text-slate-500 font-medium">EXP สะสมทั้งหมด</span>
              <div className="text-xl font-bold font-mono text-sky-600 mt-0.5">
                +{xp.toLocaleString()} EXP
              </div>
            </div>
            <Sparkles className="w-8 h-8 text-sky-500" />
          </div>
        </div>

        {/* Footer */}
        <div className="pt-2 flex items-center justify-between border-t border-purple-50">
          <button
            onClick={handleResetStats}
            disabled={isResetting}
            className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-rose-50 hover:bg-rose-100 text-rose-600 font-bold text-xs border border-rose-200 transition active:scale-95 disabled:opacity-50 cursor-pointer"
            title="ลบสถิติสะสมและรีเซ็ตค่าทั้งหมดให้เป็น 0"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>{isResetting ? 'กำลังล้าง...' : 'ลบสถิติทั้งหมด'}</span>
          </button>

          <button
            onClick={onClose}
            className="px-5 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs transition active:scale-95 cursor-pointer"
          >
            ปิดหน้าต่าง
          </button>
        </div>
      </div>
    </div>
  );
};
