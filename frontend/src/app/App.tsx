import { useEffect, useState } from "react";

type BackendStatus = "checking" | "connected" | "offline";

type BackendHealth = {
  status?: string;
  app?: string;
  version?: string;
  environment?: string;
  phase?: string;
  message?: string;
};

const navItems = [
  "Dashboard",
  "Commands",
  "Automations",
  "File Organizer",
  "App Launcher",
  "Web Search",
  "AI Chat",
  "History",
  "Settings",
  "Security",
];

const quickActions = [
  {
    title: "Open YouTube",
    subtitle: "Launch media workspace",
    accent: "#ef4444",
  },
  {
    title: "Organize Files",
    subtitle: "Sort downloads and documents",
    accent: "#00e5ff",
  },
  {
    title: "Start Study Mode",
    subtitle: "Focus timer and learning setup",
    accent: "#22c55e",
  },
  {
    title: "Ask AI",
    subtitle: "Talk naturally with Nexa",
    accent: "#8b5cf6",
  },
];

export default function App() {
  const platform = window.nexa?.platform ?? "win32";
  const appMode = window.nexa?.appMode ?? "desktop";
  const backendUrl = window.nexa?.backendUrl ?? "http://127.0.0.1:8000";

  const [backendStatus, setBackendStatus] =
    useState<BackendStatus>("checking");
  const [backendHealth, setBackendHealth] = useState<BackendHealth | null>(
    null
  );

  useEffect(() => {
    const checkBackend = async () => {
      try {
        setBackendStatus("checking");

        const response = await fetch(`${backendUrl}/api/health`);

        if (!response.ok) {
          throw new Error("Backend health request failed");
        }

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

  const backendConnected = backendStatus === "connected";

  return (
    <main className="desktop-app">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-orb">N</div>
          <div>
            <h1>Nexa AI</h1>
            <p>Desktop Assistant</p>
          </div>
        </div>

        <nav className="nav-list">
          {navItems.map((item, index) => (
            <button
              key={item}
              className={index === 0 ? "nav-item active" : "nav-item"}
              type="button"
            >
              <span>{item}</span>
            </button>
          ))}
        </nav>

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
            <p className="eyebrow">Phase 05.4</p>
            <h2>AI Command Center</h2>
          </div>

          <div className="topbar-actions">
            <div className="mode-badge">
              {appMode.toUpperCase()} · {platform}
            </div>
            <div
              className={
                backendConnected ? "backend-badge connected" : "backend-badge"
              }
            >
              {backendConnected ? "Backend Connected" : "Backend Pending"}
            </div>
          </div>
        </header>

        <div className="content-grid">
          <section className="command-hero">
            <div className="hero-copy">
              <p className="eyebrow">Desktop Shell Active</p>
              <h3>
                Nexa <span>AI</span>
              </h3>
              <p>
                Your futuristic Windows desktop assistant workspace is now
                connected to a backend health layer. Voice, commands, and
                automation modules will be attached in later phases.
              </p>
            </div>

            <div className="voice-orb-wrap">
              <div className="voice-orb">
                <div className="voice-orb-core" />
              </div>
              <p>Listening UI Ready</p>
            </div>

            <div className="command-input">
              <span>Try saying:</span>
              <strong>“Open YouTube and play a song”</strong>
              <button type="button">Transmit</button>
            </div>
          </section>

          <aside className="right-panel">
            <div className="panel-card">
              <h4>System Status</h4>
              <ul>
                <li>
                  <span className="dot green" />
                  Electron Window Ready
                </li>
                <li>
                  <span className="dot green" />
                  React Renderer Working
                </li>
                <li>
                  <span className="dot blue" />
                  Vite Dev Server Connected
                </li>
                <li>
                  <span className={backendConnected ? "dot green" : "dot orange"} />
                  {backendConnected ? "Python Backend Connected" : "Python Backend Pending"}
                </li>
              </ul>
            </div>

            <div className="panel-card">
              <h4>Backend Health</h4>

              {backendConnected ? (
                <div className="backend-health">
                  <p>
                    <span>App</span>
                    <strong>{backendHealth?.app ?? "Nexa AI Backend"}</strong>
                  </p>
                  <p>
                    <span>Version</span>
                    <strong>{backendHealth?.version ?? "0.1.0"}</strong>
                  </p>
                  <p>
                    <span>Environment</span>
                    <strong>{backendHealth?.environment ?? "development"}</strong>
                  </p>
                  <p>
                    <span>Message</span>
                    <strong>{backendHealth?.message ?? "OK"}</strong>
                  </p>
                </div>
              ) : (
                <div className="backend-offline">
                  <strong>Backend is not running.</strong>
                  <p>
                    Start the Python backend with <code>python run_backend.py</code>
                    from the backend folder.
                  </p>
                </div>
              )}
            </div>
          </aside>
        </div>

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
          <span>Backend Health Aware</span>
        </footer>
      </section>
    </main>
  );
}

export { App };