import type { RecognitionHandlers } from "./recognitionService";

type GoogleMessage = { type?: "ready" | "interim" | "final" | "unavailable" | "error"; text?: string; message?: string };

function pcm16(input: Float32Array): ArrayBuffer {
  const output = new Int16Array(input.length);
  for (let index = 0; index < input.length; index += 1) {
    const sample = Math.max(-1, Math.min(1, input[index]));
    output[index] = sample < 0 ? sample * 0x8000 : sample * 0x7fff;
  }
  return output.buffer;
}

export class GoogleStreamingService {
  private socket: WebSocket | null = null;
  private stream: MediaStream | null = null;
  private context: AudioContext | null = null;
  private processor: ScriptProcessorNode | null = null;
  private source: MediaStreamAudioSourceNode | null = null;
  private stopped = true;

  async start(language: string, handlers: RecognitionHandlers): Promise<void> {
    this.stop();
    const readiness = await fetch("http://127.0.0.1:8000/api/setup/readiness").then((response) => {
      if (!response.ok) throw new Error("Backend readiness check failed.");
      return response.json() as Promise<{ capabilities?: { google_streaming_stt?: { ready?: boolean; action?: string } } }>;
    });
    const google = readiness.capabilities?.google_streaming_stt;
    if (!google?.ready) throw new Error(google?.action || "Google streaming STT is not configured.");

    this.stream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true } });
    this.context = new AudioContext();
    this.source = this.context.createMediaStreamSource(this.stream);
    this.processor = this.context.createScriptProcessor(4096, 1, 1);
    const socket = new WebSocket("ws://127.0.0.1:8000/api/voice/stt/google-stream");
    socket.binaryType = "arraybuffer";
    this.socket = socket;
    this.stopped = false;

    await new Promise<void>((resolve, reject) => {
      let ready = false;
      const timeout = window.setTimeout(() => reject(new Error("Google STT connection timed out.")), 8_000);
      socket.onopen = () => {
        socket.send(JSON.stringify({ language, sample_rate: this.context?.sampleRate ?? 48_000 }));
      };
      socket.onmessage = (event) => {
        const message = JSON.parse(String(event.data)) as GoogleMessage;
        if (message.type === "ready") {
          ready = true;
          window.clearTimeout(timeout);
          handlers.onStart?.();
          resolve();
        } else if (message.type === "interim" && message.text) handlers.onInterim?.(message.text);
        else if (message.type === "final" && message.text) handlers.onFinal?.(message.text);
        else if (message.type === "unavailable" || message.type === "error") {
          window.clearTimeout(timeout);
          const detail = message.message || "Google streaming STT is unavailable.";
          if (ready) handlers.onError?.("network", detail);
          else reject(new Error(detail));
        }
      };
      socket.onerror = () => { window.clearTimeout(timeout); reject(new Error("Google streaming STT connection failed.")); };
    });

    this.processor.onaudioprocess = (event) => {
      if (this.stopped || socket.readyState !== WebSocket.OPEN) return;
      socket.send(pcm16(event.inputBuffer.getChannelData(0)));
    };
    this.source.connect(this.processor);
    this.processor.connect(this.context.destination);
  }

  stop(): void {
    this.stopped = true;
    if (this.processor) { this.processor.disconnect(); this.processor.onaudioprocess = null; }
    this.source?.disconnect();
    this.stream?.getTracks().forEach((track) => track.stop());
    void this.context?.close();
    if (this.socket && this.socket.readyState < WebSocket.CLOSING) this.socket.close(1000, "client stopped");
    this.socket = null; this.stream = null; this.context = null; this.processor = null; this.source = null;
  }
}
