import { useEffect, useMemo, useRef, useState } from "react";
import { SplashScreen, useStartupSequence } from "@/components/splash";
import { WelcomeOnboarding } from "@/components/onboarding";
import { useVoiceSession, VoiceCommandDraft, VoiceModeSelector, VoiceStatusPanel, VoiceTranscriptPanel } from "@/components/voice";
import { ActionPreviewCard } from "@/components/action-preview";
import { clearProfile, checkMicrophonePermission, clearMicrophonePermissionRecord, formatAddressingName, getMicrophoneStatusLabel, getIntentLabel, isCommandSensitive, shouldAskConfirmation, createActionPreview, detectCommandIntent, loadMicrophonePermissionRecord, loadProfile, isOnboardingComplete, MicrophonePermissionStatus, requestMicrophoneAccess, saveMicrophonePermissionRecord, UserProfile, CommandUnderstandingResult, CommandIntent, CommandRiskLevel, requestBackendCommandPreview, BackendCommandPreviewResponse, createCommandHistoryEntry, saveCommandHistoryEntry, loadCommandHistory, clearCommandHistory, getLatestCommandHistory, deleteCommandHistoryEntry, CommandHistoryEntry, BackendAuditPreviewResponse, requestBackendAuditPreview, BackendAuditHealthResponse, getBackendAuditHealth, BackendAuditMigrationPreviewResponse, getBackendAuditMigrationPreview, BackendDatabaseStatusResponse, getBackendDatabaseStatus, BackendSystemStatusSummary, getBackendSystemStatus } from "@/lib";

type BackendStatus = "checking" | "connected" | "offline";

type BackendHealth = {
  status?: string;
  app?: string;
  version?: string;
  environment?: string;
  phase?: string;
  message?: string;
};

type PageId =
  | "dashboard"
  | "voice"
  | "commands"
  | "automations"
  | "files"
  | "launcher"
  | "web"
  | "chat"
  | "history"
  | "settings"
  | "security";

const navItems: Array<{ id: PageId; label: string; description: string }> = [
  { id: "dashboard", label: "Dashboard", description: "Main command center" },
  { id: "voice", label: "Voice", description: "Voice assistant interface" },
  { id: "commands", label: "Commands", description: "Intent and command testing" },
  { id: "automations", label: "Automations", description: "Workflow builder" },
  { id: "files", label: "File Organizer", description: "Search and organize files" },
  { id: "launcher", label: "App Launcher", description: "Open apps and websites" },
  { id: "web", label: "Web Search", description: "News, weather, dictionary" },
  { id: "chat", label: "AI Chat", description: "Assistant conversation" },
  { id: "history", label: "History", description: "Command activity logs" },
  { id: "settings", label: "Settings", description: "Profile and preferences" },
  { id: "security", label: "Security", description: "Permissions and safety" },
];

const quickActions = [
  { title: "Open YouTube", subtitle: "Launch media workspace", accent: "#ef4444" },
  { title: "Organize Files", subtitle: "Sort downloads and documents", accent: "#00e5ff" },
  { title: "Start Study Mode", subtitle: "Focus timer and learning setup", accent: "#22c55e" },
  { title: "Ask AI", subtitle: "Talk naturally with Nexa", accent: "#8b5cf6" },
  { title: "System Status", subtitle: "View backend preview services and database readiness", accent: "#6366f1", page: "settings" as PageId },
];

const dashboardMetrics = [
  { title: "Voice Core", value: "Visual Ready", detail: "STT/TTS will be added later", color: "#00e5ff" },
  { title: "Command Brain", value: "Planned", detail: "Bangla/English intent engine", color: "#8b5cf6" },
  { title: "Desktop Shell", value: "Active", detail: "Electron renderer is working", color: "#22c55e" },
  { title: "Automation", value: "Pending", detail: "Safe action executor later", color: "#f59e0b" },
];

const activityItems = [
  { title: "Desktop shell initialized", text: "Electron window and React renderer are running." },
  { title: "Sidebar navigation active", text: "Dashboard and module pages can be switched." },
  { title: "Backend health watcher added", text: "FastAPI health state can be detected from the desktop UI." },
];

const defaultDemoTranscript = "ইউটিউব খুলে একটা বাংলা গান চালাও";

const liveTranscriptPhrases = [
  "ইউটিউব",
  "ইউটিউব খুলে",
  "ইউটিউব খুলে একটা",
  "ইউটিউব খুলে একটা বাংলা গান",
  defaultDemoTranscript,
];

const pageCards: Record<PageId, Array<{ title: string; text: string }>> = {
  dashboard: [
    { title: "Voice Core", text: "Listening UI is ready. Real STT comes later." },
    { title: "Command Input", text: "Typed command execution will be added soon." },
    { title: "Backend Health", text: "FastAPI health state is displayed live." },
  ],
  commands: [
    { title: "Intent Detection", text: "Detect open_app, youtube_search, file_search, reminder_create, and more." },
    { title: "Bangla/Banglish Support", text: "Commands like ইউটিউব খুলো, YouTube open koro, and song চালাও will be mapped." },
    { title: "Confidence Score", text: "Low-confidence commands will ask clarification before execution." },
  ],
  automations: [
    { title: "Workflow Steps", text: "Multi-step desktop workflows will be designed here." },
    { title: "Safe Run", text: "Sensitive automation steps will need confirmation." },
    { title: "Run History", text: "Automation results will be logged." },
  ],
  files: [
    { title: "File Search", text: "Search Desktop, Downloads, Documents by partial name and type." },
    { title: "Organizer Preview", text: "Preview moves before changing files." },
    { title: "Undo Support", text: "Safe file operations will keep history." },
  ],
  launcher: [
    { title: "Apps", text: "Launch Chrome, VS Code, WhatsApp, YouTube, and more." },
    { title: "Websites", text: "Open saved URLs through natural commands." },
    { title: "Aliases", text: "Multiple names can point to the same app." },
  ],
  web: [
    { title: "Weather", text: "Free/public sources only." },
    { title: "News", text: "RSS-based news retrieval planned." },
    { title: "Dictionary", text: "English-Bangla meaning support planned." },
  ],
  chat: [
    { title: "Assistant Chat", text: "Conversational UI will live here." },
    { title: "Memory Context", text: "Local SQLite memory will personalize replies." },
    { title: "Study Help", text: "Student-friendly explanation mode planned." },
  ],
  history: [
    { title: "Command Logs", text: "Previous requests and results." },
    { title: "Corrections", text: "Wrongly understood commands can be improved." },
    { title: "Audit Trail", text: "Sensitive actions will be traceable." },
  ],
  settings: [
    { title: "Profile", text: "Name, language, and addressing style." },
    { title: "Voice", text: "Voice preference and response style." },
    { title: "Performance", text: "Low-end laptop friendly options." },
  ],
  security: [
    { title: "Permissions", text: "Mic, files, browser, apps, and internet access." },
    { title: "Confirmation Rules", text: "Delete, send, shutdown, and move actions guarded." },
    { title: "Privacy", text: "Local-first data and memory reset controls." },
  ],
  voice: [
    { title: "Voice UI", text: "Frontend-only voice panels for future STT/TTS integration." },
    { title: "Mode Selector", text: "Switch between push-to-talk and always listening later." },
    { title: "Transcript Preview", text: "Transcript and command drafts are visible here." },
  ],
};

