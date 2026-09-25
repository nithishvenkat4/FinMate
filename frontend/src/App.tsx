import React, { useState } from 'react';
import { Header } from './components/common/Header';
import { PageTab, Sidebar } from './components/common/Sidebar';
import { AIAdvisorPage } from './pages/AIAdvisorPage';
import { CSVImportPage } from './pages/CSVImportPage';
import { DashboardPage } from './pages/DashboardPage';
import { GoalsPage } from './pages/GoalsPage';
import { InvestmentsPage } from './pages/InvestmentsPage';
import { ProfilePage } from './pages/ProfilePage';
import { SettingsPage } from './pages/SettingsPage';
import { TransactionsPage } from './pages/TransactionsPage';

export function App() {
  const [currentTab, setCurrentTab] = useState<PageTab>('dashboard');
  const [refreshKey, setRefreshKey] = useState(0);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  const handleGlobalRefresh = () => {
    setIsRefreshing(true);
    setRefreshKey((k) => k + 1);
    setTimeout(() => setIsRefreshing(false), 500);
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col antialiased">
      <Header
        onRefresh={handleGlobalRefresh}
        isRefreshing={isRefreshing}
        onToggleMobileSidebar={() => setIsMobileSidebarOpen(true)}
        onNavigateTab={setCurrentTab}
      />

      <div className="flex-1 flex overflow-hidden">
        <Sidebar
          currentTab={currentTab}
          onSelectTab={setCurrentTab}
          isMobileOpen={isMobileSidebarOpen}
          onCloseMobile={() => setIsMobileSidebarOpen(false)}
        />

        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
          <div className="max-w-7xl mx-auto">
            {currentTab === 'dashboard' && (
              <DashboardPage onNavigateTab={setCurrentTab} refreshKey={refreshKey} />
            )}
            {currentTab === 'transactions' && (
              <TransactionsPage
                refreshKey={refreshKey}
                onRefresh={handleGlobalRefresh}
                onNavigateTab={setCurrentTab}
              />
            )}
            {currentTab === 'import' && (
              <CSVImportPage
                onImportSuccess={handleGlobalRefresh}
                onNavigateTab={setCurrentTab}
              />
            )}
            {currentTab === 'goals' && (
              <GoalsPage
                refreshKey={refreshKey}
                onRefresh={handleGlobalRefresh}
              />
            )}
            {currentTab === 'investments' && (
              <InvestmentsPage
                refreshKey={refreshKey}
                onRefresh={handleGlobalRefresh}
              />
            )}
            {currentTab === 'profile' && (
              <ProfilePage
                refreshKey={refreshKey}
                onRefresh={handleGlobalRefresh}
              />
            )}
            {currentTab === 'ai-advisor' && <AIAdvisorPage />}
            {currentTab === 'settings' && <SettingsPage onNavigateTab={setCurrentTab} />}
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
