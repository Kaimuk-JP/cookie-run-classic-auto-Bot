import React, { useState } from 'react';
import { TrendingUp, Coins, Zap, Clock, Package, BarChart2 } from 'lucide-react';
import { RoundHistoryItem } from '../../types/bot';

interface FarmingChartProps {
  history: RoundHistoryItem[];
  coinsPerHour?: number;
}

type ChartMode = 'coins' | 'rate' | 'boxes';

export const FarmingChart: React.FC<FarmingChartProps> = ({
  history,
  coinsPerHour = 0,
}) => {
  const [mode, setMode] = useState<ChartMode>('coins');
  const [hoveredRound, setHoveredRound] = useState<RoundHistoryItem | null>(null);

  // Use up to 25 latest rounds, ordered chronologically (oldest to newest for graph left-to-right)
  const chartData = [...history].slice(0, 25).reverse();

  // Metrics calculations
  const totalRounds = history.length;
  const avgCoins =
    totalRounds > 0
      ? Math.round(history.reduce((sum, r) => sum + (r.coins || 0), 0) / totalRounds)
      : 0;

  const totalBoxes = history.reduce((sum, r) => sum + (r.box_count || 0), 0);
  const avgBoxesPerRound = totalRounds > 0 ? (totalBoxes / totalRounds).toFixed(2) : '0';

  // Calculate average duration in seconds
  let totalDurSec = 0;
  history.forEach((r) => {
    const dur = String(r.duration || '');
    const m = dur.match(/(\d+)m/);
    const s = dur.match(/(\d+)s/);
    const sec = (m ? parseInt(m[1], 10) * 60 : 0) + (s ? parseInt(s[1], 10) : 0);
    totalDurSec += sec;
  });
  const avgDurSec = totalRounds > 0 ? Math.round(totalDurSec / totalRounds) : 0;
  const avgDurStr =
    avgDurSec >= 60
      ? `${Math.floor(avgDurSec / 60)}m ${avgDurSec % 60}s`
      : `${avgDurSec}s`;

  // Chart scaling
  const maxCoins = Math.max(...chartData.map((d) => d.coins || 0), 1000);
  const maxBoxes = Math.max(...chartData.map((d) => d.box_count || 0), 2);

  // SVG dimensions
  const svgWidth = 600;
  const svgHeight = 180;
  const paddingX = 35;
  const paddingBottom = 30;
  const paddingTop = 20;
  const chartAreaWidth = svgWidth - paddingX * 2;
  const chartAreaHeight = svgHeight - paddingTop - paddingBottom;

  return (
    <div className="space-y-4">
      {/* 4 Summary Stat Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-xs">
        <div className="p-2.5 rounded-2xl bg-amber-500/10 border border-amber-500/20 shadow-xs space-y-0.5">
          <div className="flex items-center gap-1.5 text-amber-800 font-semibold text-[11px]">
            <Zap className="w-3.5 h-3.5 text-amber-600" />
            <span>ความเร็วฟาร์ม</span>
          </div>
          <div className="text-base font-bold font-mono text-amber-700">
            {coinsPerHour.toLocaleString()} <span className="text-[10px] font-medium text-amber-600">🪙/ชม.</span>
          </div>
        </div>

        <div className="p-2.5 rounded-2xl bg-brand-50 border border-brand-200 shadow-xs space-y-0.5">
          <div className="flex items-center gap-1.5 text-brand-800 font-semibold text-[11px]">
            <Coins className="w-3.5 h-3.5 text-brand-600" />
            <span>เหรียญเฉลี่ย / รอบ</span>
          </div>
          <div className="text-base font-bold font-mono text-brand-700">
            {avgCoins.toLocaleString()} <span className="text-[10px] font-medium text-brand-600">🪙</span>
          </div>
        </div>

        <div className="p-2.5 rounded-2xl bg-sky-50 border border-sky-200 shadow-xs space-y-0.5">
          <div className="flex items-center gap-1.5 text-sky-800 font-semibold text-[11px]">
            <Clock className="w-3.5 h-3.5 text-sky-600" />
            <span>เวลาเฉลี่ย / รอบ</span>
          </div>
          <div className="text-base font-bold font-mono text-sky-700">
            {avgDurStr}
          </div>
        </div>

        <div className="p-2.5 rounded-2xl bg-emerald-50 border border-emerald-200 shadow-xs space-y-0.5">
          <div className="flex items-center gap-1.5 text-emerald-800 font-semibold text-[11px]">
            <Package className="w-3.5 h-3.5 text-emerald-600" />
            <span>ดรอปกล่อง / รอบ</span>
          </div>
          <div className="text-base font-bold font-mono text-emerald-700">
            {avgBoxesPerRound} <span className="text-[10px] font-medium text-emerald-600">กล่อง</span>
          </div>
        </div>
      </div>

      {/* Chart Header & Mode Tabs */}
      <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-purple-50">
        <div className="flex items-center gap-1.5">
          <BarChart2 className="w-4 h-4 text-brand-600" />
          <h4 className="text-xs font-bold text-slate-800">
            กราฟวิเคราะห์ย้อนหลัง {chartData.length} รอบล่าสุด
          </h4>
        </div>

        <div className="flex items-center gap-1 p-0.5 bg-slate-100 rounded-xl text-[11px] font-semibold">
          <button
            onClick={() => setMode('coins')}
            className={`px-2.5 py-1 rounded-lg transition cursor-pointer ${
              mode === 'coins'
                ? 'bg-white text-brand-700 shadow-xs font-bold'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            เหรียญต่อรอบ
          </button>
          <button
            onClick={() => setMode('rate')}
            className={`px-2.5 py-1 rounded-lg transition cursor-pointer ${
              mode === 'rate'
                ? 'bg-white text-brand-700 shadow-xs font-bold'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            อัตราความเร็ว
          </button>
          <button
            onClick={() => setMode('boxes')}
            className={`px-2.5 py-1 rounded-lg transition cursor-pointer ${
              mode === 'boxes'
                ? 'bg-white text-brand-700 shadow-xs font-bold'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            กล่องปริศนา
          </button>
        </div>
      </div>

      {/* Interactive SVG Chart Container */}
      <div className="relative bg-slate-50/70 rounded-2xl border border-purple-100 p-3 overflow-hidden shadow-inner">
        {chartData.length === 0 ? (
          <div className="h-44 flex flex-col items-center justify-center text-slate-400 text-xs space-y-1">
            <TrendingUp className="w-8 h-8 text-slate-300 stroke-[1.5]" />
            <span>ยังไม่มีข้อมูลการเล่นในเซสชันนี้</span>
          </div>
        ) : (
          <div className="relative w-full">
            <svg
              viewBox={`0 0 ${svgWidth} ${svgHeight}`}
              className="w-full h-auto overflow-visible select-none"
            >
              {/* Horizontal Grid lines */}
              {[0, 0.33, 0.66, 1].map((ratio, idx) => {
                const y = paddingTop + chartAreaHeight * (1 - ratio);
                const val =
                  mode === 'boxes'
                    ? Math.round(maxBoxes * ratio)
                    : Math.round(maxCoins * ratio);
                return (
                  <g key={idx}>
                    <line
                      x1={paddingX}
                      y1={y}
                      x2={svgWidth - paddingX}
                      y2={y}
                      stroke="#E2E8F0"
                      strokeDasharray={ratio > 0 && ratio < 1 ? '3 3' : undefined}
                      strokeWidth="1"
                    />
                    <text
                      x={paddingX - 6}
                      y={y + 3}
                      textAnchor="end"
                      fontSize="9"
                      fill="#94A3B8"
                      fontFamily="monospace"
                    >
                      {val >= 1000 ? `${Math.round(val / 1000)}k` : val}
                    </text>
                  </g>
                );
              })}

              {/* Mode: Coins Bar Chart */}
              {mode === 'coins' && (
                <>
                  {/* Average Line */}
                  {avgCoins > 0 && (
                    <line
                      x1={paddingX}
                      y1={paddingTop + chartAreaHeight * (1 - Math.min(1, avgCoins / maxCoins))}
                      x2={svgWidth - paddingX}
                      y2={paddingTop + chartAreaHeight * (1 - Math.min(1, avgCoins / maxCoins))}
                      stroke="#D97706"
                      strokeDasharray="4 4"
                      strokeWidth="1.5"
                    />
                  )}

                  {chartData.map((d, i) => {
                    const barWidth = Math.max(6, Math.min(22, (chartAreaWidth / chartData.length) * 0.65));
                    const step = chartAreaWidth / chartData.length;
                    const x = paddingX + i * step + (step - barWidth) / 2;
                    const barHeight = Math.max(4, (d.coins / maxCoins) * chartAreaHeight);
                    const y = paddingTop + chartAreaHeight - barHeight;
                    const isHovered = hoveredRound?.round === d.round;

                    return (
                      <g
                        key={d.round || i}
                        onMouseEnter={() => setHoveredRound(d)}
                        onMouseLeave={() => setHoveredRound(null)}
                        className="cursor-pointer transition"
                      >
                        <rect
                          x={x}
                          y={y}
                          width={barWidth}
                          height={barHeight}
                          rx={Math.min(4, barWidth / 2)}
                          fill={isHovered ? '#F59E0B' : '#FBBF24'}
                          className="transition-all duration-150"
                        />
                        {/* Round number label */}
                        <text
                          x={x + barWidth / 2}
                          y={svgHeight - 10}
                          textAnchor="middle"
                          fontSize="8"
                          fill={isHovered ? '#D97706' : '#94A3B8'}
                          fontWeight={isHovered ? 'bold' : 'normal'}
                          fontFamily="monospace"
                        >
                          #{d.round ?? i + 1}
                        </text>
                      </g>
                    );
                  })}
                </>
              )}

              {/* Mode: Farming Rate Trend Line */}
              {mode === 'rate' && (
                <>
                  {(() => {
                    const step = chartAreaWidth / (chartData.length - 1 || 1);
                    const points = chartData.map((d, i) => {
                      const x = paddingX + i * step;
                      const y = paddingTop + chartAreaHeight * (1 - (d.coins / maxCoins));
                      return { x, y, d };
                    });

                    const pathStr = points.reduce((acc, p, idx) => {
                      return idx === 0 ? `M ${p.x} ${p.y}` : `${acc} L ${p.x} ${p.y}`;
                    }, '');

                    const areaStr = `${pathStr} L ${points[points.length - 1].x} ${
                      paddingTop + chartAreaHeight
                    } L ${points[0].x} ${paddingTop + chartAreaHeight} Z`;

                    return (
                      <g>
                        {/* Gradient Area Fill */}
                        <defs>
                          <linearGradient id="rateGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#8B5CF6" stopOpacity="0.4" />
                            <stop offset="100%" stopColor="#8B5CF6" stopOpacity="0.0" />
                          </linearGradient>
                        </defs>
                        <path d={areaStr} fill="url(#rateGradient)" />
                        {/* Line Stroke */}
                        <path
                          d={pathStr}
                          fill="none"
                          stroke="#7C3AED"
                          strokeWidth="2.5"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                        {/* Point Circles */}
                        {points.map((p, idx) => (
                          <circle
                            key={idx}
                            cx={p.x}
                            cy={p.y}
                            r={hoveredRound?.round === p.d.round ? 5 : 3.5}
                            fill="#FFFFFF"
                            stroke="#7C3AED"
                            strokeWidth="2"
                            onMouseEnter={() => setHoveredRound(p.d)}
                            onMouseLeave={() => setHoveredRound(null)}
                            className="cursor-pointer transition-all"
                          />
                        ))}
                      </g>
                    );
                  })()}
                </>
              )}

              {/* Mode: Mystery Boxes Breakdown */}
              {mode === 'boxes' && (
                <>
                  {chartData.map((d, i) => {
                    const barWidth = Math.max(6, Math.min(22, (chartAreaWidth / chartData.length) * 0.65));
                    const step = chartAreaWidth / chartData.length;
                    const x = paddingX + i * step + (step - barWidth) / 2;
                    const barHeight = Math.max(4, ((d.box_count || 0) / maxBoxes) * chartAreaHeight);
                    const y = paddingTop + chartAreaHeight - barHeight;
                    const isHovered = hoveredRound?.round === d.round;

                    // Box grade color determination
                    const boxesList = Array.isArray(d.boxes) ? d.boxes : [];
                    let barColor = '#D97706'; // default wood amber
                    if (boxesList.some((b) => String(b).toLowerCase().includes('rainbow'))) {
                      barColor = '#EC4899'; // pink/rainbow
                    } else if (boxesList.some((b) => String(b).toLowerCase().includes('gold'))) {
                      barColor = '#EAB308'; // gold
                    } else if (boxesList.some((b) => String(b).toLowerCase().includes('silver'))) {
                      barColor = '#94A3B8'; // silver
                    }

                    return (
                      <g
                        key={d.round || i}
                        onMouseEnter={() => setHoveredRound(d)}
                        onMouseLeave={() => setHoveredRound(null)}
                        className="cursor-pointer transition"
                      >
                        <rect
                          x={x}
                          y={y}
                          width={barWidth}
                          height={barHeight}
                          rx={Math.min(4, barWidth / 2)}
                          fill={barColor}
                          opacity={isHovered ? 1 : 0.85}
                          className="transition-all duration-150"
                        />
                        <text
                          x={x + barWidth / 2}
                          y={svgHeight - 10}
                          textAnchor="middle"
                          fontSize="8"
                          fill={isHovered ? '#1E293B' : '#94A3B8'}
                          fontWeight={isHovered ? 'bold' : 'normal'}
                          fontFamily="monospace"
                        >
                          #{d.round ?? i + 1}
                        </text>
                      </g>
                    );
                  })}
                </>
              )}
            </svg>

            {/* Hover Tooltip Overlay */}
            {hoveredRound && (
              <div className="absolute top-2 right-2 bg-slate-900/90 text-white rounded-xl px-3 py-1.5 text-xs shadow-lg backdrop-blur-xs space-y-0.5 pointer-events-none animate-in fade-in duration-100 border border-slate-700">
                <div className="flex items-center gap-2 font-bold text-amber-400">
                  <span>รอบที่ #{hoveredRound.round ?? '-'}</span>
                  <span className="text-[10px] font-mono text-slate-300">
                    {hoveredRound.time || '-'}
                  </span>
                </div>
                <div className="flex items-center gap-3 text-[11px] font-mono text-slate-200">
                  <span>🪙 {(hoveredRound.coins || 0).toLocaleString()}</span>
                  <span>⭐ {(hoveredRound.xp || 0).toLocaleString()} EXP</span>
                  <span>📦 {hoveredRound.box_count || 0} กล่อง</span>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
