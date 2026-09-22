import React from 'react';
import {
  LayoutDashboard,
  Receipt,
  UploadCloud,
  Target,
  TrendingUp,
  UserCheck,
  BrainCircuit,
  Settings,
  ShieldAlert,
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
  duplicateCount?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, onSelectTab, duplicateCount = 0 }) => {
  const navItems = [
    { id: 'dashboard' as PageTab, label: 'Dashboard', icon: LayoutDashboard },
    { id: 'transactions' as PageTab, label: 'Transactions', icon: Receipt },
    {
      id: 'import' as PageTab,
      label: 'CSV Import',
      icon: UploadCloud,
      badge: 'Phase 2',
      badgeColor: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
    },
    { id: 'goals' as PageTab, label: 'Goals', icon: Target },
    { id: 'investments' as PageTab, label: 'Investments', icon: TrendingUp },
    { id: 'profile' as PageTab, label: 'Financial Profile', icon: UserCheck },
    {
      id: 'ai-advisor' as PageTab,
      label: 'AI Advisor',
      icon: BrainCircuit,
      badge: 'Future',
      badgeColor: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
    },
    { id: 'settings' as PageTab, label: 'Settings', icon: Settings },
  ];

  return (
    <aside className="w-64 border-r border-slate-800 bg-slate-950 flex flex-col justify-between shrink-0">
      <div className="p-4 space-y-1">
        <div className="px-3 py-2 text-[11px] font-semibold tracking-wider text-slate-500 uppercase">
          Financial Management
        </div>

        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-sm font-medium transition ${
                isActive
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon className={`w-4 h-4 ${isActive ? 'text-emerald-400' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono border ${item.badgeColor}`}>
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Decision-Support System Notice */}
      <div className="p-4 m-3 rounded-xl border border-slate-800/80 bg-slate-900/50 text-xs text-slate-400 space-y-1.5">
        <div className="flex items-center gap-1.5 text-slate-300 font-semibold text-[11px]">
          <ShieldAlert className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
          <span>Decision Support System</span>
        </div>
        <p className="text-[11px] leading-relaxed text-slate-400">
          FinMate assists and informs your financial planning. You remain in control of every transaction and decision.
        </p>
      </div>
    </aside>
  );
};
