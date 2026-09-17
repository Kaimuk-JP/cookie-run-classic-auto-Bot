import React, { useState, useEffect } from 'react';
import { Navbar } from './components/layout/Navbar';
import { MetricsCards } from './components/dashboard/MetricsCards';
import { StreamPlayer } from './components/dashboard/StreamPlayer';
import { QuickActions } from './components/dashboard/QuickActions';
import { RoundHistory } from './components/dashboard/RoundHistory';
import { LogsConsole } from './components/dashboard/LogsConsole';
import { DeviceBreakdown } from './components/dashboard/DeviceBreakdown';

// Modals
import { StatsModal } from './components/modals/StatsModal';
import { HistoryModal } from './components/modals/HistoryModal';
import { SettingsModal } from './components/modals/SettingsModal';
import { DiscordModal } from './components/modals/DiscordModal';
import { ToolsModal } from './components/modals/ToolsModal';
import { MacroModal } from './components/modals/MacroModal';

import { Device } from './types/bot';
import { botApi } from './api/botApi';
import { toast, confirmModal } from './context/ToastContext';

export function App() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [selectedSerial, setSelectedSerial] = useState<string>('');
  const [isScanning, setIsScanning] = useState(false);

  // Modals state
  const [isStatsOpen, setIsStatsOpen] = useState(false);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isDiscordOpen, setIsDiscordOpen] = useState(false);
  const [isToolsOpen, setIsToolsOpen] = useState(false);
  const [isMacroOpen, setIsMacroOpen] = useState(false);

  // Fetch devices poll
  const fetchDevices = async () => {
    try {
      const list = await botApi.getDevices();
      setDevices(list);
      if (list.length > 0 && !selectedSerial) {
        setSelectedSerial(list[0].serial);
      }
    } catch (err) {
      console.error('Failed to fetch devices:', err);
    }
  };

  useEffect(() => {
    fetchDevices();
    const timer = setInterval(fetchDevices, 2000);
    return () => clearInterval(timer);
  }, [selectedSerial]);

  // Helper to parse "HH:MM:SS" string to total seconds
  const parseTimeToSeconds = (t?: string): number => {
    if (!t || typeof t !== 'string' || !t.includes(':')) return 0;
    const parts = t.split(':').map(Number);
    if (parts.length === 3) {
      return (parts[0] || 0) * 3600 + (parts[1] || 0) * 60 + (parts[2] || 0);
    } else if (parts.length === 2) {
      return (parts[0] || 0) * 60 + (parts[1] || 0);
    }
    return 0;
  };

  const formatSecondsToTime = (totalSec: number): string => {
    if (totalSec < 0) totalSec = 0;
    const h = Math.floor(totalSec / 3600);
    const m = Math.floor((totalSec % 3600) / 60);
    const s = totalSec % 60;
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  };

  const activeDevice = devices.find((d) => d.serial === selectedSerial) || devices[0];
  const runningCount = devices.filter((d) => d.is_running).length;

  // Track live ticking elapsed seconds for the active device
  const [liveSeconds, setLiveSeconds] = useState<number>(0);

  // Sync with device runtime when devices poll update
  useEffect(() => {
    if (!activeDevice) return;
    const rawTime =
      (activeDevice.session_uptime && activeDevice.session_uptime !== '00:00:00' && activeDevice.session_uptime !== 'กำลังทำงาน'
        ? activeDevice.session_uptime
        : (activeDevice.uptime && activeDevice.uptime !== '00:00:00' && activeDevice.uptime !== 'กำลังทำงาน'
          ? activeDevice.uptime
          : activeDevice.total_uptime || '00:00:00'));

    const parsed = parseTimeToSeconds(rawTime);
    setLiveSeconds((prev) => {
      if (activeDevice.is_running) {
        if (Math.abs(prev - parsed) > 2 || prev === 0) {
          return parsed;
        }
        return prev;
      }
      return parsed;
    });
  }, [activeDevice?.session_uptime, activeDevice?.uptime, activeDevice?.total_uptime, activeDevice?.is_running, activeDevice?.serial]);

  // Live 1-second ticking timer whenever activeDevice is running
  useEffect(() => {
    if (!activeDevice?.is_running) return;

    const interval = setInterval(() => {
      setLiveSeconds((prev) => prev + 1);
    }, 1000);

    return () => clearInterval(interval);
  }, [activeDevice?.is_running, activeDevice?.serial]);

  const currentRuntime = formatSecondsToTime(liveSeconds);

  const handleScan = async () => {
    setIsScanning(true);
    await fetchDevices();
    setTimeout(() => setIsScanning(false), 800);
  };

  const handleStartAll = async () => {
    const ok = await confirmModal({
      title: 'เริ่มทุกจอ',
      message: 'ต้องการเริ่มบอททุกจอหรือไม่?',
      confirmText: 'เริ่มทุกจอ',
      type: 'info',
    });
    if (!ok) return;
    try {
      const res = await botApi.startAllBots();
      toast.success(res.message || 'เริ่มบอททุกจอแล้ว');
      fetchDevices();
    } catch (e: any) {
      toast.error('เริ่มไม่สำเร็จ: ' + e.message);
    }
  };

  const handleStopAll = async () => {
    const ok = await confirmModal({
      title: 'หยุดทุกจอ',
      message: 'ต้องการหยุดบอททุกจอทันทีหรือไม่?',
      confirmText: 'หยุดทุกจอ',
      type: 'danger',
    });
    if (!ok) return;

    setDevices((prev) =>
      prev.map((d) => ({
        ...d,
        is_running: false,
        active_mode: 'idle',
        activity_description: 'พร้อมทำงาน',
        heart_stats: d.heart_stats ? { ...d.heart_stats, running: false } : undefined,
      }))
    );
    try {
      const res = await botApi.stopAllBots();
      toast.success(res.message || 'หยุดทุกจอแล้ว');
    } catch {
      toast.success('หยุดทุกจอแล้ว');
    } finally {
      fetchDevices();
    }
  };

  const handleStartDevice = async (serial: string) => {
    if (!serial) return toast.warning('กรุณาระบุจอที่ต้องการเริ่ม');
    try {
      const res = await botApi.startBot(serial);
      if (!res.success) {
        toast.error(res.message);
      } else {
        toast.success(res.message || `เริ่มบอทจอ ${serial} แล้ว`);
      }
      fetchDevices();
    } catch (e: any) {
      toast.error('เริ่มบอทไม่สำเร็จ: ' + e.message);
    }
  };

  const handleStopDevice = async (serial: string) => {
    if (!serial) return toast.warning('กรุณาระบุจอที่ต้องการหยุด');
    setDevices((prev) =>
      prev.map((d) =>
        d.serial === serial
          ? {
            ...d,
            is_running: false,
            active_mode: 'idle',
            activity_description: 'พร้อมทำงาน',
            heart_stats: d.heart_stats ? { ...d.heart_stats, running: false } : undefined,
          }
          : d
      )
    );
    try {
      const res = await botApi.stopBot(serial);
      toast.success(res.message || `หยุดจอ ${serial} แล้ว`);
    } catch {
      toast.success(`หยุดจอ ${serial} แล้ว`);
    } finally {
      fetchDevices();
    }
  };

  const handleStartCurrent = () => {
    if (!activeDevice) return toast.warning('กรุณาเลือกจอก่อน');
    handleStartDevice(activeDevice.serial);
  };

  const handleStopCurrent = () => {
    if (!activeDevice) return toast.warning('กรุณาเลือกจอก่อน');
    handleStopDevice(activeDevice.serial);
  };

  return (
    <div className="min-h-screen flex flex-col overflow-x-hidden custom-scrollbar">
      {/* Top Header Bar */}
      <Navbar
        devicesCount={devices.length}
        runningCount={runningCount}
        onScan={handleScan}
        onStartAll={handleStartAll}
        onStopAll={handleStopAll}
        isScanning={isScanning}
        devices={devices}
        selectedSerial={activeDevice?.serial || ''}
        onSelectDevice={(s) => setSelectedSerial(s)}
        runtime={currentRuntime}
        onOpenSettings={() => setIsSettingsOpen(true)}
        onOpenMacro={() => setIsMacroOpen(true)}
        onOpenTools={() => setIsToolsOpen(true)}
        onOpenDiscord={() => setIsDiscordOpen(true)}
      />

      {/* Main Content Grid (7 cols on Left, 5 cols on Right) */}
      <main className="flex-1 p-4 md:p-6 grid grid-cols-1 lg:grid-cols-12 gap-6 max-w-[1600px] mx-auto w-full">
        {/* Left Column: Stats, Stream & Round History (7 cols) */}
        <div className="lg:col-span-7 flex flex-col space-y-6">
          {/* Premium Stats & Loot Tracker Cards */}
          <MetricsCards
            device={activeDevice}
            devices={devices}
            onOpenStats={() => setIsStatsOpen(true)}
          />

          {/* Live Emulator Screen Section */}
          <StreamPlayer
            deviceSerial={activeDevice?.serial || ''}
            stageName={activeDevice?.current_stage || ''}
            isRunning={activeDevice?.is_running || false}
          />

          {/* Multi-Device Loot & Status Breakdown (จอไหนได้อะไรเท่าไหร่) */}
          <DeviceBreakdown
            devices={devices}
            selectedSerial={activeDevice?.serial || ''}
            onSelectDevice={(s) => setSelectedSerial(s)}
            onStartDevice={handleStartDevice}
            onStopDevice={handleStopDevice}
          />

          {/* Round History & Efficiency Chart */}
          <RoundHistory
            history={activeDevice?.round_history || []}
            device={activeDevice}
            onOpenHistoryModal={() => setIsHistoryOpen(true)}
          />
        </div>

        {/* Right Column: Control Center & Real-time Event Feed (5 cols) */}
        <div className="lg:col-span-5 flex flex-col space-y-6">
          {/* Quick Control Center Card */}
          <QuickActions
            deviceSerial={activeDevice?.serial || ''}
            isRunning={activeDevice?.is_running || false}
            onStart={handleStartCurrent}
            onStop={handleStopCurrent}
            onOpenSettings={() => setIsSettingsOpen(true)}
            onOpenMacro={() => setIsMacroOpen(true)}
            onOpenDiscord={() => setIsDiscordOpen(true)}
            onOpenTools={() => setIsToolsOpen(true)}
          />

          {/* Real-time Event Feed */}
          <LogsConsole deviceSerial={activeDevice?.serial} />
        </div>
      </main>

      {/* Footer */}
      <footer className="text-center py-4 text-xs text-[#8C6D58] border-t-2 border-[#EEDBCE] mt-auto bg-[#FFFDF6]/80 font-semibold flex items-center justify-center gap-1.5">
        <span>CookieRun AutoBot • Candy Kingdom & Warm Bakery Edition</span>
      </footer>

      {/* Modals */}
      <StatsModal
        isOpen={isStatsOpen}
        onClose={() => setIsStatsOpen(false)}
        device={activeDevice}
        onReset={() => fetchDevices()}
      />

      <HistoryModal
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
        history={activeDevice?.round_history || []}
        deviceSerial={activeDevice?.serial || ''}
        onReset={() => fetchDevices()}
      />

      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        deviceSerial={activeDevice?.serial || ''}
        onOpenDiscord={() => setIsDiscordOpen(true)}
      />

      <MacroModal
        isOpen={isMacroOpen}
        onClose={() => setIsMacroOpen(false)}
        deviceSerial={activeDevice?.serial || ''}
        onSelectMacro={async (macroId) => {
          try {
            await botApi.selectMacro(activeDevice?.serial || '', macroId, true);
            fetchDevices();
          } catch {
            // ignore
          }
        }}
      />

      <DiscordModal
        isOpen={isDiscordOpen}
        onClose={() => setIsDiscordOpen(false)}
      />

      <ToolsModal
        isOpen={isToolsOpen}
        onClose={() => setIsToolsOpen(false)}
        deviceSerial={activeDevice?.serial || ''}
        devices={devices}
      />
    </div>
  );
}

export default App;
