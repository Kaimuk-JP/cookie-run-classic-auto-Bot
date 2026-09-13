import React, { useState, useEffect } from 'react';
import { Navbar } from './components/layout/Navbar';
import { MetricsCards } from './components/dashboard/MetricsCards';
import { DeviceTabs } from './components/dashboard/DeviceTabs';
import { StreamPlayer } from './components/dashboard/StreamPlayer';
import { QuickActions } from './components/dashboard/QuickActions';
import { RoundHistory } from './components/dashboard/RoundHistory';
import { LogsConsole } from './components/dashboard/LogsConsole';
import { Play, Square, Settings, Sparkles, Heart } from 'lucide-react';

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

  const activeDevice = devices.find((d) => d.serial === selectedSerial) || devices[0];
  const runningCount = devices.filter((d) => d.is_running).length;

  const handleScan = async () => {
    setIsScanning(true);
    await fetchDevices();
    setTimeout(() => setIsScanning(false), 800);
  };

  const handleStartAll = async () => {
    const ok = await confirmModal({
      title: 'เริ่มการทำงานทุกจอ',
      message: 'ต้องการเริ่มบอททุกจอพร้อมกันหรือไม่?',
      confirmText: 'เริ่มทุกจอ',
      type: 'info',
    });
    if (!ok) return;
    try {
      const res = await botApi.startAllBots();
      toast.success(res.message || 'สั่งการเริ่มบอททุกจอเรียบร้อยแล้ว');
      fetchDevices();
    } catch (e: any) {
      toast.error('เริ่มไม่สำเร็จ: ' + e.message);
    }
  };

  const handleStopAll = async () => {
    const ok = await confirmModal({
      title: 'สั่งหยุดบอททุกจอ',
      message: 'ต้องการสั่งหยุดบอททุกจอทันทีหรือไม่?',
      confirmText: 'หยุดทุกจอ',
      type: 'danger',
    });
    if (!ok) return;

    // Instantly reflect stopped state on all devices
    setDevices((prev) =>
      prev.map((d) => ({
        ...d,
        is_running: false,
        active_mode: 'idle',
        activity_description: 'พร้อมทำงาน (หยุดพัก)',
        heart_stats: d.heart_stats ? { ...d.heart_stats, running: false } : undefined,
      }))
    );
    try {
      const res = await botApi.stopAllBots();
      toast.success(res.message || 'สั่งหยุดทุกจอทันทีเรียบร้อยแล้ว');
    } catch {
      toast.success('สั่งหยุดทุกจอทันทีเรียบร้อยแล้ว');
    } finally {
      fetchDevices();
    }
  };

  const handleStartCurrent = async () => {
    if (!activeDevice) return toast.warning('กรุณาเลือกจอก่อน');
    try {
      const res = await botApi.startBot(activeDevice.serial);
      if (!res.success) {
        toast.error(res.message);
      } else {
        toast.success(res.message || `เริ่มบอทจอ ${activeDevice.serial} เรียบร้อยแล้ว`);
      }
      fetchDevices();
    } catch (e: any) {
      toast.error('เริ่มบอทไม่สำเร็จ: ' + e.message);
    }
  };

  const handleStopCurrent = async () => {
    if (!activeDevice) return toast.warning('กรุณาเลือกจอก่อน');
    setDevices((prev) =>
      prev.map((d) =>
        d.serial === activeDevice.serial
          ? {
              ...d,
              is_running: false,
              active_mode: 'idle',
              activity_description: 'พร้อมทำงาน (หยุดพัก)',
              heart_stats: d.heart_stats ? { ...d.heart_stats, running: false } : undefined,
            }
          : d
      )
    );
    try {
      const res = await botApi.stopBot(activeDevice.serial);
      toast.success(res.message || `สั่งหยุดจอ ${activeDevice.serial} ทันทีเรียบร้อยแล้ว`);
    } catch {
      toast.success(`สั่งหยุดจอ ${activeDevice.serial} ทันทีเรียบร้อยแล้ว`);
    } finally {
      fetchDevices();
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-800">
      {/* Navbar */}
      <Navbar
        devicesCount={devices.length}
        runningCount={runningCount}
        onScan={handleScan}
        onStartAll={handleStartAll}
        onStopAll={handleStopAll}
        isScanning={isScanning}
      />

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8 py-4 sm:py-6 space-y-4 sm:space-y-6 w-full grow pb-24 lg:pb-8">
        {/* Device Switcher Tabs */}
        <DeviceTabs
          devices={devices}
          selectedSerial={activeDevice?.serial || ''}
          onSelectDevice={(s) => setSelectedSerial(s)}
        />

        {/* Desktop: Top 4 Metrics Summary Cards */}
        <div className="hidden lg:block">
          <MetricsCards
            device={activeDevice}
            devices={devices}
            onOpenStats={() => setIsStatsOpen(true)}
          />
        </div>

        {/* Main Responsive Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 sm:gap-6 items-start">
          {/* Stream Section (Top priority on mobile) */}
          <div className="lg:col-span-8 space-y-4 sm:space-y-6">
            <StreamPlayer
              deviceSerial={activeDevice?.serial || ''}
              stageName={activeDevice?.current_stage || ''}
              isRunning={activeDevice?.is_running || false}
            />

            {/* Mobile: Metrics Cards right below Stream */}
            <div className="block lg:hidden">
              <MetricsCards
                device={activeDevice}
                devices={devices}
                onOpenStats={() => setIsStatsOpen(true)}
              />
            </div>

            {/* Desktop: Round History on Left */}
            <div className="hidden lg:block">
              <RoundHistory
                history={activeDevice?.round_history || []}
                onOpenHistoryModal={() => setIsHistoryOpen(true)}
              />
            </div>
          </div>

          {/* Controls & Logs Section */}
          <div className="lg:col-span-4 space-y-4 sm:space-y-6">
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

            {/* Mobile: Round History below QuickActions */}
            <div className="block lg:hidden">
              <RoundHistory
                history={activeDevice?.round_history || []}
                onOpenHistoryModal={() => setIsHistoryOpen(true)}
              />
            </div>

            <LogsConsole deviceSerial={activeDevice?.serial} />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-purple-100/60 bg-white/70 py-4 text-center text-xs text-slate-400 hidden lg:block">
        CookieRun AutoBot Pro • Mobile Ready Dashboard
      </footer>

      {/* Sticky Mobile Bottom Quick Bar (Visible only on Mobile & Tablets) */}
      <nav className="lg:hidden fixed bottom-0 left-0 right-0 z-40 bg-white/95 backdrop-blur-md border-t border-purple-100 shadow-2xl px-3 py-2 flex items-center justify-between gap-2 safe-bottom">
        <div className="flex items-center gap-2 min-w-0">
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse shrink-0"></div>
          <span className="text-xs font-bold text-slate-800 truncate">
            {activeDevice?.name || activeDevice?.serial || 'ยังไม่เลือกจอ'}
          </span>
        </div>

        <div className="flex items-center gap-1.5 shrink-0">
          <button
            onClick={() => setIsMacroOpen(true)}
            className="p-2 rounded-xl bg-purple-50 text-purple-700 hover:bg-purple-100 transition active:scale-95"
            title="มาโครวิ่ง"
          >
            <Sparkles className="w-4 h-4" />
          </button>

          <button
            onClick={() => setIsToolsOpen(true)}
            className="p-2 rounded-xl bg-pink-50 text-pink-600 hover:bg-pink-100 transition active:scale-95"
            title="ปั๊มหัวใจ"
          >
            <Heart className="w-4 h-4" />
          </button>

          <button
            onClick={() => setIsSettingsOpen(true)}
            className="p-2 rounded-xl bg-slate-100 text-slate-700 hover:bg-slate-200 transition active:scale-95"
            title="ตั้งค่าบอท"
          >
            <Settings className="w-4 h-4" />
          </button>

          {activeDevice?.is_running ? (
            <button
              onClick={handleStopCurrent}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs shadow-md shadow-rose-600/30 transition active:scale-95 cursor-pointer"
            >
              <Square className="w-3.5 h-3.5 fill-current" />
              <span>หยุด</span>
            </button>
          ) : (
            <button
              onClick={handleStartCurrent}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-gradient-to-r from-brand-600 to-brand-500 hover:from-brand-700 text-white font-bold text-xs shadow-md shadow-brand-500/30 transition active:scale-95 cursor-pointer"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>เริ่มบอท</span>
            </button>
          )}
        </div>
      </nav>

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
