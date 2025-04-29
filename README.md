## 📖 Preach Sync

This project provides a complete pipeline for detecting and fetching Bible verses from spoken language. It leverages Deepgram for real-time audio transcription and Mistral AI for extracting structured Bible verse references, followed by retrieving the verse content from a local Bible JSON dataset.

---

### 🚀 Features

- 🎙️ Real-time transcription using **Deepgram WebSocket API**
- 🧠 Structured verse detection using **Mistral AI**
- 📚 Bible verse retrieval from local **NKJV**
- ✅ Handles fuzzy/approximate references (e.g., "John three sixteen", "first Corinthians chapter 13 verse 4 to 10")

---

### 🧰 Tech Stack

- Python 3.10+
- [Deepgram](https://deepgram.com/)
- [Mistral AI](https://docs.mistral.ai/)
- Websockets
- Asyncio

---

### ⚙️ Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/daniell-olaitan/preach-sync.git
   cd preach-sync
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Add `.env` file**
   Create a `.env` file at the root of your project:
   ```env
   DEEPGRAM_API_KEY=your_deepgram_api_key
   MISTRAL_API_KEY=your_mistral_api_key
   MISTRAL_MODEL=the_model_you_want_to_use
   ```

4. **Run the FastAPI App**
   ```bash
   cd fastapi_app
   fastapi dev main.py
   ```

5. **Test the App**
   - Open your browser and go to: [http://localhost:8000/test](http://localhost:8000/test)
   - Watch the **terminal output** for the detected verse and its content

---

### 🧪 Run Demo (Verse Detection Only)

```bash
python detector.py
```

This will run predefined test inputs through the Mistral-based verse detector and print the verse if found.

---

### ✅ Example Output

**Input (transcript):**
> "John chapter three verse sixteen"

**Output:**
```
John 3:16
16. For God so loved the world, that He gave His only begotten Son...
```

---

### 📌 To Do

- Add microphone audio streaming support (in progress)
- Support multiple translations (NIV, ESV, etc.)

---

### 📜 License

MIT License
