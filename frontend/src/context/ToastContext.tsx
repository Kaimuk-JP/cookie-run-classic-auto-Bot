import React, { createContext, useContext, useState, useCallback } from 'react';
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Info,
  X,
  AlertCircle,
  HelpCircle,
} from 'lucide-react';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface ToastItem {
  id: string;
  type: ToastType;
  message: string;
  title?: string;
}

export interface ConfirmOptions {
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  type?: 'danger' | 'warning' | 'info';
}

interface ToastContextType {
  showToast: (type: ToastType, message: string, title?: string) => void;
  confirm: (options: ConfirmOptions) => Promise<boolean>;
}

const ToastContext = createContext<ToastContextType | null>(null);

let globalToast: ((type: ToastType, message: string, title?: string) => void) | null = null;
let globalConfirm: ((options: ConfirmOptions) => Promise<boolean>) | null = null;

export const toast = {
  success: (message: string, title?: string) => globalToast?.('success', message, title),
  error: (message: string, title?: string) => globalToast?.('error', message, title),
  warning: (message: string, title?: string) => globalToast?.('warning', message, title),
  info: (message: string, title?: string) => globalToast?.('info', message, title),
};

export const confirmModal = (options: ConfirmOptions) => {
  if (globalConfirm) {
    return globalConfirm(options);
  }
  return Promise.resolve(window.confirm(options.message));
};

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const [confirmState, setConfirmState] = useState<{
    isOpen: boolean;
    options: ConfirmOptions;
    resolve: ((value: boolean) => void) | null;
  }>({
    isOpen: false,
    options: { title: '', message: '' },
    resolve: null,
  });

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const showToast = useCallback((type: ToastType, message: string, title?: string) => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev.slice(-4), { id, type, message, title }]);

    setTimeout(() => {
      removeToast(id);
    }, 4000);
  }, [removeToast]);

  const confirm = useCallback((options: ConfirmOptions): Promise<boolean> => {
    return new Promise((resolve) => {
      setConfirmState({
        isOpen: true,
        options,
        resolve,
      });
    });
  }, []);

  // Bind to globals
  globalToast = showToast;
  globalConfirm = confirm;

  const handleConfirmClose = (result: boolean) => {
    if (confirmState.resolve) {
      confirmState.resolve(result);
    }
    setConfirmState((prev) => ({ ...prev, isOpen: false, resolve: null }));
  };

  return (
    <ToastContext.Provider value={{ showToast, confirm }}>
      {children}

      {/* Floating Toasts Container */}
      <div className="fixed top-5 right-5 z-[9999] flex flex-col gap-2.5 max-w-sm w-full pointer-events-none">
        {toasts.map((item) => (
          <div
            key={item.id}
            className={`pointer-events-auto p-4 rounded-2xl shadow-xl border backdrop-blur-md transition-all animate-in slide-in-from-top-3 fade-in duration-200 flex items-start gap-3 ${
              item.type === 'success'
                ? 'bg-emerald-950/90 text-emerald-50 border-emerald-700/60 shadow-emerald-950/20'
                : item.type === 'error'
                ? 'bg-rose-950/90 text-rose-50 border-rose-700/60 shadow-rose-950/20'
                : item.type === 'warning'
                ? 'bg-amber-950/90 text-amber-50 border-amber-700/60 shadow-amber-950/20'
                : 'bg-slate-900/90 text-slate-50 border-slate-700/60 shadow-slate-950/20'
            }`}
          >
            <div className="shrink-0 mt-0.5">
              {item.type === 'success' && (
                <div className="w-7 h-7 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center border border-emerald-500/30">
                  <CheckCircle2 className="w-4 h-4" />
                </div>
              )}
              {item.type === 'error' && (
                <div className="w-7 h-7 rounded-xl bg-rose-500/20 text-rose-400 flex items-center justify-center border border-rose-500/30">
                  <XCircle className="w-4 h-4" />
                </div>
              )}
              {item.type === 'warning' && (
                <div className="w-7 h-7 rounded-xl bg-amber-500/20 text-amber-400 flex items-center justify-center border border-amber-500/30">
                  <AlertTriangle className="w-4 h-4" />
                </div>
              )}
              {item.type === 'info' && (
                <div className="w-7 h-7 rounded-xl bg-indigo-500/20 text-indigo-400 flex items-center justify-center border border-indigo-500/30">
                  <Info className="w-4 h-4" />
                </div>
              )}
            </div>

            <div className="flex-1 min-w-0 pr-1">
              {item.title && (
                <h4 className="text-xs font-bold tracking-wide uppercase opacity-90 mb-0.5">
                  {item.title}
                </h4>
              )}
              <p className="text-xs font-medium leading-relaxed break-words opacity-95">
                {item.message}
              </p>
            </div>

            <button
              onClick={() => removeToast(item.id)}
              className="shrink-0 text-white/50 hover:text-white p-1 rounded-lg hover:bg-white/10 transition cursor-pointer"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        ))}
      </div>

      {/* Modern Confirm Modal */}
      {confirmState.isOpen && (
        <div className="fixed inset-0 z-[99999] bg-slate-950/60 backdrop-blur-xs flex items-center justify-center p-4 animate-in fade-in duration-150">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 space-y-4 shadow-2xl border border-slate-100 animate-in zoom-in-95 duration-150">
            <div className="flex items-start gap-3.5">
              <div
                className={`w-12 h-12 rounded-2xl flex items-center justify-center shrink-0 border ${
                  confirmState.options.type === 'danger'
                    ? 'bg-rose-50 text-rose-600 border-rose-100 shadow-xs'
                    : confirmState.options.type === 'warning'
                    ? 'bg-amber-50 text-amber-600 border-amber-100 shadow-xs'
                    : 'bg-brand-50 text-brand-600 border-brand-100 shadow-xs'
                }`}
              >
                {confirmState.options.type === 'danger' ? (
                  <AlertCircle className="w-6 h-6" />
                ) : confirmState.options.type === 'warning' ? (
                  <AlertTriangle className="w-6 h-6" />
                ) : (
                  <HelpCircle className="w-6 h-6" />
                )}
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900 leading-snug">
                  {confirmState.options.title || 'ยืนยันการทำรายการ'}
                </h3>
                <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                  {confirmState.options.message}
                </p>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
              <button
                onClick={() => handleConfirmClose(false)}
                className="px-4 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs transition cursor-pointer"
              >
                {confirmState.options.cancelText || 'ยกเลิก'}
              </button>
              <button
                onClick={() => handleConfirmClose(true)}
                className={`px-5 py-2.5 rounded-xl text-white font-bold text-xs shadow-btn transition active:scale-95 cursor-pointer ${
                  confirmState.options.type === 'danger'
                    ? 'bg-rose-600 hover:bg-rose-700'
                    : confirmState.options.type === 'warning'
                    ? 'bg-amber-600 hover:bg-amber-700'
                    : 'bg-brand-600 hover:bg-brand-700'
                }`}
              >
                {confirmState.options.confirmText || 'ยืนยัน'}
              </button>
            </div>
          </div>
        </div>
      )}
    </ToastContext.Provider>
  );
};

export const useToast = () => {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return ctx;
};
