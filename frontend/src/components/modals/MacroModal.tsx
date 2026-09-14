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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm animate-fadeIn">
      <div className="relative w-full max-w-4xl max-h-[90vh] flex flex-col bg-[#FFFDF6] border-2 border-[#F0DFCE] rounded-3xl shadow-2xl shadow-[#D4A373]/25 overflow-hidden text-[#452311]">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b-2 border-[#F0DFCE] bg-gradient-to-r from-[#FFF9E8] via-[#FFF3DF] to-[#FFF9E8]">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-2xl bg-gradient-to-br from-amber-400 to-amber-500 shadow-md shadow-amber-500/25 border-2 border-amber-300 text-white">
              <Sparkles className="w-5 h-5 text-white drop-shadow-sm" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-[#452311] flex items-center gap-2 font-heading">
                ระบบมาโคร (Macro)
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-[#FEF3C7] text-[#B45309] border border-[#FCD34D] font-bold">
                  Zero Delay
                </span>
              </h2>
              <p className="text-xs text-[#8C6D58]">
                อัดการเล่นสดและจัดการไทม์ไลน์มาโคร
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="p-2 text-[#8C6D58] hover:text-[#452311] rounded-xl hover:bg-[#F5E6D3] transition-colors cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex border-b-2 border-[#F0DFCE] px-6 bg-[#FFF8EC] gap-2 pt-2">
          <button
            onClick={() => setActiveTab('profiles')}
            className={`flex items-center gap-2 py-2.5 px-4 text-xs font-bold transition-all rounded-t-xl cursor-pointer ${
              activeTab === 'profiles'
                ? 'border-b-4 border-[#F59E0B] text-[#B45309] bg-white shadow-sm'
                : 'border-b-4 border-transparent text-[#8C6D58] hover:text-[#452311] hover:bg-[#FFF2DE]'
            }`}
          >
            <Sliders className="w-4 h-4" />
            คลังมาโคร ({macros.length})
          </button>
          
          <button
            onClick={() => setActiveTab('recorder')}
            className={`flex items-center gap-2 py-2.5 px-4 text-xs font-bold transition-all rounded-t-xl cursor-pointer ${
              activeTab === 'recorder'
                ? 'border-b-4 border-[#F43F5E] text-[#BE123C] bg-white shadow-sm'
                : 'border-b-4 border-transparent text-[#8C6D58] hover:text-[#452311] hover:bg-[#FFF2DE]'
            }`}
          >
            <Radio className="w-4 h-4 text-rose-500 animate-pulse" />
            อัดมาโครสด
            {recordStatus === 'RECORDING' && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-rose-500 text-white font-mono animate-bounce shadow-sm">
                REC {recordElapsed}s
              </span>
            )}
            {recordStatus === 'ARMED' && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 border border-amber-300 font-bold">
                รอเข้าเกม
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab('editor')}
            className={`flex items-center gap-2 py-2.5 px-4 text-xs font-bold transition-all rounded-t-xl cursor-pointer ${
              activeTab === 'editor'
                ? 'border-b-4 border-[#8B5CF6] text-[#6D28D9] bg-white shadow-sm'
                : 'border-b-4 border-transparent text-[#8C6D58] hover:text-[#452311] hover:bg-[#FFF2DE]'
            }`}
          >
            <FileCode className="w-4 h-4" />
            แก้ไขไทม์ไลน์
            {editActions.length > 0 && (
              <span className="text-xs px-2 py-0.2 rounded-full bg-[#EDE9FE] text-[#6D28D9] font-mono border border-[#DDD6FE]">
                {editActions.length} แอ็กชัน
              </span>
            )}
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar bg-[#FFFDF6]">

          {/* TAB 1: PROFILES */}
          {activeTab === 'profiles' && (
            <div className="space-y-4">
              <div className="space-y-2.5">
                <div>
                  <h3 className="text-sm font-bold text-[#452311] font-heading">เลือกมาโคร</h3>
                  <p className="text-xs text-[#8C6D58]">ตั้งค่ามาโครสำหรับจอ {deviceSerial || 'นี้'}</p>
                </div>
                <div className="flex items-center gap-2 flex-wrap">
                  <button
                    onClick={fetchMacros}
                    disabled={loading}
                    className="candy-btn-soft px-3 py-1.5 text-xs font-semibold rounded-xl flex items-center gap-1.5 cursor-pointer"
                    title="รีเฟรชรายการ"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
                    รีเฟรช
                  </button>
                  <button
                    onClick={() => setActiveTab('recorder')}
                    className="candy-btn-strawberry px-3.5 py-1.5 text-xs font-bold rounded-xl flex items-center gap-1.5 cursor-pointer"
                  >
                    <Radio className="w-3.5 h-3.5" />
                    อัดสด
                  </button>
                  <button
                    onClick={handleCreateNew}
                    className="candy-btn-grape px-3.5 py-1.5 text-xs font-bold rounded-xl flex items-center gap-1.5 cursor-pointer"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    สร้างเอง
                  </button>
                </div>
              </div>

              {loading ? (
                <div className="py-16 text-center text-[#8C6D58] text-sm animate-pulse font-medium">
                  กำลังโหลดข้อมูลมาโคร...
                </div>
              ) : macros.length === 0 ? (
                <div className="p-8 text-center border-2 border-dashed border-[#E5D0BD] rounded-2xl bg-[#FFF9F0] space-y-3">
                  <p className="text-sm text-[#8C6D58] font-medium">ยังไม่มีมาโครในระบบ</p>
                  <div className="flex items-center justify-center gap-2">
                    <button
                      onClick={() => setActiveTab('recorder')}
                      className="candy-btn-strawberry px-4 py-2 text-xs font-bold rounded-xl cursor-pointer"
                    >
                      เริ่มอัดมาโคร
                    </button>
                    <button
                      onClick={fetchMacros}
                      className="candy-btn-soft px-4 py-2 text-xs font-semibold rounded-xl flex items-center gap-1.5 cursor-pointer"
                    >
                      <RefreshCw className="w-3.5 h-3.5" />
                      รีเฟรช
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
                          toast.success(`เปิดใช้ "${m.name}" แล้ว`);
                        } else {
                          toast.info(`ปิดใช้ "${m.name}" แล้ว`);
                        }
                        if (onSelectMacro && willEnable) {
                          onSelectMacro(m.id);
                        }
                      } catch {
                        toast.error('ไม่สามารถเปลี่ยนการตั้งค่าได้');
                      }
                    };

                    const handleTestPlay = async () => {
                      if (!deviceSerial) return;
                      if (isTestingThis) {
                        await botApi.testMacroAction({ device_serial: deviceSerial, action: 'stop' });
                        setRunningTestMacroId(null);
                        toast.info(`หยุดรัน "${m.name}" แล้ว`);
                        return;
                      }
                      setRunningTestMacroId(m.id);
                      toast.info(`กำลังทดสอบ "${m.name}" บนจอ...`);
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
                        toast.error('เกิดข้อผิดพลาดในการทดสอบ');
                        setRunningTestMacroId(null);
                      }
                    };

                    return (
                      <div
                        key={m.id}
                        className={`relative group p-4 rounded-2xl border-2 transition-all duration-200 flex flex-col justify-between ${
                          isActive
                            ? 'bg-gradient-to-br from-[#F0FDF4] to-[#DCFCE7] border-[#10B981] shadow-lg shadow-emerald-500/10 ring-2 ring-emerald-400/30'
                            : 'bg-white border-[#F0DFCE] hover:border-[#E2BC9B] hover:shadow-md'
                        }`}
                      >
                        <div>
                          <div className="flex items-start justify-between gap-2 mb-1.5">
                            <h4 className="text-sm font-bold text-[#452311] group-hover:text-[#B45309] transition-colors flex items-center gap-2 font-heading">
                              {m.name}
                              {isActive && (
                                <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300 font-bold flex items-center gap-1">
                                  <Check className="w-3 h-3" /> ใช้งานอยู่
                                </span>
                              )}
                            </h4>
                          </div>

                          <p className="text-xs text-[#8C6D58] line-clamp-2 mb-3">
                            {m.description || 'ไม่มีคำอธิบาย'}
                          </p>

                          <div className="flex items-center gap-3 text-[11px] text-[#8C6D58] font-mono mb-4">
                            <span className="flex items-center gap-1">
                              <Clock className="w-3 h-3 text-[#D97706]" />
                              {m.duration_seconds ? `${m.duration_seconds}s` : 'Auto'}
                            </span>
                            <span className="flex items-center gap-1">
                              <Zap className="w-3 h-3 text-[#F59E0B]" />
                              {m.action_count || 0} แอ็กชัน
                            </span>
                            {m.loop && (
                              <span className="px-1.5 py-0.5 rounded bg-[#EDE9FE] text-[#6D28D9] border border-[#DDD6FE] font-bold text-[10px]">
                                วนซ้ำ
                              </span>
                            )}
                          </div>
                        </div>

                        {/* Actions */}
                        <div className="flex flex-col gap-2 pt-2.5 border-t border-[#F0DFCE]">
                          <div className="flex items-center gap-2">
                            <button
                              onClick={handleToggleActive}
                              className={`flex-1 py-1.5 px-3 rounded-xl text-xs font-bold flex items-center justify-center gap-1.5 transition-all cursor-pointer ${
                                isActive
                                  ? 'candy-btn-mint'
                                  : 'candy-btn-soft hover:border-[#D97706]'
                              }`}
                            >
                              <Check className="w-3.5 h-3.5" />
                              <span>{isActive ? 'ใช้งานอยู่' : 'เลือกใช้'}</span>
                            </button>

                            <button
                              onClick={handleTestPlay}
                              className={`py-1.5 px-3 rounded-xl text-xs font-bold flex items-center justify-center gap-1 transition-all cursor-pointer ${
                                isTestingThis
                                  ? 'candy-btn-honey animate-pulse'
                                  : 'candy-btn-soft hover:text-[#0284C7] hover:border-sky-300'
                              }`}
                              title={isTestingThis ? 'หยุดรัน' : 'ทดสอบรันบนจอ'}
                            >
                              {isTestingThis ? <Square className="w-3.5 h-3.5 fill-current" /> : <Play className="w-3.5 h-3.5 fill-current" />}
                              <span>{isTestingThis ? 'หยุด' : 'รันเลย'}</span>
                            </button>
                          </div>

                          <div className="flex items-center justify-end gap-2">
                            <button
                              onClick={() => handleEdit(m)}
                              className="flex-1 py-1 px-2.5 rounded-lg text-[11px] font-semibold bg-[#FFF9F0] hover:bg-[#FFF0DD] text-[#8A3B04] border border-[#EEDBCE] transition-all flex items-center justify-center gap-1 cursor-pointer"
                            >
                              <Sliders className="w-3 h-3" />
                              แก้ไข
                            </button>

                            <button
                              onClick={() => handleDelete(m.id, m.name)}
                              className="p-1.5 rounded-lg text-xs text-rose-500 hover:text-rose-700 hover:bg-rose-50 border border-transparent hover:border-rose-200 transition-all cursor-pointer"
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
              <div className="p-4 rounded-2xl bg-[#FFF5F5] border-2 border-[#FECDD3] space-y-1.5">
                <div className="flex items-center gap-2 text-rose-600 font-bold text-sm font-heading">
                  <Radio className="w-4 h-4 animate-pulse text-rose-500" />
                  ระบบอัดมาโครสด
                </div>
                <p className="text-xs text-[#6B4226] leading-relaxed">
                  กดเตรียมอัด แล้วเริ่มวิ่งในเกม ระบบจะเริ่มจับเวลา (t=0s) อัตโนมัติเมื่อเริ่มวิ่งจริง รองรับคีย์บอร์ด Space/Z (กระโดด) และ X (สไลด์)
                </p>
              </div>

              {/* Recorder Settings & Trigger */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 rounded-2xl bg-white border-2 border-[#F0DFCE] shadow-sm items-center">
                <div className="md:col-span-2 space-y-1.5">
                  <label className="text-xs font-bold text-[#6B4226]">ชื่อมาโคร:</label>
                  <input
                    type="text"
                    value={recordName}
                    onChange={(e) => setRecordName(e.target.value)}
                    placeholder="เช่น ด่าน 1 วิ่งเก็บเหรียญ"
                    className="w-full px-3.5 py-2 text-xs rounded-xl bg-[#FFFDF6] border-2 border-[#EEDBCE] focus:border-[#F59E0B] focus:outline-none text-[#452311] font-medium"
                  />
                </div>

                <div className="space-y-1.5 flex flex-col justify-end">
                  <label className="text-xs font-bold text-[#6B4226]">สถานะ:</label>
                  <div className="flex items-center gap-2">
                    {recordStatus === 'IDLE' && (
                      <span className="text-xs px-3 py-1.5 rounded-xl bg-[#F8FAFC] text-[#64748B] border border-[#E2E8F0] font-bold flex items-center gap-1.5 w-full justify-center">
                        <Circle className="w-2.5 h-2.5 text-slate-400 fill-slate-400 shrink-0" />
                        <span>พร้อมอัด</span>
                      </span>
                    )}
                    {recordStatus === 'ARMED' && (
                      <span className="text-xs px-3 py-1.5 rounded-xl bg-amber-100 text-amber-800 border border-amber-300 font-bold flex items-center gap-1.5 w-full justify-center animate-pulse">
                        <Circle className="w-2.5 h-2.5 text-amber-500 fill-amber-500 shrink-0 animate-ping" />
                        <span>รอเข้าเกม...</span>
                      </span>
                    )}
                    {recordStatus === 'RECORDING' && (
                      <span className="text-xs px-3 py-1.5 rounded-xl bg-rose-500 text-white font-bold font-mono flex items-center gap-1.5 w-full justify-center shadow-md shadow-rose-500/30">
                        <Circle className="w-2.5 h-2.5 text-white fill-white shrink-0 animate-pulse" />
                        <span>กำลังอัด {recordElapsed}s</span>
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Main Action Trigger Buttons */}
              <div className="flex flex-wrap items-center justify-between gap-3 p-4 rounded-2xl bg-[#FFF9F0] border-2 border-[#F0DFCE]">
                {recordStatus === 'IDLE' && (
                  <button
                    onClick={handleArmRecording}
                    className="candy-btn-strawberry flex-1 py-3 px-5 text-sm font-bold rounded-2xl flex items-center justify-center gap-2 cursor-pointer active:scale-98"
                  >
                    <Radio className="w-4 h-4" />
                    <span>เตรียมเริ่มอัด (รอจับหน้าเกม)</span>
                  </button>
                )}

                {recordStatus === 'ARMED' && (
                  <>
                    <div className="flex-1 flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full bg-amber-500 animate-ping"></div>
                      <span className="text-xs text-[#8A3B04] font-bold">
                        รอตรวจจับหน้าเกมวิ่ง หรือกดเริ่มนับเวลาทันที
                      </span>
                    </div>

                    <button
                      onClick={handleTriggerRecordingNow}
                      className="candy-btn-mint py-2.5 px-4 text-xs font-bold rounded-xl flex items-center gap-1.5 cursor-pointer"
                    >
                      <Zap className="w-3.5 h-3.5 text-amber-200" />
                      <span>เริ่มจับเวลาทันที</span>
                    </button>

                    <button
                      onClick={async () => {
                        if (deviceSerial) await botApi.stopMacroRecording(deviceSerial);
                      }}
                      className="candy-btn-soft py-2.5 px-3 text-xs font-semibold rounded-xl cursor-pointer"
                    >
                      ยกเลิก
                    </button>
                  </>
                )}

                {recordStatus === 'RECORDING' && (
                  <>
                    <div className="flex items-center gap-3">
                      <span className="text-xl font-bold font-mono text-rose-500 flex items-center gap-1">
                        <Clock className="w-4 h-4 inline" />
                        <span>{recordElapsed}s</span>
                      </span>
                      <span className="text-xs px-2.5 py-1 rounded-lg bg-[#FEF3C7] text-[#B45309] border border-[#FCD34D] font-mono font-bold">
                        บันทึกแล้ว {recordActionCount} แอ็กชัน
                      </span>
                    </div>

                    <button
                      onClick={handleStopRecording}
                      className="candy-btn-mint py-2.5 px-5 text-xs font-bold rounded-xl flex items-center gap-2 cursor-pointer"
                    >
                      <Save className="w-4 h-4" />
                      <span>หยุดและบันทึก</span>
                    </button>
                  </>
                )}
              </div>

              {/* Interactive Gameplay Pad during Record */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold text-[#452311] flex items-center gap-1.5 font-heading">
                    <Gamepad2 className="w-4 h-4 text-[#8B5CF6]" />
                    ปุ่มควบคุมสด (Space/Z กระโดด, X สไลด์)
                  </h4>
                  <span className="text-[11px] text-[#8C6D58] font-mono">
                    ส่งคำสั่งเข้าจอพร้อมบันทึกจังหวะ
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  {/* Jump Button Pad */}
                  <button
                    onClick={() => {
                      if (deviceSerial) botApi.recordMacroAction(deviceSerial, 'jump');
                    }}
                    className="h-28 rounded-2xl bg-gradient-to-b from-[#A78BFA] to-[#8B5CF6] border-2 border-[#7C3AED] border-b-4 border-b-[#6D28D9] text-white flex flex-col items-center justify-center gap-1 shadow-lg shadow-purple-500/20 active:translate-y-1 active:border-b-2 transition-all cursor-pointer select-none group"
                  >
                    <ChevronsUp className="w-8 h-8 text-white group-hover:scale-110 transition-transform" />
                    <span className="text-sm font-bold">กระโดด</span>
                    <span className="text-[11px] text-purple-100 font-mono">Space / Z</span>
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
                    className="h-28 rounded-2xl bg-gradient-to-b from-[#FBBF24] to-[#F59E0B] border-2 border-[#D97706] border-b-4 border-b-[#B45309] text-white flex flex-col items-center justify-center gap-1 shadow-lg shadow-amber-500/20 active:translate-y-1 active:border-b-2 transition-all cursor-pointer select-none group"
                  >
                    <ChevronsDown className="w-8 h-8 text-white group-hover:scale-110 transition-transform" />
                    <span className="text-sm font-bold">สไลด์ (กดค้าง)</span>
                    <span className="text-[11px] text-amber-100 font-mono">กดค้าง X</span>
                  </button>
                </div>
              </div>

              {/* Live Action Stream Log */}
              {recentActions.length > 0 && (
                <div className="p-3.5 rounded-2xl bg-white border-2 border-[#F0DFCE] space-y-2">
                  <span className="text-[11px] font-bold text-[#8C6D58]">แอ็กชันล่าสุด:</span>
                  <div className="flex flex-wrap gap-2">
                    {recentActions.map((act, idx) => (
                      <span
                        key={idx}
                        className="px-2.5 py-1 rounded-lg bg-[#FFF9F0] text-xs font-mono border border-[#EEDBCE] flex items-center gap-1.5 animate-fadeIn"
                      >
                        <span className="text-[#8B5CF6] font-bold">{act.t}s:</span>
                        <span className="text-[#452311] font-semibold inline-flex items-center gap-1">
                          {act.action === 'jump' && (
                            <>
                              <ChevronsUp className="w-3.5 h-3.5 text-[#0284C7]" />
                              <span>Jump</span>
                            </>
                          )}
                          {act.action === 'double_jump' && (
                            <>
                              <Rocket className="w-3.5 h-3.5 text-[#7C3AED]" />
                              <span>Double Jump ({act.air_time}s)</span>
                            </>
                          )}
                          {act.action === 'slide' && (
                            <>
                              <ChevronsDown className="w-3.5 h-3.5 text-[#E11D48]" />
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
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 rounded-2xl bg-white border-2 border-[#F0DFCE] shadow-sm">
                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-[#6B4226]">ชื่อมาโคร</label>
                  <input
                    type="text"
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    placeholder="เช่น ด่าน 1 สเต็ปเหรียญ"
                    className="w-full px-3.5 py-2 text-xs rounded-xl bg-[#FFFDF6] border-2 border-[#EEDBCE] focus:border-[#F59E0B] focus:outline-none text-[#452311]"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-[#6B4226]">คำอธิบาย</label>
                  <input
                    type="text"
                    value={editDesc}
                    onChange={(e) => setEditDesc(e.target.value)}
                    placeholder="เช่น กระโดดเก็บเหรียญต้นเกม"
                    className="w-full px-3.5 py-2 text-xs rounded-xl bg-[#FFFDF6] border-2 border-[#EEDBCE] focus:border-[#F59E0B] focus:outline-none text-[#452311]"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-[#6B4226]">ระยะเวลา (วินาที)</label>
                  <input
                    type="number"
                    step="1"
                    min="5"
                    max="600"
                    value={editDuration}
                    onChange={(e) => setEditDuration(Number(e.target.value))}
                    className="w-full px-3.5 py-2 text-xs rounded-xl bg-[#FFFDF6] border-2 border-[#EEDBCE] focus:border-[#F59E0B] focus:outline-none text-[#452311] font-mono"
                  />
                </div>

                <div className="flex items-center justify-between p-2.5 rounded-xl bg-[#FFF9F0] border border-[#EEDBCE] mt-auto">
                  <div className="space-y-0.5">
                    <span className="text-xs font-bold text-[#452311]">วนซ้ำต่อเนื่อง</span>
                    <p className="text-[11px] text-[#8C6D58]">วนกลับมาเริ่มใหม่เมื่อจบไทม์ไลน์</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={editLoop}
                    onChange={(e) => setEditLoop(e.target.checked)}
                    className="w-4 h-4 rounded text-amber-600 focus:ring-amber-500 accent-amber-500"
                  />
                </div>
              </div>

              {/* Quick Action Test Bar */}
              <div className="p-3.5 rounded-2xl bg-[#FFF8EC] border-2 border-[#F0DFCE] flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <Zap className="w-4 h-4 text-[#F59E0B]" />
                  <span className="text-xs font-bold text-[#6B4226]">ทดสอบส่งคำสั่ง:</span>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleTestAction('jump')}
                    disabled={testingAction !== null}
                    className="candy-btn-grape px-3 py-1.5 text-xs font-bold rounded-xl flex items-center gap-1.5 cursor-pointer"
                  >
                    <ChevronsUp className="w-3.5 h-3.5" />
                    <span>กระโดด</span>
                  </button>
                  <button
                    onClick={() => handleTestAction('double_jump', 0.15)}
                    disabled={testingAction !== null}
                    className="candy-btn-honey px-3 py-1.5 text-xs font-bold rounded-xl flex items-center gap-1.5 cursor-pointer"
                  >
                    <Rocket className="w-3.5 h-3.5" />
                    <span>กระโดด 2 ชั้น</span>
                  </button>
                  <button
                    onClick={() => handleTestAction('slide', undefined, 0.4)}
                    disabled={testingAction !== null}
                    className="candy-btn-strawberry px-3 py-1.5 text-xs font-bold rounded-xl flex items-center gap-1.5 cursor-pointer"
                  >
                    <ChevronsDown className="w-3.5 h-3.5" />
                    <span>สไลด์ (0.4s)</span>
                  </button>
                </div>
              </div>

              {/* Time Offset / Delay Adjustment Panel */}
              <div className="p-3.5 rounded-2xl bg-white border-2 border-[#F0DFCE] flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-[#D97706]" />
                  <div>
                    <span className="text-xs font-bold text-[#452311]">ปรับเวลาชดเชย (Time Offset):</span>
                    <p className="text-[11px] text-[#8C6D58]">ขยับเวลาทุกแอ็กชันเร็วขึ้น (-) หรือช้าลง (+)</p>
                  </div>
                </div>
                <div className="flex items-center gap-1.5 flex-wrap">
                  <button
                    onClick={() => handleShiftActions(-1.0)}
                    className="px-2.5 py-1 text-xs font-mono font-bold rounded-lg bg-[#FFF1F2] hover:bg-[#FFE4E6] text-[#E11D48] border border-[#FECDD3] cursor-pointer transition-all active:scale-95"
                    title="เลื่อนทุกแอ็กชันเร็วขึ้น 1.0 วินาที (-1.0s)"
                  >
                    -1.0s
                  </button>
                  <button
                    onClick={() => handleShiftActions(-0.5)}
                    className="px-2.5 py-1 text-xs font-mono font-bold rounded-lg bg-[#FFF1F2] hover:bg-[#FFE4E6] text-[#E11D48] border border-[#FECDD3] cursor-pointer transition-all active:scale-95"
                    title="เลื่อนทุกแอ็กชันเร็วขึ้น 0.5 วินาที (-0.5s)"
                  >
                    -0.5s
                  </button>
                  <button
                    onClick={() => handleShiftActions(-0.2)}
                    className="px-2.5 py-1 text-xs font-mono font-bold rounded-lg bg-[#FFF1F2] hover:bg-[#FFE4E6] text-[#E11D48] border border-[#FECDD3] cursor-pointer transition-all active:scale-95"
                    title="เลื่อนทุกแอ็กชันเร็วขึ้น 0.2 วินาที (-0.2s)"
                  >
                    -0.2s
                  </button>
                  <button
                    onClick={() => handleShiftActions(0.2)}
                    className="px-2.5 py-1 text-xs font-mono font-bold rounded-lg bg-[#F0FDF4] hover:bg-[#DCFCE7] text-[#059669] border border-[#BBF7D0] cursor-pointer transition-all active:scale-95"
                    title="เลื่อนทุกแอ็กชันช้าลง 0.2 วินาที (+0.2s)"
                  >
                    +0.2s
                  </button>
                  <button
                    onClick={() => handleShiftActions(0.5)}
                    className="px-2.5 py-1 text-xs font-mono font-bold rounded-lg bg-[#F0FDF4] hover:bg-[#DCFCE7] text-[#059669] border border-[#BBF7D0] cursor-pointer transition-all active:scale-95"
                    title="เลื่อนทุกแอ็กชันช้าลง 0.5 วินาที (+0.5s)"
                  >
                    +0.5s
                  </button>
                  <button
                    onClick={() => handleShiftActions(1.0)}
                    className="px-2.5 py-1 text-xs font-mono font-bold rounded-lg bg-[#F0FDF4] hover:bg-[#DCFCE7] text-[#059669] border border-[#BBF7D0] cursor-pointer transition-all active:scale-95"
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
                    <h4 className="text-sm font-bold text-[#452311] flex items-center gap-2 font-heading">
                      ไทม์ไลน์แอ็กชัน ({editActions.length})
                    </h4>
                    <p className="text-xs text-[#8C6D58]">เรียงเวลาให้อัตโนมัติเมื่อบันทึก</p>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleAddAction('jump')}
                      className="candy-btn-grape px-2.5 py-1 text-xs font-bold rounded-xl flex items-center gap-1 cursor-pointer"
                    >
                      <Plus className="w-3 h-3" /> + กระโดด
                    </button>
                    <button
                      onClick={() => handleAddAction('double_jump')}
                      className="candy-btn-honey px-2.5 py-1 text-xs font-bold rounded-xl flex items-center gap-1 cursor-pointer"
                    >
                      <Plus className="w-3 h-3" /> + กระโดด 2 ชั้น
                    </button>
                    <button
                      onClick={() => handleAddAction('slide')}
                      className="candy-btn-strawberry px-2.5 py-1 text-xs font-bold rounded-xl flex items-center gap-1 cursor-pointer"
                    >
                      <Plus className="w-3 h-3" /> + สไลด์
                    </button>
                  </div>
                </div>

                {editActions.length === 0 ? (
                  <div className="p-8 text-center border-2 border-dashed border-[#E5D0BD] rounded-2xl bg-[#FFF9F0] text-[#8C6D58] text-xs font-medium">
                    ยังไม่มีแอ็กชันในมาโครนี้ — กดปุ่มเพิ่มด้านบน หรือกดแท็บ "อัดมาโครสด" เพื่ออัดจากการเล่นจริง
                  </div>
                ) : (
                  <div className="space-y-2 max-h-[360px] overflow-y-auto pr-1 custom-scrollbar">
                    {editActions.map((act, idx) => (
                      <div
                        key={idx}
                        className="flex items-center gap-3 p-2.5 rounded-xl bg-white border border-[#EEDBCE] hover:border-[#D4A373] shadow-sm transition-all text-xs"
                      >
                        <span className="text-[11px] font-mono text-[#8C6D58] w-6 text-center font-bold">
                          #{idx + 1}
                        </span>

                        {/* Timestamp */}
                        <div className="flex items-center gap-1.5">
                          <span className="text-[#6B4226] font-semibold">เวลา (t):</span>
                          <input
                            type="number"
                            step="0.05"
                            min="0"
                            value={act.t}
                            onChange={(e) => handleUpdateAction(idx, { t: parseFloat(e.target.value) || 0 })}
                            className="w-20 px-2 py-1 rounded-lg bg-[#FFFDF6] border border-[#EEDBCE] text-[#8B5CF6] font-mono font-bold focus:border-[#F59E0B] focus:outline-none"
                          />
                          <span className="text-[#8C6D58]">วิ</span>
                        </div>

                        {/* Action Selector */}
                        <div className="flex items-center gap-1.5">
                          <select
                            value={act.action}
                            onChange={(e) => handleUpdateAction(idx, { action: e.target.value as any })}
                            className="px-2.5 py-1 rounded-lg bg-[#FFFDF6] border border-[#EEDBCE] text-[#452311] font-bold focus:border-[#F59E0B] focus:outline-none"
                          >
                            <option value="jump">กระโดด</option>
                            <option value="double_jump">กระโดด 2 ชั้น</option>
                            <option value="slide">สไลด์</option>
                          </select>
                        </div>

                        {/* Extra Params */}
                        {act.action === 'double_jump' && (
                          <div className="flex items-center gap-1 text-[#6B4226]">
                            <span className="font-semibold">ช่วงลอย:</span>
                            <input
                              type="number"
                              step="0.01"
                              min="0.05"
                              max="0.4"
                              value={act.air_time || 0.15}
                              onChange={(e) => handleUpdateAction(idx, { air_time: parseFloat(e.target.value) || 0.15 })}
                              className="w-16 px-1.5 py-1 rounded-lg bg-[#FFFDF6] border border-[#EEDBCE] text-[#7C3AED] font-mono font-bold"
                            />
                            <span className="text-[#8C6D58]">วิ</span>
                          </div>
                        )}

                        {act.action === 'slide' && (
                          <div className="flex items-center gap-1 text-[#6B4226]">
                            <span className="font-semibold">ระยะเวลา:</span>
                            <input
                              type="number"
                              step="0.05"
                              min="0.1"
                              max="2.0"
                              value={act.duration || 0.4}
                              onChange={(e) => handleUpdateAction(idx, { duration: parseFloat(e.target.value) || 0.4 })}
                              className="w-16 px-1.5 py-1 rounded-lg bg-[#FFFDF6] border border-[#EEDBCE] text-[#E11D48] font-mono font-bold"
                            />
                            <span className="text-[#8C6D58]">วิ</span>
                          </div>
                        )}

                        {/* Delete Action */}
                        <button
                          onClick={() => handleRemoveAction(idx)}
                          className="ml-auto p-1.5 text-[#8C6D58] hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors cursor-pointer"
                          title="ลบแอ็กชันนี้"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Bottom Editor Action Buttons */}
              <div className="flex items-center justify-between pt-4 border-t-2 border-[#F0DFCE]">
                <button
                  onClick={() => setActiveTab('profiles')}
                  className="candy-btn-soft px-4 py-2 text-xs font-bold rounded-xl cursor-pointer"
                >
                  ย้อนกลับ
                </button>

                <button
                  onClick={handleSave}
                  className="candy-btn-mint px-5 py-2.5 text-xs font-bold rounded-xl flex items-center gap-2 cursor-pointer"
                >
                  <Save className="w-4 h-4" />
                  บันทึก
                </button>
              </div>
            </div>
          )}

        </div>

      </div>
    </div>
  );
};