export default function App() {
  const platform = window.nexa?.platform ?? "win32";
  const appMode = window.nexa?.appMode ?? "desktop";
  const backendUrl = window.nexa?.backendUrl ?? "http://127.0.0.1:8000";

  const [showSplash, setShowSplash] = useState(true);
  const [profile, setProfile] = useState<UserProfile>(() => loadProfile());
  const [showOnboarding, setShowOnboarding] = useState(() => !isOnboardingComplete());
  const startup = useStartupSequence();

  const [activePage, setActivePage] = useState<PageId>("dashboard");
  const [backendStatus, setBackendStatus] = useState<BackendStatus>("checking");
  const [backendHealth, setBackendHealth] = useState<BackendHealth | null>(null);
  const [draftCommand, setDraftCommand] = useState("Open YouTube and play a relaxing Bangla song");

  const activeNav = navItems.find((item) => item.id === activePage) ?? navItems[0];
  const backendConnected = backendStatus === "connected";

  const commandPreview = useMemo(() => {
    if (!draftCommand.trim()) return "Waiting for your command...";
    return draftCommand.trim();
  }, [draftCommand]);

  useEffect(() => {
    let timeout: number | undefined;
    if (startup.isComplete) {
      timeout = window.setTimeout(() => {
        setShowSplash(false);
      }, 400);
    }
    return () => {
      if (timeout !== undefined) {
        window.clearTimeout(timeout);
      }
    };
  }, [startup.isComplete]);

  useEffect(() => {
    const checkBackend = async () => {
      try {
        setBackendStatus("checking");
        const response = await fetch(`${backendUrl}/api/health`);
        if (!response.ok) throw new Error("Backend health request failed");
        const data = (await response.json()) as BackendHealth;
        setBackendHealth(data);
        setBackendStatus("connected");
      } catch {
        setBackendHealth(null);
        setBackendStatus("offline");
      }
    };

    checkBackend();
    const timer = window.setInterval(checkBackend, 10000);
    return () => window.clearInterval(timer);
  }, [backendUrl]);

  const handleResetSetup = () => {
    clearProfile();
    const freshProfile = loadProfile();
    setProfile(freshProfile);
    setShowOnboarding(true);
    setActivePage("dashboard");
  };

  if (showSplash) {
    return (
      <SplashScreen
        progress={startup.progress}
        statusText={startup.statusText}
        activeStep={startup.activeStep}
        steps={startup.steps}
      />
    );
  }

  if (showOnboarding) {
    return (
      <WelcomeOnboarding
        onContinue={(savedProfile) => {
          if (savedProfile) {
            setProfile(savedProfile);
          }
          setShowOnboarding(false);
        }}
      />
    );
  }

  return (
    <main className="desktop-app dashboard-enter">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-orb">N</div>
          <div>
            <h1>Nexa AI</h1>
            <p>Desktop Assistant</p>
          </div>
        </div>

        <nav className="nav-list">
          {navItems.map((item) => (
            <button
              key={item.id}
              className={activePage === item.id ? "nav-item active" : "nav-item"}
              type="button"
              onClick={() => setActivePage(item.id)}
            >
              <span>{item.label}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-card">
          <p>Profile</p>
          <strong>{profile.userName ? profile.userName : "Local User"}</strong>
          <span>Profile: {profile.userName ? profile.userName : "Local User"}</span>
        </div>

        <div className="sidebar-card">
          <p>Backend</p>
          <strong>{backendConnected ? "Connected" : "Pending"}</strong>
          <span>
            {backendConnected
              ? "Python FastAPI is reachable."
              : "Start Python backend to enable real actions."}
          </span>
        </div>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">Phase 16.2</p>
            <h2>{activeNav.label}</h2>
          </div>

          <div className="topbar-actions">
            <div className="mode-badge">{appMode.toUpperCase()} · {platform}</div>
            <div className={backendConnected ? "backend-badge connected" : "backend-badge"}>
              {backendConnected ? "Backend Connected" : "Backend Pending"}
            </div>
          </div>
        </header>

        {activePage === "dashboard" ? (
          <DashboardPage
            backendConnected={backendConnected}
            backendHealth={backendHealth}
            draftCommand={draftCommand}
            commandPreview={commandPreview}
            onCommandChange={setDraftCommand}
            onOpenSettings={() => setActivePage("settings")}
          />
        ) : (
          <ModulePage
            page={activePage}
            pageTitle={activeNav.label}
            description={activeNav.description}
            profile={profile}
            onResetSetup={handleResetSetup}
          />
        )}

        <section className="quick-section">
          <div className="section-title">
            <p className="eyebrow">Quick Actions</p>
            <h3>Desktop Assistant Shortcuts</h3>
          </div>

          <div className="quick-grid">
            {quickActions.map((action) => (
              <button
                className="quick-card"
                key={action.title}
                type="button"
                onClick={() => {
                  if ("page" in action && action.page) {
                    setActivePage(action.page as PageId);
                  }
                }}
              >
                <span style={{ background: action.accent }} />
                <h4>{action.title}</h4>
                <p>{action.subtitle}</p>
              </button>
            ))}
          </div>
        </section>

        <footer className="footer-strip">
          <span>Private</span>
          <span>Secure</span>
          <span>Desktop Ready</span>
          <span>Core Pages Active</span>
        </footer>
      </section>
    </main>
  );
}

function DashboardPage({
  backendConnected,
  backendHealth,
  draftCommand,
  commandPreview,
  onCommandChange,
  onOpenSettings,
}: {
  backendConnected: boolean;
  backendHealth: BackendHealth | null;
  draftCommand: string;
  commandPreview: string;
  onCommandChange: (value: string) => void;
  onOpenSettings?: () => void;
}) {
  const [dashboardSystemStatus, setDashboardSystemStatus] = useState<BackendSystemStatusSummary | null>(null);
  const [dashboardSystemStatusLoading, setDashboardSystemStatusLoading] = useState(false);
  const [dashboardSystemStatusError, setDashboardSystemStatusError] = useState<string | null>(null);

  useEffect(() => {
    handleRefreshDashboardSystemStatus();
  }, []);

  const handleRefreshDashboardSystemStatus = async () => {
    setDashboardSystemStatusLoading(true);
    setDashboardSystemStatusError(null);
    try {
      const response = await getBackendSystemStatus();
      setDashboardSystemStatus(response);
    } catch (err) {
      setDashboardSystemStatusError(err instanceof Error ? err.message : "Failed to check system status.");
    } finally {
      setDashboardSystemStatusLoading(false);
    }
  };

  const formatTime = (iso: string) => {
    try {
      return new Date(iso).toLocaleString();
    } catch {
      return iso;
    }
  };

  const dashboardBackendOffline =
    !!dashboardSystemStatusError ||
    (dashboardSystemStatus !== null && dashboardSystemStatus.modules.some((m) => !m.ok));

  const onlineCount = dashboardSystemStatus
    ? dashboardSystemStatus.modules.filter((m) => m.ok).length
    : 0;
  const offlineCount = dashboardSystemStatus
    ? dashboardSystemStatus.modules.filter((m) => !m.ok).length
    : 0;

  return (
    <div className="dashboard-layout">
      <section className="dashboard-main">
        <div className="dashboard-hero">
          <div className="hero-copy">
            <p className="eyebrow">Polished Dashboard</p>
            <h3>Nexa <span>AI</span></h3>
            <p>
              Your futuristic Windows desktop assistant command center is taking shape.
              The UI now has a stronger dashboard surface for voice, command, automation,
              and backend state.
            </p>
          </div>

          <div className="voice-orb-wrap">
            <div className="voice-orb"><div className="voice-orb-core" /></div>
            <p>Voice UI Standby</p>
          </div>
        </div>

        <div className="command-console">
          <div>
            <p className="eyebrow">Command Preview</p>
            <h4>{commandPreview}</h4>
          </div>

          <div className="command-editor">
            <input
              value={draftCommand}
              onChange={(event) => onCommandChange(event.target.value)}
              placeholder="Type a future voice command..."
            />
            <button type="button">Preview</button>
          </div>
        </div>

        <div className="metric-grid">
          {dashboardMetrics.map((metric) => (
            <div className="dashboard-metric" key={metric.title}>
              <span style={{ background: metric.color }} />
              <p>{metric.title}</p>
              <h4 style={{ color: metric.color }}>{metric.value}</h4>
              <small>{metric.detail}</small>
            </div>
          ))}
        </div>

        <div className="roadmap-panel">
          <p className="eyebrow">Next Build Path</p>
          <h4>From UI shell to real assistant behavior</h4>
          <div className="roadmap-steps">
            <span>Pages</span>
            <span>Command Engine</span>
            <span>Voice</span>
            <span>Automation</span>
          </div>
        </div>
      </section>

      <aside className="dashboard-side">
        <StatusPanel backendConnected={backendConnected} />
        <BackendPanel backendConnected={backendConnected} backendHealth={backendHealth} />
        <ActivityPanel />
        <div className="dashboard-system-card">
          <div className="dashboard-system-header">
            <p className="eyebrow">System Status</p>
            <button
              type="button"
              className="dashboard-system-button"
              onClick={handleRefreshDashboardSystemStatus}
              disabled={dashboardSystemStatusLoading}
            >
              {dashboardSystemStatusLoading ? "Checking..." : "Refresh Status"}
            </button>
          </div>
          {dashboardSystemStatusError && (
            <div className="dashboard-system-error">{dashboardSystemStatusError}</div>
          )}
          {dashboardSystemStatus && (
            <>
              <div className={`dashboard-system-notice${dashboardBackendOffline ? " warning" : " ok"}`}>
                {dashboardBackendOffline ? (
                  <>
                    <p>Some backend preview services are offline.</p>
                    <p>Start the backend server, then click Refresh Status.</p>
                    <div className="dashboard-system-command">
                      <code>cd "C:\Users\Abdur Rahman\Desktop\nexaai\backend"</code><br />
                      <code>python run_backend.py</code>
                    </div>
                  </>
                ) : (
                  <p>Backend preview services are reachable. Execution and storage remain disabled.</p>
                )}
              </div>
              <div className={`dashboard-system-summary${dashboardSystemStatus.overallOk ? " ok" : " warning"}`}>
                {dashboardSystemStatus.overallOk
                  ? "Preview services ready."
                  : "Some services offline."}
              </div>
              <div className="dashboard-system-stats">
                <div className="dashboard-system-stat">
                  <span>Total</span>
                  <strong>{dashboardSystemStatus.modules.length}</strong>
                </div>
                <div className="dashboard-system-stat">
                  <span>Online</span>
                  <strong>{onlineCount}</strong>
                </div>
                <div className="dashboard-system-stat">
                  <span>Offline</span>
                  <strong>{offlineCount}</strong>
                </div>
              </div>
              <div className="dashboard-service-grid">
                <p className="eyebrow">Service Health</p>
                {dashboardSystemStatus.modules.map((mod) => (
                  <div
                    key={mod.key}
                    className={`dashboard-service-card${mod.ok ? " ok" : " offline"}`}
                  >
                    <div className="dashboard-service-header">
                      <strong>{mod.label}</strong>
                      <span className={`dashboard-service-badge${mod.ok ? " ok" : " offline"}`}>
                        {mod.ok ? "OK" : "Offline"}
                      </span>
                    </div>
                    <div className="dashboard-service-detail">
                      <span>Status</span>
                      <strong>{mod.status}</strong>
                    </div>
                    {mod.phase && (
                      <div className="dashboard-service-detail">
                        <span>Phase</span>
                        <strong>{mod.phase}</strong>
                      </div>
                    )}
                    {mod.message && (
                      <div className="dashboard-service-detail">
                        <span>Message</span>
                        <strong>{mod.message}</strong>
                      </div>
                    )}
                    {mod.error && (
                      <div className="dashboard-service-detail error">
                        <span>Error</span>
                        <strong>{mod.error}</strong>
                      </div>
                    )}
                  </div>
                ))}
              </div>
              <div className="dashboard-system-checked">
                Checked at: {formatTime(dashboardSystemStatus.checkedAt)}
              </div>
              {onOpenSettings && (
                <button
                  type="button"
                  className="dashboard-system-link"
                  onClick={onOpenSettings}
                >
                  Open System Settings
                </button>
              )}
            </>
          )}
          {!dashboardSystemStatus && !dashboardSystemStatusError && !dashboardSystemStatusLoading && (
            <div className="dashboard-system-empty">Click "Refresh Status" to check.</div>
          )}
        </div>
      </aside>
    </div>
  );
}

function ModulePage({
  page,
  pageTitle,
  description,
  profile,
  onResetSetup,
}: {
  page: PageId;
  pageTitle: string;
  description: string;
  profile: UserProfile;
  onResetSetup: () => void;
}) {
  if (page === "voice") return <VoicePage />;
  if (page === "commands") return <CommandsPage />;
  if (page === "launcher") return <LauncherPage />;
  if (page === "files") return <FileOrganizerPage />;
  if (page === "history") return <HistoryPage />;
  if (page === "settings") return <SettingsPage profile={profile} onResetSetup={onResetSetup} />;
  if (page === "security") return <SecurityPage />;

  return (
    <section className="page-surface">
      <div className="page-hero">
        <p className="eyebrow">Module Page</p>
        <h3>{pageTitle}</h3>
        <p>{description}</p>
      </div>

      <div className="page-card-grid">
        {pageCards[page].map((card) => (
          <div className="page-card" key={card.title}>
            <h4>{card.title}</h4>
            <p>{card.text}</p>
          </div>
        ))}
      </div>

      <div className="module-note">
        This page is a layout placeholder. Real functionality will be added in later phases.
      </div>
    </section>
  );
}

function VoicePage() {
  const voiceSession = useVoiceSession();
  const liveTranscriptTimer = useRef<number | null>(null);
  const liveTranscriptIndex = useRef(0);
  const [selectedMode, setSelectedMode] = useState<"Push to Talk" | "Always Listening" | "Manual Text">("Push to Talk");
  const [realMicStatus, setRealMicStatus] = useState<MicrophonePermissionStatus>("unknown");
  const [micStatusMessage, setMicStatusMessage] = useState(getMicrophoneStatusLabel("unknown"));
  const [isRequestingMic, setIsRequestingMic] = useState(false);
  const [micRequestError, setMicRequestError] = useState<string | null>(null);
  const [lastCheckedAt, setLastCheckedAt] = useState<string | null>(null);
  const [lastRequestedAt, setLastRequestedAt] = useState<string | null>(null);
  const [demoMicPermissionStatus, setDemoMicPermissionStatus] = useState<"not_requested" | "allowed" | "blocked">("not_requested");
  const [transcriptText, setTranscriptText] = useState(defaultDemoTranscript);
  const initialVoiceResult = detectCommandIntent(defaultDemoTranscript);
  const [voiceCommandResult, setVoiceCommandResult] = useState<CommandUnderstandingResult>(initialVoiceResult);
  const [commandDraft, setCommandDraft] = useState(initialVoiceResult.originalText);
  const [detectedIntent, setDetectedIntent] = useState<CommandIntent>(initialVoiceResult.intent);
  const [riskLevel, setRiskLevel] = useState<CommandRiskLevel>(initialVoiceResult.riskLevel);
  const voiceActionPreview = createActionPreview(voiceCommandResult);

  const [voiceBackendPreview, setVoiceBackendPreview] = useState<BackendCommandPreviewResponse | null>(null);
  const [voiceBackendPreviewLoading, setVoiceBackendPreviewLoading] = useState(false);
  const [voiceBackendPreviewError, setVoiceBackendPreviewError] = useState<string | null>(null);

  const handleVoiceBackendPreview = async () => {
    setVoiceBackendPreviewLoading(true);
    setVoiceBackendPreviewError(null);
    setVoiceBackendPreview(null);
    try {
      const response = await requestBackendCommandPreview(voiceCommandResult);
      setVoiceBackendPreview(response);
    } catch (err) {
      setVoiceBackendPreviewError(
        err instanceof Error ? err.message : "Backend preview request failed",
      );
    } finally {
      setVoiceBackendPreviewLoading(false);
    }
  };

  const [voiceHistorySaveMessage, setVoiceHistorySaveMessage] = useState<string | null>(null);
  const [voiceHistorySaveError, setVoiceHistorySaveError] = useState<string | null>(null);

  const handleVoiceSaveToHistory = () => {
    setVoiceHistorySaveMessage(null);
    setVoiceHistorySaveError(null);
    try {
      const entry = createCommandHistoryEntry({
        source: "voice_page",
        result: voiceCommandResult,
        actionPreview: voiceActionPreview,
        backendPreview: voiceBackendPreview ?? undefined,
      });
      saveCommandHistoryEntry(entry);
      setVoiceHistorySaveMessage("Saved voice preview to local command history.");
    } catch {
      setVoiceHistorySaveError("Failed to save command history.");
    }
  };

  const voiceStatus = realMicStatus === "denied" || realMicStatus === "unsupported" || realMicStatus === "error"
    ? "error"
    : voiceSession.state.status === "listening"
    ? "listening"
    : voiceSession.state.status === "processing"
    ? "thinking"
    : voiceSession.state.status === "error"
    ? "error"
    : realMicStatus === "granted"
    ? "idle"
    : "idle";

  const voiceStatusSubtitle = realMicStatus === "denied" || realMicStatus === "unsupported" || realMicStatus === "error"
    ? realMicStatus === "denied"
      ? "Microphone permission is blocked. Resolve permission issues before listening."
      : realMicStatus === "unsupported"
      ? "Microphone is unsupported in this environment."
      : "Microphone permission check failed."
    : voiceSession.state.status === "listening"
    ? "Frontend listening session is active."
    : voiceSession.state.status === "stopped"
    ? "Listening session stopped."
    : voiceSession.state.status === "error"
    ? voiceSession.state.errorMessage || "A listening error occurred."
    : "Ready to start a listening session after microphone permission.";

  const micReadiness = (() => {
    switch (realMicStatus) {
      case "granted":
        return { label: "Ready", cls: "ready" };
      case "denied":
        return { label: "Blocked", cls: "blocked" };
      case "unsupported":
        return { label: "Unsupported", cls: "blocked" };
      default:
        return { label: "Pending", cls: "pending" };
    }
  })();

  const listeningReadiness = (() => {
    const s = voiceSession.state.status;
    if (s === "listening") return { label: "Active", cls: "ready" };
    if (s === "processing") return { label: "Processing", cls: "pending" };
    if (realMicStatus === "granted") return { label: "Ready", cls: "ready" };
    return { label: "Not ready", cls: "disabled" };
  })();

  const readinessSummary = realMicStatus === "granted"
    ? "Voice UI is ready for simulated listening."
    : realMicStatus === "denied"
    ? "Microphone is blocked. Enable permission before real listening."
    : realMicStatus === "unsupported"
    ? "Microphone is unsupported in this environment."
    : "Microphone permission is required before real listening.";

  const demoPermissionLabel = demoMicPermissionStatus === "allowed"
    ? "Allowed"
    : demoMicPermissionStatus === "blocked"
    ? "Blocked"
    : "Not requested";

  const applyTranscriptAsCommand = () => {
    const text = transcriptText.trim();
    const result = detectCommandIntent(text || "");

    setVoiceCommandResult(result);
    setCommandDraft(result.originalText || "No command draft yet");
    setDetectedIntent(result.intent);
    setRiskLevel(result.riskLevel);
  };

  const loadDemoBangla = () => setTranscriptText("ইউটিউব খুলে একটা বাংলা গান চালাও");
  const loadDemoEmail = () => setTranscriptText("Boss ke email draft koro");
  const loadDemoSensitive = () => setTranscriptText("Downloads folder clean koro");
  const loadDemoBlocked = () => setTranscriptText("delete system32");
  const clearTranscript = () => {
    const emptyResult = detectCommandIntent("");
    setTranscriptText("");
    setVoiceCommandResult(emptyResult);
    setCommandDraft("No command draft yet");
    setDetectedIntent(emptyResult.intent);
    setRiskLevel(emptyResult.riskLevel);
  };

  const refreshPermissionStatus = async () => {
    const status = await checkMicrophonePermission();
    const updated = saveMicrophonePermissionRecord({ status });
    setRealMicStatus(updated.status);
    setMicStatusMessage(updated.label);
    setLastCheckedAt(updated.lastCheckedAt);
    setMicRequestError(updated.error || null);
  };

  const handleRequestMicrophoneAccess = async () => {
    try {
      setIsRequestingMic(true);
      setMicRequestError(null);
      const result = await requestMicrophoneAccess();
      const now = new Date().toISOString();
      const updated = saveMicrophonePermissionRecord({
        status: result.status,
        lastRequestedAt: now,
        error: result.error,
      });
      setRealMicStatus(updated.status);
      setMicStatusMessage(updated.label);
      setLastRequestedAt(updated.lastRequestedAt || null);
      setLastCheckedAt(updated.lastCheckedAt);
      setMicRequestError(updated.error || null);
    } finally {
      setIsRequestingMic(false);
    }
  };

  const stopLiveTranscriptSimulation = () => {
    if (liveTranscriptTimer.current !== null) {
      window.clearInterval(liveTranscriptTimer.current);
      liveTranscriptTimer.current = null;
    }
  };

  const handleClearMicrophoneCache = () => {
    stopLiveTranscriptSimulation();
    clearMicrophonePermissionRecord();
    setRealMicStatus("unknown");
    setMicStatusMessage("Permission unknown");
    setLastCheckedAt(null);
    setLastRequestedAt(null);
    setMicRequestError(null);
  };

  const getMicHelperText = (): string => {
    switch (realMicStatus) {
      case "granted":
        return "Microphone access is allowed. Speech recognition will be added later.";
      case "denied":
        return "Microphone access is blocked. Enable it from Windows privacy settings or browser/site settings, then refresh.";
      case "unsupported":
        return "This environment does not support microphone access.";
      case "prompt":
        return "Permission has not been granted yet. Use Request Microphone Access.";
      case "unknown":
        return "Permission state is unknown. Refresh or request access.";
      case "error":
        return "Permission check failed. See error details below.";
      default:
        return "Click request to allow Nexa AI to use your microphone in a later voice phase.";
    }
  };

  useEffect(() => {
    // Load saved microphone permission record from localStorage
    const record = loadMicrophonePermissionRecord();
    setRealMicStatus(record.status);
    setMicStatusMessage(record.label);
    setLastCheckedAt(record.lastCheckedAt);
    setLastRequestedAt(record.lastRequestedAt || null);
    setMicRequestError(record.error || null);
  }, []);

  useEffect(() => {
    stopLiveTranscriptSimulation();

    if (voiceSession.state.status !== "listening") {
      return () => {
        stopLiveTranscriptSimulation();
      };
    }

    liveTranscriptIndex.current = 0;
    voiceSession.setInterimTranscript("");
    voiceSession.setTranscript("");
    setTranscriptText("");

    const firstPhrase = liveTranscriptPhrases[0];
    voiceSession.setInterimTranscript(firstPhrase);
    setTranscriptText(firstPhrase);
    liveTranscriptIndex.current = 1;

    liveTranscriptTimer.current = window.setInterval(() => {
      const index = liveTranscriptIndex.current;
      if (index >= liveTranscriptPhrases.length) {
        stopLiveTranscriptSimulation();
        return;
      }

      const phrase = liveTranscriptPhrases[index];
      voiceSession.setInterimTranscript(phrase);
      setTranscriptText(phrase);

      if (index === liveTranscriptPhrases.length - 1) {
        voiceSession.setTranscript(phrase);
        voiceSession.simulateProcessing();
      }

      liveTranscriptIndex.current += 1;
    }, 700);

    return () => {
      stopLiveTranscriptSimulation();
    };
  }, [voiceSession.state.status, voiceSession]);

  return (
    <section className="page-surface">
      <div className="page-hero">
        <p className="eyebrow">Voice Interface</p>
        <h3>Voice Control Center</h3>
        <p>
          The voice page is currently a frontend-only interface. Microphone permission,
          live speech recognition, and backend voice actions will arrive in later phases.
        </p>
      </div>

      <div className="voice-page-grid">
        <VoiceStatusPanel status={voiceStatus} subtitle={voiceStatusSubtitle} />
        <VoiceModeSelector selectedMode={selectedMode} onModeChange={setSelectedMode} />
      </div>

      <div className="voice-page-grid" style={{ marginTop: 24 }}>
        <div className="voice-panel voice-session-card">
          <div className="voice-panel-header">
            <div>
              <p className="eyebrow">Listening Session</p>
              <h4>Session controls</h4>
              <p>Manage the frontend-only listening session for future voice interaction phases.</p>
            </div>
          </div>

          <div className="voice-session-grid">
            <div className="voice-session-row">
              <span>Status</span>
              <strong>{voiceSession.state.status}</strong>
            </div>
            <div className="voice-session-row">
              <span>Elapsed</span>
              <strong>{voiceSession.state.elapsedSeconds}s</strong>
            </div>
            <div className="voice-session-row">
              <span>Started at</span>
              <strong>{voiceSession.state.startedAt ? new Date(voiceSession.state.startedAt).toLocaleTimeString() : "—"}</strong>
            </div>
            <div className="voice-session-row">
              <span>Stopped at</span>
              <strong>{voiceSession.state.stoppedAt ? new Date(voiceSession.state.stoppedAt).toLocaleTimeString() : "—"}</strong>
            </div>
            <div className="live-transcript-box">
              <span className="live-transcript-label">Live interim transcript</span>
              <p className="live-transcript-text">
                {voiceSession.state.interimTranscript || "No live transcript yet."}
              </p>
            </div>
            {voiceSession.state.errorMessage && (
              <div className="voice-session-error">
                <strong>Error:</strong> {voiceSession.state.errorMessage}
              </div>
            )}
          </div>

          <div className="voice-session-actions">
            <button
              type="button"
              className="voice-session-button"
              onClick={voiceSession.startSession}
              disabled={realMicStatus !== "granted" || voiceSession.state.isListening}
            >
              Start Listening
            </button>
            <button
              type="button"
              className="voice-session-button secondary"
              onClick={voiceSession.stopSession}
              disabled={!voiceSession.state.isListening}
            >
              Stop Listening
            </button>
            <button
              type="button"
              className="voice-session-button danger"
              onClick={() => {
                voiceSession.resetSession();
                setTranscriptText(defaultDemoTranscript);
              }}
            >
              Reset Session
            </button>
          </div>

          <p className="voice-session-help">
            {realMicStatus !== "granted"
              ? "Microphone permission is required before listening can start."
              : "This starts a frontend-only listening session. No audio is recorded yet."}
          </p>
        </div>

        <div className="voice-panel mic-permission-card">
        <div className="voice-panel-header">
          <div>
            <p className="eyebrow">Microphone Permission</p>
            <h4>Permission status check</h4>
            <p>Nexa AI can check and request microphone access for voice input in future phases.</p>
          </div>
        </div>

        <div className="real-mic-status-card">
          <span className={`real-mic-status-value ${realMicStatus}`}>
            {micStatusMessage}
          </span>
          <div className="mic-permission-note">
            <strong>Internal status:</strong> {realMicStatus}
          </div>
          {lastCheckedAt && (
            <div className="mic-meta-grid">
              <div className="mic-meta-row">
                <span className="mic-meta-label">Last checked:</span>
                <span className="mic-meta-value">{new Date(lastCheckedAt).toLocaleString()}</span>
              </div>
              {lastRequestedAt && (
                <div className="mic-meta-row">
                  <span className="mic-meta-label">Last requested:</span>
                  <span className="mic-meta-value">{new Date(lastRequestedAt).toLocaleString()}</span>
                </div>
              )}
            </div>
          )}
          <p
            className={`mic-helper-text ${
              realMicStatus === "denied" || realMicStatus === "unsupported" || realMicStatus === "error"
                ? "mic-help-warning"
                : ""
            }`}
          >
            {getMicHelperText()}
          </p>
          {micRequestError && (
            <div className="mic-error-detail">
              <strong>Error details:</strong> {micRequestError}
            </div>
          )}
          <div className="transcript-action-row">
            <button
              type="button"
              className="permission-refresh-button"
              onClick={refreshPermissionStatus}
              disabled={isRequestingMic}
            >
              Refresh Permission Status
            </button>
            <button
              type="button"
              className="permission-refresh-button primary"
              onClick={handleRequestMicrophoneAccess}
              disabled={isRequestingMic}
            >
              {isRequestingMic ? "Requesting..." : "Request Microphone Access"}
            </button>
            <button
              type="button"
              className="mic-cache-button secondary"
              onClick={handleClearMicrophoneCache}
              disabled={isRequestingMic}
            >
              Clear Mic Permission Cache
            </button>
          </div>
        </div>

        <div className="mic-permission-actions">
          <p className="eyebrow">Demo state controls</p>
          <div className="transcript-action-row">
            <button
              type="button"
              className="transcript-action-button"
              onClick={() => setDemoMicPermissionStatus("allowed")}
            >
              Simulate Allow
            </button>
            <button
              type="button"
              className="transcript-action-button danger"
              onClick={() => setDemoMicPermissionStatus("blocked")}
            >
              Simulate Block
            </button>
            <button
              type="button"
              className="transcript-action-button secondary"
              onClick={() => setDemoMicPermissionStatus("not_requested")}
            >
              Reset Demo
            </button>
          </div>
          <div className="mic-permission-note">
            Demo status: {demoPermissionLabel}. This does not change the real permission state.
          </div>
        </div>
        </div>
        </div>

        <div className="voice-panel simulated-transcript-card" style={{ marginTop: 24 }}>
          <div className="voice-panel-header">
            <div>
              <p className="eyebrow">Transcript Simulation</p>
              <h4>Draft from transcript</h4>
              <p>Turn a transcript into a preview-only command draft before any execution flow exists.</p>
            </div>
          </div>

          <textarea
            className="simulated-transcript-input"
            value={transcriptText}
            onChange={(event) => setTranscriptText(event.target.value)}
            placeholder="Type or simulate a transcript..."
          />

          <div className="transcript-action-row">
            <button
              type="button"
              className="transcript-action-button"
              onClick={applyTranscriptAsCommand}
            >
              Use Transcript as Command
            </button>
            <button
              type="button"
              className="transcript-action-button secondary"
              onClick={loadDemoBangla}
            >
              Load Bangla Demo
            </button>
            <button
              type="button"
              className="transcript-action-button secondary"
              onClick={loadDemoEmail}
            >
              Load Email Demo
            </button>
            <button
              type="button"
              className="transcript-action-button secondary"
              onClick={loadDemoSensitive}
            >
              Load Sensitive Demo
            </button>
            <button
              type="button"
              className="transcript-action-button secondary"
              onClick={loadDemoBlocked}
            >
              Load Blocked Demo
            </button>
            <button
              type="button"
              className="transcript-action-button danger"
              onClick={clearTranscript}
            >
              Clear Transcript
            </button>
          </div>
        </div>

        <div className="voice-page-grid" style={{ marginTop: 16 }}>
          <div className="voice-panel speech-readiness-card">
            <div className="voice-panel-header">
              <div>
                <p className="eyebrow">Speech Readiness</p>
                <h4>Readiness checks</h4>
                <p className="readiness-summary">{readinessSummary}</p>
              </div>
            </div>

            <div className="readiness-grid">
              <div className={`readiness-item ${micReadiness.cls}`}>
                <span>Microphone permission</span>
                <strong>{micReadiness.label}</strong>
              </div>

              <div className={`readiness-item ${listeningReadiness.cls}`}>
                <span>Listening session</span>
                <strong>{listeningReadiness.label}</strong>
              </div>

              <div className={`readiness-item disabled`}>
                <span>Speech recognition engine</span>
                <strong>Not connected yet</strong>
                <small>Real STT will be added in a later phase.</small>
              </div>

              <div className={`readiness-item disabled`}>
                <span>Command execution</span>
                <strong>Disabled</strong>
                <small>Voice commands are preview-only. Nothing will be executed.</small>
              </div>

              <div className={`readiness-item ready`}>
                <span>Safety confirmation</span>
                <strong>Enabled by design</strong>
                <small>Sensitive future actions will require confirmation.</small>
              </div>
            </div>
          </div>

          <div className="voice-panel safety-notice-box">
            <div className="voice-panel-header">
              <div>
                <p className="eyebrow">Safety Notice</p>
                <h4>Operational safeguards</h4>
              </div>
            </div>

            <div className="voice-status-note">
              Nexa AI will not execute voice commands automatically. Future risky actions like delete, send, move, shutdown, or browser automation will require confirmation.
            </div>
          </div>
        </div>

        <div className="voice-page-grid" style={{ marginTop: 24 }}>
          <VoiceTranscriptPanel
            transcript={transcriptText}
            confidence={voiceCommandResult.confidence}
            language={voiceCommandResult.language === "Bangla" || voiceCommandResult.language === "English" ? voiceCommandResult.language : "Mixed"}
          />
          <VoiceCommandDraft
            command={commandDraft}
            intent={detectedIntent}
            riskLevel={(riskLevel === "blocked" ? "sensitive" : riskLevel) as "safe" | "confirmation_required" | "sensitive"}
          />
          <section className="voice-panel command-analysis-card">
            <div className="voice-panel-header">
              <div>
                <p className="eyebrow">Command analysis</p>
                <h4>Understanding preview</h4>
                <p>This preview remains UI-only. No command is executed.</p>
              </div>
            </div>

            <div className="voice-meta-grid">
              <div>
                <span>Confirmation required</span>
                <strong>{shouldAskConfirmation(voiceCommandResult) ? "Yes" : "No"}</strong>
              </div>
              <div>
                <span>Sensitive</span>
                <strong>{isCommandSensitive(voiceCommandResult) ? "Yes" : "No"}</strong>
              </div>
              <div>
                <span>Confirmation reason</span>
                <strong>{voiceCommandResult.confirmationReason || "None"}</strong>
              </div>
            </div>
          </section>
        </div>

        <div className="command-action-preview-wrap" style={{ marginTop: 24 }}>
          <ActionPreviewCard preview={voiceActionPreview} />
        </div>

        <div className="command-preview-note">
          Voice command execution is disabled. Preview only.
        </div>

        <div className="history-save-row">
          <button
            type="button"
            className="history-save-button"
            onClick={handleVoiceSaveToHistory}
          >
            Save Voice Preview to History
          </button>
          {voiceHistorySaveMessage && (
            <span className="history-save-message">{voiceHistorySaveMessage}</span>
          )}
          {voiceHistorySaveError && (
            <span className="history-save-error">{voiceHistorySaveError}</span>
          )}
        </div>

        <div className="backend-preview-card">
          <p className="eyebrow">Backend Preview</p>
          <div className="backend-preview-actions">
            <button
              type="button"
              className="backend-preview-button"
              onClick={handleVoiceBackendPreview}
              disabled={voiceBackendPreviewLoading}
            >
              {voiceBackendPreviewLoading ? "Requesting..." : "Request Backend Preview"}
            </button>
          </div>

          {voiceBackendPreviewError && (
            <div className="backend-preview-error">{voiceBackendPreviewError}</div>
          )}

          {voiceBackendPreview && (
            <div className="backend-preview-grid">
              <div className="backend-preview-row">
                <span>Status</span>
                <strong>{voiceBackendPreview.status}</strong>
              </div>
              <div className="backend-preview-row">
                <span>Can execute</span>
                <strong>{String(voiceBackendPreview.can_execute)}</strong>
              </div>
              <div className="backend-preview-row">
                <span>Execution mode</span>
                <strong>{voiceBackendPreview.execution_mode}</strong>
              </div>
              <div className="backend-preview-row">
                <span>Message</span>
                <strong>{voiceBackendPreview.message}</strong>
              </div>
              <div className="backend-preview-row">
                <span>Intent</span>
                <strong>{voiceBackendPreview.intent}</strong>
              </div>
              <div className="backend-preview-row">
                <span>Risk level</span>
                <strong>{voiceBackendPreview.risk_level}</strong>
              </div>

              {voiceBackendPreview.preview_steps.length > 0 && (
                <div className="backend-preview-steps">
                  <span>Preview steps</span>
                  <ul>
                    {voiceBackendPreview.preview_steps.map((step, i) => (
                      <li key={i}>{step}</li>
                    ))}
                  </ul>
                </div>
              )}

              {voiceBackendPreview.warning && (
                <div className="backend-preview-row">
                  <span>Warning</span>
                  <strong>{voiceBackendPreview.warning}</strong>
                </div>
              )}

              {voiceBackendPreview.blocked_reason && (
                <div className="backend-preview-row">
                  <span>Blocked reason</span>
                  <strong>{voiceBackendPreview.blocked_reason}</strong>
                </div>
              )}
            </div>
          )}

          <div className="backend-preview-note">
            Backend preview is still execution-disabled.
          </div>
        </div>

      <div className="module-note">
        Microphone permission and real speech recognition will be added in Phase 10.3 and later backend phases.
      </div>
    </section>
  );
}

function HistoryPage() {
  const timeline = [
    {
      time: "Now",
      title: "Desktop app opened",
      text: "Nexa AI Electron shell started successfully.",
      status: "success",
    },
    {
      time: "Phase 06",
      title: "Navigation system active",
      text: "Sidebar pages can switch without reload.",
      status: "success",
    },
    {
      time: "Phase 05",
      title: "Backend health watcher added",
      text: "Desktop UI can detect FastAPI backend state.",
      status: "info",
    },
    {
      time: "Future",
      title: "Command audit logs",
      text: "Voice commands and sensitive actions will be logged here.",
      status: "pending",
    },
  ];

  const [commandHistory, setCommandHistory] = useState<CommandHistoryEntry[]>(() =>
    getLatestCommandHistory(),
  );
  const [sourceFilter, setSourceFilter] = useState("all");
  const [riskFilter, setRiskFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedHistoryEntryId, setSelectedHistoryEntryId] = useState<string | null>(null);
  const [auditPreviewResponse, setAuditPreviewResponse] = useState<BackendAuditPreviewResponse | null>(null);
  const [auditPreviewLoading, setAuditPreviewLoading] = useState(false);
  const [auditPreviewError, setAuditPreviewError] = useState<string | null>(null);
  const [auditHealth, setAuditHealth] = useState<BackendAuditHealthResponse | null>(null);
  const [auditHealthLoading, setAuditHealthLoading] = useState(false);
  const [auditHealthError, setAuditHealthError] = useState<string | null>(null);
  const [migrationPreview, setMigrationPreview] = useState<BackendAuditMigrationPreviewResponse | null>(null);
  const [migrationPreviewLoading, setMigrationPreviewLoading] = useState(false);
  const [migrationPreviewError, setMigrationPreviewError] = useState<string | null>(null);

  useEffect(() => {
    handleRefreshAuditHealth();
    handleRefreshMigrationPreview();
  }, []);

  const selectedEntry = selectedHistoryEntryId
    ? commandHistory.find((e) => e.id === selectedHistoryEntryId) ?? null
    : null;

  const filteredHistory = commandHistory.filter((entry) => {
    if (sourceFilter !== "all" && entry.source !== sourceFilter) return false;
    if (riskFilter !== "all" && entry.riskLevel !== riskFilter) return false;
    if (statusFilter !== "all") {
      const entryStatus = entry.actionStatus ?? entry.backendStatus;
      if (entryStatus !== statusFilter) return false;
    }
    const query = searchQuery.trim().toLowerCase();
    if (query) {
      const haystack = [
        entry.originalText,
        entry.intent,
        entry.language,
        entry.riskLevel,
        entry.source,
        entry.actionStatus,
        entry.backendStatus,
        entry.summary,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      if (!haystack.includes(query)) return false;
    }
    return true;
  });

  const hasHistory = commandHistory.length > 0;
  const hasFiltered = filteredHistory.length > 0;
  const totalCount = commandHistory.length;
  const shownCount = filteredHistory.length;

  const handleRefreshHistory = () => {
    setCommandHistory(getLatestCommandHistory());
  };

  const clearFilters = () => {
    setSourceFilter("all");
    setRiskFilter("all");
    setStatusFilter("all");
  };

  const clearAll = () => {
    clearFilters();
    setSearchQuery("");
  };

  const handleClearHistory = () => {
    clearCommandHistory();
    setCommandHistory([]);
    setSelectedHistoryEntryId(null);
  };

  const handleSelectEntry = (id: string) => {
    setSelectedHistoryEntryId((prev) => (prev === id ? null : id));
  };

  const handleCloseDetail = () => {
    setSelectedHistoryEntryId(null);
  };

  const handleDeleteHistoryEntry = (id: string) => {
    const updated = deleteCommandHistoryEntry(id);
    setCommandHistory(updated);
    if (selectedHistoryEntryId === id) {
      setSelectedHistoryEntryId(null);
    }
  };

  const handleRefreshMigrationPreview = async () => {
    setMigrationPreviewLoading(true);
    setMigrationPreviewError(null);
    try {
      const response = await getBackendAuditMigrationPreview();
      setMigrationPreview(response);
    } catch (err) {
      setMigrationPreviewError(err instanceof Error ? err.message : "Failed to reach backend migration preview.");
    } finally {
      setMigrationPreviewLoading(false);
    }
  };

  const handleRefreshAuditHealth = async () => {
    setAuditHealthLoading(true);
    setAuditHealthError(null);
    try {
      const response = await getBackendAuditHealth();
      setAuditHealth(response);
    } catch (err) {
      setAuditHealthError(err instanceof Error ? err.message : "Failed to reach backend audit health.");
    } finally {
      setAuditHealthLoading(false);
    }
  };

  const handleSyncHistoryEntryToAudit = async (entry: CommandHistoryEntry) => {
    setAuditPreviewLoading(true);
    setAuditPreviewError(null);
    setAuditPreviewResponse(null);
    try {
      const response = await requestBackendAuditPreview(entry);
      setAuditPreviewResponse(response);
    } catch (err) {
      setAuditPreviewError(err instanceof Error ? err.message : "Failed to sync with backend audit.");
    } finally {
      setAuditPreviewLoading(false);
    }
  };

  const formatTime = (iso: string) => {
    try {
      return new Date(iso).toLocaleString();
    } catch {
      return iso;
    }
  };

  return (
    <section className="page-surface system-page">
      <div className="page-hero">
        <p className="eyebrow">Activity & Audit</p>
        <h3>History Center</h3>
        <p>
          This page will track command history, automation events, safety confirmations,
          and assistant activity logs.
        </p>
      </div>

      <div className="timeline-panel">
        {timeline.map((item) => (
          <div className="timeline-item" key={item.title}>
            <div className={`timeline-dot ${item.status}`} />
            <div>
              <span>{item.time}</span>
              <h4>{item.title}</h4>
              <p>{item.text}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="audit-health-panel">
        <div className="audit-health-header">
          <p className="eyebrow">Backend Audit Storage Status</p>
          <button
            type="button"
            className="audit-health-button"
            onClick={handleRefreshAuditHealth}
            disabled={auditHealthLoading}
          >
            {auditHealthLoading ? "Refreshing..." : "Refresh Audit Status"}
          </button>
        </div>
        {auditHealthError && (
          <div className="audit-health-error">{auditHealthError}</div>
        )}
        {auditHealth && (
          <>
            <div className="audit-health-grid">
              <div className="audit-health-row">
                <span>Status</span>
                <strong>{auditHealth.status}</strong>
              </div>
              <div className="audit-health-row">
                <span>Module</span>
                <strong>{auditHealth.module}</strong>
              </div>
              <div className="audit-health-row">
                <span>Phase</span>
                <strong>{auditHealth.phase}</strong>
              </div>
              <div className="audit-health-row">
                <span>Storage enabled</span>
                <strong>{String(auditHealth.storage_enabled)}</strong>
              </div>
              <div className="audit-health-row">
                <span>Storage mode</span>
                <strong>{auditHealth.storage_mode ?? "N/A"}</strong>
              </div>
              <div className="audit-health-row">
                <span>Execution enabled</span>
                <strong>{String(auditHealth.execution_enabled)}</strong>
              </div>
              {auditHealth.message && (
                <div className="audit-health-row full-width">
                  <span>Message</span>
                  <strong>{auditHealth.message}</strong>
                </div>
              )}
            </div>
            <div className="audit-health-note">
              Storage is not enabled yet. This panel only displays backend audit status.
            </div>
          </>
        )}
        {!auditHealth && !auditHealthError && !auditHealthLoading && (
          <div className="audit-health-empty">Click "Refresh Audit Status" to load backend audit status.</div>
        )}
      </div>

      <div className="migration-preview-panel">
        <div className="migration-preview-header">
          <p className="eyebrow">SQLite Migration Preview</p>
          <button
            type="button"
            className="migration-preview-button"
            onClick={handleRefreshMigrationPreview}
            disabled={migrationPreviewLoading}
          >
            {migrationPreviewLoading ? "Refreshing..." : "Refresh Migration Preview"}
          </button>
        </div>
        {migrationPreviewError && (
          <div className="migration-preview-error">{migrationPreviewError}</div>
        )}
        {migrationPreview && (
          <>
            <div className="migration-preview-grid">
              <div className="migration-preview-row">
                <span>Status</span>
                <strong>{migrationPreview.status}</strong>
              </div>
              <div className="migration-preview-row">
                <span>Script path</span>
                <strong>{migrationPreview.script_path}</strong>
              </div>
              <div className="migration-preview-row">
                <span>Exists</span>
                <strong>{String(migrationPreview.exists)}</strong>
              </div>
              <div className="migration-preview-row">
                <span>Can run</span>
                <strong>{String(migrationPreview.can_run)}</strong>
              </div>
              <div className="migration-preview-row">
                <span>Migrations enabled</span>
                <strong>{String(migrationPreview.migrations_enabled)}</strong>
              </div>
              <div className="migration-preview-row">
                <span>Statement count</span>
                <strong>{migrationPreview.statement_count}</strong>
              </div>
              <div className="migration-preview-row">
                <span>Table name</span>
                <strong>{migrationPreview.table_name}</strong>
              </div>
              <div className="migration-preview-row">
                <span>Execution enabled</span>
                <strong>{String(migrationPreview.execution_enabled)}</strong>
              </div>
              <div className="migration-preview-row full-width">
                <span>Message</span>
                <strong>{migrationPreview.preview_message}</strong>
              </div>
            </div>
            <div className="migration-preview-notes">
              {migrationPreview.safety_notes.map((note, i) => (
                <div key={i} className="migration-preview-note">{note}</div>
              ))}
            </div>
          </>
        )}
        {!migrationPreview && !migrationPreviewError && !migrationPreviewLoading && (
          <div className="migration-preview-empty">Click "Refresh Migration Preview" to load migration status.</div>
        )}
      </div>

      <div className="command-history-panel">
        <div className="command-history-header">
          <p className="eyebrow">Command Audit Log</p>
          <div className="command-history-actions">
            <button
              type="button"
              className="command-history-button"
              onClick={handleRefreshHistory}
            >
              Refresh History
            </button>
            <button
              type="button"
              className="command-history-button danger"
              onClick={handleClearHistory}
            >
              Clear Command History
            </button>
          </div>
        </div>

        <div className="database-readiness-note">
          <p className="eyebrow">Database Readiness Note</p>
          <p className="database-readiness-desc">
            Current command history is stored locally in browser/Electron localStorage.
            Backend SQLite database storage is prepared but disabled.
            Audit sync endpoint is preview-only and does not store to database.
            No command execution is connected to history records.
          </p>
          <div className="database-readiness-grid">
            <div className="database-readiness-item enabled">
              <span>Local history</span>
              <strong>Enabled</strong>
            </div>
            <div className="database-readiness-item enabled">
              <span>Backend audit preview</span>
              <strong>Enabled</strong>
            </div>
            <div className="database-readiness-item disabled">
              <span>SQLite storage</span>
              <strong>Disabled</strong>
            </div>
            <div className="database-readiness-item disabled">
              <span>Migrations</span>
              <strong>Disabled</strong>
            </div>
            <div className="database-readiness-item disabled">
              <span>Command execution</span>
              <strong>Disabled</strong>
            </div>
          </div>
        </div>

        {!hasHistory ? (
          <div className="command-history-empty">
            No command history saved yet.
          </div>
        ) : (
          <>
            <div className="command-history-search-row">
              <input
                className="command-history-search-input"
                type="text"
                placeholder="Search command history..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              {searchQuery && (
                <button
                  type="button"
                  className="command-history-search-clear"
                  onClick={() => setSearchQuery("")}
                >
                  Clear Search
                </button>
              )}
              <button
                type="button"
                className="command-history-clear-all"
                onClick={clearAll}
              >
                Clear All
              </button>
            </div>
            <div className="command-history-result-count">
              Showing {shownCount} of {totalCount} history entries
            </div>
            <div className="command-history-filter-bar">
              <div className="command-history-filter-group">
                <label>Source</label>
                <select
                  className="command-history-select"
                  value={sourceFilter}
                  onChange={(e) => setSourceFilter(e.target.value)}
                >
                  <option value="all">All sources</option>
                  <option value="commands_page">Commands Page</option>
                  <option value="voice_page">Voice Page</option>
                  <option value="backend_preview">Backend Preview</option>
                  <option value="manual_test">Manual Test</option>
                </select>
              </div>
              <div className="command-history-filter-group">
                <label>Risk</label>
                <select
                  className="command-history-select"
                  value={riskFilter}
                  onChange={(e) => setRiskFilter(e.target.value)}
                >
                  <option value="all">All risks</option>
                  <option value="safe">Safe</option>
                  <option value="confirmation_required">Confirmation Required</option>
                  <option value="sensitive">Sensitive</option>
                  <option value="blocked">Blocked</option>
                </select>
              </div>
              <div className="command-history-filter-group">
                <label>Status</label>
                <select
                  className="command-history-select"
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                >
                  <option value="all">All statuses</option>
                  <option value="preview_only">Preview Only</option>
                  <option value="requires_confirmation">Requires Confirmation</option>
                  <option value="sensitive_warning">Sensitive Warning</option>
                  <option value="blocked">Blocked</option>
                  <option value="confirmation_required">Confirmation Required</option>
                  <option value="warning">Warning</option>
                  <option value="preview">Preview</option>
                </select>
              </div>
              <button
                type="button"
                className="command-history-clear-filter"
                onClick={clearFilters}
              >
                Clear Filters
              </button>
            </div>

            {!hasFiltered ? (
              <div className="command-history-empty">
                No history entries match your search or filters.
              </div>
            ) : (
              <div className="command-history-list">
                {filteredHistory.map((entry) => (
              <div
                className={`command-history-item${selectedHistoryEntryId === entry.id ? " active" : ""}`}
                key={entry.id}
                onClick={() => handleSelectEntry(entry.id)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") handleSelectEntry(entry.id); }}
              >
                <div className="command-history-meta">
                  <div>
                    <span>Source</span>
                    <strong>{entry.source}</strong>
                  </div>
                  <div>
                    <span>Time</span>
                    <strong>{formatTime(entry.createdAt)}</strong>
                  </div>
                  <div>
                    <span>Intent</span>
                    <strong>{entry.intent}</strong>
                  </div>
                  <div>
                    <span>Language</span>
                    <strong>{entry.language}</strong>
                  </div>
                  <div>
                    <span>Confidence</span>
                    <strong>{entry.confidence}%</strong>
                  </div>
                  <div className="command-history-risk">
                    <span>Risk level</span>
                    <strong>{entry.riskLevel}</strong>
                  </div>
                  <div>
                    <span>Can execute</span>
                    <strong>No</strong>
                  </div>
                  {entry.actionStatus && (
                    <div>
                      <span>Action status</span>
                      <strong>{entry.actionStatus}</strong>
                    </div>
                  )}
                  {entry.backendStatus && (
                    <div>
                      <span>Backend status</span>
                      <strong>{entry.backendStatus}</strong>
                    </div>
                  )}
                </div>
                <p className="command-history-command">
                  {entry.originalText}
                </p>
                <p className="command-history-summary">
                  {entry.summary}
                </p>
                <div className="command-history-item-actions">
                  <button
                    type="button"
                    className="audit-sync-button"
                    onClick={(e) => { e.stopPropagation(); handleSyncHistoryEntryToAudit(entry); }}
                    disabled={auditPreviewLoading}
                  >
                    {auditPreviewLoading ? "Syncing..." : "Sync Audit Preview"}
                  </button>
                  <button
                    type="button"
                    className="command-history-delete-button"
                    onClick={(e) => { e.stopPropagation(); handleDeleteHistoryEntry(entry.id); }}
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {selectedEntry ? (
          <div className="command-history-detail">
            <div className="command-history-detail-header">
              <p className="eyebrow">History Detail</p>
              <button
                type="button"
                className="command-history-close-detail"
                onClick={handleCloseDetail}
              >
                Close Detail
              </button>
            </div>
            <div className="command-history-detail-grid">
              <div className="command-history-detail-row">
                <span>Original command</span>
                <strong>{selectedEntry.originalText}</strong>
              </div>
              <div className="command-history-detail-row">
                <span>Source</span>
                <strong>{selectedEntry.source}</strong>
              </div>
              <div className="command-history-detail-row">
                <span>Intent</span>
                <strong>{selectedEntry.intent}</strong>
              </div>
              <div className="command-history-detail-row">
                <span>Language</span>
                <strong>{selectedEntry.language}</strong>
              </div>
              <div className="command-history-detail-row">
                <span>Confidence</span>
                <strong>{selectedEntry.confidence}%</strong>
              </div>
              <div className="command-history-detail-row">
                <span>Risk level</span>
                <strong>{selectedEntry.riskLevel}</strong>
              </div>
              {selectedEntry.actionStatus && (
                <div className="command-history-detail-row">
                  <span>Action status</span>
                  <strong>{selectedEntry.actionStatus}</strong>
                </div>
              )}
              {selectedEntry.backendStatus && (
                <div className="command-history-detail-row">
                  <span>Backend status</span>
                  <strong>{selectedEntry.backendStatus}</strong>
                </div>
              )}
              <div className="command-history-detail-row">
                <span>Can execute</span>
                <strong>No</strong>
              </div>
              <div className="command-history-detail-row">
                <span>Created at</span>
                <strong>{formatTime(selectedEntry.createdAt)}</strong>
              </div>
              <div className="command-history-detail-row">
                <span>Summary</span>
                <strong>{selectedEntry.summary}</strong>
              </div>
            </div>
            <div className="command-history-safety-note">
              This is a preview/audit record only. No command was executed.
            </div>
            <div className="command-history-danger-note">
              <button
                type="button"
                className="audit-sync-button detail"
                onClick={() => handleSyncHistoryEntryToAudit(selectedEntry)}
                disabled={auditPreviewLoading}
              >
                {auditPreviewLoading ? "Syncing..." : "Sync Selected to Backend Audit"}
              </button>
              <button
                type="button"
                className="command-history-detail-delete"
                onClick={() => handleDeleteHistoryEntry(selectedEntry.id)}
              >
                Delete This Entry
              </button>
            </div>
            {auditPreviewError && (
              <div className="audit-preview-error">{auditPreviewError}</div>
            )}
            {auditPreviewResponse && (
              <div className="audit-preview-panel">
                <p className="eyebrow" style={{ margin: "0 0 10px" }}>Backend Audit Preview</p>
                <div className="audit-preview-grid">
                  <div className="audit-preview-row">
                    <span>Status</span>
                    <strong>{auditPreviewResponse.status}</strong>
                  </div>
                  <div className="audit-preview-row">
                    <span>Audit ID</span>
                    <strong>{auditPreviewResponse.audit_id}</strong>
                  </div>
                  <div className="audit-preview-row">
                    <span>Stored</span>
                    <strong>{String(auditPreviewResponse.stored)}</strong>
                  </div>
                  <div className="audit-preview-row">
                    <span>Execution enabled</span>
                    <strong>{String(auditPreviewResponse.execution_enabled)}</strong>
                  </div>
                  <div className="audit-preview-row">
                    <span>Message</span>
                    <strong>{auditPreviewResponse.message}</strong>
                  </div>
                  <div className="audit-preview-row">
                    <span>Source</span>
                    <strong>{auditPreviewResponse.source}</strong>
                  </div>
                  <div className="audit-preview-row">
                    <span>Intent</span>
                    <strong>{auditPreviewResponse.intent}</strong>
                  </div>
                  <div className="audit-preview-row">
                    <span>Risk level</span>
                    <strong>{auditPreviewResponse.risk_level}</strong>
                  </div>
                </div>
                <div className="audit-preview-note">
                  Backend audit preview does not store to database yet.
                </div>
              </div>
            )}
          </div>
        ) : hasHistory && hasFiltered ? (
          <div className="command-history-detail-empty">
            Select a history entry to view details.
          </div>
        ) : null}
      </>
    )}
      </div>

      <div className="module-note">
        Real history will be stored locally in SQLite after the database phase.
      </div>
    </section>
  );
}

function SettingsPage({
  profile,
  onResetSetup,
}: {
  profile: UserProfile;
  onResetSetup: () => void;
}) {
  const [databaseStatus, setDatabaseStatus] = useState<BackendDatabaseStatusResponse | null>(null);
  const [databaseStatusLoading, setDatabaseStatusLoading] = useState(false);
  const [databaseStatusError, setDatabaseStatusError] = useState<string | null>(null);
  const [databaseStatusLastCheckedAt, setDatabaseStatusLastCheckedAt] = useState<string | null>(null);
  const [systemStatus, setSystemStatus] = useState<BackendSystemStatusSummary | null>(null);
  const [systemStatusLoading, setSystemStatusLoading] = useState(false);
  const [systemStatusError, setSystemStatusError] = useState<string | null>(null);
  const [backendServicesRefreshing, setBackendServicesRefreshing] = useState(false);
  const [backendServicesLastRefreshedAt, setBackendServicesLastRefreshedAt] = useState<string | null>(null);
  const [backendServicesRefreshError, setBackendServicesRefreshError] = useState<string | null>(null);

  useEffect(() => {
    handleRefreshDatabaseStatus();
    handleRefreshSystemStatus();
  }, []);

  const handleRefreshSystemStatus = async () => {
    setSystemStatusLoading(true);
    setSystemStatusError(null);
    try {
      const response = await getBackendSystemStatus();
      setSystemStatus(response);
    } catch (err) {
      setSystemStatusError(err instanceof Error ? err.message : "Failed to check backend system status.");
    } finally {
      setSystemStatusLoading(false);
    }
  };

  const handleRefreshAllBackendServices = async () => {
    setBackendServicesRefreshing(true);
    setBackendServicesRefreshError(null);
    const results = await Promise.allSettled([
      getBackendDatabaseStatus(),
      getBackendSystemStatus(),
    ]);
    const dbResult = results[0];
    const sysResult = results[1];
    if (dbResult.status === "fulfilled") {
      setDatabaseStatus(dbResult.value);
      setDatabaseStatusError(null);
    } else {
      setDatabaseStatusError("Backend database status is unavailable. Start the backend server and try again.");
    }
    if (sysResult.status === "fulfilled") {
      setSystemStatus(sysResult.value);
      setSystemStatusError(null);
    } else {
      setSystemStatusError("Failed to check backend system status.");
    }
    const anyFailed = results.some((r) => r.status === "rejected");
    if (anyFailed) {
      setBackendServicesRefreshError("Some backend services could not be refreshed. Check that the backend server is running.");
    }
    setDatabaseStatusLastCheckedAt(new Date().toISOString());
    setBackendServicesLastRefreshedAt(new Date().toISOString());
    setBackendServicesRefreshing(false);
  };

  const backendOffline =
    !!databaseStatusError ||
    !!systemStatusError ||
    !!backendServicesRefreshError ||
    (systemStatus !== null && systemStatus.modules.some((m) => !m.ok));

  const handleRefreshDatabaseStatus = async () => {
    setDatabaseStatusLoading(true);
    setDatabaseStatusError(null);
    try {
      const response = await getBackendDatabaseStatus();
      setDatabaseStatus(response);
      setDatabaseStatusLastCheckedAt(new Date().toISOString());
    } catch (err) {
      setDatabaseStatusError("Backend database status is unavailable. Start the backend server and try again.");
      setDatabaseStatusLastCheckedAt(new Date().toISOString());
    } finally {
      setDatabaseStatusLoading(false);
    }
  };

  const formatTime = (iso: string) => {
    try {
      return new Date(iso).toLocaleString();
    } catch {
      return iso;
    }
  };

  const settingsGroups = [
    {
      title: "Profile",
      items: ["Preferred name", "Sir/Madam addressing", "Language mode"],
    },
    {
      title: "Voice",
      items: ["Voice style", "Response speed", "Reply tone"],
    },
    {
      title: "Performance",
      items: ["Low-end laptop mode", "Animation intensity", "Background polling"],
    },
  ];

  return (
    <section className="page-surface system-page">
      <div className="page-hero">
        <p className="eyebrow">Assistant Preferences</p>
        <h3>Settings</h3>
        <p>
          This page will control personal profile, language mode, voice behavior,
          and performance options for low-end laptops.
        </p>
      </div>

      <div className={`backend-connection-banner${backendOffline ? " warning" : " ok"}`}>
        <p className="eyebrow">Backend Connection Notice</p>
        {backendOffline ? (
          <>
            <p className="backend-connection-text">
              Some backend services are offline or unavailable.
            </p>
            <p className="backend-connection-text">
              Start the backend server with <code>python run_backend.py</code>, then refresh services.
            </p>
            <div className="backend-connection-command">
              <code>cd "C:\Users\Abdur Rahman\Desktop\nexaai\backend"</code><br />
              <code>python run_backend.py</code>
            </div>
          </>
        ) : (
          <>
            <p className="backend-connection-text">
              Backend preview services are reachable.
            </p>
            <p className="backend-connection-text">
              Storage and execution remain disabled by design.
            </p>
          </>
        )}
      </div>

      <div className="backend-refresh-panel">
        <div className="backend-refresh-row">
          <div>
            <p className="eyebrow" style={{ margin: 0 }}>Backend Services Refresh</p>
            {backendServicesLastRefreshedAt && (
              <span className="backend-refresh-meta">
                Last refreshed: {formatTime(backendServicesLastRefreshedAt)}
              </span>
            )}
          </div>
          <button
            type="button"
            className="backend-refresh-button"
            onClick={handleRefreshAllBackendServices}
            disabled={backendServicesRefreshing}
          >
            {backendServicesRefreshing ? "Refreshing..." : "Refresh All Backend Services"}
          </button>
        </div>
        {backendServicesRefreshError && (
          <div className="backend-refresh-error">{backendServicesRefreshError}</div>
        )}
      </div>

      <div className="settings-grid">
        <div className="settings-card profile-preview-card">
          <h4>Profile Preview</h4>
          <div className="profile-preview-grid">
            <div className="profile-preview-row">
              <span>Name</span>
              <strong>{profile.userName || "Local User"}</strong>
            </div>
            <div className="profile-preview-row">
              <span>Addressing</span>
              <strong>{formatAddressingName(profile)}</strong>
            </div>
            <div className="profile-preview-row">
              <span>Language mode</span>
              <strong>{profile.languageMode}</strong>
            </div>
            <div className="profile-preview-row">
              <span>Voice preference</span>
              <strong>{profile.voicePreference}</strong>
            </div>
            <div className="profile-preview-row">
              <span>Onboarding complete</span>
              <strong>{profile.hasCompletedOnboarding ? "Yes" : "No"}</strong>
            </div>
          </div>
          <div className="reset-zone">
            <p>
              Resetting onboarding clears your local profile setup and returns you
              to the welcome setup flow.
            </p>
            <button type="button" className="reset-button" onClick={onResetSetup}>
              Reset Onboarding
            </button>
          </div>
        </div>

        {settingsGroups.map((group) => (
          <div className="settings-card" key={group.title}>
            <h4>{group.title}</h4>

            <div className="settings-list">
              {group.items.map((item) => (
                <label className="settings-row" key={item}>
                  <span>{item}</span>
                  <input type="checkbox" disabled />
                </label>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="database-status-panel">
        <div className="database-status-header">
          <p className="eyebrow">Local Database Status</p>
          <button
            type="button"
            className="database-status-button"
            onClick={handleRefreshDatabaseStatus}
            disabled={databaseStatusLoading}
          >
            {databaseStatusLoading ? "Checking..." : "Refresh Database Status"}
          </button>
        </div>
        <div className="database-status-meta">
          <span className="database-status-last-checked">
            Last checked: {databaseStatusLastCheckedAt ? formatTime(databaseStatusLastCheckedAt) : "Not checked yet"}
          </span>
        </div>
        {databaseStatusError && (
          <div className="database-status-error">
            <strong>Offline</strong>: {databaseStatusError}
          </div>
        )}
        {databaseStatus && (
          <>
            <div className="database-status-grid">
              <div className="database-status-row">
                <span>Status</span>
                <strong>{databaseStatus.status}</strong>
              </div>
              <div className="database-status-row">
                <span>Module</span>
                <strong>{databaseStatus.module}</strong>
              </div>
              <div className="database-status-row">
                <span>Phase</span>
                <strong>{databaseStatus.phase}</strong>
              </div>
              <div className="database-status-row">
                <span>Database enabled</span>
                <strong>{String(databaseStatus.database_enabled)}</strong>
              </div>
              <div className="database-status-row">
                <span>Database mode</span>
                <strong>{databaseStatus.database_mode}</strong>
              </div>
              <div className="database-status-row">
                <span>Database path</span>
                <strong>{databaseStatus.database_path}</strong>
              </div>
              <div className="database-status-row">
                <span>Migrations enabled</span>
                <strong>{String(databaseStatus.migrations_enabled)}</strong>
              </div>
              <div className="database-status-row">
                <span>Reads enabled</span>
                <strong>{String(databaseStatus.reads_enabled)}</strong>
              </div>
              <div className="database-status-row">
                <span>Writes enabled</span>
                <strong>{String(databaseStatus.writes_enabled)}</strong>
              </div>
              <div className="database-status-row">
                <span>Execution enabled</span>
                <strong>{String(databaseStatus.execution_enabled)}</strong>
              </div>
              <div className="database-status-row full-width">
                <span>Reason</span>
                <strong>{databaseStatus.reason}</strong>
              </div>
            </div>
            <div className="database-status-note">
              Database is not enabled yet. This panel only displays backend database status.
            </div>
          </>
        )}
        {!databaseStatus && !databaseStatusError && !databaseStatusLoading && (
          <div className="database-status-empty">Click "Refresh Database Status" to load backend database status.</div>
        )}
      </div>

      <div className="system-status-panel">
        <div className="system-status-header">
          <p className="eyebrow">Backend System Status</p>
          <button
            type="button"
            className="system-status-button"
            onClick={handleRefreshSystemStatus}
            disabled={systemStatusLoading}
          >
            {systemStatusLoading ? "Checking..." : "Refresh System Status"}
          </button>
        </div>
        {systemStatusError && (
          <div className="system-status-error">{systemStatusError}</div>
        )}
        {systemStatus && (
          <>
            <div className={`system-status-summary${systemStatus.overallOk ? " ok" : " warning"}`}>
              {systemStatus.overallOk
                ? "All systems preview-ready."
                : "Some systems are offline."}
              <span className="system-status-checked">
                Checked at: {formatTime(systemStatus.checkedAt)}
              </span>
            </div>
            <div className="system-status-grid">
              {systemStatus.modules.map((mod) => (
                <div
                  key={mod.key}
                  className={`system-status-card${mod.ok ? " ok" : " offline"}`}
                >
                  <div className="system-status-card-header">
                    <strong>{mod.label}</strong>
                    <span className={`system-status-badge${mod.ok ? " ok" : " offline"}`}>
                      {mod.ok ? "OK" : "Offline"}
                    </span>
                  </div>
                  <div className="system-status-card-detail">
                    <span>Status</span>
                    <strong>{mod.status}</strong>
                  </div>
                  {mod.phase && (
                    <div className="system-status-card-detail">
                      <span>Phase</span>
                      <strong>{mod.phase}</strong>
                    </div>
                  )}
                  {mod.message && (
                    <div className="system-status-card-detail">
                      <span>Message</span>
                      <strong>{mod.message}</strong>
                    </div>
                  )}
                  {mod.error && (
                    <div className="system-status-card-detail error">
                      <span>Error</span>
                      <strong>{mod.error}</strong>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </>
        )}
        {!systemStatus && !systemStatusError && !systemStatusLoading && (
          <div className="system-status-empty">Click "Refresh System Status" to check backend systems.</div>
        )}
      </div>

      <div className="module-note">
        Settings are disabled for now. They will become active after SQLite profile
        and preferences storage is implemented.
      </div>
    </section>
  );
}

function SecurityPage() {
  const permissions = [
    {
      name: "Microphone Access",
      status: "Planned",
      detail: "Required for voice input.",
    },
    {
      name: "File System Access",
      status: "Confirmation Required",
      detail: "Needed for search, open, organize, move, and rename actions.",
    },
    {
      name: "Browser Automation",
      status: "Safe Mode",
      detail: "Used for YouTube, web search, WhatsApp, and website workflows.",
    },
    {
      name: "Sensitive Actions",
      status: "Locked",
      detail: "Delete, send, shutdown, restart, and file move actions require confirmation.",
    },
  ];

  return (
    <section className="page-surface system-page">
      <div className="page-hero">
        <p className="eyebrow">Safety & Permissions</p>
        <h3>Security Center</h3>
        <p>
          This page defines what Nexa AI can access and which actions must require
          strong user confirmation before execution.
        </p>
      </div>

      <div className="security-grid">
        {permissions.map((permission) => (
          <div className="security-card" key={permission.name}>
            <div>
              <h4>{permission.name}</h4>
              <p>{permission.detail}</p>
            </div>
            <span>{permission.status}</span>
          </div>
        ))}
      </div>

      <div className="danger-zone">
        <p className="eyebrow">Protected Actions</p>
        <h4>Never execute destructive actions without confirmation.</h4>
        <p>
          Future delete, send message, send email, shutdown, restart, file move,
          and folder cleanup commands will go through the safety confirmation engine.
        </p>
      </div>
    </section>
  );
}
function CommandsPage() {
  const defaultCommand = "ইউটিউব খুলে একটা বাংলা গান চালাও";
  const [commandInput, setCommandInput] = useState(defaultCommand);
  const [result, setResult] = useState<CommandUnderstandingResult>(() => detectCommandIntent(defaultCommand));
  const actionPreview = createActionPreview(result);

  const [backendPreview, setBackendPreview] = useState<BackendCommandPreviewResponse | null>(null);
  const [backendPreviewLoading, setBackendPreviewLoading] = useState(false);
  const [backendPreviewError, setBackendPreviewError] = useState<string | null>(null);

  const handleBackendPreview = async () => {
    setBackendPreviewLoading(true);
    setBackendPreviewError(null);
    setBackendPreview(null);
    try {
      const response = await requestBackendCommandPreview(result);
      setBackendPreview(response);
    } catch (err) {
      setBackendPreviewError(
        err instanceof Error ? err.message : "Backend preview request failed",
      );
    } finally {
      setBackendPreviewLoading(false);
    }
  };

  const [historySaveMessage, setHistorySaveMessage] = useState<string | null>(null);
  const [historySaveError, setHistorySaveError] = useState<string | null>(null);

  const handleSaveToHistory = () => {
    setHistorySaveMessage(null);
    setHistorySaveError(null);
    try {
      const entry = createCommandHistoryEntry({
        source: "commands_page",
        result,
        actionPreview,
        backendPreview: backendPreview ?? undefined,
      });
      saveCommandHistoryEntry(entry);
      setHistorySaveMessage("Saved to local command history.");
    } catch {
      setHistorySaveError("Failed to save command history.");
    }
  };

  const examples = [
    { label: "YouTube Bangla", value: "ইউটিউব খুলে একটা বাংলা গান চালাও" },
    { label: "Find PDF File", value: "Downloads folder theke PDF file khuje dao" },
    { label: "Draft Email", value: "Boss ke email draft koro" },
    { label: "Delete Folder", value: "Delete folder ta clean koro" },
    { label: "Light Off", value: "Light off koro" },
  ];

  const handleInputChange = (value: string) => {
    setCommandInput(value);
    setResult(detectCommandIntent(value));
  };

  const applyExample = (value: string) => {
    setCommandInput(value);
    setResult(detectCommandIntent(value));
  };

  return (
    <section className="page-surface module-enhanced command-lab-layout">
      <div className="page-hero">
        <p className="eyebrow">Command Understanding</p>
        <h3>Commands Lab</h3>
        <p>
          This page is the interactive testing ground for Bengali, English, and Banglish command
          understanding. All previews are disabled from executing real actions in this phase.
        </p>
      </div>

      <div className="command-input-card">
        <p className="eyebrow">Command input</p>
        <textarea
          className="command-lab-textarea"
          value={commandInput}
          onChange={(event) => handleInputChange(event.target.value)}
          rows={5}
          placeholder="Enter a command to see detection results"
        />

        <div className="command-example-row">
          {examples.map((example) => (
            <button
              key={example.label}
              type="button"
              className="command-example-button"
              onClick={() => applyExample(example.value)}
            >
              {example.label}
            </button>
          ))}
        </div>

        <p className="execution-disabled-note">
          Command execution is disabled in this phase. This is a preview-only command lab.
        </p>
      </div>

      <div className="command-result-card">
        <p className="eyebrow">Result preview</p>
        <div className="command-result-grid">
          <div className="command-result-row">
            <span>Original text</span>
            <strong>{result.originalText || "—"}</strong>
          </div>
          <div className="command-result-row">
            <span>Normalized text</span>
            <strong>{result.normalizedText || "—"}</strong>
          </div>
          <div className="command-result-row">
            <span>Intent label</span>
            <strong>{getIntentLabel(result.intent)}</strong>
          </div>
          <div className="command-result-row">
            <span>Raw intent</span>
            <strong>{result.intent}</strong>
          </div>
          <div className="command-result-row">
            <span>Language</span>
            <strong>{result.language}</strong>
          </div>
          <div className="command-result-row">
            <span>Confidence</span>
            <strong>{result.confidence}%</strong>
          </div>
          <div className="command-result-row">
            <span>Risk level</span>
            <strong className={`command-risk-${result.riskLevel}`}>{result.riskLevel}</strong>
          </div>
          <div className="command-result-row">
            <span>Confirmation required</span>
            <strong>{shouldAskConfirmation(result) ? "Yes" : "No"}</strong>
          </div>
          <div className="command-result-row">
            <span>Sensitive</span>
            <strong>{isCommandSensitive(result) ? "Yes" : "No"}</strong>
          </div>
          <div className="command-result-row">
            <span>Can execute</span>
            <strong>No</strong>
          </div>
          <div className="command-result-row">
            <span>Explanation</span>
            <strong>{result.explanation}</strong>
          </div>
          {result.confirmationReason && (
            <div className="command-result-row">
              <span>Confirmation reason</span>
              <strong>{result.confirmationReason}</strong>
            </div>
          )}
        </div>

        <div className="entities-box">
          <p className="eyebrow">Entities</p>
          {Object.keys(result.entities).length === 0 ? (
            <p>No entities detected yet.</p>
          ) : (
            <div className="command-result-grid">
              {Object.entries(result.entities).map(([key, value]) => (
                <div className="command-result-row" key={key}>
                  <span>{key}</span>
                  <strong>{value}</strong>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="command-action-preview-wrap">
        <ActionPreviewCard preview={actionPreview} />
      </div>

      <div className="command-preview-note">
        Execution is disabled. Preview only.
      </div>

      <div className="history-save-row">
        <button
          type="button"
          className="history-save-button"
          onClick={handleSaveToHistory}
        >
          Save Preview to History
        </button>
        {historySaveMessage && (
          <span className="history-save-message">{historySaveMessage}</span>
        )}
        {historySaveError && (
          <span className="history-save-error">{historySaveError}</span>
        )}
      </div>

      <div className="backend-preview-card">
        <p className="eyebrow">Backend Preview</p>
        <div className="backend-preview-actions">
          <button
            type="button"
            className="backend-preview-button"
            onClick={handleBackendPreview}
            disabled={backendPreviewLoading}
          >
            {backendPreviewLoading ? "Requesting..." : "Request Backend Preview"}
          </button>
        </div>

        {backendPreviewError && (
          <div className="backend-preview-error">{backendPreviewError}</div>
        )}

        {backendPreview && (
          <div className="backend-preview-grid">
            <div className="backend-preview-row">
              <span>Status</span>
              <strong>{backendPreview.status}</strong>
            </div>
            <div className="backend-preview-row">
              <span>Can execute</span>
              <strong>{String(backendPreview.can_execute)}</strong>
            </div>
            <div className="backend-preview-row">
              <span>Execution mode</span>
              <strong>{backendPreview.execution_mode}</strong>
            </div>
            <div className="backend-preview-row">
              <span>Message</span>
              <strong>{backendPreview.message}</strong>
            </div>
            <div className="backend-preview-row">
              <span>Intent</span>
              <strong>{backendPreview.intent}</strong>
            </div>
            <div className="backend-preview-row">
              <span>Risk level</span>
              <strong>{backendPreview.risk_level}</strong>
            </div>

            {backendPreview.preview_steps.length > 0 && (
              <div className="backend-preview-steps">
                <span>Preview steps</span>
                <ul>
                  {backendPreview.preview_steps.map((step, i) => (
                    <li key={i}>{step}</li>
                  ))}
                </ul>
              </div>
            )}

            {backendPreview.warning && (
              <div className="backend-preview-row">
                <span>Warning</span>
                <strong>{backendPreview.warning}</strong>
              </div>
            )}

            {backendPreview.blocked_reason && (
              <div className="backend-preview-row">
                <span>Blocked reason</span>
                <strong>{backendPreview.blocked_reason}</strong>
              </div>
            )}
          </div>
        )}

        <div className="backend-preview-note">
          Backend preview is still execution-disabled.
        </div>
      </div>

      <div className="module-note">
        Actual command execution will remain disabled until the command engine and confirmation flow are fully implemented.
      </div>
    </section>
  );
}

function LauncherPage() {
  const launchers = [
    ["YouTube", "https://youtube.com", "#ef4444"],
    ["Google", "https://google.com", "#00e5ff"],
    ["VS Code", "Desktop app", "#60a5fa"],
    ["WhatsApp", "Web/Desktop", "#22c55e"],
  ];

  return (
    <section className="page-surface module-enhanced">
      <div className="page-hero">
        <p className="eyebrow">App & Website Launcher</p>
        <h3>Launcher Hub</h3>
        <p>
          This module will open desktop apps and websites from natural voice or text commands.
        </p>
      </div>

      <div className="launcher-grid">
        {launchers.map(([name, target, color]) => (
          <div className="launcher-card" key={name}>
            <span style={{ background: color }} />
            <h4>{name}</h4>
            <p>{target}</p>
            <button type="button">Preview Launch</button>
          </div>
        ))}
      </div>

      <div className="module-note">
        Real launcher execution will be connected after safety checks and command routing are ready.
      </div>
    </section>
  );
}

function FileOrganizerPage() {
  const locations = ["Desktop", "Downloads", "Documents", "Pictures"];

  return (
    <section className="page-surface module-enhanced">
      <div className="page-hero">
        <p className="eyebrow">File Search & Organizer</p>
        <h3>File Control Center</h3>
        <p>
          This page will search, preview, organize, move, and safely manage local files.
        </p>
      </div>

      <div className="file-layout">
        <div className="module-console">
          <p className="eyebrow">Search Query</p>
          <div className="fake-input">Find my project report PDF</div>
          <div className="intent-preview">
            <p><span>Search Scope</span><strong>Desktop + Downloads</strong></p>
            <p><span>Action Mode</span><strong>Preview Only</strong></p>
            <p><span>Safety</span><strong>Delete Disabled</strong></p>
          </div>
        </div>

        <div className="module-list">
          <h4>Search Locations</h4>
          {locations.map((item) => (
            <div className="module-row" key={item}>{item}</div>
          ))}
        </div>
      </div>

      <div className="module-note">
        File actions will always use preview and confirmation before moving, renaming, or deleting files.
      </div>
    </section>
  );
}

function StatusPanel({ backendConnected }: { backendConnected: boolean }) {
  return (
    <div className="panel-card">
      <h4>System Status</h4>
      <ul>
        <li><span className="dot green" />Electron Window Ready</li>
        <li><span className="dot green" />React Renderer Working</li>
        <li><span className="dot blue" />Vite Dev Server Connected</li>
        <li>
          <span className={backendConnected ? "dot green" : "dot orange"} />
          {backendConnected ? "Python Backend Connected" : "Python Backend Pending"}
        </li>
      </ul>
    </div>
  );
}

function BackendPanel({
  backendConnected,
  backendHealth,
}: {
  backendConnected: boolean;
  backendHealth: BackendHealth | null;
}) {
  return (
    <div className="panel-card">
      <h4>Backend Health</h4>

      {backendConnected ? (
        <div className="backend-health">
          <p><span>App</span><strong>{backendHealth?.app ?? "Nexa AI Backend"}</strong></p>
          <p><span>Version</span><strong>{backendHealth?.version ?? "0.1.0"}</strong></p>
          <p><span>Environment</span><strong>{backendHealth?.environment ?? "development"}</strong></p>
          <p><span>Message</span><strong>{backendHealth?.message ?? "OK"}</strong></p>
        </div>
      ) : (
        <div className="backend-offline">
          <strong>Backend is not running.</strong>
          <p>
            Start the Python backend with <code>python run_backend.py</code> from the backend folder.
          </p>
        </div>
      )}
    </div>
  );
}

function ActivityPanel() {
  return (
    <div className="panel-card">
      <h4>Today Activity</h4>
      <div className="activity-list">
        {activityItems.map((item) => (
          <div className="activity-card" key={item.title}>
            <strong>{item.title}</strong>
            <p>{item.text}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export { App };
