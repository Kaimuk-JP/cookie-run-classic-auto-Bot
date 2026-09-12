import React, { useState, useEffect } from 'react';
import { Navbar } from './components/layout/Navbar';
import { MetricsCards } from './components/dashboard/MetricsCards';
import { DeviceTabs } from './components/dashboard/DeviceTabs';
import { StreamPlayer } from './components/dashboard/StreamPlayer';
import { QuickActions } from './components/dashboard/QuickActions';
import { RoundHistory } from './components/dashboard/RoundHistory';
import { LogsConsole } from './components/dashboard/LogsConsole';

// Modals
import { StatsModal } from './components/modals/StatsModal';
import { HistoryModal } from './components/modals/HistoryModal';
import { SettingsModal } from './components/modals/SettingsModal';
import { DiscordModal } from './components/modals/DiscordModal';
import { ToolsModal } from './components/modals/ToolsModal';

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
    // Instantly reflect stopped state on current device
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
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6 w-full grow">
        {/* Device Switcher Tabs */}
        <DeviceTabs
          devices={devices}
          selectedSerial={activeDevice?.serial || ''}
          onSelectDevice={(s) => setSelectedSerial(s)}
        />

        {/* Top 4 Metrics Summary Cards */}
        <MetricsCards
          device={activeDevice}
          onOpenStats={() => setIsStatsOpen(true)}
        />

        {/* Main Grid: Stream & History on Left (8 cols), Quick Actions & Controls on Right (4 cols) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Canvas & History Area */}
          <div className="lg:col-span-8 space-y-6">
            <StreamPlayer
              deviceSerial={activeDevice?.serial || ''}
              stageName={activeDevice?.current_stage || ''}
              isRunning={activeDevice?.is_running || false}
            />

            <RoundHistory
              history={activeDevice?.round_history || []}
              onOpenHistoryModal={() => setIsHistoryOpen(true)}
            />

            <LogsConsole deviceSerial={activeDevice?.serial} />
          </div>

          {/* Right Action Panel */}
          <div className="lg:col-span-4 space-y-6">
            <QuickActions
              deviceSerial={activeDevice?.serial || ''}
              isRunning={activeDevice?.is_running || false}
              onStart={handleStartCurrent}
              onStop={handleStopCurrent}
              onOpenSettings={() => setIsSettingsOpen(true)}
              onOpenDiscord={() => setIsDiscordOpen(true)}
              onOpenTools={() => setIsToolsOpen(true)}
            />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-purple-100/60 bg-white/70 py-4 text-center text-xs text-slate-400">
        CookieRun AutoBot Pro • Powered by Vite + React + FastAPI
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
