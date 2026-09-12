import React, { useState } from 'react';
import { X, ScrollText, Image as ImageIcon, Trash2 } from 'lucide-react';
import { RoundHistoryItem } from '../../types/bot';
import { renderBoxBadge } from '../dashboard/RoundHistory';
import { botApi } from '../../api/botApi';
import { toast, confirmModal } from '../../context/ToastContext';

interface HistoryModalProps {
  isOpen: boolean;
  onClose: () => void;
  history: RoundHistoryItem[];
  deviceSerial: string;
  onReset?: () => void;
}

export const HistoryModal: React.FC<HistoryModalProps> = ({
  isOpen,
  onClose,
  history,
  deviceSerial,
  onReset,
}) => {
  const [isResetting, setIsResetting] = useState(false);
  const [selectedRound, setSelectedRound] = useState<RoundHistoryItem | null>(
    history.length > 0 ? history[0] : null
  );

  if (!isOpen) return null;

  const handleResetHistory = async () => {
    const ok = await confirmModal({
      title: 'ลบประวัติการเล่น',
      message: `ต้องการลบประวัติการเล่นทั้งหมดของจอ ${deviceSerial || 'ทั้งหมด'} ใช่หรือไม่?`,
      confirmText: 'ลบประวัติ',
      type: 'danger',
    });
    if (!ok) return;

    setIsResetting(true);
    try {
      const res = await botApi.resetStats(deviceSerial);
      toast.success(res.message || 'ลบประวัติเรียบร้อยแล้ว');
      if (onReset) onReset();
      onClose();
    } catch (e: any) {
      toast.error('ลบไม่สำเร็จ: ' + e.message);
    } finally {
      setIsResetting(false);
    }
  };

  const currentRound = selectedRound || (history.length > 0 ? history[0] : null);
  const screenshotUrl = currentRound
    ? `/api/round-screenshot/${currentRound.round}?device=${encodeURIComponent(deviceSerial)}`
    : '';

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl max-w-4xl w-full p-6 space-y-4 shadow-2xl border border-purple-100 max-h-[90vh] overflow-hidden flex flex-col animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-purple-100 shrink-0">
          <div className="flex items-center gap-2">
            <ScrollText className="w-6 h-6 text-brand-600" />
            <div>
              <h3 className="text-base font-bold text-slate-900">
                ประวัติการเล่นย้อนหลัง 50 รอบ
              </h3>
              <p className="text-xs text-slate-500">
                คลิกที่แต่ละรอบเพื่อดูภาพสกรีนช็อตสรุปผล • {deviceSerial}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {history.length > 0 && (
              <button
                onClick={handleResetHistory}
                disabled={isResetting}
                className="flex items-center gap-1 px-3 py-1.5 rounded-xl bg-rose-50 hover:bg-rose-100 text-rose-600 font-bold text-xs border border-rose-200 transition active:scale-95 cursor-pointer disabled:opacity-50"
                title="ลบประวัติการเล่นทั้งหมดของจอนี้"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>{isResetting ? 'กำลังลบ...' : 'ลบประวัติ'}</span>
              </button>
            )}
            <button
              onClick={onClose}
              className="w-8 h-8 rounded-full bg-slate-100 hover:bg-slate-200 flex items-center justify-center text-slate-600 font-bold transition cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-4 overflow-hidden grow">
          {/* History List (7 cols) */}
          <div className="md:col-span-7 space-y-2 overflow-y-auto custom-scrollbar pr-2 max-h-[460px]">
            {history.length === 0 ? (
              <div className="p-8 text-center text-slate-400 italic">
                ยังไม่มีประวัติการเล่นที่บันทึกไว้
              </div>
            ) : (
              history.map((r, i) => {
                const isSelected = currentRound?.round === r.round;
                const hasBoxes = Array.isArray(r.boxes) && r.boxes.length > 0;

                return (
                  <div
                    key={r.round !== undefined && r.round !== null ? r.round : i}
                    onClick={() => setSelectedRound(r)}
                    className={`p-3 rounded-2xl border cursor-pointer transition flex items-center justify-between group ${
                      isSelected
                        ? 'bg-purple-50/70 border-brand-500 shadow-xs ring-1 ring-brand-400/30'
                        : 'border-purple-100 hover:border-brand-300 hover:bg-purple-50/40'
                    }`}
                  >
                    <div className="space-y-0.5">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-brand-700">
                          รอบที่ {r.round !== undefined && r.round !== null ? r.round : history.length - i}
                        </span>
                        <span className="text-[11px] text-slate-400 font-mono">
                          {r.time || '-'}
                        </span>
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-mono">
                          {r.duration || '-'}
                        </span>
                      </div>
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-amber-600 font-semibold font-mono">
                          🪙 +{(r.coins || 0).toLocaleString()}
                        </span>
                        <span className="text-indigo-600 font-semibold font-mono">
                          ⭐ +{(r.xp || 0).toLocaleString()} EXP
                        </span>
                        {r.score ? (
                          <span className="text-slate-500 font-mono">
                            คะแนน {(r.score).toLocaleString()}
                          </span>
                        ) : null}
                      </div>
                    </div>

                    <div className="text-right">
                      {hasBoxes ? (
                        <div className="flex flex-wrap items-center justify-end gap-1">
                          {r.boxes.map((b, bIdx) => renderBoxBadge(b, bIdx))}
                        </div>
                      ) : (
                        <span className="text-slate-400 text-[11px]">-</span>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* Screenshot Preview (5 cols) */}
          <div className="md:col-span-5 space-y-2 flex flex-col justify-center">
            <h4 className="text-xs font-bold text-slate-700">
              ภาพสกรีนช็อตจบเกม (Game Screenshot)
            </h4>
            <div className="bg-slate-950 rounded-2xl aspect-video overflow-hidden border border-purple-100 flex items-center justify-center shadow-inner">
              {screenshotUrl ? (
                <img
                  src={screenshotUrl}
                  alt="Round Screenshot"
                  className="w-full h-full object-contain"
                />
              ) : (
                <div className="text-slate-500 text-xs flex flex-col items-center gap-1">
                  <ImageIcon className="w-8 h-8 text-slate-600" />
                  <span>ไม่มีภาพสกรีนช็อต</span>
                </div>
              )}
            </div>
            {currentRound && (
              <p className="text-xs text-slate-500 text-center font-mono italic">
                รอบที่ {currentRound.round} ({currentRound.time || '-'}) • เหรียญ +
                {(currentRound.coins || 0).toLocaleString()} 🪙
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
