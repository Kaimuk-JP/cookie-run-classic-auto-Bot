import React, { useState, useEffect } from 'react';
import { X, Heart, UserMinus, Play, Square, PlayCircle, Clipboard, Smartphone, RefreshCw, Mail, Link, Zap, Clock } from 'lucide-react';
import { botApi } from '../../api/botApi';
import { Device } from '../../types/bot';
import { toast, confirmModal } from '../../context/ToastContext';

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
  }>({ running: false, rounds: 0, success_count: 0 });

  const [selectedCleanerDevice, setSelectedCleanerDevice] = useState<string>(deviceSerial || 'all');
  const [cleanerInterval, setCleanerInterval] = useState<number>(30);
  const [cleanerStatus, setCleanerStatus] = useState<{
    is_running: boolean;
    is_busy: boolean;
    current_device?: string | null;
    current_step?: string;
    next_run?: string | null;
    next_run_seconds?: number;
    target_devices?: string[];
    history?: any[];
  }>({ is_running: false, is_busy: false });

  const [loading, setLoading] = useState<string | null>(null);

  // Sync selected device when deviceSerial prop changes
  useEffect(() => {
    if (deviceSerial) {
      setSelectedFarmerDevice(deviceSerial);
      setSelectedCleanerDevice(deviceSerial);
    }
  }, [deviceSerial]);

  // Load defaults from first available device
  useEffect(() => {
    if (isOpen) {
      const dev = deviceSerial || devices[0]?.serial;
      if (dev) {
        botApi.getSettings(dev).then((s) => {
          if (s && s.heart_farmer_invite && s.heart_farmer_invite !== 'ใส่ลิงก์เชิญเพื่อนของคุณ') {
            setInviteUrl(s.heart_farmer_invite);
          }
        }).catch(() => {});
      }
      refreshStatus();
    }
  }, [isOpen, deviceSerial, devices]);

  // Polling status when open
  useEffect(() => {
    if (!isOpen) return;
    const t = setInterval(refreshStatus, 2000);
    return () => clearInterval(t);
  }, [isOpen, selectedFarmerDevice, selectedCleanerDevice]);

  const refreshStatus = async () => {
    try {
      const devList = await botApi.getDevices();
      // Farmer status
      const fDev = selectedFarmerDevice === 'all'
        ? devList.find((d: any) => d.heart_stats?.running) || devList[0]
        : devList.find((d: any) => d.serial === selectedFarmerDevice);

      if (fDev?.heart_stats) {
        setFarmerStatus({
          running: !!fDev.heart_stats.running,
          rounds: fDev.heart_stats.rounds || 0,
          success_count: fDev.heart_stats.success_count || 0,
          current_step: fDev.heart_stats.current_step || '',
        });
      }

      // Cleaner status
      const cleanerRes = await botApi.getCleanerStatus();
      if (cleanerRes) {
        setCleanerStatus(cleanerRes);
        if (cleanerRes.interval_minutes) {
          setCleanerInterval(cleanerRes.interval_minutes);
        }
      }
    } catch (e) {
      // ignore poll error
    }
  };

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
      const confirmRun = await confirmModal({
        title: 'ตรวจสอบลิงก์เชิญเพื่อน',
        message: 'คุณยังไม่ได้ใส่ลิงก์เชิญเพื่อนจริง (ยังเป็นข้อความดีฟอลต์) ต้องการดำเนินการต่อหรือไม่?',
        confirmText: 'ดำเนินการต่อ',
        type: 'warning',
      });
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

      toast.success(res.message || 'สั่งเริ่มระบบปั๊มหัวใจเรียบร้อยแล้ว');
      setFarmerStatus((prev) => ({ ...prev, running: true }));
    } catch (e: any) {
      toast.error('เริ่มไม่สำเร็จ: ' + e.message);
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
      toast.success(res.message || 'สั่งหยุดระบบปั๊มหัวใจทันทีเรียบร้อย');
    } catch {
      toast.success('สั่งหยุดระบบปั๊มหัวใจทันทีเรียบร้อยแล้ว');
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
      toast.success(res.message || 'สั่งเริ่มระบบลบเพื่อนเวล 1 เรียบร้อย');
      setCleanerStatus((prev) => ({
        ...prev,
        is_running: true,
        current_step: 'เริ่มวนลูปแล้ว กำลังเตรียมพร้อม...',
        current_device: targetDev || (targetDevs ? targetDevs[0] : null),
        target_devices: targetDevs || (targetDev ? [targetDev] : []),
      }));
    } catch (e: any) {
      toast.error('เริ่มไม่สำเร็จ: ' + e.message);
    } finally {
      setLoading(null);
    }
  };

  const handleStopCleaner = async () => {
    setLoading('cleaner_stop');
    try {
      const res = await botApi.stopFriendCleaner();
      toast.success(res.message || 'สั่งหยุดระบบลบเพื่อนเรียบร้อย');
      setCleanerStatus((prev) => ({
        ...prev,
        is_running: false,
        current_device: null,
        current_step: 'หยุดการทำงานเรียบร้อยแล้ว',
      }));
    } catch (e: any) {
      toast.error('หยุดไม่สำเร็จ: ' + e.message);
    } finally {
      setLoading(null);
    }
  };

  const handleRunOnceCleaner = async () => {
    const targetDev = selectedCleanerDevice !== 'all' ? selectedCleanerDevice : devices[0]?.serial;
    if (!targetDev) return toast.warning('กรุณาเลือกจอก่อน');

    setLoading('cleaner_once');
    setCleanerStatus((prev) => ({
      ...prev,
      current_device: targetDev,
      current_step: `กำลังเริ่มลบเพื่อนเวล 1 ทันทีบนจอ ${targetDev}...`,
    }));
    try {
      const res = await botApi.runOnceFriendCleaner(targetDev);
      toast.success(res.message || `ส่งคำสั่งลบเพื่อนเวล 1 บนจอ ${targetDev} เรียบร้อยแล้ว`);
    } catch (e: any) {
      toast.error('เริ่มไม่สำเร็จ: ' + e.message);
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
                เครื่องมือเสริม
              </h3>
              <p className="text-xs text-slate-500">
                ปั๊มหัวใจ & ลบเพื่อนอัตโนมัติ
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
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div className="flex items-center gap-2.5">
                <Heart className="w-5 h-5 text-pink-600 fill-pink-500 shrink-0" />
                <div>
                  <h4 className="font-bold text-slate-900 text-sm flex items-center gap-1.5 whitespace-nowrap">
                    ปั๊มหัวใจ
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-pink-500 text-white">NEW</span>
                  </h4>
                  <p className="text-[11px] text-slate-500">
                    วนลูปเชิญเพื่อนและรับของขวัญ
                  </p>
                </div>
              </div>

              {/* Status Badge */}
              <div className="flex items-center sm:justify-end">
                <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full font-bold text-[10px] border whitespace-nowrap ${
                  farmerStatus.running
                    ? 'bg-pink-100 text-pink-700 border-pink-200 shadow-2xs'
                    : 'bg-slate-100 text-slate-500 border-slate-200'
                }`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${farmerStatus.running ? 'bg-pink-500 animate-pulse' : 'bg-slate-400'}`}></span>
                  {farmerStatus.running
                    ? `กำลังปั๊ม (รอบ ${farmerStatus.rounds} • สำเร็จ ${farmerStatus.success_count})`
                    : 'ยังไม่เริ่ม'}
                </span>
              </div>
            </div>

            {/* 1. Device Selector for Farmer */}
            <div className="space-y-1">
              <label className="text-slate-700 font-bold flex items-center gap-1">
                <Smartphone className="w-3.5 h-3.5 text-pink-600" />
                <span>เลือก Emulator</span>
              </label>
              <select
                value={selectedFarmerDevice}
                onChange={(e) => setSelectedFarmerDevice(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-white border border-pink-200 text-xs font-semibold focus:ring-2 focus:ring-pink-500 outline-none text-slate-800 shadow-2xs"
              >
                <option value="all">ทุกจอ ({devices.length} จอ)</option>
                {devices.map((d, idx) => (
                  <option key={d.serial} value={d.serial}>
                    {d.name || d.emu_name || `จอ ${idx + 1}`} ({d.serial}) {d.model ? `[${d.model}]` : ''}
                  </option>
                ))}
              </select>
            </div>

            {/* 2. Invite URL Input for Farmer */}
            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <label className="text-slate-700 font-bold flex items-center gap-1.5">
                  <Link className="w-3.5 h-3.5 text-pink-600" />
                  <span>ลิงก์เชิญเพื่อน</span>
                </label>
                <button
                  type="button"
                  onClick={handlePasteInvite}
                  className="flex items-center gap-1 text-[11px] text-pink-600 hover:text-pink-700 font-bold hover:underline cursor-pointer"
                >
                  <Clipboard className="w-3 h-3" />
                  <span>วางจากคลิปบอร์ด</span>
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
                * คัดลอกลิงก์เชิญเพื่อนจากในเกม แล้วกดวางลิงก์
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
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div className="flex items-center gap-2.5">
                <Mail className="w-5 h-5 text-teal-600 shrink-0" />
                <div>
                  <h4 className="font-bold text-slate-900 text-sm flex items-center gap-1.5 whitespace-nowrap">
                    ลบเพื่อนเลิกเล่น
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-teal-600 text-white">AUTO</span>
                  </h4>
                  <p className="text-[11px] text-slate-500">
                    ลบเพื่อนเลิกเล่นหรือเพื่อนเวล 1
                  </p>
                </div>
              </div>

              {/* Status Badge */}
              <div className="flex items-center sm:justify-end">
                <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full font-bold text-[10px] border whitespace-nowrap ${
                  cleanerStatus.is_running
                    ? 'bg-teal-500/10 text-teal-700 border-teal-500/30'
                    : 'bg-slate-100 text-slate-500 border-slate-200'
                }`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${cleanerStatus.is_running ? 'bg-teal-500 animate-pulse' : 'bg-slate-400'}`}></span>
                  {cleanerStatus.is_running
                    ? (cleanerStatus.current_device ? `กำลังทำ: ${devices.find((d) => d.serial === cleanerStatus.current_device)?.name || cleanerStatus.current_device}` : 'กำลังทำงาน')
                    : 'ยังไม่เริ่ม'}
                </span>
              </div>
            </div>

            {/* Real-time Machine & Action Display Card */}
            {(cleanerStatus.is_running || cleanerStatus.current_step) && (
              <div className="p-3 rounded-xl bg-white border border-teal-200 shadow-2xs space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-bold text-slate-700 flex items-center gap-1.5">
                    <Smartphone className="w-3.5 h-3.5 text-teal-600" />
                    เครื่องที่ทำ:
                    <span className="text-teal-800 font-extrabold bg-teal-50 px-2 py-0.5 rounded-md border border-teal-200">
                      {devices.find((d) => d.serial === cleanerStatus.current_device)?.name
                        ? `${devices.find((d) => d.serial === cleanerStatus.current_device)?.name} (${cleanerStatus.current_device})`
                        : cleanerStatus.current_device || (cleanerStatus.target_devices && cleanerStatus.target_devices.length > 0 ? cleanerStatus.target_devices.join(', ') : 'ทุกจอ')}
                    </span>
                  </span>
                  {cleanerStatus.next_run && (
                    <span className="text-[10px] text-slate-500 font-mono flex items-center gap-1">
                      <Clock className="w-3 h-3 text-teal-600" />
                      <span>รอบถัดไป: <b className="text-teal-700">{cleanerStatus.next_run}</b></span>
                    </span>
                  )}
                </div>

                {cleanerStatus.current_step && (
                  <div className="p-2 rounded-lg bg-teal-50/70 border border-teal-100 flex items-start gap-2">
                    <span className="w-2 h-2 rounded-full bg-teal-500 mt-1 shrink-0 animate-pulse"></span>
                    <div className="flex-1">
                      <p className="text-[10px] font-bold text-teal-800">สถานะปัจจุบัน:</p>
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
                      ลบสำเร็จ {cleanerStatus.history[cleanerStatus.history.length - 1].ticked ?? 0} คน
                    </span>
                  </div>
                )}
              </div>
            )}

            {/* 1. Device Selector for Cleaner */}
            <div className="space-y-1">
              <label className="text-slate-700 font-bold flex items-center gap-1">
                <Smartphone className="w-3.5 h-3.5 text-teal-600" />
                <span>เลือก Emulator</span>
              </label>
              <select
                value={selectedCleanerDevice}
                onChange={(e) => setSelectedCleanerDevice(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-white border border-teal-200 text-xs font-semibold focus:ring-2 focus:ring-teal-500 outline-none text-slate-800 shadow-2xs"
              >
                <option value="all">ทุกจอ ({devices.length} จอ)</option>
                {devices.map((d, idx) => (
                  <option key={d.serial} value={d.serial}>
                    {d.name || d.emu_name || `จอ ${idx + 1}`} ({d.serial}) {d.model ? `[${d.model}]` : ''}
                  </option>
                ))}
              </select>
            </div>

            {/* 2. Repeat Interval */}
            <div className="flex items-center justify-between p-2.5 rounded-xl bg-white border border-teal-200 shadow-2xs">
              <span className="font-bold text-slate-700">ทำซ้ำทุก (นาที)</span>
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
            <div className="flex flex-wrap items-center gap-2 pt-1">
              <button
                onClick={handleStartCleaner}
                disabled={loading === 'cleaner_start' || cleanerStatus.is_running}
                className="flex-1 min-w-[120px] flex items-center justify-center gap-1.5 px-3.5 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-bold transition shadow-xs active:scale-95 disabled:opacity-50 cursor-pointer whitespace-nowrap text-xs"
              >
                <Play className="w-3.5 h-3.5 fill-current shrink-0" />
                <span>{loading === 'cleaner_start' ? 'กำลังเริ่ม...' : 'เริ่มวนลูป'}</span>
              </button>
              <button
                onClick={handleRunOnceCleaner}
                disabled={loading === 'cleaner_once'}
                className="flex-1 min-w-[110px] flex items-center justify-center gap-1.5 px-3.5 py-2.5 rounded-xl bg-white hover:bg-slate-100 text-teal-800 font-bold border border-teal-200 transition active:scale-95 disabled:opacity-50 cursor-pointer whitespace-nowrap text-xs"
                title="ลบทันที 1 รอบ"
              >
                <PlayCircle className="w-3.5 h-3.5 text-teal-600 shrink-0" />
                <span>ลบรอบเดียว</span>
              </button>
              <button
                onClick={handleStopCleaner}
                disabled={loading === 'cleaner_stop' || !cleanerStatus.is_running}
                className="px-4 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold transition active:scale-95 disabled:opacity-40 cursor-pointer flex items-center justify-center gap-1 whitespace-nowrap text-xs shrink-0"
              >
                <Square className="w-3.5 h-3.5 fill-current shrink-0" />
                <span>หยุด</span>
              </button>
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="pt-2 flex items-center justify-between border-t border-slate-100">
          <span className="text-[11px] text-slate-400">
            ทำงานเบื้องหลัง ไม่รบกวนหน้าต่างหลัก
          </span>
          <button
            onClick={onClose}
            className="px-5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs transition cursor-pointer"
          >
            ปิด
          </button>
        </div>
      </div>
    </div>
  );
};
