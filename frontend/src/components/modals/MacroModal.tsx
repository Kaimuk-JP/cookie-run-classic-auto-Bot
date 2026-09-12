import React, { useState, useEffect, useRef } from 'react';
import { 
  Sparkles, 
  X, 
  Play, 
  Square, 
  Plus, 
  Trash2, 
  Save, 
  RotateCcw, 
  Clock, 
  Zap, 
  ChevronRight, 
  Sliders, 
  Check, 
  HelpCircle,
  FileCode,
  Radio,
  Gamepad2,
  RefreshCw,
  Circle,
  Rocket,
  ChevronsUp,
  ChevronsDown
} from 'lucide-react';
import { botApi } from '../../api/botApi';
import { MacroProfile, MacroAction } from '../../types/bot';
import { toast, confirmModal } from '../../context/ToastContext';

interface MacroModalProps {
  isOpen: boolean;
  onClose: () => void;
  deviceSerial?: string;
  activeMacroId?: string;
  onSelectMacro?: (macroId: string) => void;
}

export const MacroModal: React.FC<MacroModalProps> = ({
  isOpen,
  onClose,
  deviceSerial,
  activeMacroId,
  onSelectMacro,
}) => {
  const [activeTab, setActiveTab] = useState<'profiles' | 'editor' | 'recorder'>('profiles');
  const [macros, setMacros] = useState<MacroProfile[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [selectedMacro, setSelectedMacro] = useState<MacroProfile | null>(null);

  // Editor State
  const [editId, setEditId] = useState<string>('');
  const [editName, setEditName] = useState<string>('');
  const [editDesc, setEditDesc] = useState<string>('');
  const [editDuration, setEditDuration] = useState<number>(60);
  const [editLoop, setEditLoop] = useState<boolean>(true);
  const [editActions, setEditActions] = useState<MacroAction[]>([]);
  const [testingAction, setTestingAction] = useState<string | null>(null);
  const [selectedMacroId, setSelectedMacroId] = useState<string>(activeMacroId || '');
  const [isMacroEnabled, setIsMacroEnabled] = useState<boolean>(false);
  const [runningTestMacroId, setRunningTestMacroId] = useState<string | null>(null);

  // Recorder State
  const [recordName, setRecordName] = useState<string>('มาโครบันทึกจากการเล่นสด');
  const [recordStatus, setRecordStatus] = useState<string>('IDLE');
  const [recordElapsed, setRecordElapsed] = useState<number>(0);
  const [recordActionCount, setRecordActionCount] = useState<number>(0);
  const [recentActions, setRecentActions] = useState<any[]>([]);
  const isSlidePressedRef = useRef<boolean>(false);
  const recordStatusRef = useRef<string>('IDLE');

  const fetchSettings = async () => {
    if (!deviceSerial) return;
    try {
      const cfg = await botApi.getSettings(deviceSerial);
      if (cfg) {
        setSelectedMacroId(cfg.selected_macro_id || '');
        setIsMacroEnabled(Boolean(cfg.macro_enabled));
      }
    } catch {
      // ignore
    }
  };

  const fetchMacros = async () => {
    setLoading(true);
    try {
      const res = await botApi.getMacros();
      if (res.success && Array.isArray(res.macros)) {
        setMacros(res.macros);
      }
    } catch {
      toast.error('ไม่สามารถโหลดรายการมาโครได้');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchMacros();
      fetchSettings();
    }
  }, [isOpen, deviceSerial, activeTab]);

  // Polling recorder status when recorder tab is active
  useEffect(() => {
    if (!isOpen || !deviceSerial) return;
    const interval = setInterval(async () => {
      try {
        const st = await botApi.getMacroRecordStatus(deviceSerial);
        if (st) {
          const prevStatus = recordStatusRef.current;
          setRecordStatus(st.status || 'IDLE');
          setRecordElapsed(st.elapsed || 0);
          setRecordActionCount(st.action_count || 0);
          if (Array.isArray(st.recent_actions)) {
            setRecentActions(st.recent_actions);
          }
          // Auto reload macro profiles when recording finishes
          if (prevStatus === 'RECORDING' && st.status === 'IDLE') {
            fetchMacros();
            toast.success('🎉 บันทึกมาโครลงคลังสำเร็จแล้ว!');
          }
          recordStatusRef.current = st.status || 'IDLE';
        }
      } catch {
        // ignore
      }
    }, 400);

    return () => clearInterval(interval);
  }, [isOpen, deviceSerial, activeTab]);

  // Keyboard shortcut listener for recording (Space/Z for Jump, X/Down for Slide)
  useEffect(() => {
    if (!isOpen || activeTab !== 'recorder' || recordStatus !== 'RECORDING' || !deviceSerial) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;

      if (e.code === 'Space' || e.code === 'KeyZ' || e.code === 'ArrowLeft' || e.code === 'KeyJ' || e.code === 'KeyW' || e.code === 'ArrowUp') {
        e.preventDefault();
        botApi.recordMacroAction(deviceSerial, 'jump');
      } else if ((e.code === 'KeyX' || e.code === 'ArrowRight' || e.code === 'ArrowDown' || e.code === 'KeyS' || e.code === 'KeyC') && !isSlidePressedRef.current) {
        e.preventDefault();
        isSlidePressedRef.current = true;
        botApi.recordMacroAction(deviceSerial, 'slide_down');
      }
    };

    const handleKeyUp = (e: KeyboardEvent) => {
      if (e.code === 'KeyX' || e.code === 'ArrowRight' || e.code === 'ArrowDown' || e.code === 'KeyS' || e.code === 'KeyC') {
        if (isSlidePressedRef.current) {
          isSlidePressedRef.current = false;
          botApi.recordMacroAction(deviceSerial, 'slide_up');
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, [isOpen, activeTab, recordStatus, deviceSerial]);

  const handleEdit = async (m: MacroProfile) => {
    try {
      const detail = await botApi.getMacro(m.id);
      if (detail.success && detail.macro) {
        const full = detail.macro;
        setEditId(full.id);
        setEditName(full.name || '');
        setEditDesc(full.description || '');
        setEditDuration(full.duration_seconds || 60);
        setEditLoop(full.loop !== undefined ? full.loop : true);
        setEditActions(full.actions || []);
        setSelectedMacro(full);
        setActiveTab('editor');
      }
    } catch {
      toast.error('ไม่สามารถโหลดข้อมูลสเต็ปมาโครได้');
    }
  };

  const handleCreateNew = () => {
    setEditId('');
    setEditName('มาโครใหม่ (My Custom Macro)');
    setEditDesc('คำอธิบายสเต็ปการเล่น');
    setEditDuration(45);
    setEditLoop(true);
    setEditActions([
      { t: 2.0, action: 'jump' },
      { t: 4.5, action: 'double_jump', air_time: 0.15 },
      { t: 7.0, action: 'slide', duration: 0.4 },
    ]);
    setSelectedMacro(null);
    setActiveTab('editor');
  };

  const handleDelete = async (id: string, name: string) => {
    const ok = await confirmModal({
      title: 'ยืนยันการลบมาโคร',
      message: `คุณต้องการลบไฟล์มาโคร "${name}" ใช่หรือไม่?`,
      type: 'danger',
      confirmText: 'ลบไฟล์',
    });
    if (!ok) return;

    try {
      const res = await botApi.deleteMacro(id);
      if (res.success) {
        toast.success(`ลบมาโคร "${name}" เรียบร้อยแล้ว`);
        fetchMacros();
        if (editId === id) {
          handleCreateNew();
        }
      } else {
        toast.error(res.message || 'ลบไม่สำเร็จ');
      }
    } catch {
      toast.error('เกิดข้อผิดพลาดในการลบมาโคร');
    }
  };

  const handleSave = async () => {
    if (!editName.trim()) {
      toast.warning('กรุณาระบุชื่อมาโคร');
      return;
    }

    const payload = {
      id: editId || undefined,
      name: editName.trim(),
      description: editDesc.trim(),
      duration_seconds: Number(editDuration) || 45,
      loop: editLoop,
      actions: editActions.sort((a, b) => a.t - b.t),
    };

    try {
      const res = await botApi.saveMacro(payload);
      if (res.success) {
        toast.success(`บันทึกมาโคร "${editName}" สำเร็จ!`);
        if (res.id) setEditId(res.id);
        fetchMacros();
        setActiveTab('profiles');
      } else {
        toast.error(res.message || 'บันทึกไม่สำเร็จ');
      }
    } catch {
      toast.error('เกิดข้อผิดพลาดในการเชื่อมต่อเซิร์ฟเวอร์');
    }
  };

  const handleShiftActions = (offset: number) => {
    if (!editActions || editActions.length === 0) {
      toast.warning('ยังไม่มีแอ็กชันให้ปรับเวลา');
      return;
    }
    const updated = editActions.map(act => ({
      ...act,
      t: Math.max(0.0, Math.round((Number(act.t) + offset) * 100) / 100)
    }));
    updated.sort((a, b) => a.t - b.t);
    setEditActions(updated);
    toast.info(`⏱️ ปรับเลื่อนเวลาทุกแอ็กชัน ${offset > 0 ? '+' : ''}${offset}s เรียบร้อยแล้ว (กดบันทึกเพื่อใช้งาน)`);
  };

  const handleAddAction = (type: 'jump' | 'double_jump' | 'slide') => {
    const lastT = editActions.length > 0 ? editActions[editActions.length - 1].t : 1.0;
    const nextT = Math.round((lastT + 2.5) * 100) / 100;

    let newAction: MacroAction;
    if (type === 'jump') {
      newAction = { t: nextT, action: 'jump' };
    } else if (type === 'double_jump') {
      newAction = { t: nextT, action: 'double_jump', air_time: 0.15 };
    } else {
      newAction = { t: nextT, action: 'slide', duration: 0.4 };
    }

    setEditActions([...editActions, newAction]);
  };

  const handleUpdateAction = (index: number, patch: Partial<MacroAction>) => {
    const next = [...editActions];
    next[index] = { ...next[index], ...patch };
    setEditActions(next);
  };

  const handleRemoveAction = (index: number) => {
    setEditActions(editActions.filter((_, i) => i !== index));
  };

  const handleTestAction = async (action: string, air_time?: number, duration?: number) => {
    setTestingAction(action);
    try {
      const res = await botApi.testMacroAction({
        device_serial: deviceSerial,
        action,
        air_time,
        duration,
      });
      if (res.success) {
        toast.info(`ส่งคำสั่ง ${action} สำเร็จ (Delay < 0.2ms)`);
      }
    } catch {
      toast.error('ไม่สามารถส่งคำสั่งทดสอบได้');
    } finally {
      setTimeout(() => setTestingAction(null), 300);
    }
  };

  // RECORDER CONTROLS
  const handleArmRecording = async () => {
    if (!deviceSerial) return toast.warning('กรุณาเลือกจอก่อน');
    try {
      const res = await botApi.armMacroRecording(deviceSerial, recordName);
      if (res.success) {
        toast.info('🟡 โหมดเตรียมบันทึกทำงานแล้ว — เมื่อเริ่มวิ่งในเกม ระบบจะเริ่มนับเวลาและบันทึกอัตโนมัติ!');
      }
    } catch {
      toast.error('เกิดข้อผิดพลาดในการเปิดโหมดบันทึก');
    }
  };

  const handleTriggerRecordingNow = async () => {
    if (!deviceSerial) return toast.warning('กรุณาเลือกจอก่อน');
    try {
      const res = await botApi.triggerMacroRecording(deviceSerial);
      if (res.success) {
        toast.success('🟢 เริ่มจับเวลาและบันทึกมาโครสดแล้ว (t=0.00s)!');
      }
    } catch {
      toast.error('เริ่มบันทึกไม่สำเร็จ');
    }
  };

  const handleStopRecording = async () => {
    if (!deviceSerial) return;
    try {
      const res = await botApi.stopMacroRecording(deviceSerial, recordName);
      if (res.success && res.macro) {
        toast.success(`🎉 บันทึกมาโครเป็นไฟล์ JSON สำเร็จ! มีทั้งหมด ${res.macro.actions?.length || 0} แอ็กชัน`);
        fetchMacros();
        setActiveTab('profiles');
      } else {
        toast.warning(res.message || 'ไม่มีข้อมูลแอ็กชันที่บันทึก');
      }
    } catch {
      toast.error('เกิดข้อผิดพลาดในการหยุดบันทึก');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md animate-fadeIn">
      <div className="relative w-full max-w-4xl max-h-[90vh] flex flex-col bg-slate-900/95 border border-purple-500/30 rounded-3xl shadow-2xl shadow-purple-950/50 overflow-hidden text-slate-100">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-gradient-to-r from-slate-900 via-purple-950/40 to-slate-900">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-2xl bg-gradient-to-br from-purple-500 to-indigo-600 shadow-lg shadow-purple-500/25">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                ระบบมาโครวิ่งอัตโนมัติ (Macro Timeline System)
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30 font-semibold">
                  Zero Delay &lt; 0.2ms
                </span>
              </h2>
              <p className="text-xs text-slate-400">
                รองรับการบันทึกจากการเล่นสด (Auto-Trigger In-Game) และเขียนไทม์ไลน์เป็น JSON อย่างแม่นยำ
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-white rounded-xl hover:bg-slate-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex border-b border-slate-800 px-6 bg-slate-950/40">
          <button
            onClick={() => setActiveTab('profiles')}
            className={`flex items-center gap-2 py-3 px-4 text-sm font-semibold border-b-2 transition-all ${
              activeTab === 'profiles'
                ? 'border-purple-500 text-purple-400 bg-purple-500/10'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Sliders className="w-4 h-4" />
            คลังมาโคร ({macros.length})
          </button>
          
          <button
            onClick={() => setActiveTab('recorder')}
            className={`flex items-center gap-2 py-3 px-4 text-sm font-semibold border-b-2 transition-all ${
              activeTab === 'recorder'
                ? 'border-rose-500 text-rose-400 bg-rose-500/10'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Radio className="w-4 h-4 text-rose-500 animate-pulse" />
            อัดมาโครสด (Auto In-Game Recorder)
            {recordStatus === 'RECORDING' && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-rose-600 text-white font-mono animate-bounce">
                REC {recordElapsed}s
              </span>
            )}
            {recordStatus === 'ARMED' && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/40">
                รอเข้าเกม
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab('editor')}
            className={`flex items-center gap-2 py-3 px-4 text-sm font-semibold border-b-2 transition-all ${
              activeTab === 'editor'
                ? 'border-purple-500 text-purple-400 bg-purple-500/10'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <FileCode className="w-4 h-4" />
            แก้ไขไทม์ไลน์ (Timeline Editor)
            {editActions.length > 0 && (
              <span className="text-xs px-2 py-0.2 rounded-full bg-purple-900/60 text-purple-300 font-mono">
                {editActions.length} แอ็กชัน
              </span>
            )}
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">

          {/* TAB 1: PROFILES */}
          {activeTab === 'profiles' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-white">เลือกมาโครที่ต้องการใช้งาน</h3>
                  <p className="text-xs text-slate-400">เลือกมาโครเพื่อตั้งให้จอ {deviceSerial || 'นี้'} นำไปเล่นเมื่อเข้าสู่เกม</p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={fetchMacros}
                    disabled={loading}
                    className="flex items-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition-all cursor-pointer border border-slate-700 hover:border-slate-600"
                    title="รีเฟรชรายการมาโคร"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
                    รีเฟรช
                  </button>
                  <button
                    onClick={() => setActiveTab('recorder')}
                    className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-xl bg-rose-600 hover:bg-rose-500 text-white shadow-lg shadow-rose-600/25 transition-all"
                  >
                    <Radio className="w-3.5 h-3.5" />
                    อัดมาโครจากการเล่นสด
                  </button>
                  <button
                    onClick={handleCreateNew}
                    className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-xl bg-purple-600 hover:bg-purple-500 text-white shadow-lg shadow-purple-600/25 transition-all"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    เขียนสเต็ปเอง
                  </button>
                </div>
              </div>

              {loading ? (
                <div className="py-16 text-center text-slate-500 text-sm animate-pulse">
                  กำลังโหลดข้อมูลมาโคร...
                </div>
              ) : macros.length === 0 ? (
                <div className="p-8 text-center border border-dashed border-slate-800 rounded-2xl space-y-3">
                  <p className="text-sm text-slate-400">ยังไม่มีไฟล์มาโครในระบบ</p>
                  <div className="flex items-center justify-center gap-2">
                    <button
                      onClick={() => setActiveTab('recorder')}
                      className="px-4 py-2 text-xs font-semibold rounded-xl bg-rose-600 hover:bg-rose-500 text-white shadow-lg shadow-rose-600/25 transition-all cursor-pointer"
                    >
                      อัดมาโครจากการเล่นรอบแรก
                    </button>
                    <button
                      onClick={fetchMacros}
                      className="px-4 py-2 text-xs font-semibold rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 flex items-center gap-1.5 transition-all cursor-pointer"
                    >
                      <RefreshCw className="w-3.5 h-3.5" />
                      รีเฟรชรายการ
                    </button>
                  </div>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                  {macros.map((m) => {
                    const isActive = isMacroEnabled && (selectedMacroId === m.id);
                    const isTestingThis = runningTestMacroId === m.id;

                    const handleToggleActive = async () => {
                      if (!deviceSerial) return;
                      const willEnable = !(isMacroEnabled && selectedMacroId === m.id);
                      try {
                        await botApi.selectMacro(deviceSerial, m.id, willEnable);
                        setSelectedMacroId(m.id);
                        setIsMacroEnabled(willEnable);
                        if (willEnable) {
                          toast.success(`เปิดใช้งานมาโคร "${m.name}" สำเร็จ!`);
                        } else {
                          toast.info(`ปิดใช้งานมาโคร "${m.name}" แล้ว`);
                        }
                        if (onSelectMacro && willEnable) {
                          onSelectMacro(m.id);
                        }
                      } catch {
                        toast.error('ไม่สามารถเปลี่ยนการตั้งค่ามาโครได้');
                      }
                    };

                    const handleTestPlay = async () => {
                      if (!deviceSerial) return;
                      if (isTestingThis) {
                        await botApi.testMacroAction({ device_serial: deviceSerial, action: 'stop' });
                        setRunningTestMacroId(null);
                        toast.info(`⏹️ สั่งหยุดการรันมาโคร "${m.name}" แล้ว`);
                        return;
                      }
                      setRunningTestMacroId(m.id);
                      toast.info(`▶️ กำลังทดสอบรันมาโคร "${m.name}" บนจอ...`);
                      try {
                        const res = await botApi.testMacroAction({
                          device_serial: deviceSerial,
                          action: 'test_macro',
                          macro_id: m.id,
                        });
                        if (res && res.success) {
                          toast.success(res.message || 'เริ่มรันมาโครแล้ว');
                        }
                      } catch {
                        toast.error('เกิดข้อผิดพลาดในการสั่งทดสอบ');
                        setRunningTestMacroId(null);
                      }
                    };

                    return (
                      <div
                        key={m.id}
                        className={`relative group p-4 rounded-2xl border transition-all duration-200 flex flex-col justify-between ${
                          isActive
                            ? 'bg-purple-950/40 border-purple-500/70 shadow-lg shadow-purple-950/40 ring-1 ring-purple-500/40'
                            : 'bg-slate-800/40 border-slate-700/60 hover:border-purple-500/40 hover:bg-slate-800/70'
                        }`}
                      >
                        <div>
                          <div className="flex items-start justify-between gap-2 mb-1.5">
                            <h4 className="text-sm font-bold text-white group-hover:text-purple-300 transition-colors flex items-center gap-2">
                              {m.name}
                              {isActive && (
                                <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-semibold flex items-center gap-1">
                                  <Check className="w-3 h-3" /> ใช้งานอยู่
                                </span>
                              )}
                            </h4>
                          </div>

                          <p className="text-xs text-slate-400 line-clamp-2 mb-3">
                            {m.description || 'ไม่มีคำอธิบาย'}
                          </p>

                          <div className="flex items-center gap-3 text-[11px] text-slate-400 font-mono mb-4">
                            <span className="flex items-center gap-1">
                              <Clock className="w-3 h-3 text-purple-400" />
                              {m.duration_seconds ? `${m.duration_seconds}s` : 'Auto'}
                            </span>
                            <span className="flex items-center gap-1">
                              <Zap className="w-3 h-3 text-amber-400" />
                              {m.action_count || 0} แอ็กชัน
                            </span>
                            {m.loop && (
                              <span className="px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-300 border border-blue-500/20">
                                วนซ้ำ (Loop)
                              </span>
                            )}
                          </div>
                        </div>

                        {/* Actions */}
                        <div className="flex flex-col gap-2 pt-2 border-t border-slate-800/80">
                          <div className="flex items-center gap-2">
                            <button
                              onClick={handleToggleActive}
                              className={`flex-1 py-1.5 px-3 rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition-all cursor-pointer ${
                                isActive
                                  ? 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-600/30'
                                  : 'bg-purple-600/20 hover:bg-purple-600/40 text-purple-300 border border-purple-500/30'
                              }`}
                            >
                              <Check className="w-3.5 h-3.5" />
                              <span>{isActive ? 'ใช้งานอยู่ (Active)' : 'เลือกใช้สำหรับบอท'}</span>
                            </button>

                            <button
                              onClick={handleTestPlay}
                              className={`py-1.5 px-3 rounded-xl text-xs font-semibold flex items-center justify-center gap-1 transition-all cursor-pointer ${
                                isTestingThis
                                  ? 'bg-amber-600 text-white animate-pulse'
                                  : 'bg-blue-600/30 hover:bg-blue-600/50 text-blue-300 border border-blue-500/30'
                              }`}
                              title={isTestingThis ? 'คลิกเพื่อหยุดรัน' : 'ทดสอบเล่นตามมาโครทันที'}
                            >
                              {isTestingThis ? <Square className="w-3.5 h-3.5 fill-current" /> : <Play className="w-3.5 h-3.5 fill-current" />}
                              <span>{isTestingThis ? 'หยุด' : 'รันตอนนี้'}</span>
                            </button>
                          </div>

                          <div className="flex items-center justify-end gap-2">
                            <button
                              onClick={() => handleEdit(m)}
                              className="flex-1 py-1 px-2.5 rounded-lg text-[11px] font-medium bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-all flex items-center justify-center gap-1"
                            >
                              <Sliders className="w-3 h-3" />
                              แก้ไขสเต็ป / ไทม์ไลน์
                            </button>

                            <button
                              onClick={() => handleDelete(m.id, m.name)}
                              className="p-1.5 rounded-lg text-xs text-rose-400 hover:text-rose-300 hover:bg-rose-500/20 transition-all"
                              title="ลบมาโคร"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* TAB 2: LIVE IN-GAME RECORDER */}
          {activeTab === 'recorder' && (
            <div className="space-y-5">
              {/* How it works info banner */}
              <div className="p-4 rounded-2xl bg-gradient-to-r from-rose-950/40 via-purple-950/30 to-slate-900 border border-rose-500/30 space-y-2">
                <div className="flex items-center gap-2 text-rose-300 font-bold text-sm">
                  <Radio className="w-4 h-4 animate-pulse text-rose-400" />
                  ระบบบันทึกมาโครอัจฉริยะ (Smart In-Game Trigger)
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  กดปุ่ม <strong>"🔴 เตรียมบันทึกมาโคร"</strong> แล้วกดเข้าเกมวิ่งในอีมูเลเตอร์ตามปกติ 
                  <span className="text-amber-300 font-medium"> เมื่อเกมเข้าสู่หน้าจอวิ่งจริง ระบบจะตรวจจับและเริ่มจับเวลาบันทึก (t=0.00s) ให้อัตโนมัติ</span> 
                  คุณสามารถเล่นด้วยตนเอง หรือใช้ปุ่ม Space/Z (กระโดด) และ X (สไลด์) บนคีย์บอร์ด เมื่อวิ่งจบเกม ระบบจะตัดจบและบันทึกเป็นไฟล์ JSON ทันที!
                </p>
              </div>

              {/* Recorder Settings & Trigger */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 rounded-2xl bg-slate-800/40 border border-slate-700/60 items-center">
                <div className="md:col-span-2 space-y-1.5">
                  <label className="text-xs font-semibold text-slate-300">ตั้งชื่อมาโครที่จะบันทึก:</label>
                  <input
                    type="text"
                    value={recordName}
                    onChange={(e) => setRecordName(e.target.value)}
                    placeholder="เช่น ด่าน 1 สเต็ปวิ่งจริงเก็บเหรียญ"
                    className="w-full px-3.5 py-2 text-xs rounded-xl bg-slate-900/80 border border-slate-700 focus:border-rose-500 focus:outline-none text-white font-medium"
                  />
                </div>

                <div className="space-y-1.5 flex flex-col justify-end">
                  <label className="text-xs font-semibold text-slate-300">สถานะตัวอัด:</label>
                  <div className="flex items-center gap-2">
                    {recordStatus === 'IDLE' && (
                      <span className="text-xs px-3 py-1.5 rounded-xl bg-slate-800 text-slate-300 border border-slate-700 font-bold flex items-center gap-1.5 w-full justify-center">
                        <Circle className="w-2.5 h-2.5 text-slate-400 fill-slate-400 shrink-0" />
                        <span>พร้อมบันทึก</span>
                      </span>
                    )}
                    {recordStatus === 'ARMED' && (
                      <span className="text-xs px-3 py-1.5 rounded-xl bg-amber-500/20 text-amber-300 border border-amber-500/40 font-bold flex items-center gap-1.5 w-full justify-center animate-pulse">
                        <Circle className="w-2.5 h-2.5 text-amber-400 fill-amber-400 shrink-0 animate-ping" />
                        <span>รอเข้าหน้าวิ่งในเกม...</span>
                      </span>
                    )}
                    {recordStatus === 'RECORDING' && (
                      <span className="text-xs px-3 py-1.5 rounded-xl bg-rose-600 text-white font-bold font-mono flex items-center gap-1.5 w-full justify-center shadow-lg shadow-rose-600/40">
                        <Circle className="w-2.5 h-2.5 text-white fill-white shrink-0 animate-pulse" />
                        <span>กำลังอัด {recordElapsed}s</span>
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Main Action Trigger Buttons */}
              <div className="flex flex-wrap items-center justify-between gap-3 p-4 rounded-2xl bg-slate-950/60 border border-slate-800">
                {recordStatus === 'IDLE' && (
                  <button
                    onClick={handleArmRecording}
                    className="flex-1 py-3 px-5 text-sm font-bold rounded-2xl bg-gradient-to-r from-rose-600 to-red-600 hover:from-rose-500 hover:to-red-500 text-white shadow-xl shadow-rose-600/30 transition-all flex items-center justify-center gap-2 cursor-pointer active:scale-98"
                  >
                    <Radio className="w-4 h-4" />
                    <span>เตรียมเริ่มบันทึก (รอตรวจจับหน้าเกมวิ่งอัตโนมัติ)</span>
                  </button>
                )}

                {recordStatus === 'ARMED' && (
                  <>
                    <div className="flex-1 flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full bg-amber-400 animate-ping"></div>
                      <span className="text-xs text-amber-300 font-semibold">
                        กำลังรอหน้าจอวิ่งจริง... กรุณากดเริ่มเกมในอีมูเลเตอร์ หรือกดปุ่มข้างๆ เพื่อเริ่มนับเวลาทันที
                      </span>
                    </div>

                    <button
                      onClick={handleTriggerRecordingNow}
                      className="py-2.5 px-4 text-xs font-bold rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg transition-all flex items-center gap-1.5"
                    >
                      <Zap className="w-3.5 h-3.5 text-amber-300" />
                      <span>กำลังวิ่งอยู่ในเกมแล้ว เริ่มจับเวลาเลย!</span>
                    </button>

                    <button
                      onClick={async () => {
                        if (deviceSerial) await botApi.stopMacroRecording(deviceSerial);
                      }}
                      className="py-2.5 px-3 text-xs font-semibold rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition-all"
                    >
                      ยกเลิก
                    </button>
                  </>
                )}

                {recordStatus === 'RECORDING' && (
                  <>
                    <div className="flex items-center gap-3">
                      <span className="text-xl font-bold font-mono text-rose-400 flex items-center gap-1">
                        <Clock className="w-4 h-4 inline" />
                        <span>{recordElapsed}s</span>
                      </span>
                      <span className="text-xs px-2.5 py-1 rounded-lg bg-slate-800 text-slate-300 font-mono">
                        บันทึกแล้ว {recordActionCount} แอ็กชัน
                      </span>
                    </div>

                    <button
                      onClick={handleStopRecording}
                      className="py-2.5 px-5 text-xs font-bold rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white shadow-lg shadow-emerald-600/30 transition-all flex items-center gap-2 active:scale-98 cursor-pointer"
                    >
                      <Save className="w-4 h-4" />
                      <span>หยุดและบันทึกเป็น JSON ทันที</span>
                    </button>
                  </>
                )}
              </div>

              {/* Interactive Gameplay Pad during Record */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold text-slate-300 flex items-center gap-1.5">
                    <Gamepad2 className="w-4 h-4 text-purple-400" />
                    ปุ่มควบคุมสด (หรือกดคีย์บอร์ด Space / Z สำหรับ Jump, X สำหรับ Slide)
                  </h4>
                  <span className="text-[11px] text-slate-500 font-mono">
                    บันทึกจังหวะลงมาโคร + สั่งตัวละครในจอจริงพร้อมกัน
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  {/* Jump Button Pad */}
                  <button
                    onClick={() => {
                      if (deviceSerial) botApi.recordMacroAction(deviceSerial, 'jump');
                    }}
                    className="h-28 rounded-2xl bg-gradient-to-br from-purple-900/60 to-indigo-900/60 hover:from-purple-800/80 hover:to-indigo-800/80 border-2 border-purple-500/50 hover:border-purple-400 text-white flex flex-col items-center justify-center gap-1 shadow-xl active:scale-95 transition-all cursor-pointer select-none group"
                  >
                    <ChevronsUp className="w-8 h-8 text-purple-300 group-hover:scale-110 transition-transform" />
                    <span className="text-sm font-bold">กระโดด (Jump)</span>
                    <span className="text-[11px] text-purple-300/80 font-mono">กดปุ่ม Space / Z</span>
                  </button>

                  {/* Slide Button Pad (Supports Hold & Release) */}
                  <button
                    onMouseDown={() => {
                      if (deviceSerial) botApi.recordMacroAction(deviceSerial, 'slide_down');
                    }}
                    onMouseUp={() => {
                      if (deviceSerial) botApi.recordMacroAction(deviceSerial, 'slide_up');
                    }}
                    onTouchStart={() => {
                      if (deviceSerial) botApi.recordMacroAction(deviceSerial, 'slide_down');
                    }}
                    onTouchEnd={() => {
                      if (deviceSerial) botApi.recordMacroAction(deviceSerial, 'slide_up');
                    }}
                    className="h-28 rounded-2xl bg-gradient-to-br from-amber-900/60 to-orange-900/60 hover:from-amber-800/80 hover:to-orange-800/80 border-2 border-amber-500/50 hover:border-amber-400 text-white flex flex-col items-center justify-center gap-1 shadow-xl active:scale-95 transition-all cursor-pointer select-none group"
                  >
                    <ChevronsDown className="w-8 h-8 text-amber-300 group-hover:scale-110 transition-transform" />
                    <span className="text-sm font-bold">สไลด์ (Slide - กดค้าง)</span>
                    <span className="text-[11px] text-amber-300/80 font-mono">กดค้างปุ่ม X / ลูกศรลง</span>
                  </button>
                </div>
              </div>

              {/* Live Action Stream Log */}
              {recentActions.length > 0 && (
                <div className="p-3.5 rounded-2xl bg-slate-950/50 border border-slate-800 space-y-2">
                  <span className="text-[11px] font-bold text-slate-400">แอ็กชันล่าสุดที่เพิ่งบันทึกได้:</span>
                  <div className="flex flex-wrap gap-2">
                    {recentActions.map((act, idx) => (
                      <span
                        key={idx}
                        className="px-2.5 py-1 rounded-lg bg-slate-800 text-xs font-mono border border-slate-700 flex items-center gap-1.5 animate-fadeIn"
                      >
                        <span className="text-purple-400 font-bold">{act.t}s:</span>
                        <span className="text-white font-semibold inline-flex items-center gap-1">
                          {act.action === 'jump' && (
                            <>
                              <ChevronsUp className="w-3.5 h-3.5 text-cyan-400" />
                              <span>Jump</span>
                            </>
                          )}
                          {act.action === 'double_jump' && (
                            <>
                              <Rocket className="w-3.5 h-3.5 text-indigo-400" />
                              <span>Double Jump ({act.air_time}s)</span>
                            </>
                          )}
                          {act.action === 'slide' && (
                            <>
                              <ChevronsDown className="w-3.5 h-3.5 text-pink-400" />
                              <span>Slide ({act.duration}s)</span>
                            </>
                          )}
                        </span>
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 3: TIMELINE EDITOR */}
          {activeTab === 'editor' && (
            <div className="space-y-6">
              {/* Meta Config */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 rounded-2xl bg-slate-800/40 border border-slate-700/60">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-300">ชื่อมาโคร (Macro Name)</label>
                  <input
                    type="text"
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    placeholder="เช่น ด่าน 1 หนีเตาอบ - สเต็ปเหรียญ"
                    className="w-full px-3.5 py-2 text-xs rounded-xl bg-slate-900/80 border border-slate-700 focus:border-purple-500 focus:outline-none text-white"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-300">คำอธิบาย (Description)</label>
                  <input
                    type="text"
                    value={editDesc}
                    onChange={(e) => setEditDesc(e.target.value)}
                    placeholder="เช่น กระโดดเก็บเหรียญตามแนวเหรียญต้นเกม"
                    className="w-full px-3.5 py-2 text-xs rounded-xl bg-slate-900/80 border border-slate-700 focus:border-purple-500 focus:outline-none text-white"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-300">ระยะเวลาจบรอบ (วินาที)</label>
                  <input
                    type="number"
                    step="1"
                    min="5"
                    max="600"
                    value={editDuration}
                    onChange={(e) => setEditDuration(Number(e.target.value))}
                    className="w-full px-3.5 py-2 text-xs rounded-xl bg-slate-900/80 border border-slate-700 focus:border-purple-500 focus:outline-none text-white font-mono"
                  />
                </div>

                <div className="flex items-center justify-between p-2 rounded-xl bg-slate-900/40 border border-slate-700/40 mt-auto">
                  <div className="space-y-0.5">
                    <span className="text-xs font-semibold text-white">วนซ้ำต่อเนื่อง (Loop Playback)</span>
                    <p className="text-[11px] text-slate-400">เมื่อเล่นถึงจุดสิ้นสุด ให้เริ่มวนกลับมาที่วินาทีที่ 0 ใหม่</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={editLoop}
                    onChange={(e) => setEditLoop(e.target.checked)}
                    className="w-4 h-4 rounded text-purple-600 focus:ring-purple-500"
                  />
                </div>
              </div>

              {/* Quick Action Test Bar */}
              <div className="p-3.5 rounded-2xl bg-gradient-to-r from-purple-950/30 via-slate-800/40 to-purple-950/30 border border-purple-500/20 flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <Zap className="w-4 h-4 text-purple-400" />
                  <span className="text-xs font-semibold text-slate-300">ทดสอบกดส่งคำสั่งเข้าจอทันที:</span>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleTestAction('jump')}
                    disabled={testingAction !== null}
                    className="px-3 py-1.5 text-xs font-semibold rounded-xl bg-purple-600/30 hover:bg-purple-600/60 text-purple-200 border border-purple-500/40 transition-all flex items-center gap-1.5"
                  >
                    <ChevronsUp className="w-3.5 h-3.5 text-purple-400" />
                    <span>ทดสอบ Jump</span>
                  </button>
                  <button
                    onClick={() => handleTestAction('double_jump', 0.15)}
                    disabled={testingAction !== null}
                    className="px-3 py-1.5 text-xs font-semibold rounded-xl bg-indigo-600/30 hover:bg-indigo-600/60 text-indigo-200 border border-indigo-500/40 transition-all flex items-center gap-1.5"
                  >
                    <Rocket className="w-3.5 h-3.5 text-indigo-400" />
                    <span>ทดสอบ Double Jump</span>
                  </button>
                  <button
                    onClick={() => handleTestAction('slide', undefined, 0.4)}
                    disabled={testingAction !== null}
                    className="px-3 py-1.5 text-xs font-semibold rounded-xl bg-amber-600/30 hover:bg-amber-600/60 text-amber-200 border border-amber-500/40 transition-all flex items-center gap-1.5"
                  >
                    <ChevronsDown className="w-3.5 h-3.5 text-amber-400" />
                    <span>ทดสอบ Slide (0.4s)</span>
                  </button>
                </div>
              </div>

              {/* Time Offset / Delay Adjustment Panel */}
              <div className="p-3.5 rounded-2xl bg-slate-800/60 border border-slate-700/60 flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-amber-400" />
                  <div>
                    <span className="text-xs font-bold text-slate-200">ปรับชดเชยดีเลย์ทั้งมาโคร (Time Offset):</span>
                    <p className="text-[11px] text-slate-400">เลื่อนเวลาทุกแอ็กชันเร็วขึ้น (-) หรือช้าลง (+) ในคลิกเดียว</p>
                  </div>
                </div>
                <div className="flex items-center gap-1.5 flex-wrap">
                  <button
                    onClick={() => handleShiftActions(-1.0)}
                    className="px-2.5 py-1 text-xs font-mono font-bold rounded-lg bg-slate-900 hover:bg-slate-700 text-rose-300 border border-slate-700 cursor-pointer transition-all"
                    title="เลื่อนทุกแอ็กชันเร็วขึ้น 1.0 วินาที (-1.0s)"
                  >
                    -1.0s
                  </button>
                  <button
                    onClick={() => handleShiftActions(-0.5)}
                    className="px-2.5 py-1 text-xs font-mono font-bold rounded-lg bg-slate-900 hover:bg-slate-700 text-rose-300 border border-slate-700 cursor-pointer transition-all"
                    title="เลื่อนทุกแอ็กชันเร็วขึ้น 0.5 วินาที (-0.5s)"
                  >
                    -0.5s
                  </button>
                  <button
                    onClick={() => handleShiftActions(-0.2)}
                    className="px-2.5 py-1 text-xs font-mono font-bold rounded-lg bg-slate-900 hover:bg-slate-700 text-rose-300 border border-slate-700 cursor-pointer transition-all"
                    title="เลื่อนทุกแอ็กชันเร็วขึ้น 0.2 วินาที (-0.2s)"
                  >
                    -0.2s
                  </button>
                  <button
                    onClick={() => handleShiftActions(0.2)}
                    className="px-2.5 py-1 text-xs font-mono font-bold rounded-lg bg-slate-900 hover:bg-slate-700 text-emerald-300 border border-slate-700 cursor-pointer transition-all"
                    title="เลื่อนทุกแอ็กชันช้าลง 0.2 วินาที (+0.2s)"
                  >
                    +0.2s
                  </button>
                  <button
                    onClick={() => handleShiftActions(0.5)}
                    className="px-2.5 py-1 text-xs font-mono font-bold rounded-lg bg-slate-900 hover:bg-slate-700 text-emerald-300 border border-slate-700 cursor-pointer transition-all"
                    title="เลื่อนทุกแอ็กชันช้าลง 0.5 วินาที (+0.5s)"
                  >
                    +0.5s
                  </button>
                  <button
                    onClick={() => handleShiftActions(1.0)}
                    className="px-2.5 py-1 text-xs font-mono font-bold rounded-lg bg-slate-900 hover:bg-slate-700 text-emerald-300 border border-slate-700 cursor-pointer transition-all"
                    title="เลื่อนทุกแอ็กชันช้าลง 1.0 วินาที (+1.0s)"
                  >
                    +1.0s
                  </button>
                </div>
              </div>

              {/* Action List Section */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-bold text-white flex items-center gap-2">
                      จังหวะแอ็กชันตามไทม์ไลน์ ({editActions.length} รายการ)
                    </h4>
                    <p className="text-xs text-slate-400">ระบบจะเรียงลำดับเวลา (t) ให้อัตโนมัติเมื่อบันทึก</p>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleAddAction('jump')}
                      className="px-2.5 py-1.5 text-xs font-semibold rounded-xl bg-purple-600 hover:bg-purple-500 text-white transition-all flex items-center gap-1"
                    >
                      <Plus className="w-3 h-3" /> + Jump
                    </button>
                    <button
                      onClick={() => handleAddAction('double_jump')}
                      className="px-2.5 py-1.5 text-xs font-semibold rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white transition-all flex items-center gap-1"
                    >
                      <Plus className="w-3 h-3" /> + Double Jump
                    </button>
                    <button
                      onClick={() => handleAddAction('slide')}
                      className="px-2.5 py-1.5 text-xs font-semibold rounded-xl bg-amber-600 hover:bg-amber-500 text-white transition-all flex items-center gap-1"
                    >
                      <Plus className="w-3 h-3" /> + Slide
                    </button>
                  </div>
                </div>

                {editActions.length === 0 ? (
                  <div className="p-8 text-center border border-dashed border-slate-800 rounded-2xl text-slate-400 text-xs">
                    ยังไม่มีแอ็กชันในมาโครนี้ — กดปุ่ม "+ Jump" หรือ "+ Slide" ด้านบนเพื่อเพิ่มจังหวะ หรือกดแท็บ "อัดมาโครสด" เพื่ออัดจากการเล่นจริง
                  </div>
                ) : (
                  <div className="space-y-2 max-h-[360px] overflow-y-auto pr-1">
                    {editActions.map((act, idx) => (
                      <div
                        key={idx}
                        className="flex items-center gap-3 p-2.5 rounded-xl bg-slate-800/50 border border-slate-700/60 hover:border-purple-500/40 transition-all text-xs"
                      >
                        <span className="text-[11px] font-mono text-slate-500 w-6 text-center">
                          #{idx + 1}
                        </span>

                        {/* Timestamp */}
                        <div className="flex items-center gap-1.5">
                          <span className="text-slate-400 font-medium">วินาทีที่ (t):</span>
                          <input
                            type="number"
                            step="0.05"
                            min="0"
                            value={act.t}
                            onChange={(e) => handleUpdateAction(idx, { t: parseFloat(e.target.value) || 0 })}
                            className="w-20 px-2 py-1 rounded-lg bg-slate-900 border border-slate-700 text-purple-300 font-mono focus:border-purple-500 focus:outline-none"
                          />
                          <span className="text-slate-500">วิ</span>
                        </div>

                        {/* Action Selector */}
                        <div className="flex items-center gap-1.5">
                          <select
                            value={act.action}
                            onChange={(e) => handleUpdateAction(idx, { action: e.target.value as any })}
                            className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-700 text-white font-semibold focus:border-purple-500 focus:outline-none"
                          >
                            <option value="jump">กระโดด (Jump)</option>
                            <option value="double_jump">กระโดด 2 จังหวะ (Double Jump)</option>
                            <option value="slide">สไลด์ (Slide)</option>
                          </select>
                        </div>

                        {/* Extra Params */}
                        {act.action === 'double_jump' && (
                          <div className="flex items-center gap-1 text-slate-400">
                            <span>เว้นจังหวะ:</span>
                            <input
                              type="number"
                              step="0.01"
                              min="0.05"
                              max="0.4"
                              value={act.air_time || 0.15}
                              onChange={(e) => handleUpdateAction(idx, { air_time: parseFloat(e.target.value) || 0.15 })}
                              className="w-16 px-1.5 py-1 rounded-lg bg-slate-900 border border-slate-700 text-indigo-300 font-mono"
                            />
                            <span>วิ</span>
                          </div>
                        )}

                        {act.action === 'slide' && (
                          <div className="flex items-center gap-1 text-slate-400">
                            <span>ความยาวสไลด์:</span>
                            <input
                              type="number"
                              step="0.05"
                              min="0.1"
                              max="2.0"
                              value={act.duration || 0.4}
                              onChange={(e) => handleUpdateAction(idx, { duration: parseFloat(e.target.value) || 0.4 })}
                              className="w-16 px-1.5 py-1 rounded-lg bg-slate-900 border border-slate-700 text-amber-300 font-mono"
                            />
                            <span>วิ</span>
                          </div>
                        )}

                        {/* Delete Action */}
                        <button
                          onClick={() => handleRemoveAction(idx)}
                          className="ml-auto p-1.5 text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Bottom Editor Action Buttons */}
              <div className="flex items-center justify-between pt-4 border-t border-slate-800">
                <button
                  onClick={() => setActiveTab('profiles')}
                  className="px-4 py-2 text-xs font-semibold rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition-all"
                >
                  ย้อนกลับ
                </button>

                <button
                  onClick={handleSave}
                  className="px-5 py-2.5 text-xs font-bold rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white shadow-lg shadow-purple-600/30 transition-all flex items-center gap-2 cursor-pointer"
                >
                  <Save className="w-4 h-4" />
                  บันทึกมาโคร
                </button>
              </div>
            </div>
          )}

        </div>

      </div>
    </div>
  );
};
