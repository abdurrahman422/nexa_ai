import { useEffect, useMemo, useRef, useState } from "react";
import { SplashScreen, useStartupSequence } from "@/components/splash";
import { WelcomeOnboarding } from "@/components/onboarding";
import { useVoiceSession, VoiceCommandDraft, VoiceModeSelector, VoiceStatusPanel, VoiceTranscriptPanel } from "@/components/voice";
import { clearProfile, checkMicrophonePermission, clearMicrophonePermissionRecord, formatAddressingName, getMicrophoneStatusLabel, loadMicrophonePermissionRecord, loadProfile, isOnboardingComplete, MicrophonePermissionStatus, requestMicrophoneAccess, saveMicrophonePermissionRecord, UserProfile } from "@/lib";

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
            <p className="eyebrow">Phase 12.3</p>
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
              <button className="quick-card" key={action.title} type="button">
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
}: {
  backendConnected: boolean;
  backendHealth: BackendHealth | null;
  draftCommand: string;
  commandPreview: string;
  onCommandChange: (value: string) => void;
}) {
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
  const [commandDraft, setCommandDraft] = useState("Open YouTube and play a Bangla song");
  const [detectedIntent, setDetectedIntent] = useState("youtube_search");
  const [riskLevel, setRiskLevel] = useState<"safe" | "confirmation_required" | "sensitive">("safe");

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

  const detectIntent = (text: string) => {
    const lower = text.toLowerCase();
    if (/youtube|ইউটিউব/.test(lower)) return "youtube_search";
    if (/file|folder|ফাইল|ফোল্ডার/.test(lower)) return "file_search";
    if (/email|mail|মেইল/.test(lower)) return "email_draft";
    if (/delete|remove|ডিলিট/.test(lower)) return "sensitive_file_action";
    return "general_assistant_query";
  };

  const applyTranscriptAsCommand = () => {
    const text = transcriptText.trim();
    const intent = detectIntent(text);
    const risk = intent === "sensitive_file_action"
      ? "sensitive"
      : intent === "email_draft"
      ? "confirmation_required"
      : "safe";

    setCommandDraft(text || "No command draft yet");
    setDetectedIntent(intent);
    setRiskLevel(risk);
  };

  const loadDemoBangla = () => setTranscriptText("ইউটিউব খুলে একটা বাংলা গান চালাও");
  const loadDemoFile = () => setTranscriptText("Downloads folder theke PDF file khuje dao");
  const clearTranscript = () => {
    setTranscriptText("");
    setCommandDraft("No command draft yet");
    setDetectedIntent("none");
    setRiskLevel("safe");
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
          confidence={0}
          language="Mixed"
        />
        <VoiceCommandDraft
          command={commandDraft}
          intent={detectedIntent}
          riskLevel={riskLevel}
        />
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
  const examples = [
    "YouTube open koro",
    "ইউটিউব খুলো",
    "Downloads folder clean koro",
    "Boss ke email draft koro",
  ];

  return (
    <section className="page-surface module-enhanced">
      <div className="page-hero">
        <p className="eyebrow">Command Understanding</p>
        <h3>Commands Lab</h3>
        <p>
          This page will become the testing ground for Bengali, English, and Banglish command
          understanding before commands are executed.
        </p>
      </div>

      <div className="module-split">
        <div className="module-console">
          <p className="eyebrow">Test Command</p>
          <div className="fake-input">ইউটিউব খুলো এবং গান চালাও</div>
          <div className="intent-preview">
            <p><span>Detected Intent</span><strong>youtube_search</strong></p>
            <p><span>Confidence</span><strong>92%</strong></p>
            <p><span>Risk Level</span><strong>Safe</strong></p>
          </div>
        </div>

        <div className="module-list">
          <h4>Example Commands</h4>
          {examples.map((item) => (
            <div className="module-row" key={item}>{item}</div>
          ))}
        </div>
      </div>

      <div className="module-note">
        Actual command engine will be implemented later in Phase 13 and Phase 14.
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