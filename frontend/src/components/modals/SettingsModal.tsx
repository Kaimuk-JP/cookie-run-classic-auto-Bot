import React, { useState, useEffect, useRef } from 'react';
import {
  X,
  Settings,
  Save,
  RotateCcw,
  Loader2,
  Activity,
  ChevronsUp,
  ChevronsDown,
  Zap,
  Target,
  ChevronDown,
  Check,
  Sparkles,
  Clock,
  Bell,
  Package,
} from 'lucide-react';
import { BotSettings } from '../../types/bot';
import { botApi } from '../../api/botApi';
import { toast, confirmModal } from '../../context/ToastContext';

interface RandomBoostOption {
  id: string;
  label: string;
  desc: string;
  tag?: string;
  icon: string;
  color: string;
}

const RANDOM_BOOST_OPTIONS: RandomBoostOption[] = [
  { id: 'double_coins', label: 'เหรียญ x2', desc: 'ฟาร์มเหรียญคุ้มค่าที่สุด', tag: 'แนะนำ', icon: '🪙', color: 'from-amber-400 to-yellow-500' },
  { id: 'coin_magic', label: 'เหรียญทองเวทมนตร์', desc: 'เปลี่ยนเยลลี่หมีเป็นเหรียญทอง', tag: 'ฟาร์มเหรียญ', icon: '✨', color: 'from-yellow-400 to-amber-500' },
  { id: 'score_15', label: 'คะแนน +15%', desc: 'เพิ่มคะแนนรวมหลังจบเกม', tag: 'สายคะแนน', icon: '🏆', color: 'from-orange-400 to-amber-500' },
  { id: 'hp_drain_15', label: 'เลือดลดช้าลง 15%', desc: 'วิ่งได้ไกลขึ้น เลือดลดช้า', tag: 'ยอดนิยม', icon: '💖', color: 'from-rose-400 to-pink-500' },
  { id: 'revive_80', label: 'ฟื้นคืนชีพ (80 HP)', desc: 'ชุบชีวิตเมื่อเลือดหมด 1 ครั้ง', tag: 'ชุบชีวิต', icon: '🕊️', color: 'from-emerald-400 to-teal-500' },
  { id: 'crush_70', label: 'ชนทำลาย 70%', desc: 'โอกาสทำลายสิ่งกีดขวางเมื่อชน', tag: 'ป้องกัน', icon: '💥', color: 'from-red-400 to-rose-500' },
  { id: 'speed_17', label: 'ความเร็ว +17%', desc: 'วิ่งเร็วขึ้น จบรอบไว', tag: 'ความเร็ว', icon: '⚡', color: 'from-sky-400 to-blue-500' },
  { id: 'damage_30', label: 'ลดดาเมจชน 30%', desc: 'ลดความเสียหายจากการชน', tag: 'ป้องกัน', icon: '🛡️', color: 'from-indigo-400 to-blue-500' },
  { id: 'potions_20', label: 'ขวดยาเลือด +20%', desc: 'เพิ่มประสิทธิภาพขวดยาฟื้นเลือด', tag: 'ฟื้นฟู', icon: '🧪', color: 'from-teal-400 to-emerald-500' },
  { id: 'magnetic', label: 'แม่เหล็กดูดเหรียญ', desc: 'ดึงดูดเหรียญและเยลลี่เข้าหาตัว', tag: 'ดูดไอเทม', icon: '🧲', color: 'from-purple-400 to-violet-500' },
  { id: 'pit_lifts_2', label: 'ช่วยตกเหว 2 ครั้ง', desc: 'ดึงขึ้นจากเหวเมื่อตก 2 ครั้ง', tag: 'ช่วยชีวิต', icon: '🪂', color: 'from-cyan-400 to-teal-500' },
];

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  deviceSerial?: string;
  onOpenDiscord?: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  deviceSerial = '',
  onOpenDiscord,
}) => {
  const [settings, setSettings] = useState<BotSettings | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const [isBoostDropdownOpen, setIsBoostDropdownOpen] = useState(false);
  const boostDropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (boostDropdownRef.current && !boostDropdownRef.current.contains(e.target as Node)) {
        setIsBoostDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    if (isOpen) {
      setIsLoading(true);
      botApi
        .getSettings(deviceSerial)
        .then((data) => setSettings(data))
        .catch((err) => {
          console.error('Failed to load settings:', err);
          toast.error('โหลดการตั้งค่าไม่สำเร็จ: ' + err.message);
        })
        .finally(() => setIsLoading(false));
    }
  }, [isOpen, deviceSerial]);

  if (!isOpen) return null;

  const handleSave = async () => {
    if (!settings) return;
    setIsSaving(true);
    try {
      const res = await botApi.saveSettings(deviceSerial, settings);
      toast.success(res.message || 'บันทึกการตั้งค่าเรียบร้อยแล้ว');
      onClose();
    } catch (err: any) {
      toast.error('บันทึกไม่สำเร็จ: ' + err.message);
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = async () => {
    const ok = await confirmModal({
      title: 'รีเซ็ตการตั้งค่า',
      message: 'คุณต้องการรีเซ็ตการตั้งค่าทั้งหมดกลับเป็นค่าเริ่มต้นดั้งเดิมหรือไม่?',
      confirmText: 'รีเซ็ตค่าเริ่มต้น',
      type: 'warning',
    });
    if (!ok) return;

    setIsResetting(true);
    try {
      const res = await botApi.resetSettings(deviceSerial);
      if (res.settings) {
        setSettings(res.settings);
      }
      toast.success('รีเซ็ตการตั้งค่าเป็นค่าเริ่มต้นเรียบร้อยแล้ว');
    } catch (err: any) {
      toast.error('รีเซ็ตไม่สำเร็จ: ' + err.message);
    } finally {
      setIsResetting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl max-w-xl w-full p-6 space-y-4 shadow-2xl border border-purple-100 max-h-[90vh] overflow-y-auto custom-scrollbar animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-purple-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-brand-50 text-brand-600 flex items-center justify-center text-xl border border-brand-100 shadow-xs">
              <Settings className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">
                ตั้งค่าบอท
              </h3>
              <p className="text-xs text-slate-500">
                {deviceSerial ? `จอ: ${deviceSerial}` : 'ค่าเริ่มต้นส่วนกลาง'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-slate-100 hover:bg-slate-200 flex items-center justify-center text-slate-600 font-bold transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {isLoading || !settings ? (
          <div className="py-16 flex flex-col items-center justify-center gap-3 text-slate-400">
            <Loader2 className="w-8 h-8 animate-spin text-brand-500" />
            <span className="text-xs font-medium">กำลังโหลด...</span>
          </div>
        ) : (
          /* Form Body */
          <div className="space-y-4 text-xs">
          {/* ADB Host & Port */}
          <div className="grid grid-cols-2 gap-3 p-3 bg-slate-50 rounded-2xl border border-slate-200/70">
            <div>
              <label className="font-bold text-slate-700 block mb-1">IP เครื่อง</label>
              <input
                type="text"
                value={settings.device_ip}
                onChange={(e) => setSettings({ ...settings, device_ip: e.target.value })}
                className="w-full px-3 py-2 rounded-xl bg-white border border-slate-200 font-mono text-xs focus:ring-2 focus:ring-brand-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="font-bold text-slate-700 block mb-1">พอร์ต ADB</label>
              <input
                type="number"
                value={settings.device_port}
                onChange={(e) => setSettings({ ...settings, device_port: parseInt(e.target.value) || 5555 })}
                className="w-full px-3 py-2 rounded-xl bg-white border border-slate-200 font-mono text-xs focus:ring-2 focus:ring-brand-500 focus:outline-none"
              />
            </div>
          </div>

          {/* Core In-Game Boosts */}
          <div className="space-y-2">
            <h4 className="font-bold text-slate-900">ไอเทมและบูสต์</h4>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              <label className="flex items-center gap-2 p-2.5 rounded-xl border border-slate-200 hover:bg-slate-50 cursor-pointer transition select-none">
                <input
                  type="checkbox"
                  checked={settings.use_hp_boost}
                  onChange={(e) => setSettings({ ...settings, use_hp_boost: e.target.checked })}
                  className="rounded text-brand-600 focus:ring-0"
                />
                <div>
                  <span className="font-semibold text-slate-800 block">HP Boost</span>
                  <span className="text-[10px] text-slate-400">เพิ่มเลือดตัวละคร</span>
                </div>
              </label>

              <label className="flex items-center gap-2 p-2.5 rounded-xl border border-slate-200 hover:bg-slate-50 cursor-pointer transition select-none">
                <input
                  type="checkbox"
                  checked={settings.use_item_extension}
                  onChange={(e) => setSettings({ ...settings, use_item_extension: e.target.checked })}
                  className="rounded text-brand-600 focus:ring-0"
                />
                <div>
                  <span className="font-semibold text-slate-800 block">Item Extension</span>
                  <span className="text-[10px] text-slate-400">ยืดเวลาไอเทม</span>
                </div>
              </label>

              <label className="flex items-center gap-2 p-2.5 rounded-xl border border-slate-200 hover:bg-slate-50 cursor-pointer transition select-none">
                <input
                  type="checkbox"
                  checked={settings.use_double_xp}
                  onChange={(e) => setSettings({ ...settings, use_double_xp: e.target.checked })}
                  className="rounded text-brand-600 focus:ring-0"
                />
                <div>
                  <span className="font-semibold text-slate-800 block">Double EXP</span>
                  <span className="text-[10px] text-slate-400">EXP x2</span>
                </div>
              </label>

              <label className="flex items-center gap-2 p-2.5 rounded-xl border border-slate-200 hover:bg-slate-50 cursor-pointer transition select-none">
                <input
                  type="checkbox"
                  checked={settings.detect_relic}
                  onChange={(e) => setSettings({ ...settings, detect_relic: e.target.checked })}
                  className="rounded text-brand-600 focus:ring-0"
                />
                <div>
                  <span className="font-semibold text-slate-800 block">ชิ้นส่วนโบราณ</span>
                  <span className="text-[10px] text-slate-400">เก็บวัตถุโบราณอัตโนมัติ</span>
                </div>
              </label>

              <label className="flex items-center gap-2 p-2.5 rounded-xl border border-slate-200 hover:bg-slate-50 cursor-pointer transition select-none">
                <input
                  type="checkbox"
                  checked={settings.send_friend_lives}
                  onChange={(e) => setSettings({ ...settings, send_friend_lives: e.target.checked })}
                  className="rounded text-brand-600 focus:ring-0"
                />
                <div>
                  <span className="font-semibold text-slate-800 block">ส่งหัวใจเพื่อน</span>
                  <span className="text-[10px] text-slate-400">ส่งก่อนเริ่มรอบ</span>
                </div>
              </label>
            </div>
          </div>

          {/* Auto Jump / Slide Action */}
          <div className="space-y-3 p-3.5 bg-gradient-to-br from-emerald-50/70 via-white to-teal-50/50 rounded-2xl border border-emerald-200 shadow-2xs">
            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={settings.auto_action_enabled ?? false}
                  onChange={(e) => setSettings({ ...settings, auto_action_enabled: e.target.checked })}
                  className="rounded text-emerald-600 focus:ring-0"
                />
                <span className="font-bold text-slate-800 text-xs flex items-center gap-1.5">
                  <Activity className="w-4 h-4 text-emerald-600" />
                  <span>กระโดด / สไลด์ อัตโนมัติ</span>
                </span>
              </label>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border transition ${
                settings.auto_action_enabled
                  ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
                  : 'bg-slate-100 text-slate-500 border-slate-200'
              }`}>
                {settings.auto_action_enabled ? 'เปิดใช้งาน' : 'ปิดอยู่'}
              </span>
            </div>

            <div className={`space-y-2.5 pt-1 transition-opacity ${settings.auto_action_enabled ? 'opacity-100' : 'opacity-40 pointer-events-none'}`}>
              <div>
                <label className="text-[11px] font-semibold text-slate-700 block mb-1.5">
                  รูปแบบแอ็กชัน:
                </label>
                <div className="grid grid-cols-3 gap-2">
                  <button
                    type="button"
                    onClick={() => setSettings({ ...settings, auto_action_mode: 'jump_only' })}
                    className={`py-2 px-2 rounded-xl border text-center transition font-semibold text-xs flex flex-col items-center gap-1 cursor-pointer ${
                      (settings.auto_action_mode ?? 'both') === 'jump_only'
                        ? 'bg-emerald-600 text-white border-emerald-600 shadow-xs ring-2 ring-emerald-300'
                        : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
                    }`}
                  >
                    <ChevronsUp className="w-5 h-5" />
                    <span className="text-[11px]">กระโดดเท่านั้น</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setSettings({ ...settings, auto_action_mode: 'slide_only' })}
                    className={`py-2 px-2 rounded-xl border text-center transition font-semibold text-xs flex flex-col items-center gap-1 cursor-pointer ${
                      settings.auto_action_mode === 'slide_only'
                        ? 'bg-emerald-600 text-white border-emerald-600 shadow-xs ring-2 ring-emerald-300'
                        : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
                    }`}
                  >
                    <ChevronsDown className="w-5 h-5" />
                    <span className="text-[11px]">สไลด์เท่านั้น</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setSettings({ ...settings, auto_action_mode: 'both' })}
                    className={`py-2 px-2 rounded-xl border text-center transition font-semibold text-xs flex flex-col items-center gap-1 cursor-pointer ${
                      (settings.auto_action_mode ?? 'both') === 'both'
                        ? 'bg-emerald-600 text-white border-emerald-600 shadow-xs ring-2 ring-emerald-300'
                        : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
                    }`}
                  >
                    <Zap className="w-5 h-5" />
                    <span className="text-[11px]">กระโดด + สไลด์</span>
                  </button>
                </div>
              </div>

              <div className="flex items-center justify-between p-2.5 bg-white/90 rounded-xl border border-emerald-100">
                <div>
                  <label className="font-semibold text-slate-800 text-[11px] block">
                    ระยะห่างแอ็กชัน (วินาที)
                  </label>
                  <span className="text-[10px] text-slate-400">
                    ความถี่ระหว่างการกด เช่น ทุก 1.5 วิ
                  </span>
                </div>
                <div className="flex items-center gap-1.5">
                  <input
                    type="number"
                    step="0.1"
                    min="0.3"
                    max="10.0"
                    value={settings.auto_action_interval ?? 1.5}
                    onChange={(e) => setSettings({ ...settings, auto_action_interval: parseFloat(e.target.value) || 1.5 })}
                    className="w-20 px-2.5 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-center font-mono font-bold text-xs focus:bg-white focus:ring-2 focus:ring-emerald-500 outline-none"
                  />
                  <span className="text-xs font-semibold text-slate-600">วิ</span>
                </div>
              </div>
            </div>
          </div>

          {/* Random Boost Option */}
          <div className="space-y-2.5 p-3.5 bg-gradient-to-br from-amber-50/60 via-white to-yellow-50/40 rounded-2xl border border-amber-200">
            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={settings.use_desired_random_boost}
                  onChange={(e) => setSettings({ ...settings, use_desired_random_boost: e.target.checked })}
                  className="rounded text-amber-600 focus:ring-0"
                />
                <span className="font-bold text-slate-800 text-xs flex items-center gap-1.5">
                  <Target className="w-4 h-4 text-amber-600" />
                  <span>สุ่มบูสต์ที่ต้องการ</span>
                </span>
              </label>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 border border-amber-200">
                สุ่มอัตโนมัติ
              </span>
            </div>

            <div className="pt-1">
              <label className="text-[11px] font-semibold text-slate-600 block mb-1.5">
                เลือกบูสต์ที่ต้องการสุ่ม:
              </label>

              {/* Custom Sweet Candy Dropdown */}
              <div ref={boostDropdownRef} className="relative">
                {(() => {
                  const selectedBoost =
                    RANDOM_BOOST_OPTIONS.find((b) => b.id === (settings.desired_boost_id || 'double_coins')) ||
                    RANDOM_BOOST_OPTIONS[0];

                  return (
                    <>
                      <button
                        type="button"
                        disabled={!settings.use_desired_random_boost}
                        onClick={() => setIsBoostDropdownOpen((prev) => !prev)}
                        className={`w-full px-3 py-2.5 rounded-2xl bg-white border-2 text-left transition-all flex items-center justify-between shadow-xs cursor-pointer ${
                          !settings.use_desired_random_boost
                            ? 'opacity-50 cursor-not-allowed bg-slate-50 border-slate-200'
                            : isBoostDropdownOpen
                            ? 'border-[#F59E0B] ring-2 ring-[#F59E0B]/20 shadow-md'
                            : 'border-[#EEDBCE] hover:border-[#D4A373]'
                        }`}
                      >
                        <div className="truncate">
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-xs text-[#452311]">
                              {selectedBoost.label}
                            </span>
                            {selectedBoost.tag && (
                              <span className="text-[9px] px-1.5 py-0.2 rounded-full bg-amber-100 text-amber-800 font-bold border border-amber-200">
                                {selectedBoost.tag}
                              </span>
                            )}
                          </div>
                          <p className="text-[10px] text-[#8C6D58] truncate mt-0.5">
                            {selectedBoost.desc}
                          </p>
                        </div>
                        <ChevronDown
                          className={`w-4 h-4 text-[#D97706] shrink-0 transition-transform duration-200 ${
                            isBoostDropdownOpen ? 'rotate-180' : ''
                          }`}
                        />
                      </button>

                      {/* Custom Dropdown Menu with sweet items */}
                      {isBoostDropdownOpen && settings.use_desired_random_boost && (
                        <div className="absolute left-0 right-0 top-full mt-1.5 z-50 bg-[#FFFDF6] border-2 border-[#EEDBCE] rounded-2xl shadow-xl max-h-64 overflow-y-auto custom-scrollbar p-1.5 space-y-1 animate-fadeIn">
                          {RANDOM_BOOST_OPTIONS.map((opt) => {
                            const isSelected = opt.id === (settings.desired_boost_id || 'double_coins');
                            return (
                              <button
                                key={opt.id}
                                type="button"
                                onClick={() => {
                                  setSettings({ ...settings, desired_boost_id: opt.id });
                                  setIsBoostDropdownOpen(false);
                                }}
                                className={`w-full px-3 py-2 rounded-xl text-left transition-all flex items-center justify-between gap-2 cursor-pointer ${
                                  isSelected
                                    ? 'bg-[#FFF3DF] border-2 border-[#F59E0B] shadow-2xs text-[#452311]'
                                    : 'hover:bg-[#FFF8EC] hover:border-[#F0DFCE] border-2 border-transparent text-[#6B4226]'
                                }`}
                              >
                                <div className="truncate">
                                  <div className="flex items-center gap-2">
                                    <span
                                      className={`text-xs ${
                                        isSelected ? 'font-bold text-[#B45309]' : 'font-semibold text-[#452311]'
                                      }`}
                                    >
                                      {opt.label}
                                    </span>
                                    {opt.tag && (
                                      <span className="text-[9px] px-1.5 py-0.2 rounded-full bg-amber-100/80 text-amber-800 border border-amber-200 font-bold">
                                        {opt.tag}
                                      </span>
                                    )}
                                  </div>
                                  <p className="text-[10px] text-[#8C6D58] truncate mt-0.5">
                                    {opt.desc}
                                  </p>
                                </div>
                                {isSelected && (
                                  <span className="w-5 h-5 rounded-full bg-[#F59E0B] text-white flex items-center justify-center shrink-0 shadow-2xs">
                                    <Check className="w-3 h-3 stroke-[3]" />
                                  </span>
                                )}
                              </button>
                            );
                          })}
                        </div>
                      )}
                    </>
                  );
                })()}
              </div>

              <p className="text-[10px] text-[#8C6D58] mt-1.5">
                * สุ่มบูสต์ก่อนเริ่มเกมจนกว่าจะได้ตามที่เลือก
              </p>
            </div>
          </div>

          {/* Item Purchasing & Stock Thresholds */}
          <div className="space-y-3 p-3.5 bg-gradient-to-br from-purple-50/70 via-white to-pink-50/40 rounded-2xl border border-purple-200 shadow-2xs">
            <h4 className="font-bold text-[#452311] text-xs flex items-center gap-1.5">
              <Sparkles className="w-4 h-4 text-purple-600" />
              <span>ซื้อไอเทมอัตโนมัติ & สต็อกขั้นต่ำ</span>
            </h4>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="p-2.5 rounded-xl bg-white/90 border border-purple-100 space-y-2">
                <label className="flex items-center gap-2 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={settings.use_fast_start}
                    onChange={(e) => setSettings({ ...settings, use_fast_start: e.target.checked })}
                    className="rounded text-purple-600 focus:ring-0"
                  />
                  <div>
                    <span className="font-bold text-xs text-[#452311] block">Fast Start</span>
                    <span className="text-[10px] text-[#8C6D58]">วิ่งเร็วช่วงต้นเกม</span>
                  </div>
                </label>
                <div className="flex items-center justify-between pt-1 border-t border-purple-50">
                  <span className="text-[11px] text-[#6B4226] font-medium">สต็อกขั้นต่ำ:</span>
                  <div className="flex items-center gap-1">
                    <input
                      type="number"
                      value={settings.fast_start_min_stock}
                      onChange={(e) => setSettings({ ...settings, fast_start_min_stock: parseInt(e.target.value) || 0 })}
                      className="w-16 px-2 py-1 rounded-lg bg-[#FFFDF6] border border-purple-200 text-center font-mono font-bold text-xs text-[#452311] focus:bg-white focus:ring-2 focus:ring-purple-400 outline-none"
                    />
                    <span className="text-[10px] text-[#8C6D58]">ชิ้น</span>
                  </div>
                </div>
              </div>

              <div className="p-2.5 rounded-xl bg-white/90 border border-purple-100 space-y-2">
                <label className="flex items-center gap-2 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={settings.use_cookie_relay}
                    onChange={(e) => setSettings({ ...settings, use_cookie_relay: e.target.checked })}
                    className="rounded text-purple-600 focus:ring-0"
                  />
                  <div>
                    <span className="font-bold text-xs text-[#452311] block">Cookie Relay</span>
                    <span className="text-[10px] text-[#8C6D58]">ผลัดคุกกี้ตัวที่ 2</span>
                  </div>
                </label>
                <div className="flex items-center justify-between pt-1 border-t border-purple-50">
                  <span className="text-[11px] text-[#6B4226] font-medium">สต็อกขั้นต่ำ:</span>
                  <div className="flex items-center gap-1">
                    <input
                      type="number"
                      value={settings.cookie_relay_min_stock}
                      onChange={(e) => setSettings({ ...settings, cookie_relay_min_stock: parseInt(e.target.value) || 0 })}
                      className="w-16 px-2 py-1 rounded-lg bg-[#FFFDF6] border border-purple-200 text-center font-mono font-bold text-xs text-[#452311] focus:bg-white focus:ring-2 focus:ring-purple-400 outline-none"
                    />
                    <span className="text-[10px] text-[#8C6D58]">ชิ้น</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Mystery Box Early Exit Farming */}
          <div className="space-y-3 p-3.5 bg-gradient-to-br from-amber-50/80 via-white to-yellow-50/50 rounded-2xl border border-amber-300 shadow-2xs">
            <div className="flex items-center justify-between">
              <h4 className="font-bold text-[#452311] text-xs flex items-center gap-1.5">
                <Package className="w-4 h-4 text-amber-600" />
                <span>ฟาร์มกล่องปริศนา: ออกจากห้องเมื่อได้กล่องครบ</span>
              </h4>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 font-bold border border-amber-200">
                Fast Farm
              </span>
            </div>

            <div className="p-2.5 rounded-xl bg-white/90 border border-amber-200 space-y-2.5">
              <label className="flex items-center gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={settings.early_exit_boxes_enabled ?? true}
                  onChange={(e) => setSettings({ ...settings, early_exit_boxes_enabled: e.target.checked })}
                  className="rounded text-amber-600 focus:ring-0"
                />
                <div>
                  <span className="font-bold text-xs text-[#452311] block">กด Pause ออกจากห้องทันทีเมื่อเก็บกล่องครบ</span>
                  <span className="text-[10px] text-[#8C6D58]">
                    เมื่อเก็บกล่องในรอบวิ่งครบ บอทจะกด Pause แล้วกดออกจากห้องทันทีเพื่อเริ่มรอบใหม่ (ไม่ต้องรอวิ่งจนหมดแรง)
                  </span>
                </div>
              </label>

              {(settings.early_exit_boxes_enabled ?? true) && (
                <div className="flex items-center justify-between pt-2 border-t border-amber-100">
                  <span className="text-[11px] text-[#6B4226] font-medium">จำนวนกล่องที่ต้องการก่อนกดออก:</span>
                  <div className="flex items-center gap-1.5">
                    <select
                      value={settings.early_exit_boxes_target ?? 2}
                      onChange={(e) => setSettings({ ...settings, early_exit_boxes_target: parseInt(e.target.value) || 2 })}
                      className="px-2.5 py-1 rounded-lg bg-[#FFFDF6] border border-amber-300 font-mono font-bold text-xs text-[#452311] focus:bg-white focus:ring-2 focus:ring-amber-400 outline-none"
                    >
                      <option value={1}>1 กล่อง</option>
                      <option value={2}>2 กล่อง (แนะนำ - สูงสุดต่อรอบ)</option>
                    </select>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Auto-Stop Goals */}
          <div className="space-y-3 p-3.5 bg-gradient-to-br from-amber-50/60 via-white to-orange-50/40 rounded-2xl border border-amber-200 shadow-2xs">
            <h4 className="font-bold text-[#452311] text-xs flex items-center gap-1.5">
              <Clock className="w-4 h-4 text-amber-600" />
              <span>หยุดบอทอัตโนมัติ (Auto-Stop Goals)</span>
            </h4>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="p-2.5 rounded-xl bg-white/90 border border-amber-100 space-y-2">
                <label className="flex items-center gap-2 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={settings.stop_goal_rounds_enabled}
                    onChange={(e) => setSettings({ ...settings, stop_goal_rounds_enabled: e.target.checked })}
                    className="rounded text-amber-600 focus:ring-0"
                  />
                  <div>
                    <span className="font-bold text-xs text-[#452311] block">หยุดตามรอบ</span>
                    <span className="text-[10px] text-[#8C6D58]">เมื่อครบตามเป้าหมาย</span>
                  </div>
                </label>
                <div className="flex items-center justify-between pt-1 border-t border-amber-50">
                  <span className="text-[11px] text-[#6B4226] font-medium">เป้าหมาย:</span>
                  <div className="flex items-center gap-1">
                    <input
                      type="number"
                      value={settings.stop_goal_rounds_target}
                      onChange={(e) => setSettings({ ...settings, stop_goal_rounds_target: parseInt(e.target.value) || 50 })}
                      className="w-16 px-2 py-1 rounded-lg bg-[#FFFDF6] border border-amber-200 text-center font-mono font-bold text-xs text-[#452311] focus:bg-white focus:ring-2 focus:ring-amber-400 outline-none"
                    />
                    <span className="text-[10px] text-[#8C6D58]">รอบ</span>
                  </div>
                </div>
              </div>

              <div className="p-2.5 rounded-xl bg-white/90 border border-amber-100 space-y-2">
                <label className="flex items-center gap-2 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={settings.stop_goal_time_enabled}
                    onChange={(e) => setSettings({ ...settings, stop_goal_time_enabled: e.target.checked })}
                    className="rounded text-amber-600 focus:ring-0"
                  />
                  <div>
                    <span className="font-bold text-xs text-[#452311] block">หยุดตามเวลา</span>
                    <span className="text-[10px] text-[#8C6D58]">เมื่อครบชั่วโมงที่ตั้ง</span>
                  </div>
                </label>
                <div className="flex items-center justify-between pt-1 border-t border-amber-50">
                  <span className="text-[11px] text-[#6B4226] font-medium">เป้าหมาย:</span>
                  <div className="flex items-center gap-1">
                    <input
                      type="number"
                      step="0.5"
                      value={settings.stop_goal_time_hours}
                      onChange={(e) => setSettings({ ...settings, stop_goal_time_hours: parseFloat(e.target.value) || 2.0 })}
                      className="w-16 px-2 py-1 rounded-lg bg-[#FFFDF6] border border-amber-200 text-center font-mono font-bold text-xs text-[#452311] focus:bg-white focus:ring-2 focus:ring-amber-400 outline-none"
                    />
                    <span className="text-[10px] text-[#8C6D58]">ชม.</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        )}

        {/* Footer Actions */}
        <div className="flex items-center justify-between pt-3 border-t border-purple-100">
          <div className="flex items-center gap-2">
            <button
              onClick={handleReset}
              disabled={isSaving || isResetting || !settings}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl border border-rose-200 bg-rose-50/50 hover:bg-rose-100 text-rose-700 font-bold text-xs transition active:scale-95 disabled:opacity-50 cursor-pointer"
              title="รีเซ็ตค่าเริ่มต้น"
            >
              <RotateCcw className={`w-3.5 h-3.5 ${isResetting ? 'animate-spin' : ''}`} />
              <span>{isResetting ? 'กำลังรีเซ็ต...' : 'รีเซ็ต'}</span>
            </button>

            {onOpenDiscord && (
              <button
                type="button"
                onClick={() => {
                  onClose();
                  onOpenDiscord();
                }}
                className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl border border-indigo-200 bg-indigo-50/70 hover:bg-indigo-100 text-indigo-700 font-bold text-xs transition active:scale-95 cursor-pointer"
                title="เปิดการตั้งค่า Discord Webhook"
              >
                <Bell className="w-3.5 h-3.5 text-indigo-600 fill-indigo-600/20" />
                <span>แจ้งเตือน Discord</span>
              </button>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs transition"
            >
              ยกเลิก
            </button>
            <button
              onClick={handleSave}
              disabled={isSaving || isResetting || !settings}
              className="flex items-center gap-1.5 px-5 py-2 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-bold text-xs shadow-btn transition active:scale-95 disabled:opacity-50"
            >
              {isSaving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
              <span>{isSaving ? 'กำลังบันทึก...' : 'บันทึก'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
