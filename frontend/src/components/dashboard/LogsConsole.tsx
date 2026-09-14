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
    <div className="biscuit-panel rounded-3xl p-5 shadow-md flex-1 flex flex-col min-h-[350px]">
      {/* Header Bar */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <Terminal className="w-4 h-4 text-[#D97706]" />
          <h3 className="font-bold text-sm text-[#3D2012] font-heading">
            บันทึกการทำงาน
          </h3>
          {isConnected ? (
            <span className="text-[10px] bg-[#D1FAE5] text-[#047857] px-2 py-0.5 rounded-full border border-[#A7F3D0] flex items-center space-x-1 font-bold shadow-xs">
              <span className="w-1.5 h-1.5 rounded-full bg-[#10B981] animate-pulse"></span>
              <span>Live</span>
            </span>
          ) : (
            <span className="text-[10px] bg-[#FEE2E2] text-[#B91C1C] px-2 py-0.5 rounded-full border border-[#FECACA] font-bold">
              Off
            </span>
          )}
        </div>

        <div className="flex items-center space-x-2">
          <label className="flex items-center space-x-1.5 text-[11px] text-[#6B4226] font-semibold cursor-pointer select-none">
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={(e) => setAutoScroll(e.target.checked)}
              className="accent-[#D97706] w-3.5 h-3.5 rounded"
            />
            <span>เลื่อนอัตโนมัติ</span>
          </label>
          <button
            onClick={() => setLogs([])}
            className="candy-btn-soft text-xs text-[#8A3B04] p-1.5 rounded-xl transition cursor-pointer"
            title="ล้างบันทึก"
          >
            <Trash2 className="w-3.5 h-3.5 text-[#D97706]" />
          </button>
        </div>
      </div>

      {/* Log Stream Box (Warm Chocolate & Candy Terminal) */}
      <div
        ref={containerRef}
        id="log-container"
        className="flex-1 bg-[#23140A] rounded-2xl p-3.5 border-2 border-[#5C3317] font-mono text-[11px] text-[#FFF8EC] overflow-y-auto max-h-[300px] custom-scrollbar space-y-2 shadow-inner"
      >
        {logs.length === 0 ? (
          <div className="text-[#C4A48A] italic text-center py-8">
            ยังไม่มีบันทึก...
          </div>
        ) : (
          logs.map((log, idx) => {
            const msg = log.message || '';
            let type = 'INFO';
            let typeColor = 'text-[#FDE047]';

            if (msg.includes('[BOT]') || log.level === 'bot') {
              type = 'BOT';
              typeColor = 'text-[#F59E0B]';
            } else if (msg.includes('[ADB]') || log.level === 'adb' || msg.includes('Tap')) {
              type = 'ACTION';
              typeColor = 'text-[#38BDF8]';
            } else if (msg.includes('[MACRO]') || msg.includes('มาโคร')) {
              type = 'MACRO';
              typeColor = 'text-[#C084FC]';
            } else if (msg.includes('[FARMER]') || msg.includes('[HeartFarmer]') || log.level === 'farmer' || msg.includes('หัวใจ')) {
              type = 'HEART';
              typeColor = 'text-[#FB7185]';
            } else if (msg.includes('[CLEANER]') || msg.includes('[FriendCleaner]') || log.level === 'cleaner' || msg.includes('ลบเพื่อน')) {
              type = 'CLEAN';
              typeColor = 'text-[#34D399]';
            } else if (msg.includes('[ERROR]') || log.level === 'error' || msg.includes('Error') || msg.includes('ล้มเหลว')) {
              type = 'ERR';
              typeColor = 'text-[#F43F5E]';
            } else if (msg.includes('[SYSTEM]') || log.level === 'sys') {
              type = 'SYSTEM';
              typeColor = 'text-[#FBBF24]';
            }

            const cleanMsg = msg
              .replace(/^\[(BOT|ADB|INFO|ERROR|SYS|FARMER|HeartFarmer|CLEANER|FriendCleaner|STREAM|STAGE|SUCCESS|WARNING|MACRO)\]\s*/i, '')
              .replace(/^\[(emulator-\d+|\d+\.\d+\.\d+\.\d+:\d+)\]\s*/i, '');

            return (
              <div
                key={idx}
                className="flex items-start space-x-2 border-b border-[#3D2312] pb-1.5 last:border-b-0"
              >
                <span className="text-[#C4A48A] shrink-0 font-mono text-[10px]">
                  {log.timestamp || '00:00:00'}
                </span>
                <span className={`${typeColor} font-bold shrink-0 text-[10px]`}>
                  [{type}]
                </span>
                {log.target && (
                  <span className="text-[#FBBF24] shrink-0 text-[10px] font-mono">
                    {log.target}
                  </span>
                )}
                <span className="text-[#FFF8EC] truncate">
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
