import React from 'react';
import { ScrollText, ChevronRight, Check } from 'lucide-react';
import { RoundHistoryItem } from '../../types/bot';

interface RoundHistoryProps {
  history: RoundHistoryItem[];
  onOpenHistoryModal: () => void;
}

export const renderBoxBadge = (b: string, index?: number) => {
  const type = String(b || '').trim().toLowerCase();
  if (!type) return null;

  if (type === 'gold' || type.includes('gold') || type.includes('ทอง')) {
    return (
      <span
        key={index}
        className="inline-flex items-center gap-1 px-2 py-0.5 rounded-xl border border-yellow-200 bg-yellow-50 text-yellow-900 text-[11px] font-bold shadow-xs"
      >
        <img src="/templates/BOX_GOLD.png" alt="กล่องทอง" className="w-5 h-5 object-contain inline-block drop-shadow-xs" />
        <span>กล่องทอง</span>
      </span>
    );
  }
  if (type === 'silver' || type.includes('silver') || type.includes('เงิน')) {
    return (
      <span
        key={index}
        className="inline-flex items-center gap-1 px-2 py-0.5 rounded-xl border border-slate-200 bg-slate-100 text-slate-800 text-[11px] font-bold shadow-xs"
      >
        <img src="/templates/BOX_SILVER.png" alt="กล่องเงิน" className="w-5 h-5 object-contain inline-block drop-shadow-xs" />
        <span>กล่องเงิน</span>
      </span>
    );
  }
  if (type === 'rainbow' || type.includes('rainbow') || type.includes('รุ้ง')) {
    return (
      <span
        key={index}
        className="inline-flex items-center gap-1 px-2 py-0.5 rounded-xl border border-pink-200 bg-gradient-to-r from-pink-50 to-purple-50 text-purple-900 text-[11px] font-bold shadow-xs"
      >
        <img src="/templates/BOX_RAINBOW.png" alt="กล่องรุ้ง" className="w-5 h-5 object-contain inline-block drop-shadow-xs" />
        <span>กล่องรุ้ง</span>
      </span>
    );
  }
  if (type === 'wood' || type.includes('wood') || type.includes('ไม้')) {
    return (
      <span
        key={index}
        className="inline-flex items-center gap-1 px-2 py-0.5 rounded-xl border border-amber-200 bg-amber-50 text-amber-900 text-[11px] font-bold shadow-xs"
      >
        <img src="/templates/BOX_WOOD.png" alt="กล่องไม้" className="w-5 h-5 object-contain inline-block drop-shadow-xs" />
        <span>กล่องไม้</span>
      </span>
    );
  }
  return null;
};

export const RoundHistory: React.FC<RoundHistoryProps> = ({
  history,
  onOpenHistoryModal,
}) => {
  const recentRounds = history.slice(0, 5);

  return (
    <section className="bg-white border border-purple-100 rounded-3xl p-5 shadow-card space-y-3">
      <div className="flex items-center justify-between pb-2 border-b border-purple-50">
        <div className="flex items-center gap-2">
          <ScrollText className="w-5 h-5 text-brand-600" />
          <h3 className="text-sm font-bold text-slate-900">
            ประวัติล่าสุด (Round History)
          </h3>
        </div>
        <button
          onClick={onOpenHistoryModal}
          className="text-xs font-bold text-brand-600 hover:text-brand-700 flex items-center gap-0.5 cursor-pointer"
        >
          <span>ดูทั้งหมด</span>
          <ChevronRight className="w-3.5 h-3.5" />
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="text-slate-400 font-semibold border-b border-purple-50">
              <th className="py-2.5 px-3">ลำดับ</th>
              <th className="py-2.5 px-3">เวลา</th>
              <th className="py-2.5 px-3">รอบที่</th>
              <th className="py-2.5 px-3">เหรียญ</th>
              <th className="py-2.5 px-3">EXP</th>
              <th className="py-2.5 px-3">กล่องปริศนา</th>
              <th className="py-2.5 px-3">ผลลัพธ์</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-purple-50 font-medium text-slate-700">
            {recentRounds.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-8 text-center text-slate-400 italic">
                  ยังไม่มีประวัติการเล่นในเซสชันนี้
                </td>
              </tr>
            ) : (
              recentRounds.map((r, i) => {
                const hasBoxes = Array.isArray(r.boxes) && r.boxes.length > 0;
                return (
                  <tr key={r.round !== undefined && r.round !== null ? r.round : i} className="hover:bg-purple-50/40 transition">
                    <td className="py-2.5 px-3 text-slate-400 font-mono">{i + 1}</td>
                    <td className="py-2.5 px-3 text-slate-500 font-mono">{r.time || '-'}</td>
                    <td className="py-2.5 px-3 font-bold text-brand-700">
                      รอบที่ {r.round !== undefined && r.round !== null ? r.round : '-'}
                    </td>
                    <td className="py-2.5 px-3 text-amber-600 font-semibold font-mono">
                      🪙 {(r.coins || 0).toLocaleString()}
                    </td>
                    <td className="py-2.5 px-3 text-indigo-600 font-semibold font-mono">
                      ⭐ {(r.xp || 0).toLocaleString()}
                    </td>
                    <td className="py-2.5 px-3">
                      {hasBoxes ? (
                        <div className="flex flex-wrap items-center gap-1.5">
                          {r.boxes.map((b, bIdx) => renderBoxBadge(b, bIdx))}
                        </div>
                      ) : (
                        <span className="text-slate-400 font-normal">-</span>
                      )}
                    </td>
                    <td className="py-2.5 px-3">
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-700">
                        <Check className="w-2.5 h-2.5" />
                        <span>สำเร็จ</span>
                      </span>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
};
