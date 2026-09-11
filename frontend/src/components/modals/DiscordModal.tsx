import React, { useState, useEffect } from 'react';
import { X, Bell, Send, Save } from 'lucide-react';
import { DiscordSettings } from '../../types/bot';
import { botApi } from '../../api/botApi';

interface DiscordModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const DiscordModal: React.FC<DiscordModalProps> = ({ isOpen, onClose }) => {
  const [settings, setSettings] = useState<DiscordSettings>({
    webhook_url: '',
    enabled: true,
    notify_boxes: true,
    notify_antibot: true,
    notify_status: true,
    attach_screenshot: true,
  });
  const [isSaving, setIsSaving] = useState(false);
  const [isTesting, setIsTesting] = useState(false);

  useEffect(() => {
    if (isOpen) {
      botApi.getDiscordSettings().then(setSettings).catch(console.error);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const res = await botApi.saveDiscordSettings(settings);
      alert(res.message || 'บันทึกการตั้งค่า Discord เรียบร้อย');
      onClose();
    } catch (e: any) {
      alert('บันทึกไม่สำเร็จ: ' + e.message);
    } finally {
      setIsSaving(false);
    }
  };

  const handleTest = async () => {
    if (!settings.webhook_url.trim()) return alert('กรุณาระบุ Webhook URL ก่อน');
    setIsTesting(true);
    try {
      const res = await botApi.testDiscordWebhook(settings.webhook_url.trim());
      alert(res.message || 'ส่งข้อความทดสอบสำเร็จ');
    } catch (e: any) {
      alert('ทดสอบไม่สำเร็จ: ' + e.message);
    } finally {
      setIsTesting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl max-w-lg w-full p-6 space-y-4 shadow-2xl border border-purple-100 animate-in fade-in zoom-in-95 duration-150">
        <div className="flex items-center justify-between pb-3 border-b border-purple-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center text-xl shadow-xs border border-indigo-100">
              <Bell className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">
                ตั้งค่าการแจ้งเตือน Discord
              </h3>
              <p className="text-xs text-slate-500">
                รับรายงานผล เหรียญ EXP และสกรีนช็อตผ่าน Discord Webhook
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

        <div className="space-y-3 text-xs">
          <div>
            <label className="font-bold text-slate-700 block mb-1">
              Discord Webhook URL
            </label>
            <input
              type="text"
              placeholder="https://discord.com/api/webhooks/..."
              value={settings.webhook_url}
              onChange={(e) => setSettings({ ...settings, webhook_url: e.target.value })}
              className="w-full px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 font-mono text-xs focus:ring-2 focus:ring-brand-500 focus:outline-none"
            />
          </div>

          <div className="space-y-2 pt-1">
            <label className="flex items-center gap-2 p-2.5 rounded-xl border border-slate-200 hover:bg-slate-50 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={settings.enabled}
                onChange={(e) => setSettings({ ...settings, enabled: e.target.checked })}
                className="rounded text-brand-600 focus:ring-0"
              />
              <span className="font-semibold text-slate-800">เปิดใช้งานการแจ้งเตือน</span>
            </label>

            <label className="flex items-center gap-2 p-2.5 rounded-xl border border-slate-200 hover:bg-slate-50 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={settings.notify_boxes}
                onChange={(e) => setSettings({ ...settings, notify_boxes: e.target.checked })}
                className="rounded text-brand-600 focus:ring-0"
              />
              <span className="font-semibold text-slate-800">แจ้งเตือนเมื่อเจอกล่องปริศนา</span>
            </label>

            <label className="flex items-center gap-2 p-2.5 rounded-xl border border-slate-200 hover:bg-slate-50 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={settings.attach_screenshot}
                onChange={(e) => setSettings({ ...settings, attach_screenshot: e.target.checked })}
                className="rounded text-brand-600 focus:ring-0"
              />
              <span className="font-semibold text-slate-800">แนบรูปภาพสกรีนช็อตสรุปคะแนน</span>
            </label>
          </div>
        </div>

        <div className="flex items-center justify-between pt-3 border-t border-purple-100">
          <button
            onClick={handleTest}
            disabled={isTesting}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs transition active:scale-95 disabled:opacity-50"
          >
            <Send className="w-3.5 h-3.5 text-indigo-600" />
            <span>{isTesting ? 'กำลังส่ง...' : 'ทดสอบส่งข้อความ'}</span>
          </button>

          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs transition"
            >
              ปิด
            </button>
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="flex items-center gap-1.5 px-5 py-2 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-bold text-xs shadow-btn transition active:scale-95 disabled:opacity-50"
            >
              <Save className="w-3.5 h-3.5" />
              <span>{isSaving ? 'กำลังบันทึก...' : 'บันทึก'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
