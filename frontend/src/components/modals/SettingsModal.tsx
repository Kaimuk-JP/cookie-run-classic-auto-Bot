import React, { useState, useEffect } from 'react';
import { X, Settings, Save, AlertCircle } from 'lucide-react';
import { BotSettings } from '../../types/bot';
import { botApi } from '../../api/botApi';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  deviceSerial: string;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  deviceSerial,
}) => {
  const [settings, setSettings] = useState<BotSettings | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (isOpen && deviceSerial) {
      botApi.getSettings(deviceSerial).then(setSettings).catch(console.error);
    }
  }, [isOpen, deviceSerial]);

  if (!isOpen || !settings) return null;

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const res = await botApi.saveSettings(deviceSerial, settings);
      alert(res.message || 'บันทึกการตั้งค่าเรียบร้อย');
      onClose();
    } catch (err: any) {
      alert('บันทึกไม่สำเร็จ: ' + err.message);
    } finally {
      setIsSaving(false);
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
                บันทึกแยกอิสระตาม Emulator: {deviceSerial}
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

        {/* Form Body */}
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

        {/* Footer Actions */}
        <div className="flex items-center justify-end gap-2 pt-3 border-t border-purple-100">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs transition"
          >
            ยกเลิก
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="flex items-center gap-1.5 px-5 py-2 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-bold text-xs shadow-btn transition active:scale-95 disabled:opacity-50"
          >
            <Save className="w-3.5 h-3.5" />
            <span>{isSaving ? 'กำลังบันทึก...' : 'บันทึกการตั้งค่า'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
