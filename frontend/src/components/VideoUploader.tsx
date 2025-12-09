import { useState, useRef } from 'react'

interface VideoUploaderProps {
  onConvert: (file: File, language: string, model: string, withSubtitles: boolean, enableDiarization: boolean, numSpeakers: number | null, beamSize: number) => void
  loading: boolean
}

export default function VideoUploader({ onConvert, loading }: VideoUploaderProps) {
  const [file, setFile] = useState<File | null>(null)
  const [language, setLanguage] = useState('auto')
  const [model, setModel] = useState('base')
  const [withSubtitles, setWithSubtitles] = useState(false)
  const [enableDiarization, setEnableDiarization] = useState(false)
  const [numSpeakers, setNumSpeakers] = useState<string>('')
  const [beamSize, setBeamSize] = useState(5)
  const [speedMode, setSpeedMode] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    console.log('=== КНОПКА НАЖАТА ===')
    console.log('Файл:', file?.name)
    console.log('Настройки:', { language, model, withSubtitles, enableDiarization, numSpeakers, speedMode })
    
    if (!file) {
      console.error('ОШИБКА: Файл не выбран!')
      alert('Пожалуйста, выберите файл')
      return
    }
    
    const speakers = numSpeakers ? parseInt(numSpeakers) : null
    const beam = speedMode ? 1 : beamSize
    console.log('Вызов onConvert с параметрами:', { speakers, beam })
    onConvert(file, language, model, withSubtitles, enableDiarization, speakers, beam)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0])
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Загрузка файла */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Выберите видео файл
          </label>
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors cursor-pointer"
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="video/*"
              onChange={handleFileChange}
              className="hidden"
            />
            {file ? (
              <div>
                <p className="text-green-600 font-medium">✓ {file.name}</p>
                <p className="text-sm text-gray-500 mt-2">
                  {(file.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            ) : (
              <div>
                <p className="text-gray-600">Перетащите файл сюда или нажмите для выбора</p>
                <p className="text-sm text-gray-400 mt-2">
                  Поддерживаются форматы: MP4, AVI, MOV, MKV и др.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Настройки */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Язык
            </label>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="auto">Автоопределение</option>
              <option value="ru">Русский</option>
              <option value="en">Английский</option>
              <option value="es">Испанский</option>
              <option value="fr">Французский</option>
              <option value="de">Немецкий</option>
              <option value="zh">Китайский</option>
              <option value="ja">Японский</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Модель Whisper
            </label>
            <select
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="tiny">Tiny (быстро, меньше точность)</option>
              <option value="base">Base (рекомендуется)</option>
              <option value="small">Small (лучше точность)</option>
              <option value="medium">Medium (высокая точность)</option>
              <option value="large">Large (максимальная точность)</option>
            </select>
          </div>
        </div>

        {/* Опции */}
        <div className="space-y-3">
          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={withSubtitles}
              onChange={(e) => setWithSubtitles(e.target.checked)}
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <span className="text-sm text-gray-700">
              Генерировать субтитры (SRT/VTT)
            </span>
          </label>
          
          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={speedMode}
              onChange={(e) => setSpeedMode(e.target.checked)}
              className="w-4 h-4 text-green-600 border-gray-300 rounded focus:ring-green-500"
            />
            <span className="text-sm text-gray-700">
              ⚡ Режим скорости (быстрее, но менее точно)
            </span>
          </label>
          
          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={enableDiarization}
              onChange={(e) => setEnableDiarization(e.target.checked)}
              className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
            />
            <span className="text-sm text-gray-700">
              🎭 Разделение по ролям (если несколько человек)
            </span>
          </label>
          
          {enableDiarization && (
            <div className="ml-6">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Количество спикеров (оставьте пустым для автоопределения):
              </label>
              <input
                type="number"
                min="1"
                max="10"
                value={numSpeakers}
                onChange={(e) => setNumSpeakers(e.target.value)}
                placeholder="Авто"
                className="w-32 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>
          )}
        </div>

        {/* Кнопка конвертации */}
        <button
          type="submit"
          disabled={!file || loading}
          className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? (
            <span className="flex items-center justify-center">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Обработка...
            </span>
          ) : (
            'Конвертировать в текст'
          )}
        </button>
      </form>
    </div>
  )
}

