# Альтернативные варианты реализации

## Вариант 2: Flask + Vue.js + SpeechRecognition

### Backend (Flask)

```python
# backend/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import speech_recognition as sr
import moviepy.editor as mp
import tempfile
import os

app = Flask(__name__)
CORS(app)

@app.route('/api/convert', methods=['POST'])
def convert():
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    
    file = request.files['file']
    language = request.form.get('language', 'ru-RU')
    
    # Сохранение временного файла
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
        file.save(tmp.name)
        video_path = tmp.name
    
    try:
        # Извлечение аудио
        video = mp.VideoFileClip(video_path)
        audio_path = tempfile.NamedTemporaryFile(delete=False, suffix='.wav').name
        video.audio.write_audiofile(audio_path)
        
        # Распознавание
        r = sr.Recognizer()
        with sr.AudioFile(audio_path) as source:
            audio = r.record(source)
        
        text = r.recognize_google(audio, language=language)
        
        return jsonify({'text': text})
    finally:
        os.unlink(video_path)
        os.unlink(audio_path)
```

### Frontend (Vue.js)

```vue
<!-- frontend/src/components/VideoUploader.vue -->
<template>
  <div>
    <input type="file" @change="handleFile" accept="video/*" />
    <button @click="convert" :disabled="!file || loading">
      {{ loading ? 'Обработка...' : 'Конвертировать' }}
    </button>
    <div v-if="result">{{ result.text }}</div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'

const file = ref(null)
const loading = ref(false)
const result = ref(null)

const handleFile = (e) => {
  file.value = e.target.files[0]
}

const convert = async () => {
  const formData = new FormData()
  formData.append('file', file.value)
  formData.append('language', 'ru-RU')
  
  loading.value = true
  try {
    const res = await axios.post('http://localhost:5000/api/convert', formData)
    result.value = res.data
  } finally {
    loading.value = false
  }
}
</script>
```

---

## Вариант 3: Node.js + Express + AssemblyAI

### Backend (Express)

```javascript
// backend/server.js
const express = require('express');
const multer = require('multer');
const AssemblyAI = require('assemblyai');
const ffmpeg = require('fluent-ffmpeg');
const fs = require('fs');
const path = require('path');

const app = express();
const upload = multer({ dest: 'uploads/' });
const client = new AssemblyAI({ apiKey: process.env.ASSEMBLYAI_API_KEY });

app.post('/api/convert', upload.single('file'), async (req, res) => {
  const videoPath = req.file.path;
  const audioPath = path.join('uploads', `${req.file.filename}.wav`);
  
  // Извлечение аудио
  await new Promise((resolve, reject) => {
    ffmpeg(videoPath)
      .toFormat('wav')
      .on('end', resolve)
      .on('error', reject)
      .save(audioPath);
  });
  
  // Загрузка в AssemblyAI
  const audioUrl = await client.files.upload(audioPath);
  
  // Транскрипция
  const transcript = await client.transcripts.create({
    audio_url: audioUrl,
    language_code: req.body.language || 'ru'
  });
  
  // Очистка
  fs.unlinkSync(videoPath);
  fs.unlinkSync(audioPath);
  
  res.json({ text: transcript.text });
});

app.listen(3000);
```

---

## Вариант 4: Django + Vosk

### Backend (Django)

```python
# backend/views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import vosk
import ffmpeg
import tempfile

model = vosk.Model("model")  # Загрузить модель Vosk

@csrf_exempt
def convert_video(request):
    if request.method == 'POST':
        video_file = request.FILES['file']
        
        # Сохранение временного файла
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(video_file.read())
            video_path = tmp.name
        
        # Извлечение аудио
        audio_path = extract_audio(video_path)
        
        # Распознавание
        rec = vosk.KaldiRecognizer(model, 16000)
        text_parts = []
        
        with open(audio_path, 'rb') as f:
            while True:
                data = f.read(4000)
                if len(data) == 0:
                    break
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    text_parts.append(result.get('text', ''))
        
        final_result = json.loads(rec.FinalResult())
        text_parts.append(final_result.get('text', ''))
        
        return JsonResponse({'text': ' '.join(text_parts)})
```

---

## Сравнение времени разработки

| Вариант | Backend | Frontend | Общее время |
|---------|---------|----------|-------------|
| Вариант 1 (Whisper) | 4-6 часов | 3-4 часа | 1 день |
| Вариант 2 (SpeechRec) | 2-3 часа | 2-3 часа | 4-6 часов |
| Вариант 3 (AssemblyAI) | 1-2 часа | 2-3 часа | 3-5 часов |
| Вариант 4 (Vosk) | 3-4 часа | 2-3 часа | 5-7 часов |

---

## Рекомендации

- **Для продакшена:** Вариант 1 (Whisper) - лучшее качество
- **Для прототипа:** Вариант 2 (SpeechRec) - быстрый старт
- **Для масштабирования:** Вариант 3 (AssemblyAI) - готовый сервис
- **Для приватности:** Вариант 4 (Vosk) - полностью офлайн



