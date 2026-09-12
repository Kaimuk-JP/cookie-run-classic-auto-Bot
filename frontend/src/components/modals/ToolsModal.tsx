import React, { useState, useEffect } from 'react';
import { X, Heart, UserMinus, Play, Square, PlayCircle, Clipboard, Smartphone, RefreshCw } from 'lucide-react';
import { botApi } from '../../api/botApi';
import { Device } from '../../types/bot';

interface ToolsModalProps {
  isOpen: boolean;
  onClose: () => void;
  deviceSerial: string;
  devices?: Device[];
}

export const ToolsModal: React.FC<ToolsModalProps> = ({
  isOpen,
  onClose,
  deviceSerial,
  devices = [],
}) => {
  const [selectedFarmerDevice, setSelectedFarmerDevice] = useState<string>(deviceSerial || 'all');
  const [inviteUrl, setInviteUrl] = useState<string>('ลิงก์เชิญเพื่อน');
  const [farmerStatus, setFarmerStatus] = useState<{
    running: boolean;
    rounds: number;
    success_count: number;
    current_step?: string;
  }>({ running: false, rounds: 0, success_count: 0, current_step: '' });

  const [selectedCleanerDevice, setSelectedCleanerDevice] = useState<string>(deviceSerial || 'all');
  const [cleanerInterval, setCleanerInterval] = useState<number>(30);
  const [cleanerStatus, setCleanerStatus] = useState<{
    is_running: boolean;
    next_run?: string;
    next_run_seconds?: number;
    current_device?: string | null;
    current_step?: string;
    target_devices?: string[];
    history?: any[];
  }>({ is_running: false });

  const [loading, setLoading] = useState<string | null>(null);

  // Sync selected device when deviceSerial prop changes
  useEffect(() => {
    if (deviceSerial) {
      setSelectedFarmerDevice(deviceSerial);
      setSelectedCleanerDevice(deviceSerial);
    }
  }, [deviceSerial]);

  // Load saved invite link from device settings
  useEffect(() => {
    if (!isOpen) return;
    const targetDev = selectedFarmerDevice !== 'all' ? selectedFarmerDevice : (devices[0]?.serial || deviceSerial);
    if (targetDev) {
      botApi.getSettings(targetDev).then((cfg) => {
        if (cfg && cfg.heart_farmer_invite && cfg.heart_farmer_invite !== 'ใส่ลิงก์เชิญเพื่อนของคุณ') {
          setInviteUrl(cfg.heart_farmer_invite);
        }
      }).catch(() => {});
    }
  }, [isOpen, selectedFarmerDevice]);

  // Poll status while modal is open
  useEffect(() => {
    if (!isOpen) return;

    const poll = async () => {
      try {
        const fStat = await botApi.getFarmerStatus(selectedFarmerDevice);
        if (fStat) {
          setFarmerStatus({
            running: !!fStat.running || !!fStat.any_running,
            rounds: fStat.rounds ?? fStat.total_rounds ?? 0,
            success_count: fStat.success_count ?? fStat.total_success ?? 0,
            current_step: fStat.current_step ?? '',
          });
        }
        const cStat = await botApi.getCleanerStatus();
        if (cStat) {
          setCleanerStatus({
            is_running: !!cStat.is_running,
            next_run: cStat.next_run,
            next_run_seconds: cStat.next_run_seconds,
            current_device: cStat.current_device,
            current_step: cStat.current_step,
            target_devices: cStat.target_devices,
            history: cStat.history,
          });
        }
      } catch (e) {
        // ignore
      }
    };

    poll();
    const interval = setInterval(poll, 2500);
    return () => clearInterval(interval);
  }, [isOpen, selectedFarmerDevice]);

  if (!isOpen) return null;

  const handlePasteInvite = async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text && text.trim()) {
        setInviteUrl(text.trim());
      } else {
        const manual = prompt('วางลิงก์เชิญเพื่อนที่นี่:', inviteUrl);
        if (manual !== null) setInviteUrl(manual.trim());
      }
    } catch {
      const manual = prompt('วางลิงก์เชิญเพื่อนที่นี่:', inviteUrl);
      if (manual !== null) setInviteUrl(manual.trim());
    }
  };

  const handleStartFarmer = async () => {
    const trimmedInvite = inviteUrl.trim();
    if (!trimmedInvite || trimmedInvite === 'ใส่ลิงก์เชิญเพื่อนของคุณ' || trimmedInvite === 'ลิงก์เชิญเพื่อน') {
      const confirmRun = confirm('คุณยังไม่ได้ใส่ลิงก์เชิญเพื่อนจริง (ยังเป็นข้อความดีฟอลต์) ต้องการดำเนินการต่อหรือไม่?');
      if (!confirmRun) return;
    }

    setLoading('farmer_start');
    try {
      const isAll = selectedFarmerDevice === 'all';
      const targetDevs = isAll ? devices.map((d) => d.serial) : undefined;
      const targetDev = !isAll ? selectedFarmerDevice : undefined;

      const res = await botApi.startFarmer({
        device: targetDev,
        devices: targetDevs,
        invite_url: trimmedInvite,
      });

      // Save invite link to settings as well
      const devToSave = targetDev || devices[0]?.serial;
      if (devToSave) {
        botApi.getSettings(devToSave).then((s) => {
          botApi.saveSettings(devToSave, { ...s, heart_farmer_invite: trimmedInvite });
        }).catch(() => {});
      }

      alert(res.message || 'สั่งเริ่มระบบปั๊มหัวใจเรียบร้อยแล้ว');
      setFarmerStatus((prev) => ({ ...prev, running: true }));
    } catch (e: any) {
      alert('เริ่มไม่สำเร็จ: ' + e.message);
    } finally {
      setLoading(null);
    }
  };

  const handleStopFarmer = async () => {
    setLoading('farmer_stop');
    setFarmerStatus((prev) => ({ ...prev, running: false, current_step: 'หยุดการทำงานทันทีแล้ว' }));
    try {
      const isAll = selectedFarmerDevice === 'all';
      const res = await botApi.stopFarmer({
        device: !isAll ? selectedFarmerDevice : undefined,
      });
      alert(res.message || 'สั่งหยุดระบบปั๊มหัวใจทันทีเรียบร้อย');
    } catch {
      alert('สั่งหยุดระบบปั๊มหัวใจทันทีเรียบร้อยแล้ว');
    } finally {
      setLoading(null);
    }
  };

  const handleStartCleaner = async () => {
    setLoading('cleaner_start');
    try {
      const isAll = selectedCleanerDevice === 'all';
      const targetDevs = isAll ? devices.map((d) => d.serial) : undefined;
      const targetDev = !isAll ? selectedCleanerDevice : undefined;

      const res = await botApi.startFriendCleaner({
        device: targetDev,
        devices: targetDevs,
        interval_minutes: Number(cleanerInterval) || 30,
        run_immediately: true,
      });
      alert(res.message || 'สั่งเริ่มระบบลบเพื่อนเวล 1 เรียบร้อย');
      setCleanerStatus((prev) => ({
        ...prev,
        is_running: true,
        current_step: 'เริ่มวนลูปแล้ว กำลังเตรียมพร้อม...',
        current_device: targetDev || (targetDevs ? targetDevs[0] : null),
        target_devices: targetDevs || (targetDev ? [targetDev] : []),
      }));
    } catch (e: any) {
      alert('เริ่มไม่สำเร็จ: ' + e.message);
    } finally {
      setLoading(null);
    }
  };

  const handleStopCleaner = async () => {
    setLoading('cleaner_stop');
    try {
      const res = await botApi.stopFriendCleaner();
      alert(res.message || 'สั่งหยุดระบบลบเพื่อนเรียบร้อย');
      setCleanerStatus((prev) => ({
        ...prev,
        is_running: false,
        current_device: null,
        current_step: 'หยุดการทำงานเรียบร้อยแล้ว',
      }));
    } catch (e: any) {
      alert('หยุดไม่สำเร็จ: ' + e.message);
    } finally {
      setLoading(null);
    }
  };

  const handleRunOnceCleaner = async () => {
    const targetDev = selectedCleanerDevice !== 'all' ? selectedCleanerDevice : devices[0]?.serial;
    if (!targetDev) return alert('กรุณาเลือกจอก่อน');

    setLoading('cleaner_once');
    setCleanerStatus((prev) => ({
      ...prev,
      current_device: targetDev,
      current_step: `กำลังเริ่มลบเพื่อนเวล 1 ทันทีบนจอ ${targetDev}...`,
    }));
    try {
      const res = await botApi.runOnceFriendCleaner(targetDev);
      alert(res.message || `ส่งคำสั่งลบเพื่อนเวล 1 บนจอ ${targetDev} เรียบร้อยแล้ว`);
    } catch (e: any) {
      alert('เริ่มไม่สำเร็จ: ' + e.message);
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl max-w-xl w-full p-6 space-y-4 shadow-2xl border border-purple-100 animate-in fade-in zoom-in-95 duration-150 max-h-[90vh] overflow-y-auto custom-scrollbar">
        {/* Modal Header */}
        <div className="flex items-center justify-between pb-3 border-b border-purple-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-pink-50 text-pink-600 flex items-center justify-center text-xl shadow-xs border border-pink-100">
              <Heart className="w-5 h-5 fill-current" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">
                เครื่องมือเสริม (Heart Farmer & Friend Cleaner)
              </h3>
              <p className="text-xs text-slate-500">
                ระบบปั๊มหัวใจเพื่อนใหม่ และลบเพื่อนเลิกเล่นอัตโนมัติ
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-slate-100 hover:bg-slate-200 flex items-center justify-center text-slate-600 font-bold transition cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="space-y-4 text-xs">
          {/* ================= HEART FARMER BOX ================= */}
          <div className="p-4 rounded-2xl bg-gradient-to-br from-pink-50/70 via-white to-rose-50/40 border border-pink-200 shadow-xs space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-pink-600 text-base">💖</span>
                <div>
                  <h4 className="font-bold text-slate-900 text-sm flex items-center gap-1.5">
                    ระบบปั๊มหัวใจ (Heart Farmer)
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-pink-500 text-white">NEW</span>
                  </h4>
                  <p className="text-[11px] text-slate-500">
                    วนลูปกดลิงก์เชิญเพื่อน ส่งหัวใจ และรับของขวัญอัตโนมัติ
                  </p>
                </div>
              </div>

              {/* Status Badge */}
              <div className="text-right">
                <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full font-bold text-[10px] border ${
                  farmerStatus.running
                    ? 'bg-pink-100 text-pink-700 border-pink-200 shadow-2xs'
                    : 'bg-slate-100 text-slate-500 border-slate-200'
                }`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${farmerStatus.running ? 'bg-pink-500 animate-pulse' : 'bg-slate-400'}`}></span>
                  {farmerStatus.running
                    ? `กำลังปั้ม (รอบที่ ${farmerStatus.rounds} • ส่งสำเร็จ ${farmerStatus.success_count} ครั้ง)`
                    : 'ยังไม่ได้เริ่ม'}
                </span>
                {farmerStatus.running && farmerStatus.current_step && (
                  <p className="text-[10px] font-medium text-pink-600 mt-1 truncate max-w-[220px]" title={farmerStatus.current_step}>
                    ⚡ {farmerStatus.current_step}
                  </p>
                )}
              </div>
            </div>

            {/* 1. Device Selector for Farmer */}
            <div className="space-y-1">
              <label className="text-slate-700 font-bold flex items-center gap-1">
                <Smartphone className="w-3.5 h-3.5 text-pink-600" />
                <span>เลือกจอจำลอง (Emulator เป้าหมาย)</span>
              </label>
              <select
                value={selectedFarmerDevice}
                onChange={(e) => setSelectedFarmerDevice(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-white border border-pink-200 text-xs font-semibold focus:ring-2 focus:ring-pink-500 outline-none text-slate-800 shadow-2xs"
              >
                <option value="all">🌐 ทุกจอพร้อมกัน (All Devices - {devices.length} จอ)</option>
                {devices.map((d, idx) => (
                  <option key={d.serial} value={d.serial}>
                    📱 {d.name || d.emu_name || `จอที่ ${idx + 1}`} ({d.serial}) {d.model ? `[${d.model}]` : ''}
                  </option>
                ))}
              </select>
            </div>

            {/* 2. Invite URL Input for Farmer */}
            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <label className="text-slate-700 font-bold flex items-center gap-1">
                  <span>🔗</span>
                  <span>ลิงก์เชิญเพื่อนของคุณ (Invite Link)</span>
                </label>
                <button
                  type="button"
                  onClick={handlePasteInvite}
                  className="flex items-center gap-1 text-[11px] text-pink-600 hover:text-pink-700 font-bold hover:underline cursor-pointer"
                >
                  <Clipboard className="w-3 h-3" />
                  <span>วางลิงก์จากคลิปบอร์ด</span>
                </button>
              </div>
              <input
                type="text"
                value={inviteUrl}
                onChange={(e) => setInviteUrl(e.target.value)}
                placeholder="https://cookierunglobal.onelink.me/... หรือข้อความที่มีลิงก์"
                className="w-full px-3 py-2 rounded-xl bg-white border border-pink-200 font-mono text-[11px] focus:ring-2 focus:ring-pink-500 outline-none text-slate-800 shadow-2xs placeholder-slate-400"
              />
              <p className="text-[10px] text-slate-400">
                * ก๊อปปี้ลิงก์เชิญเพื่อนจากในเกม CookieRun (เช่น จากหน้ากิจกรรมเชิญเพื่อน) แล้วกด "วางลิงก์จากคลิปบอร์ด"
              </p>
            </div>

            {/* Buttons for Farmer */}
            <div className="flex items-center gap-2 pt-1">
              <button
                onClick={handleStartFarmer}
                disabled={loading === 'farmer_start' || farmerStatus.running}
                className="flex-1 flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-xl bg-gradient-to-r from-pink-500 to-rose-500 hover:from-pink-600 hover:to-rose-600 text-white font-bold transition shadow-btn-pink active:scale-95 disabled:opacity-50 cursor-pointer"
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>{loading === 'farmer_start' ? 'กำลังส่งคำสั่ง...' : 'เริ่มปั๊มหัวใจ'}</span>
              </button>
              <button
                onClick={handleStopFarmer}
                disabled={loading === 'farmer_stop' || !farmerStatus.running}
                className="px-4 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold transition active:scale-95 disabled:opacity-40 cursor-pointer flex items-center gap-1"
              >
                <Square className="w-3.5 h-3.5 fill-current" />
                <span>หยุด</span>
              </button>
            </div>
          </div>

          {/* ================= FRIEND CLEANER BOX ================= */}
          <div className="p-4 rounded-2xl bg-gradient-to-br from-teal-50/70 via-white to-emerald-50/40 border border-teal-200 shadow-xs space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-teal-600 text-base">💌</span>
                <div>
                  <h4 className="font-bold text-slate-900 text-sm flex items-center gap-1.5">
                    ระบบลบเพื่อนเลิกเล่น (Friend Cleaner)
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-teal-600 text-white">AUTO</span>
                  </h4>
                  <p className="text-[11px] text-slate-500">
                    เข้าหน้าจัดการเพื่อน ลบเพื่อนที่เลิกเล่น หรือเวล 1 อัตโนมัติ
                  </p>
                </div>
              </div>

              {/* Status Badge */}
              <div className="text-right">
                <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full font-bold text-[10px] border ${
                  cleanerStatus.is_running
                    ? 'bg-teal-500/10 text-teal-700 border-teal-500/30'
                    : 'bg-slate-100 text-slate-500 border-slate-200'
                }`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${cleanerStatus.is_running ? 'bg-teal-500 animate-pulse' : 'bg-slate-400'}`}></span>
                  {cleanerStatus.is_running
                    ? (cleanerStatus.current_device ? `กำลังทำ: ${devices.find((d) => d.serial === cleanerStatus.current_device)?.name || cleanerStatus.current_device}` : 'วนลูปทำงานอยู่')
                    : 'ยังไม่ได้เริ่ม'}
                </span>
              </div>
            </div>

            {/* Real-time Machine & Action Display Card */}
            {(cleanerStatus.is_running || cleanerStatus.current_step) && (
              <div className="p-3 rounded-xl bg-white border border-teal-200 shadow-2xs space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-bold text-slate-700 flex items-center gap-1.5">
                    <Smartphone className="w-3.5 h-3.5 text-teal-600" />
                    เครื่องที่กำลังทำงาน:
                    <span className="text-teal-800 font-extrabold bg-teal-50 px-2 py-0.5 rounded-md border border-teal-200">
                      {devices.find((d) => d.serial === cleanerStatus.current_device)?.name
                        ? `${devices.find((d) => d.serial === cleanerStatus.current_device)?.name} (${cleanerStatus.current_device})`
                        : cleanerStatus.current_device || (cleanerStatus.target_devices && cleanerStatus.target_devices.length > 0 ? cleanerStatus.target_devices.join(', ') : 'ทุกจอ')}
                    </span>
                  </span>
                  {cleanerStatus.next_run && (
                    <span className="text-[10px] text-slate-500 font-mono">
                      ⏰ รอบถัดไป: <b className="text-teal-700">{cleanerStatus.next_run}</b>
                    </span>
                  )}
                </div>

                {cleanerStatus.current_step && (
                  <div className="p-2 rounded-lg bg-teal-50/70 border border-teal-100 flex items-start gap-2">
                    <span className="w-2 h-2 rounded-full bg-teal-500 mt-1 shrink-0 animate-pulse"></span>
                    <div className="flex-1">
                      <p className="text-[10px] font-bold text-teal-800">สถานะที่เครื่องกำลังทำอยู่:</p>
                      <p className="text-[11px] font-semibold text-teal-900 mt-0.5 leading-snug">
                        {cleanerStatus.current_step}
                      </p>
                    </div>
                  </div>
                )}

                {cleanerStatus.history && cleanerStatus.history.length > 0 && (
                  <div className="text-[10px] text-slate-500 pt-1 border-t border-slate-100 flex items-center justify-between">
                    <span>รอบล่าสุด: {cleanerStatus.history[cleanerStatus.history.length - 1].time}</span>
                    <span className="font-semibold text-teal-700">
                      ลบเพื่อนเวล 1 สำเร็จ {cleanerStatus.history[cleanerStatus.history.length - 1].ticked ?? 0} คน
                    </span>
                  </div>
                )}
              </div>
            )}

            {/* 1. Device Selector for Cleaner */}
            <div className="space-y-1">
              <label className="text-slate-700 font-bold flex items-center gap-1">
                <Smartphone className="w-3.5 h-3.5 text-teal-600" />
                <span>เลือกจอจำลอง (Emulator เป้าหมาย)</span>
              </label>
              <select
                value={selectedCleanerDevice}
                onChange={(e) => setSelectedCleanerDevice(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-white border border-teal-200 text-xs font-semibold focus:ring-2 focus:ring-teal-500 outline-none text-slate-800 shadow-2xs"
              >
                <option value="all">🌐 ทุกจอพร้อมกัน (All Devices - {devices.length} จอ)</option>
                {devices.map((d, idx) => (
                  <option key={d.serial} value={d.serial}>
                    📱 {d.name || d.emu_name || `จอที่ ${idx + 1}`} ({d.serial}) {d.model ? `[${d.model}]` : ''}
                  </option>
                ))}
              </select>
            </div>

            {/* 2. Repeat Interval */}
            <div className="flex items-center justify-between p-2.5 rounded-xl bg-white border border-teal-200 shadow-2xs">
              <span className="font-bold text-slate-700">ทำซ้ำทุกๆ (นาที)</span>
              <div className="flex items-center gap-1.5">
                <input
                  type="number"
                  min={5}
                  max={1440}
                  value={cleanerInterval}
                  onChange={(e) => setCleanerInterval(Math.max(5, parseInt(e.target.value) || 30))}
                  className="w-20 px-2 py-1 text-center font-mono font-bold rounded-lg border border-teal-300 text-xs focus:ring-2 focus:ring-teal-500 outline-none"
                />
                <span className="text-slate-500 font-medium">นาที</span>
              </div>
            </div>

            {/* Buttons for Cleaner */}
            <div className="flex items-center gap-2 pt-1">
              <button
                onClick={handleStartCleaner}
                disabled={loading === 'cleaner_start' || cleanerStatus.is_running}
                className="flex-1 flex items-center justify-center gap-1.5 px-3.5 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-bold transition shadow-xs active:scale-95 disabled:opacity-50 cursor-pointer"
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>{loading === 'cleaner_start' ? 'กำลังเริ่ม...' : 'เริ่มวนลูป'}</span>
              </button>
              <button
                onClick={handleRunOnceCleaner}
                disabled={loading === 'cleaner_once'}
                className="flex items-center gap-1.5 px-3.5 py-2.5 rounded-xl bg-white hover:bg-slate-100 text-teal-800 font-bold border border-teal-200 transition active:scale-95 disabled:opacity-50 cursor-pointer"
                title="สั่งเข้าจัดการเพื่อนและลบทันที 1 รอบ"
              >
                <PlayCircle className="w-3.5 h-3.5 text-teal-600" />
                <span>ลบรอบเดียว</span>
              </button>
              <button
                onClick={handleStopCleaner}
                disabled={loading === 'cleaner_stop' || !cleanerStatus.is_running}
                className="px-4 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold transition active:scale-95 disabled:opacity-40 cursor-pointer flex items-center gap-1"
              >
                <Square className="w-3.5 h-3.5 fill-current" />
                <span>หยุด</span>
              </button>
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="pt-2 flex items-center justify-between border-t border-slate-100">
          <span className="text-[11px] text-slate-400">
            ระบบจะทำงานแยกเธรดในพื้นหลัง ไม่รบกวนหน้าต่างหลัก
          </span>
          <button
            onClick={onClose}
            className="px-5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs transition cursor-pointer"
          >
            ปิดหน้าต่าง
          </button>
        </div>
      </div>
    </div>
  );
};
