import { MicStream } from '../pipeline.js';

import htm from 'https://esm.sh/htm';
import { h, render } from 'https://esm.sh/preact';
import { useRef, useState, useEffect } from 'https://esm.sh/preact/hooks';

const html = htm.bind(h);

function Home() {
  const [text, setText] = useState('');
  const [verses, setVerses] = useState([
    'John 3:16',
    'Psalm 23:1',
    'Romans 8:28'
  ]);
  const [selectedVerse, setSelectedVerse] = useState('');
  const [verseContent, setVerseContent] = useState('');
  let mic;

  const startMic = () => {
    mic = new MicStream("ws://localhost:8000/ws/audio");
    mic.init();

    const socket = new WebSocket("ws://localhost:8000/ws/audio");
    socket.onmessage = (event) => {
      const newText = event.data;
      setText(prev => prev + '\n' + newText);

      // Example of adding verse suggestions dynamically
      // In practice, this should come from backend detection
      if (newText.includes("John 3 16")) {
        setVerses(prev => [...new Set([...prev, 'John 3:16'])]);
      }
    };
  };

  const stopMic = () => {
    if (mic) mic.stop();
  };

  const handleVerseClick = (verse) => {
    setSelectedVerse(verse);
    // Simulate fetching full verse content
    setVerseContent(`Full content of ${verse} will be fetched and shown here.`);
  };

  return html`
    <div class="h-screen flex bg-gray-100">
      <!-- Left Panel -->
      <div class="w-1/2 p-6 overflow-y-auto border-r border-gray-300">
        <h1 class="text-3xl font-bold text-gray-800 mb-4">🎙️ VerseCast</h1>
        <div class="mb-4">
          <button class="bg-blue-500 text-white px-4 py-2 rounded-md hover:bg-blue-700 mr-2" onClick=${startMic}>Start Mic</button>
          <button class="bg-red-500 text-white px-4 py-2 rounded-md hover:bg-red-700" onClick=${stopMic}>Stop Mic</button>
        </div>
        <textarea class="w-full h-40 p-4 border rounded-md text-gray-700 mb-4" readonly value=${text}></textarea>

        <h2 class="text-xl font-semibold text-gray-700 mt-6 mb-2">Detected Verses:</h2>
        <ul>
          ${verses.map(verse => html`
            <li>
              <button
                class="text-blue-600 hover:underline"
                onClick=${() => handleVerseClick(verse)}
              >
                ${verse}
              </button>
            </li>
          `)}
        </ul>
      </div>

      <!-- Right Panel -->
      <div class="w-1/2 p-6 overflow-y-auto">
        <h2 class="text-2xl font-semibold text-gray-800 mb-4">Selected Verse:</h2>
        <p class="text-gray-700 text-lg mb-2">${selectedVerse}</p>
        <div class="bg-white shadow-md rounded-lg p-4 h-72 overflow-y-auto text-gray-800 border border-gray-200">
          ${verseContent || 'Click a verse to see its content'}
        </div>
      </div>
    </div>
  `;
}

render(html`<${Home} />`, document.getElementById('home'));
