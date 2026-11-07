import React, { useState } from 'react';
import { EngineeringConsole } from '../consoles/shared/EngineeringConsole';
import { ConsoleTabs } from '../consoles/shared/ConsoleComponents';

export function SettingsPage() {
  const [activeTab, setActiveTab] = useState('general');

  const tabs = [
    { id: 'general', label: 'General' },
    { id: 'appearance', label: 'Appearance' },
    { id: 'editor', label: 'Editor' },
    { id: 'workspace', label: 'Workspace' },
    { id: 'models', label: 'AI Models' },
    { id: 'providers', label: 'Providers' },
    { id: 'git', label: 'Git' },
    { id: 'runtime', label: 'Runtime' },
    { id: 'testing', label: 'Testing' },
    { id: 'security', label: 'Security' },
    { id: 'notifications', label: 'Notifications' },
    { id: 'account', label: 'Account' },
  ];

  return (
    <EngineeringConsole
      title="Engineering Settings"
      description="Configure workspace, agent, and system parameters"
      toolbarNode={
        <>
          <button className="consoleBtn primary">Save Preferences</button>
          <button className="consoleBtn">Discard Changes</button>
        </>
      }
    >
      <div style={{ display: 'flex', height: '100%' }}>
        <aside style={{ width: 220, borderRight: '1px solid #2b2b2b', background: '#1a1a1a', padding: '16px 0', display: 'flex', flexDirection: 'column' }}>
          {tabs.map(tab => (
            <div
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                padding: '10px 24px',
                cursor: 'pointer',
                background: activeTab === tab.id ? 'rgba(255,255,255,0.05)' : 'transparent',
                borderLeft: `3px solid ${activeTab === tab.id ? '#007ACC' : 'transparent'}`,
                color: activeTab === tab.id ? '#fff' : '#ccc',
                fontSize: 14
              }}
            >
              {tab.label}
            </div>
          ))}
        </aside>
        
        <main style={{ flex: 1, padding: 32, overflowY: 'auto' }}>
          <h2 style={{ margin: '0 0 24px 0', color: '#fff' }}>{tabs.find(t => t.id === activeTab)?.label} Settings</h2>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: 24, maxWidth: 600 }}>
            {/* Settings Form Fields based on tab */}
            {activeTab === 'general' && (
              <>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <label style={{ fontSize: 13, color: '#ccc' }}>Workspace Name</label>
                  <input type="text" defaultValue="SEAM Workspace" style={{ background: '#111', border: '1px solid #333', padding: '8px 12px', color: '#fff', borderRadius: 4 }} />
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <label style={{ fontSize: 13, color: '#ccc' }}>Telemetry Level</label>
                  <select style={{ background: '#111', border: '1px solid #333', padding: '8px 12px', color: '#fff', borderRadius: 4 }}>
                    <option>Full (Errors + Usage)</option>
                    <option>Errors Only</option>
                    <option>None</option>
                  </select>
                </div>
              </>
            )}

            {activeTab === 'models' && (
              <>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <label style={{ fontSize: 13, color: '#ccc' }}>Primary Model Selection</label>
                  <select style={{ background: '#111', border: '1px solid #333', padding: '8px 12px', color: '#fff', borderRadius: 4 }}>
                    <option>Auto (Hardware-Aware Routing)</option>
                    <option>ai/qwen3:4b-instruct-2507-q4_K_M (Local)</option>
                    <option>qwen3.8-flash-next (Local High-Tier)</option>
                  </select>
                  <p style={{ margin: 0, fontSize: 11, color: '#888' }}>Forces model selection, bypassing the model router logic.</p>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <label style={{ fontSize: 13, color: '#ccc' }}>Context Window Limit</label>
                  <input type="number" defaultValue={32000} style={{ background: '#111', border: '1px solid #333', padding: '8px 12px', color: '#fff', borderRadius: 4 }} />
                </div>
              </>
            )}

            {activeTab === 'account' && (
              <>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <label style={{ fontSize: 13, color: '#ccc' }}>Account Status</label>
                  <div style={{ color: '#73C991', fontSize: 14 }}>✓ Authenticated via Firebase</div>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <label style={{ fontSize: 13, color: '#ccc' }}>Email</label>
                  <input type="email" defaultValue="engineer@seam.internal" disabled style={{ background: '#111', border: '1px solid #333', padding: '8px 12px', color: '#888', borderRadius: 4 }} />
                </div>
              </>
            )}

            {['appearance', 'editor', 'workspace', 'providers', 'git', 'runtime', 'testing', 'security', 'notifications'].includes(activeTab) && (
              <div style={{ color: '#888', fontSize: 14 }}>
                Configuration fields for {activeTab} will appear here.
              </div>
            )}
          </div>
        </main>
      </div>
    </EngineeringConsole>
  );
}
