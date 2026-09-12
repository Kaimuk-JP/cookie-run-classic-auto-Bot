import React, { useState, useEffect, useRef } from 'react';
import { Terminal, Trash2, Wifi, WifiOff } from 'lucide-react';
import { LogEntry } from '../../types/bot';
import { botApi } from '../../api/botApi';

interface LogsConsoleProps {
  deviceSerial?: string;
}

const normalizeLogEntry = (raw: any): LogEntry | null => {
  if (!raw) return null;
  if (typeof raw === 'string') {
    const trimmed = raw.trim();
    if (!trimmed) return null;
    return {
      timestamp: new Date().toLocaleTimeString('th-TH', { hour12: false }),
      level: 'info',
      message: trimmed,
    };
  }

  // If wrapped in an event object like { type: 'log', log: {...} }
  if (raw.type === 'log' && raw.log) {
    return normalizeLogEntry(raw.log);
  }

  const msg = raw.message || raw.msg || '';
  if (!String(msg).trim()) return null;

  return {
    timestamp: raw.timestamp || raw.time || new Date().toLocaleTimeString('th-TH', { hour12: false }),
    level: (raw.level || 'info').toLowerCase() as LogEntry['level'],
    message: String(msg),
    target: raw.target || raw.device || '',
  };
};

export const LogsConsole: React.FC<LogsConsoleProps> = ({ deviceSerial }) => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [autoScroll, setAutoScroll] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Initial logs load + WebSocket connection
  useEffect(() => {
    let isMounted = true;
    let ws: WebSocket | null = null;
    let reconnectTimeout: any = null;

    const connectLogs = async () => {
      try {
        const initial = await botApi.getLogs(deviceSerial);
        if (isMounted && Array.isArray(initial)) {
          const parsed = initial.map(normalizeLogEntry).filter(Boolean) as LogEntry[];
          setLogs(parsed);
        }
      } catch (err) {
        console.error('Failed to load initial logs:', err);
      }

      // Open WebSocket
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      const devQuery = deviceSerial && deviceSerial !== 'all' ? `?device=${encodeURIComponent(deviceSerial)}` : '?device=all';
      
      try {
        ws = new WebSocket(`${protocol}//${host}/ws/logs${devQuery}`);

        ws.onopen = () => {
          if (isMounted) setIsConnected(true);
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (!isMounted) return;

            if (data.type === 'history' && Array.isArray(data.logs)) {
              const parsed = data.logs.map(normalizeLogEntry).filter(Boolean) as LogEntry[];
              setLogs(parsed);
            } else if (data.type === 'log' && data.log) {
              const item = normalizeLogEntry(data.log);
              if (item) {
                setLogs((prev) => [...prev.slice(-399), item]);
              }
            } else {
              const item = normalizeLogEntry(data);
              if (item) {
                setLogs((prev) => [...prev.slice(-399), item]);
              }
            }
          } catch (e) {
            // ignore malformed message
          }
        };

        ws.onclose = () => {
          if (isMounted) {
            setIsConnected(false);
            reconnectTimeout = setTimeout(() => {
              if (isMounted) connectLogs();
            }, 3000);
          }
        };

        ws.onerror = (e) => {
          console.warn('Logs WebSocket error:', e);
        };
      } catch (e) {
        console.error('Failed to create WebSocket:', e);
      }
    };

    connectLogs();

    return () => {
      isMounted = false;
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      if (ws) ws.close();
    };
  }, [deviceSerial]);

  // Auto scroll to bottom
  useEffect(() => {
    if (autoScroll && containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  const filteredLogs = searchQuery
    ? logs.filter((l) => l.message.toLowerCase().includes(searchQuery.toLowerCase()))
    : logs;

  return (
    <div className="bg-slate-950 border border-purple-950/60 rounded-3xl p-4 shadow-card text-slate-200 font-mono text-xs space-y-3">
      {/* Header bar */}
      <div className="flex items-center justify-between pb-2 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-brand-400" />
          <h3 className="text-xs font-bold text-slate-100 font-sans">
            บันทึกการทำงานสด (Live Logs Terminal)
          </h3>
          <span className="text-[10px] text-slate-500 font-mono">
            {filteredLogs.length} บรรทัด
          </span>
          <div className="flex items-center gap-1.5 ml-2">
            {isConnected ? (
              <span className="flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                <Wifi className="w-3 h-3" /> Live
              </span>
            ) : (
              <span className="flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/30">
                <WifiOff className="w-3 h-3" /> Reconnecting
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-3">
          <input
            type="text"
            placeholder="ค้นหา log..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-[11px] text-slate-300 placeholder-slate-500 focus:outline-none focus:border-brand-500"
          />

          <label className="flex items-center gap-1.5 text-[11px] text-slate-400 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={(e) => setAutoScroll(e.target.checked)}
              className="rounded bg-slate-800 text-brand-600 focus:ring-0"
            />
            <span>เลื่อนลงอัตโนมัติ</span>
          </label>

          <button
            onClick={() => setLogs([])}
            className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-rose-400 transition"
            title="ล้างข้อความ Log"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Logs Window */}
      <div
        ref={containerRef}
        className="h-64 overflow-y-auto space-y-1.5 custom-scrollbar pr-2 font-mono text-[11px] leading-relaxed"
      >
        {filteredLogs.length === 0 ? (
          <div className="text-slate-600 italic py-6 text-center">
            ยังไม่มีข้อความบันทึกการทำงาน...
          </div>
        ) : (
          filteredLogs.map((log, idx) => {
            const msg = log.message || '';
            let tag = 'INFO';
            let tagClass = 'text-emerald-400 bg-emerald-950/70 border-emerald-500/40';

            if (msg.includes('[BOT]') || log.level === 'bot') {
              tag = 'BOT';
              tagClass = 'text-cyan-400 bg-cyan-950/70 border-cyan-500/40';
            } else if (msg.includes('[ADB]') || log.level === 'adb' || msg.includes('Tap')) {
              tag = 'ADB';
              tagClass = 'text-amber-400 bg-amber-950/70 border-amber-500/40';
            } else if (msg.includes('[FARMER]') || msg.includes('[HeartFarmer]') || log.level === 'farmer' || msg.includes('หัวใจ')) {
              tag = 'FARM';
              tagClass = 'text-pink-400 bg-pink-950/70 border-pink-500/40';
            } else if (msg.includes('[CLEANER]') || msg.includes('[FriendCleaner]') || log.level === 'cleaner' || msg.includes('ลบเพื่อน')) {
              tag = 'CLEAN';
              tagClass = 'text-teal-400 bg-teal-950/70 border-teal-500/40';
            } else if (msg.includes('[ERROR]') || log.level === 'error' || msg.includes('ไม่สำเร็จ') || msg.includes('ล้มเหลว') || msg.includes('Error')) {
              tag = 'ERR';
              tagClass = 'text-rose-400 bg-rose-950/70 border-rose-500/40';
            } else if (msg.includes('[SYS]') || log.level === 'sys' || msg.includes('สแกน') || msg.includes('ตั้งค่า')) {
              tag = 'SYS';
              tagClass = 'text-purple-400 bg-purple-950/70 border-purple-500/40';
            } else if (msg.includes('[STREAM]')) {
              tag = 'LIVE';
              tagClass = 'text-blue-400 bg-blue-950/70 border-blue-500/40';
            } else if (log.level === 'success') {
              tag = 'OK';
              tagClass = 'text-emerald-400 bg-emerald-950/70 border-emerald-500/40';
            }

            const cleanMsg = msg.replace(/^\[(BOT|ADB|INFO|ERROR|SYS|FARMER|HeartFarmer|CLEANER|FriendCleaner|STREAM)\]\s*/i, '');

            return (
              <div key={idx} className="flex items-baseline gap-2 hover:bg-slate-900/60 px-1.5 py-0.5 rounded transition">
                <span className="text-slate-500 shrink-0 font-mono text-[10px]">
                  [{log.timestamp || '00:00:00'}]
                </span>
                <span className={`px-1.5 py-0.2 rounded border text-[9px] font-bold uppercase shrink-0 ${tagClass}`}>
                  {tag}
                </span>
                {log.target && (
                  <span className="text-brand-400/80 shrink-0 text-[10px]">
                    [{log.target.includes(':') ? log.target.split(':')[1] : log.target}]
                  </span>
                )}
                <span
                  className={
                    tag === 'ERR'
                      ? 'text-rose-400 font-semibold'
                      : tag === 'BOT'
                      ? 'text-cyan-300'
                      : tag === 'ADB'
                      ? 'text-amber-300'
                      : tag === 'FARM'
                      ? 'text-pink-300'
                      : tag === 'OK'
                      ? 'text-emerald-400'
                      : 'text-slate-300'
                  }
                >
                  {cleanMsg || msg}
                </span>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
