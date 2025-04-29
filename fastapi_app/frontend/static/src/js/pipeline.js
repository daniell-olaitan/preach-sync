export class MicStream1 {
  constructor(wsUrl) {
    this.ws = null;
    this.wsUrl = wsUrl;
    this.mediaRecorder = null;
  }

  async init(queue) {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

    this.connectWebSocket();
    this.startRecording(stream, queue);
  }

  connectWebSocket() {
    this.ws = new WebSocket(this.wsUrl);

    this.ws.onopen = () => {
      console.log('WebSocket connected to', this.wsUrl);
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.ws.onclose = () => {
      console.log('WebSocket connection closed');
    };
  }

  startRecording(stream, audioQueue) {
    const options = { mimeType: 'audio/webm;codecs=opus' };
    this.mediaRecorder = new MediaRecorder(stream, options);

    this.mediaRecorder.ondataavailable = async (e) => {
      if (e.data.size > 0) {
        await audioQueue.put(e.data);
      }
    };

    this.mediaRecorder.start(100); // Send every 100ms
    console.log('Recording started');
  }

  stop() {
    if (this.mediaRecorder) this.mediaRecorder.stop();
    if (this.ws) this.ws.close();
    console.log('Recording stopped');
  }
}

export class MicStream {
  constructor(wsUrl) {
    this.wsUrl = wsUrl;
    this.ws = null;
    this.audioContext = null;
    this.workletNode = null;
  }

  async init(audioQueue) {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

    this.audioContext = new AudioContext({ sampleRate: 16000 });

    // Inline AudioWorkletProcessor as a Blob
    const processorCode = `
      class PCMProcessor extends AudioWorkletProcessor {
        constructor() {
          super();
          this.buffer = [];
          this.bufferSize = 16000;
        }

        process(inputs) {
          const input = inputs[0][0];
          if (!input) return true;

          for (let i = 0; i < input.length; i++) {
            const sample = Math.max(-1, Math.min(1, input[i]));
            const intSample = sample < 0 ? sample * 0x8000 : sample * 0x7FFF;
            this.buffer.push(intSample);
          }

          const chunkSize = 16000 * 0.1;
          if (this.buffer.length >= chunkSize) {
            const chunk = this.buffer.splice(0, chunkSize);
            const int16Buffer = new Int16Array(chunk);
            this.port.postMessage(int16Buffer.buffer, [int16Buffer.buffer]);
          }

          return true;
        }
      }

      registerProcessor("pcm-processor", PCMProcessor);
    `;

    const blob = new Blob([processorCode], { type: "application/javascript" });
    const moduleURL = URL.createObjectURL(blob);
    await this.audioContext.audioWorklet.addModule(moduleURL);

    const source = this.audioContext.createMediaStreamSource(stream);

    this.workletNode = new AudioWorkletNode(this.audioContext, "pcm-processor");
    source.connect(this.workletNode);
    this.workletNode.connect(this.audioContext.destination);

    this.connectWebSocket();

    this.workletNode.port.onmessage = async (event) => {
      await audioQueue.put(event.data);
    };

    console.log("Recording started (inline AudioWorklet)");
  }

  connectWebSocket() {
    this.ws = new WebSocket(this.wsUrl);

    this.ws.onopen = () => console.log("WebSocket connected");
    this.ws.onerror = (e) => console.error("WebSocket error:", e);
    this.ws.onclose = () => console.log("WebSocket closed");
  }

  stop() {
    if (this.workletNode) this.workletNode.disconnect();
    if (this.ws) this.ws.close();
    if (this.audioContext) this.audioContext.close();
    console.log("Recording stopped");
  }
}
