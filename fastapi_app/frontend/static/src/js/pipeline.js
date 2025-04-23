export class MicStream {
  constructor(wsUrl) {
    this.wsUrl = wsUrl;
    this.ws = null;
    this.mediaRecorder = null;
  }

  async init() {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    this.connectWebSocket();
    this.startRecording(stream);
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

  startRecording(stream) {
    const options = { mimeType: 'audio/webm;codecs=opus' };
    this.mediaRecorder = new MediaRecorder(stream, options);

    this.mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0 && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(e.data);
      }
    };

    this.mediaRecorder.start(250); // Send every 250ms
    console.log('Recording started');
  }

  stop() {
    if (this.mediaRecorder) this.mediaRecorder.stop();
    if (this.ws) this.ws.close();
    console.log('Recording stopped');
  }
}
