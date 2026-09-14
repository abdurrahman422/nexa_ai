import { useEffect, useState } from "react";
import { Mail, RefreshCw } from "lucide-react";
import {
  connectGmailAccount,
  disconnectGmailAccount,
  getGmailConnectStatus,
  getGmailAccounts,
  GmailAccountDto,
  switchGmailAccount,
} from "@/lib/backendAssistantClient";

export function GmailAccountsSettings() {
  const [accounts, setAccounts] = useState<GmailAccountDto[]>([]);
  const [active, setActive] = useState<GmailAccountDto | null>(null);
  const [message, setMessage] = useState("No Gmail account connected.");
  const [busy, setBusy] = useState(false);

  const refresh = async () => {
    try {
      const result = await getGmailAccounts();
      setAccounts(result.accounts);
      setActive(result.active_account);
      setMessage(result.active_account ? `Connected as ${result.active_account.email}` : "No Gmail account connected.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Gmail accounts are unavailable.");
    }
  };

  useEffect(() => { void refresh(); }, []);

  const run = async (operation: () => Promise<unknown>, success: string) => {
    setBusy(true);
    try {
      await operation();
      setMessage(success);
      await refresh();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Gmail account operation failed.");
    } finally {
      setBusy(false);
    }
  };

  const connect = async () => {
    setBusy(true);
    setMessage("Opening Google authorization in your default browser...");
    try {
      await connectGmailAccount();
      for (let attempt = 0; attempt < 300; attempt += 1) {
        await new Promise((resolve) => window.setTimeout(resolve, 1000));
        const status = await getGmailConnectStatus();
        if (status.state === "completed") {
          await refresh();
          setMessage("Gmail account connected.");
          return;
        }
        if (status.state === "error") {
          throw new Error(status.error || "Gmail authorization failed.");
        }
      }
      throw new Error("Gmail authorization timed out or was cancelled.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Gmail authorization failed.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="nx-card">
      <div className="nx-card-head">
        <div className="nx-card-title"><Mail /> Gmail Accounts</div>
        <button type="button" className="nx-link-btn" onClick={() => void refresh()} disabled={busy}>
          <RefreshCw size={13} /> Refresh
        </button>
      </div>
      <div className="nx-row"><span>Connected as</span><strong>{active?.email || "None"}</strong></div>
      <div className="nx-list" style={{ marginTop: 10 }}>
        {accounts.map((account) => (
          <div className="nx-list-row" key={account.account_id}>
            <div className="nx-list-main"><strong>{account.email}</strong><small>{account.display_name || "Google Gmail account"}</small></div>
            {active?.account_id === account.account_id ? (
              <span className="nx-list-badge low">Active</span>
            ) : (
              <button type="button" className="nx-btn ghost" onClick={() => void run(() => switchGmailAccount(account.account_id), "Gmail account switched.")} disabled={busy}>Switch</button>
            )}
            <button type="button" className="nx-btn danger" onClick={() => void run(() => disconnectGmailAccount(account.account_id), "Gmail account disconnected.")} disabled={busy}>Disconnect</button>
          </div>
        ))}
      </div>
      <button type="button" className="nx-btn primary" onClick={() => void connect()} disabled={busy}>
        {busy ? "Working..." : "Connect account"}
      </button>
      <p className="youtube-control-message">{message}</p>
    </section>
  );
}