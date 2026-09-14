import React from 'react';
import { ChevronRight, TrendingUp } from 'lucide-react';
import { Device, RoundHistoryItem } from '../../types/bot';

interface RoundHistoryProps {
  history: RoundHistoryItem[];
  onOpenHistoryModal: () => void;
  device?: Device;
}

export const renderBoxBadge = (b: string, index?: number) => {
  const type = String(b || '').trim().toLowerCase();
  if (!type) return null;

  if (type === 'gold' || type.includes('gold') || type.includes('ทอง')) {
    return (
      <span
        key={index}
        title="กล่องทอง"
        className="inline-flex items-center justify-center p-1 rounded-xl border border-[#FFF4BF]/40 bg-[#FFF4BF]/20 shadow-xs shrink-0"
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
        className="inline-flex items-center justify-center p-1 rounded-xl border border-[#DC95FF]/30 bg-[#8C56D4]/20 shadow-xs shrink-0"
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
        className="inline-flex items-center justify-center p-1 rounded-xl border border-[#FFBEFB]/40 bg-gradient-to-r from-[#DC95FF]/20 to-[#FFBEFB]/20 shadow-xs shrink-0"
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
  history = [],
  onOpenHistoryModal,
  device,
}) => {
  const recentRounds = history.slice(0, 5);

  const barRounds = [...history].slice(0, 12).reverse();
  const maxCoins = Math.max(...barRounds.map((r) => r.coins || 0), 1000);

  const firstRoundLabel = barRounds.length > 0 ? `#${barRounds[0].session_round || barRounds[0].round}` : 'รอบ #1';
  const midRoundLabel = barRounds.length > 5 ? `#${barRounds[Math.floor(barRounds.length / 2)].session_round || barRounds[Math.floor(barRounds.length / 2)].round}` : 'รอบกลาง';
  const lastRoundLabel = barRounds.length > 0 ? `#${barRounds[barRounds.length - 1].session_round || barRounds[barRounds.length - 1].round} (ล่าสุด)` : 'ล่าสุด';

  // Real Efficiency Calculation based on actual Device mode & History
  let efficiencyText = '0.0%';
  let efficiencyColor = 'text-[#8C6D58]';
  let changeText = 'เก็บสถิติ ⚡';

  const isHeartFarmer = device?.active_mode === 'heart_farmer' || device?.heart_stats?.running;
  const isCleaner = device?.active_mode === 'friend_cleaner';

  if (isHeartFarmer && device?.heart_stats) {
    const totalRounds = device.heart_stats.rounds || 0;
    const successCount = device.heart_stats.success_count || 0;
    if (totalRounds > 0) {
      const eff = ((successCount / totalRounds) * 100).toFixed(1);
      efficiencyText = `${eff}%`;
      efficiencyColor = Number(eff) >= 80 ? 'text-emerald-600' : 'text-amber-600';
      changeText = `สำเร็จ ${successCount.toLocaleString()} / ${totalRounds.toLocaleString()} รอบ ⚡`;
    } else {
      efficiencyText = '100%';
      efficiencyColor = 'text-emerald-600';
      changeText = 'เริ่มรอบแรก ⚡';
    }
  } else if (isCleaner && device?.cleaner_stats) {
    efficiencyText = device.cleaner_stats.is_busy ? 'กำลังทำงาน' : 'พร้อมทำงาน';
    efficiencyColor = 'text-teal-600';
    changeText = device.cleaner_stats.current_step || 'ลบเพื่อน ⚡';
  } else if (history && history.length > 0) {
    // Normal farming mode: Calculate real success rate & round difference
    const successfulRounds = history.filter((r) => (r.coins || 0) > 0 || (r.boxes && r.boxes.length > 0)).length;
    const eff = ((successfulRounds / history.length) * 100).toFixed(1);
    efficiencyText = `${eff}%`;
    efficiencyColor = Number(eff) >= 80 ? 'text-emerald-600' : 'text-amber-600';

    const latestCoins = history[0]?.coins || 0;
    const prevCoins = history[1]?.coins;

    if (prevCoins !== undefined) {
      if (prevCoins === 0) {
        changeText = latestCoins > 0 ? `+${latestCoins.toLocaleString()} เหรียญ ⚡` : 'คงที่ ⚡';
      } else {
        const diffPct = (((latestCoins - prevCoins) / prevCoins) * 100).toFixed(1);
        const sign = Number(diffPct) >= 0 ? '+' : '';
        changeText = `${sign}${diffPct}% จากรอบก่อน ⚡`;
      }
    } else {
      changeText = `รอบ #${history[0]?.session_round || history[0]?.round || 1} (+${latestCoins.toLocaleString()} เหรียญ) ⚡`;
    }
  } else {
    efficiencyText = '0.0%';
    efficiencyColor = 'text-[#8C6D58]';
    changeText = 'ไม่มีประวัติรอบ ⚡';
  }

  return (
    <div className="biscuit-panel rounded-3xl p-5 shadow-md space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <TrendingUp className="w-4 h-4 text-[#D97706]" />
          <h3 className="font-bold text-sm text-[#3D2012] font-heading">
            ประวัติรอบวิ่ง
          </h3>
        </div>
        <button
          onClick={onOpenHistoryModal}
          className="candy-btn-soft px-2.5 py-1 rounded-xl text-xs font-bold text-[#8A3B04] transition flex items-center space-x-1 cursor-pointer"
        >
          <span>ดูทั้งหมด</span>
          <ChevronRight className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Mini Efficiency Graph Simulation (Bakery Oven / Candy Bars) */}
      <div className="w-full bg-[#FFF8EC] rounded-2xl p-3 border-2 border-[#EEDBCE] flex flex-col justify-between space-y-2 shadow-inner">
        <div className="flex justify-between text-[11px] text-[#8C6D58] font-semibold">
          <span>Efficiency: <strong className={efficiencyColor}>{efficiencyText}</strong></span>
          <span className="text-[#D97706] font-bold">{changeText}</span>
        </div>

        {/* 12 Bars using Candy Kingdom Palette */}
        <div className="w-full h-14 flex items-end space-x-1.5 pt-1">
          {barRounds.length === 0 ? (
            <div className="w-full text-center text-[#A88267] text-xs py-2">
              ไม่มีข้อมูลกราฟ
            </div>
          ) : (
            barRounds.map((r, i) => {
              const heightPct = Math.max(Math.round(((r.coins || 0) / maxCoins) * 100), 20);
              const colorClass =
                i >= 10
                  ? 'bg-gradient-to-t from-[#F59E0B] to-[#FDE047]'
                  : i >= 8
                  ? 'bg-gradient-to-t from-[#EC4899] to-[#F472B6]'
                  : i >= 5
                  ? 'bg-gradient-to-t from-[#8B5CF6] to-[#A78BFA]'
                  : 'bg-gradient-to-t from-[#10B981] to-[#34D399]';

              return (
                <div
                  key={i}
                  style={{ height: `${heightPct}%` }}
                  className={`flex-1 ${colorClass} rounded-t-lg transition-all hover:scale-105 shadow-xs cursor-pointer`}
                  title={`รอบ #${r.session_round || r.round}: +${(r.coins || 0).toLocaleString()} เหรียญ`}
                ></div>
              );
            })
          )}
        </div>

        <div className="flex justify-between text-[10px] text-[#A88267] font-bold pt-1">
          <span>{firstRoundLabel}</span>
          <span>{midRoundLabel}</span>
          <span>{lastRoundLabel}</span>
        </div>
      </div>

      {/* Mini Table List */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="text-[#8A3B04] font-bold border-b-2 border-[#F0DFCE] text-[11px]">
              <th className="py-2 px-2.5">เวลา</th>
              <th className="py-2 px-2.5">รอบ</th>
              <th className="py-2 px-2.5">เหรียญ</th>
              <th className="py-2 px-2.5">EXP</th>
              <th className="py-2 px-2.5 pr-3">กล่อง</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#F0DFCE] font-medium text-[#452311]">
            {recentRounds.length === 0 ? (
              <tr>
                <td colSpan={5} className="py-4 text-center text-[#8C6D58] italic">
                  ยังไม่มีประวัติรอบนี้
                </td>
              </tr>
            ) : (
              recentRounds.map((r, idx) => (
                <tr key={idx} className="hover:bg-[#FFF8EC] transition">
                  <td className="py-2 px-2.5 text-[#8C6D58] font-mono text-[10px]">
                    {r.time || '—'}
                  </td>
                  <td className="py-2 px-2.5 font-extrabold text-[#D97706] font-mono">
                    #{r.session_round || r.round}
                  </td>
                  <td className="py-2 px-2.5 font-mono font-extrabold text-[#B45309]">
                    +{(r.coins || 0).toLocaleString()}
                  </td>
                  <td className="py-2 px-2.5 font-mono font-bold text-[#E11D48]">
                    +{(r.xp || 0).toLocaleString()}
                  </td>
                  <td className="py-2 px-2.5 pr-3">
                    <div className="flex items-center space-x-1 flex-wrap">
                      {Array.isArray(r.boxes) && r.boxes.length > 0 ? (
                        r.boxes.map((b, bIdx) => renderBoxBadge(b, bIdx))
                      ) : (
                        <span className="text-[#A88267]/60 text-[10px]">—</span>
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
