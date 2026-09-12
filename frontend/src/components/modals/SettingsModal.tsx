import React, { useState, useEffect } from 'react';
import { X, Settings, Save, RotateCcw, Loader2 } from 'lucide-react';
import { BotSettings } from '../../types/bot';
import { botApi } from '../../api/botApi';
import { toast, confirmModal } from '../../context/ToastContext';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  deviceSerial?: string;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  deviceSerial = '',
}) => {
  const [settings, setSettings] = useState<BotSettings | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isResetting, setIsResetting] = useState(false);

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
                ตั้งค่าการทำงานของบอท (Bot Settings)
              </h3>
              <p className="text-xs text-slate-500">
                {deviceSerial ? `บันทึกแยกอิสระตาม Emulator: ${deviceSerial}` : 'การตั้งค่าเริ่มต้นส่วนกลาง (Global Default)'}
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
            <span className="text-xs font-medium">กำลังโหลดการตั้งค่า...</span>
          </div>
        ) : (
          /* Form Body */
          <div className="space-y-4 text-xs">
          {/* ADB Host & Port */}
          <div className="grid grid-cols-2 gap-3 p-3 bg-slate-50 rounded-2xl border border-slate-200/70">
            <div>
              <label className="font-bold text-slate-700 block mb-1">Device IP</label>
              <input
                type="text"
                value={settings.device_ip}
                onChange={(e) => setSettings({ ...settings, device_ip: e.target.value })}
                className="w-full px-3 py-2 rounded-xl bg-white border border-slate-200 font-mono text-xs focus:ring-2 focus:ring-brand-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="font-bold text-slate-700 block mb-1">ADB Port</label>
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
            <h4 className="font-bold text-slate-900">ไอเทมและฟังก์ชันในเกม</h4>

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
                  <span className="text-[10px] text-slate-400">เพิ่มพลังชีวิตตัวละคร</span>
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
                  <span className="text-[10px] text-slate-400">ยืดระยะเวลาไอเทม</span>
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
                  <span className="text-[10px] text-slate-400">คูณสองค่าประสบการณ์</span>
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
                  <span className="font-semibold text-slate-800 block">ชิ้นส่วนวัตถุโบราณ</span>
                  <span className="text-[10px] text-slate-400">รับชิ้นส่วนโบราณอัตโนมัติ</span>
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
                  <span className="font-semibold text-slate-800 block">ส่งหัวใจให้เพื่อน</span>
                  <span className="text-[10px] text-slate-400">ส่งหัวใจอัตโนมัติก่อนเริ่มรอบ</span>
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
                  <span>🏃‍♂️</span>
                  <span>วิ่ง + กระโดด / สไลด์ อัตโนมัติ</span>
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
                  เลือกรูปแบบแอ็กชันที่ต้องการ:
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
                    <span className="text-base">🦘</span>
                    <span className="text-[11px]">กระโดดอย่างเดียว</span>
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
                    <span className="text-base">🛹</span>
                    <span className="text-[11px]">สไลด์อย่างเดียว</span>
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
                    <span className="text-base">⚡</span>
                    <span className="text-[11px]">กระโดด + สไลด์</span>
                  </button>
                </div>
              </div>

              <div className="flex items-center justify-between p-2.5 bg-white/90 rounded-xl border border-emerald-100">
                <div>
                  <label className="font-semibold text-slate-800 text-[11px] block">
                    เวลาหน่วงที่จะกระโดด/ทำแอ็กชัน (วินาที)
                  </label>
                  <span className="text-[10px] text-slate-400">
                    เว้นระยะเวลาระหว่างการกด เช่น ทุกๆ 1.5 วินาที
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
                <span className="font-bold text-slate-800 text-xs flex items-center gap-1">
                  <span>🎯</span>
                  <span>สุ่มบูสต์จนกว่าจะได้ที่ต้องการ (Random Boost)</span>
                </span>
              </label>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 border border-amber-200">
                สุ่มอัตโนมัติ
              </span>
            </div>

            <div className="pt-1">
              <label className="text-[11px] font-semibold text-slate-600 block mb-1">
                เลือกประเภทบูสต์ที่ต้องการ:
              </label>
              <select
                value={settings.desired_boost_id || 'double_coins'}
                onChange={(e) => setSettings({ ...settings, desired_boost_id: e.target.value })}
                disabled={!settings.use_desired_random_boost}
                className="w-full px-3 py-2.5 rounded-xl bg-white border border-amber-200 text-xs font-semibold text-slate-800 focus:ring-2 focus:ring-amber-500 outline-none shadow-2xs disabled:opacity-50 disabled:bg-slate-100"
              >
                <option value="double_coins">เหรียญ 2 เท่า (Double Coins 2x) ⭐ แนะนำ</option>
                <option value="coin_magic">เหรียญทองเวทมนตร์ (Gold Coin Magic)</option>
                <option value="score_15">คะแนนเพิ่ม 15% (+15% Score Bonus)</option>
                <option value="hp_drain_15">เลือดลดช้าลง 15% (-15% HP Drain)</option>
                <option value="revive_80">ฟื้นคืนชีพ 1 ครั้งด้วยเลือด 80 (Revive Once with 80HP)</option>
                <option value="crush_70">ชนทำลายสิ่งกีดขวาง 70% (70% Crush Chance)</option>
                <option value="speed_17">ความเร็วพื้นฐาน +17% (+17% Base Speed)</option>
                <option value="damage_30">ลดดาเมจชนสิ่งกีดขวาง 30% (-30% Collision Damage)</option>
                <option value="potions_20">ขวดยาเพิ่มเลือด +20% (+20% HP from Potions)</option>
                <option value="magnetic">ออร่าแม่เหล็กดูดเหรียญ (Magnetic Aura)</option>
                <option value="pit_lifts_2">ช่วยตกเหว 2 ครั้ง (2 Pit Lifts)</option>
              </select>
              <p className="text-[10px] text-slate-400 mt-1">
                * บอทจะกดสุ่มกล่องบูสต์ก่อนเริ่มเกมซ้ำๆ จนกว่าจะได้ผลลัพธ์ตรงกับที่เลือก
              </p>
            </div>
          </div>

          {/* Item Purchasing & Stock Thresholds */}
          <div className="space-y-2 p-3 bg-purple-50/50 rounded-2xl border border-purple-100">
            <h4 className="font-bold text-slate-900">ซื้อไอเทมช่วยเหลือ & จำนวนสต็อกขั้นต่ำ</h4>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="flex items-center gap-1.5 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={settings.use_fast_start}
                    onChange={(e) => setSettings({ ...settings, use_fast_start: e.target.checked })}
                    className="rounded text-brand-600 focus:ring-0"
                  />
                  <span className="font-semibold text-slate-800">Fast Start</span>
                </label>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-slate-500 shrink-0">สต็อกขั้นต่ำ:</span>
                  <input
                    type="number"
                    value={settings.fast_start_min_stock}
                    onChange={(e) => setSettings({ ...settings, fast_start_min_stock: parseInt(e.target.value) || 0 })}
                    className="w-16 px-2 py-1 rounded-lg bg-white border border-slate-200 text-center font-mono text-xs"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="flex items-center gap-1.5 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={settings.use_cookie_relay}
                    onChange={(e) => setSettings({ ...settings, use_cookie_relay: e.target.checked })}
                    className="rounded text-brand-600 focus:ring-0"
                  />
                  <span className="font-semibold text-slate-800">Cookie Relay</span>
                </label>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-slate-500 shrink-0">สต็อกขั้นต่ำ:</span>
                  <input
                    type="number"
                    value={settings.cookie_relay_min_stock}
                    onChange={(e) => setSettings({ ...settings, cookie_relay_min_stock: parseInt(e.target.value) || 0 })}
                    className="w-16 px-2 py-1 rounded-lg bg-white border border-slate-200 text-center font-mono text-xs"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Auto-Stop Goals */}
          <div className="space-y-2 p-3 bg-amber-50/50 rounded-2xl border border-amber-200/60">
            <h4 className="font-bold text-slate-900">เป้าหมายหยุดบอทอัตโนมัติ (Auto-Stop Goals)</h4>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="flex items-center gap-1.5 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={settings.stop_goal_rounds_enabled}
                    onChange={(e) => setSettings({ ...settings, stop_goal_rounds_enabled: e.target.checked })}
                    className="rounded text-brand-600 focus:ring-0"
                  />
                  <span className="font-semibold text-slate-800">หยุดตามจำนวนรอบ</span>
                </label>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-slate-500 shrink-0">เป้าหมาย:</span>
                  <input
                    type="number"
                    value={settings.stop_goal_rounds_target}
                    onChange={(e) => setSettings({ ...settings, stop_goal_rounds_target: parseInt(e.target.value) || 50 })}
                    className="w-16 px-2 py-1 rounded-lg bg-white border border-slate-200 text-center font-mono text-xs"
                  />
                  <span className="text-[10px] text-slate-500">รอบ</span>
                </div>
              </div>

              <div className="space-y-1">
                <label className="flex items-center gap-1.5 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={settings.stop_goal_time_enabled}
                    onChange={(e) => setSettings({ ...settings, stop_goal_time_enabled: e.target.checked })}
                    className="rounded text-brand-600 focus:ring-0"
                  />
                  <span className="font-semibold text-slate-800">หยุดตามเวลา</span>
                </label>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-slate-500 shrink-0">เป้าหมาย:</span>
                  <input
                    type="number"
                    step="0.5"
                    value={settings.stop_goal_time_hours}
                    onChange={(e) => setSettings({ ...settings, stop_goal_time_hours: parseFloat(e.target.value) || 2.0 })}
                    className="w-16 px-2 py-1 rounded-lg bg-white border border-slate-200 text-center font-mono text-xs"
                  />
                  <span className="text-[10px] text-slate-500">ชม.</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        )}

        {/* Footer Actions */}
        <div className="flex items-center justify-between pt-3 border-t border-purple-100">
          <button
            onClick={handleReset}
            disabled={isSaving || isResetting || !settings}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl border border-rose-200 bg-rose-50/50 hover:bg-rose-100 text-rose-700 font-bold text-xs transition active:scale-95 disabled:opacity-50"
            title="รีเซ็ตการตั้งค่าเป็นค่าเริ่มต้นดั้งเดิม"
          >
            <RotateCcw className={`w-3.5 h-3.5 ${isResetting ? 'animate-spin' : ''}`} />
            <span>{isResetting ? 'กำลังรีเซ็ต...' : 'รีเซ็ตค่าเริ่มต้น'}</span>
          </button>

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
              <span>{isSaving ? 'กำลังบันทึก...' : 'บันทึกการตั้งค่า'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
