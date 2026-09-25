import React from 'react';
import {
  LayoutDashboard,
  Receipt,
  UploadCloud,
  Target,
  TrendingUp,
  UserCheck,
  Sparkles,
  Settings,
  ShieldCheck,
  X,
} from 'lucide-react';

export type PageTab =
  | 'dashboard'
  | 'transactions'
  | 'import'
  | 'goals'
  | 'investments'
  | 'profile'
  | 'ai-advisor'
  | 'settings';

interface SidebarProps {
  currentTab: PageTab;
  onSelectTab: (tab: PageTab) => void;
  isMobileOpen?: boolean;
  onCloseMobile?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onSelectTab,
  isMobileOpen = false,
  onCloseMobile,
}) => {
  const navItems = [
    { id: 'dashboard' as PageTab, label: 'Dashboard', icon: LayoutDashboard },
    { id: 'transactions' as PageTab, label: 'Transactions', icon: Receipt },
    { id: 'import' as PageTab, label: 'Import CSV', icon: UploadCloud },
    { id: 'goals' as PageTab, label: 'Goals', icon: Target },
    { id: 'investments' as PageTab, label: 'Investments', icon: TrendingUp },
    { id: 'profile' as PageTab, label: 'Financial Profile', icon: UserCheck },
    { id: 'ai-advisor' as PageTab, label: 'AI Advisor', icon: Sparkles },
    { id: 'settings' as PageTab, label: 'Settings', icon: Settings },
  ];

  const handleSelect = (tab: PageTab) => {
    onSelectTab(tab);
    if (onCloseMobile) onCloseMobile();
  };

  const content = (
    <div className="flex flex-col h-full justify-between p-4 bg-white select-none">
      <div className="space-y-1">
        {/* Mobile close button */}
        <div className="md:hidden flex items-center justify-between pb-3 px-2 border-b border-slate-100">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Navigation</span>
          <button
            onClick={onCloseMobile}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="px-3 py-2 text-[11px] font-semibold tracking-wider text-slate-400 uppercase hidden md:block">
          Menu
        </div>

        <nav className="space-y-1" aria-label="Main Navigation">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => handleSelect(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-teal-50 text-teal-800 font-semibold shadow-2xs'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                }`}
              >
                <Icon
                  className={`w-4 h-4 shrink-0 transition-colors ${
                    isActive ? 'text-teal-600' : 'text-slate-400'
                  }`}
                />
                <span className="truncate">{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Decision-Support System Calm Notice */}
      <div className="p-3.5 rounded-xl border border-slate-200/80 bg-slate-50/80 text-xs text-slate-500 space-y-1">
        <div className="flex items-center gap-1.5 text-slate-700 font-semibold text-[11px]">
          <ShieldCheck className="w-3.5 h-3.5 text-teal-600 shrink-0" />
          <span>Decision Support</span>
        </div>
        <p className="text-[11px] leading-relaxed text-slate-500">
          FinMate helps you evaluate spending and plan targets. You remain in control of every transaction.
        </p>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Persistent Sidebar */}
      <aside className="w-60 border-r border-slate-200/80 bg-white hidden md:flex flex-col shrink-0">
        {content}
      </aside>

      {/* Mobile Drawer */}
      {isMobileOpen && (
        <div className="fixed inset-0 z-40 md:hidden flex">
          <div
            className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs transition-opacity"
            onClick={onCloseMobile}
          />
          <aside className="relative w-64 max-w-xs bg-white shadow-xl z-50 flex flex-col">
            {content}
          </aside>
        </div>
      )}
    </>
  );
};
