import React from 'react';
import { LineChart, ChevronRight, ScrollText, TrendingUp } from 'lucide-react';
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
        className="inline-flex items-center justify-center p-1 rounded-xl border border-yellow-500/30 bg-yellow-500/20 shadow-xs shrink-0"
      >
        <img
          src="/templates/BOX_GOLD.png"
          alt="กล่องทอง"
          className="w-5 h-5 object-contain drop-shadow"
        />
      </span>
    );
  }
  if (type === 'silver' || type.includes('silver') || type.includes('เงิน')) {
    return (
      <span
        key={index}
        title="กล่องเงิน"
        className="inline-flex items-center justify-center p-1 rounded-xl border border-slate-400/30 bg-slate-500/20 shadow-xs shrink-0"
      >
        <img
          src="/templates/BOX_SILVER.png"
          alt="กล่องเงิน"
          className="w-5 h-5 object-contain drop-shadow"
        />
      </span>
    );
  }
  if (type === 'rainbow' || type.includes('rainbow') || type.includes('รุ้ง')) {
    return (
      <span
        key={index}
        title="กล่องรุ้ง"
        className="inline-flex items-center justify-center p-1 rounded-xl border border-pink-500/30 bg-gradient-to-r from-pink-500/20 to-purple-500/20 shadow-xs shrink-0"
      >
        <img
          src="/templates/BOX_RAINBOW.png"
          alt="กล่องรุ้ง"
          className="w-5 h-5 object-contain drop-shadow"
        />
      </span>
    );
  }
  if (type === 'wood' || type.includes('wood') || type.includes('ไม้')) {
    return (
      <span
        key={index}
        title="กล่องไม้"
        className="inline-flex items-center justify-center p-1 rounded-xl border border-amber-600/30 bg-amber-600/20 shadow-xs shrink-0"
      >
        <img
          src="/templates/BOX_WOOD.png"
          alt="กล่องไม้"
          className="w-5 h-5 object-contain drop-shadow"
        />
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

  // Take up to 12 latest rounds for the efficiency bar graph
  const barRounds = [...history].slice(0, 12).reverse();
  const maxCoins = Math.max(...barRounds.map((r) => r.coins || 0), 1000);

  const firstRoundLabel = barRounds.length > 0 ? `#${barRounds[0].session_round || barRounds[0].round}` : 'รอบ #1';
  const midRoundLabel = barRounds.length > 5 ? `#${barRounds[Math.floor(barRounds.length / 2)].session_round || barRounds[Math.floor(barRounds.length / 2)].round}` : 'รอบกลาง';
  const lastRoundLabel = barRounds.length > 0 ? `#${barRounds[barRounds.length - 1].session_round || barRounds[barRounds.length - 1].round} (ล่าสุด)` : 'ล่าสุด';

  return (
    <div className="glass-panel rounded-3xl p-5 shadow-xl space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <TrendingUp className="w-4 h-4 text-purple-400" />
          <h3 className="font-semibold text-sm text-white font-sans">
            ประวัติรอบล่าสุด & กราฟประสิทธิภาพ (Round History)
          </h3>
        </div>
        <button
          onClick={onOpenHistoryModal}
          className="text-xs text-purple-400 hover:text-purple-300 transition flex items-center space-x-1 cursor-pointer"
        >
          <span>ดูทั้งหมด</span>
          <ChevronRight className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Mini Efficiency Graph Simulation */}
      <div className="w-full bg-purple-950/40 rounded-xl p-3 border border-purple-500/20 flex flex-col justify-between space-y-2">
        <div className="flex justify-between text-[11px] text-purple-300">
          <span>Efficiency: 98.5%</span>
          <span className="text-emerald-400 font-semibold">+4.2% จากรอบก่อน</span>
        </div>

        {/* 12 Bars */}
        <div className="w-full h-12 flex items-end space-x-1.5 pt-1">
          {barRounds.length === 0 ? (
            <div className="w-full text-center text-purple-400 text-xs py-2">
              ยังไม่มีข้อมูลกราฟรอบ
            </div>
          ) : (
            barRounds.map((r, i) => {
              const heightPct = Math.max(Math.round(((r.coins || 0) / maxCoins) * 100), 20);
              const colorClass =
                i >= 10
                  ? 'bg-emerald-400'
                  : i >= 8
                  ? 'bg-emerald-500'
                  : i >= 6
                  ? 'bg-indigo-500'
                  : 'bg-purple-600/70';

              return (
                <div
                  key={i}
                  style={{ height: `${heightPct}%` }}
                  className={`flex-1 ${colorClass} rounded-t transition-all hover:brightness-125`}
                  title={`รอบ #${r.session_round || r.round}: +${(r.coins || 0).toLocaleString()} เหรียญ`}
                ></div>
              );
            })
          )}
        </div>

        <div className="flex justify-between text-[10px] text-purple-400/70 pt-1">
          <span>{firstRoundLabel}</span>
          <span>{midRoundLabel}</span>
          <span>{lastRoundLabel}</span>
        </div>
      </div>

      {/* Mini Table List */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="text-purple-300/60 font-semibold border-b border-purple-500/20 text-[11px]">
              <th className="py-2 px-2.5">เวลา</th>
              <th className="py-2 px-2.5">รอบ</th>
              <th className="py-2 px-2.5">เหรียญ</th>
              <th className="py-2 px-2.5">EXP</th>
              <th className="py-2 px-2.5 pr-3">กล่อง</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-purple-500/10 font-medium text-purple-200">
            {recentRounds.length === 0 ? (
              <tr>
                <td colSpan={5} className="py-4 text-center text-purple-400/60 italic">
                  ยังไม่มีประวัติการเล่นในเซสชันนี้
                </td>
              </tr>
            ) : (
              recentRounds.map((r, idx) => (
                <tr key={idx} className="hover:bg-purple-900/20 transition">
                  <td className="py-2 px-2.5 text-purple-400 font-mono text-[10px]">
                    {r.time || '—'}
                  </td>
                  <td className="py-2 px-2.5 font-bold text-white font-mono">
                    #{r.session_round || r.round}
                  </td>
                  <td className="py-2 px-2.5 font-mono font-bold text-amber-400">
                    +{(r.coins || 0).toLocaleString()}
                  </td>
                  <td className="py-2 px-2.5 font-mono text-purple-300">
                    +{(r.xp || 0).toLocaleString()}
                  </td>
                  <td className="py-2 px-2.5 pr-3">
                    <div className="flex items-center space-x-1 flex-wrap">
                      {Array.isArray(r.boxes) && r.boxes.length > 0 ? (
                        r.boxes.map((b, bIdx) => renderBoxBadge(b, bIdx))
                      ) : (
                        <span className="text-purple-400/50 text-[10px]">—</span>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
