/* ============================================================================
   VOICE · VoiceManager
   ----------------------------------------------------------------------------
   The single orchestrator/state-machine for the voice assistant. Owns the
   recognition + synthesis services, the pipeline, settings, and conversation
   state, and exposes a tiny subscription for React (useSyncExternalStore).

   Turn flow (idle → listening → thinking → speaking → …):
     mic → SpeechRecognitionService (final transcript)
         → VoicePipeline.process() → Multi-LLM chat() (model + failover)
         → display assistant message
         → SpeechSynthesisService.speak() sentence-by-sentence
         → resume listening (continuous) or go idle

   Recognition is paused during thinking/speaking to prevent the AI's own voice
   from being transcribed (echo), then resumed. "Interrupt" cancels speech and
   returns to listening.
   ========================================================================== */
import { interactionBus } from "@/interaction";
import { loadProfile } from "@/lib";
import type { ChatTurn } from "@/lib/llm";
import { SpeechRecognitionService } from "./recognitionService";
import { GoogleStreamingService } from "./googleStreamingService";
import { SpeechSynthesisService } from "./synthesisService";
import type { OnlineVoiceInfo } from "./synthesisService";
import { VoicePipeline } from "./pipeline";
import { loadVoiceSettings, saveVoiceSettings, resolveLanguage } from "./settings";
import { VOICE_ERROR_COPY } from "./types";
import type { VoiceErrorKind, VoiceMessage, VoiceSettings, VoiceState } from "./types";

type Listener = () => void;

