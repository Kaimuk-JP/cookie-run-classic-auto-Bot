import React from 'react';
import { ScrollText, ChevronRight, Coins, Star } from 'lucide-react';
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
        title="กล่องทอง"
        className="inline-flex items-center justify-center p-1 rounded-xl border border-yellow-200 bg-yellow-50 shadow-xs hover:scale-110 transition shrink-0"
      >
        <img src="/templates/BOX_GOLD.png" alt="กล่องทอง" className="w-5 h-5 sm:w-6 sm:h-6 object-contain drop-shadow-xs" />
      </span>
    );
  }
  if (type === 'silver' || type.includes('silver') || type.includes('เงิน')) {
    return (
      <span
        key={index}
        title="กล่องเงิน"
        className="inline-flex items-center justify-center p-1 rounded-xl border border-slate-200 bg-slate-100 shadow-xs hover:scale-110 transition shrink-0"
      >
        <img src="/templates/BOX_SILVER.png" alt="กล่องเงิน" className="w-5 h-5 sm:w-6 sm:h-6 object-contain drop-shadow-xs" />
      </span>
    );
  }
  if (type === 'rainbow' || type.includes('rainbow') || type.includes('รุ้ง')) {
    return (
      <span
        key={index}
        title="กล่องรุ้ง"
        className="inline-flex items-center justify-center p-1 rounded-xl border border-pink-200 bg-gradient-to-r from-pink-50 to-purple-50 shadow-xs hover:scale-110 transition shrink-0"
      >
        <img src="/templates/BOX_RAINBOW.png" alt="กล่องรุ้ง" className="w-5 h-5 sm:w-6 sm:h-6 object-contain drop-shadow-xs" />
      </span>
    );
  }
  if (type === 'wood' || type.includes('wood') || type.includes('ไม้')) {
    return (
      <span
        key={index}
        title="กล่องไม้"
        className="inline-flex items-center justify-center p-1 rounded-xl border border-amber-200 bg-amber-50 shadow-xs hover:scale-110 transition shrink-0"
      >
        <img src="/templates/BOX_WOOD.png" alt="กล่องไม้" className="w-5 h-5 sm:w-6 sm:h-6 object-contain drop-shadow-xs" />
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
              <th className="py-2.5 px-3 pr-4">กล่องปริศนา</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-purple-50 font-medium text-slate-700">
            {recentRounds.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-8 text-center text-slate-400 italic">
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
                      <span className="inline-flex items-center gap-1">
                        <Coins className="w-3.5 h-3.5 text-amber-500 shrink-0" />
                        <span>{(r.coins || 0).toLocaleString()}</span>
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-indigo-600 font-semibold font-mono">
                      <span className="inline-flex items-center gap-1">
                        <Star className="w-3.5 h-3.5 text-amber-400 fill-amber-400 shrink-0" />
                        <span>{(r.xp || 0).toLocaleString()}</span>
                      </span>
                    </td>
                    <td className="py-2.5 px-3 pr-4">
                      {hasBoxes ? (
                        <div className="flex flex-wrap items-center gap-1.5">
                          {r.boxes.map((b, bIdx) => renderBoxBadge(b, bIdx))}
                        </div>
                      ) : (
                        <span className="text-slate-400 font-normal">-</span>
                      )}
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
