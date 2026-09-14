import React from 'react';
import {
  LayoutDashboard,
  Tv,
  Package,
  BarChart3,
  Sliders,
  Settings,
  Wrench,
  HelpCircle,
  Sparkles,
} from 'lucide-react';

export type TabType = 'dashboard' | 'stream' | 'boxes' | 'analytics' | 'macro' | 'tools' | 'settings';

interface SidebarProps {
  activeTab: TabType;
  onSelectTab: (tab: TabType) => void;
  onOpenMacro: () => void;
  onOpenSettings: () => void;
  onOpenTools: () => void;
  onOpenStats: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onSelectTab,
  onOpenMacro,
  onOpenSettings,
  onOpenTools,
  onOpenStats,
}) => {
  const navItems = [
    {
      id: 'dashboard' as TabType,
      label: 'แดชบอร์ด',
      icon: LayoutDashboard,
      action: () => onSelectTab('dashboard'),
    },
    {
      id: 'stream' as TabType,
      label: 'สตรีมจอสด',
      icon: Tv,
      action: () => onSelectTab('stream'),
    },
    {
      id: 'boxes' as TabType,
      label: 'กล่องปริศนา',
      icon: Package,
      action: onOpenStats,
    },
    {
      id: 'analytics' as TabType,
      label: 'สถิติ & กราฟ',
      icon: BarChart3,
      action: () => onSelectTab('analytics'),
    },
    {
      id: 'macro' as TabType,
      label: 'มาโคร / สคริปต์',
      icon: Sliders,
      action: onOpenMacro,
    },
    {
      id: 'tools' as TabType,
      label: 'เครื่องมือบอท',
      icon: Wrench,
      action: onOpenTools,
    },
    {
      id: 'settings' as TabType,
      label: 'ตั้งค่าระบบ',
      icon: Settings,
      action: onOpenSettings,
    },
  ];

  return (
    <aside className="hidden xl:flex flex-col items-center justify-between w-18 py-6 glass-floating rounded-3xl shrink-0 my-4 ml-4 sticky top-6 h-[calc(100vh-3rem)] z-30 shadow-glass">
      {/* Brand Icon Header */}
      <div className="flex flex-col items-center gap-3">
        <div className="relative group cursor-pointer">
          <div className="w-11 h-11 rounded-2xl bg-gradient-to-tr from-brand-600 via-brand-500 to-indigo-500 flex items-center justify-center text-white shadow-md shadow-brand-500/25 transition-transform group-hover:scale-105">
            <span className="text-xl select-none">🍪</span>
          </div>
          <span className="absolute -bottom-1 -right-1 w-3.5 h-3.5 rounded-full bg-emerald-500 border-2 border-white shadow-xs"></span>
        </div>
      </div>

      {/* Main Nav Items */}
      <nav className="flex flex-col items-center gap-2 w-full px-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={item.action}
              className={`relative group w-12 h-12 rounded-2xl flex items-center justify-center transition-all duration-200 ${
                isActive
                  ? 'bg-gradient-to-tr from-brand-600 to-brand-500 text-white shadow-btn scale-105'
                  : 'text-slate-400 hover:text-brand-600 hover:bg-brand-50/80 hover:scale-102'
              }`}
              title={item.label}
            >
              {isActive && (
                <span className="absolute -left-2 top-2.5 bottom-2.5 w-1 bg-brand-600 rounded-full shadow-glow-purple" />
              )}
              <Icon className="w-5 h-5 transition-transform group-hover:scale-110" />

              {/* Tooltip on hover */}
              <span className="absolute left-16 px-2.5 py-1 bg-slate-900/90 backdrop-blur-xs text-white text-xs font-medium rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none shadow-lg z-50">
                {item.label}
              </span>
            </button>
          );
        })}
      </nav>

      {/* Bottom Actions */}
      <div className="flex flex-col items-center gap-2">
        <button
          onClick={onOpenTools}
          className="w-10 h-10 rounded-xl text-slate-400 hover:text-brand-600 hover:bg-brand-50 flex items-center justify-center transition"
          title="ช่วยเหลือ & ข้อมูล"
        >
          <HelpCircle className="w-5 h-5" />
        </button>
      </div>
    </aside>
  );
};
