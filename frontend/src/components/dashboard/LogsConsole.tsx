import React, { useState, useEffect, useRef } from 'react';
import { Terminal, Trash2 } from 'lucide-react';
import { LogEntry } from '../../types/bot';
import { botApi } from '../../api/botApi';
import { FormattedTextWithIcons } from '../../utils/iconMap';

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
  const [isConnected, setIsConnected] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

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

      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      const devQuery =
        deviceSerial && deviceSerial !== 'all'
          ? `?device=${encodeURIComponent(deviceSerial)}`
          : '?device=all';

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
            // ignore
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

  useEffect(() => {
    if (autoScroll && containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  return (
    <div className="glass-panel rounded-3xl p-5 shadow-xl flex-1 flex flex-col min-h-[350px]">
      {/* Header Bar */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <Terminal className="w-4 h-4 text-[#DC95FF]" />
          <h3 className="font-semibold text-sm text-white">Real-time Event Feed</h3>
          {isConnected ? (
            <span className="text-[10px] bg-[#DC95FF]/20 text-[#FFF4BF] px-2 py-0.5 rounded-full border border-[#DC95FF]/30 flex items-center space-x-1">
              <span className="w-1.5 h-1.5 rounded-full bg-[#FFF4BF] animate-pulse"></span>
              <span>Live</span>
            </span>
          ) : (
            <span className="text-[10px] bg-rose-500/20 text-rose-300 px-2 py-0.5 rounded-full border border-rose-500/30">
              Off
            </span>
          )}
        </div>

        <div className="flex items-center space-x-2">
          <label className="flex items-center space-x-1 text-[10px] text-[#FFBEFB] cursor-pointer select-none">
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={(e) => setAutoScroll(e.target.checked)}
              className="accent-[#8C56D4] w-3 h-3 rounded"
            />
            <span>ออโต้</span>
          </label>
          <button
            onClick={() => setLogs([])}
            className="text-xs text-[#DC95FF] hover:text-[#FFF4BF] transition p-1 cursor-pointer"
            title="ล้าง Log"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Log Stream Box */}
      <div
        ref={containerRef}
        id="log-container"
        className="flex-1 bg-[#150d24]/85 rounded-2xl p-3 border border-[#DC95FF]/25 font-mono text-[11px] text-slate-200 overflow-y-auto max-h-[300px] custom-scrollbar space-y-2"
      >
        {logs.length === 0 ? (
          <div className="text-[#DC95FF]/60 italic text-center py-8">
            ยังไม่มีข้อความบันทึกเหตุการณ์...
          </div>
        ) : (
          logs.map((log, idx) => {
            const msg = log.message || '';
            let type = 'INFO';
            let typeColor = 'text-[#FFF4BF]';

            if (msg.includes('[BOT]') || log.level === 'bot') {
              type = 'BOT';
              typeColor = 'text-[#DC95FF]';
            } else if (msg.includes('[ADB]') || log.level === 'adb' || msg.includes('Tap')) {
              type = 'ACTION';
              typeColor = 'text-[#FFF4BF]';
            } else if (msg.includes('[MACRO]') || msg.includes('มาโคร')) {
              type = 'MACRO';
              typeColor = 'text-[#FFBEFB]';
            } else if (msg.includes('[FARMER]') || msg.includes('[HeartFarmer]') || log.level === 'farmer' || msg.includes('หัวใจ')) {
              type = 'HEART';
              typeColor = 'text-[#FFBEFB]';
            } else if (msg.includes('[CLEANER]') || msg.includes('[FriendCleaner]') || log.level === 'cleaner' || msg.includes('ลบเพื่อน')) {
              type = 'CLEAN';
              typeColor = 'text-teal-300';
            } else if (msg.includes('[ERROR]') || log.level === 'error' || msg.includes('Error') || msg.includes('ล้มเหลว')) {
              type = 'ERR';
              typeColor = 'text-rose-400';
            } else if (msg.includes('[SYSTEM]') || log.level === 'sys') {
              type = 'SYSTEM';
              typeColor = 'text-[#DC95FF]';
            }

            const cleanMsg = msg
              .replace(/^\[(BOT|ADB|INFO|ERROR|SYS|FARMER|HeartFarmer|CLEANER|FriendCleaner|STREAM|STAGE|SUCCESS|WARNING|MACRO)\]\s*/i, '')
              .replace(/^\[(emulator-\d+|\d+\.\d+\.\d+\.\d+:\d+)\]\s*/i, '');

            return (
              <div
                key={idx}
                className="flex items-start space-x-2 border-b border-[#DC95FF]/10 pb-1.5 last:border-b-0"
              >
                <span className="text-[#DC95FF]/80 shrink-0 font-mono text-[10px]">
                  {log.timestamp || '00:00:00'}
                </span>
                <span className={`${typeColor} font-bold shrink-0 text-[10px]`}>
                  [{type}]
                </span>
                {log.target && (
                  <span className="text-[#FFBEFB] shrink-0 text-[10px] font-mono">
                    {log.target}
                  </span>
                )}
                <span className="text-slate-200 truncate">
                  <FormattedTextWithIcons text={cleanMsg || msg} />
                </span>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