function uid(): string {
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

class VoiceManager {
  private recognition = new SpeechRecognitionService();
  private googleRecognition = new GoogleStreamingService();
  private synthesis = new SpeechSynthesisService();
  private pipeline = new VoicePipeline();

  private settings: VoiceSettings = loadVoiceSettings();
  private conversationId = `voice-${uid()}`;

  // ---- observable state ----
  state: VoiceState = "idle";
  messages: VoiceMessage[] = [];
  interim = "";
  error: { kind: VoiceErrorKind; message: string } | null = null;

  private running = false; // continuous conversation active
  private _version = 0;
  private listeners = new Set<Listener>();

  get version(): number {
    return this._version;
  }

  static recognitionSupported(): boolean {
    return SpeechRecognitionService.isSupported() || Boolean(typeof navigator !== "undefined" && navigator.mediaDevices?.getUserMedia);
  }
  static synthesisSupported(): boolean {
    return SpeechSynthesisService.isSupported();
  }

  getSettings(): VoiceSettings {
    return this.settings;
  }

  getVoices(): OnlineVoiceInfo[] {
    return this.synthesis.getVoices();
  }

  subscribe(listener: Listener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private emit(): void {
    this._version += 1;
    for (const l of this.listeners) l();
  }

  private setState(state: VoiceState): void {
    this.state = state;
    const busState = state === "listening" ? "listening" : state === "thinking" || state === "speaking" ? "processing" : "idle";
    interactionBus.emit({ type: "voice", payload: { state: busState } });
    if (state === "thinking") interactionBus.emit({ type: "ai:thinking", payload: { active: true, label: "Nexa is thinking" } });
    else interactionBus.emit({ type: "ai:thinking", payload: { active: false } });
    this.emit();
  }

  private setError(kind: VoiceErrorKind): void {
    this.error = { kind, message: VOICE_ERROR_COPY[kind] };
    this.setState("error");
  }

  /* ---------------- settings ---------------- */

  updateSettings(patch: Partial<VoiceSettings>): void {
    this.settings = { ...this.settings, ...patch };
    saveVoiceSettings(this.settings);
    // Reflect an immediate mute while speaking.
    if (patch.muted) this.synthesis.cancel();
    this.emit();
  }

  /* ---------------- mic permission ---------------- */

  private async ensureMic(): Promise<boolean> {
    if (typeof navigator === "undefined" || !navigator.mediaDevices?.getUserMedia) {
      return true; // let the Web Speech API prompt on its own
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach((t) => t.stop()); // Web Speech opens its own
      return true;
    } catch (err) {
      const name = err instanceof DOMException ? err.name : "";
      this.setError(name === "NotFoundError" || name === "DevicesNotFoundError" ? "no-mic" : "mic-denied");
      return false;
    }
  }

  /* ---------------- lifecycle ---------------- */

  async startListening(): Promise<void> {
    if (!VoiceManager.recognitionSupported()) {
      this.setError("unsupported");
      return;
    }
    if (this.running && this.state === "listening") return;
    this.error = null;
    this.running = true;
    if (!(await this.ensureMic())) return;
    this.beginRecognition(true);
  }

  stopListening(): void {
    this.running = false;
    this.recognition.abort();
    this.googleRecognition.stop();
    this.synthesis.cancel();
    this.interim = "";
    window.dispatchEvent(new CustomEvent("nexa:voice-output-state", { detail: { active: false } }));
    this.setState("idle");
  }

  toggleListening(): void {
    if (this.running || this.state === "listening") this.stopListening();
    else void this.startListening();
  }

  /** Push-to-talk: one utterance, not a continuous loop. */
  async pushToTalkStart(): Promise<void> {
    if (!VoiceManager.recognitionSupported()) {
      this.setError("unsupported");
      return;
    }
    this.error = null;
    this.running = false;
    if (!(await this.ensureMic())) return;
    this.beginRecognition(false);
  }

  pushToTalkStop(): void {
    this.recognition.stop(); // triggers the final result → a turn
  }

  /** Submit a transcript captured by the backend push-to-talk recorder. */
  async submitTranscript(text: string): Promise<void> {
    this.error = null;
    this.running = false;
    await this.handleFinal(text);
  }

  private beginRecognition(continuous: boolean): void {
    this.interim = "";
    this.setState("listening");
    if (this.settings.sttEngine !== "browser") {
      void this.beginGoogleRecognition(continuous);
      return;
    }
    this.beginBrowserRecognition(continuous);
  }

  private beginBrowserRecognition(continuous: boolean): void {
    this.recognition.start({
      lang: resolveLanguage(this.settings.language),
      continuous,
      handlers: {
        onInterim: (text) => {
          this.interim = text;
          this.emit();
        },
        onFinal: (text) => {
          void this.handleFinal(text);
        },
        onError: (kind) => {
          if (kind === "no-speech") return; // benign
          this.setError(kind);
        },
      },
    });
  }

  private async beginGoogleRecognition(continuous: boolean): Promise<void> {
    try {
      await this.googleRecognition.start(resolveLanguage(this.settings.language), {
        onInterim: (text) => { this.interim = text; this.emit(); },
        onFinal: (text) => { void this.handleFinal(text); },
        onError: () => {
          this.googleRecognition.stop();
          if (this.state === "listening") this.beginBrowserRecognition(continuous);
        },
      });
    } catch {
      this.googleRecognition.stop();
      if (this.state !== "listening") return;
      this.beginBrowserRecognition(continuous);
    }
  }

  /* ---------------- turn ---------------- */

  private async handleFinal(text: string): Promise<void> {
    const clean = text.trim();
    if (!clean) return;
    // Pause the mic while we think + speak (no echo, no double-processing).
    this.recognition.stop();
    this.googleRecognition.stop();
    this.interim = "";
    window.dispatchEvent(new CustomEvent("nexa:voice-output-state", { detail: { active: true } }));

    this.messages = [...this.messages, { id: uid(), role: "user", text: clean, at: new Date().toISOString() }];
    this.setState("thinking");

    try {
      const history: ChatTurn[] = this.messages
        .slice(-8)
        .map((m) => ({ role: m.role, content: m.text }));
      const result = await this.pipeline.process(clean, {
        history,
        conversationId: this.conversationId,
        addressStyle: loadProfile().addressingPreference,
        onNotice: (notice) => interactionBus.emit({ type: "notify", payload: notice }),
      });
      const assistant: VoiceMessage = {
        id: uid(),
        role: "assistant",
        text: result.text,
        at: new Date().toISOString(),
        provider: result.provider,
      };
      this.messages = [...this.messages, assistant];
      this.emit();
      this.speakOrResume(result.text);
    } catch {
      this.messages = [
        ...this.messages,
        { id: uid(), role: "assistant", text: "I couldn't reach the AI. Please check your connection or provider settings.", at: new Date().toISOString() },
      ];
      interactionBus.emit({ type: "notify", payload: { title: "Voice reply failed", message: "The AI provider could not be reached.", tone: "error" } });
      this.afterReply();
    }
  }

  private get shouldSpeak(): boolean {
    return this.settings.enableVoiceReply && this.settings.autoSpeak && !this.settings.muted;
  }

  private speakOrResume(text: string): void {
    if (!this.shouldSpeak || !VoiceManager.synthesisSupported()) {
      this.afterReply();
      return;
    }
    this.setState("speaking");
    this.synthesis.speak(text, this.settings, resolveLanguage(this.settings.language), {
      onEnd: () => this.afterReply(),
      onError: () => {
        // Text is already shown — surface a soft error, then continue.
        this.error = { kind: "tts", message: VOICE_ERROR_COPY.tts };
        this.afterReply();
      },
    });
  }

  /** Speak the most recent assistant reply on demand (e.g. "unmute + replay"). */
  speakLast(): void {
    const last = [...this.messages].reverse().find((m) => m.role === "assistant");
    if (last) this.speakOrResume(last.text);
  }

  private afterReply(): void {
    window.dispatchEvent(new CustomEvent("nexa:voice-output-state", { detail: { active: false } }));
    window.dispatchEvent(new CustomEvent("nexa:voice-turn-complete"));
    if (this.running) {
      // Continuous conversation — resume listening for the next turn.
      this.beginRecognition(true);
    } else {
      this.setState("idle");
    }
  }

  /* ---------------- controls ---------------- */

  /** Stop the AI mid-sentence and return to listening (or idle). */
  interrupt(): void {
    this.synthesis.cancel();
    if (this.state === "speaking") this.afterReply();
  }

  toggleMute(): void {
    this.updateSettings({ muted: !this.settings.muted });
    if (this.settings.muted) this.synthesis.cancel();
  }

  clearConversation(): void {
    this.messages = [];
    this.conversationId = `voice-${uid()}`;
    this.emit();
  }

  /** Speak a short sample with the current settings (Settings "Test voice"). */
  previewVoice(): void {
    if (!VoiceManager.synthesisSupported()) return;
    this.synthesis.speak(
      "Hi, I'm Nexa. এইটা আমার ভয়েস টেস্ট।",
      this.settings,
      resolveLanguage(this.settings.language),
      {},
    );
  }
}

export const voiceManager = new VoiceManager();
export { VoiceManager };
