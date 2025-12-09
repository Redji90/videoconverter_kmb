import { useState, useRef } from 'react'
import type { Translations } from '../locales/ru'

interface VideoUploaderProps {
  onConvert: (file: File, language: string, model: string, withSubtitles: boolean, enableDiarization: boolean, numSpeakers: number | null, beamSize: number, speakerNames: string[]) => void
  loading: boolean
  t: Translations
}

export default function VideoUploader({ onConvert, loading, t }: VideoUploaderProps) {
  const [file, setFile] = useState<File | null>(null)
  const [language, setLanguage] = useState('auto')
  const [model, setModel] = useState('base')
  const [withSubtitles, setWithSubtitles] = useState(false)
  const [enableDiarization, setEnableDiarization] = useState(false)
  const [numSpeakers, setNumSpeakers] = useState<string>('')
  const [beamSize, setBeamSize] = useState(5)
  const [speedMode, setSpeedMode] = useState(false)
  const [speakerNames, setSpeakerNames] = useState<string[]>(['', ''])
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
      alert(t.selectFile)
      return
    }
    
    const speakers = numSpeakers ? parseInt(numSpeakers) : null
    const beam = speedMode ? 1 : beamSize
    // Фильтруем пустые имена спикеров
    const names = speakerNames.filter(name => name.trim() !== '')
    console.log('Вызов onConvert с параметрами:', { speakers, beam, speakerNames: names })
    onConvert(file, language, model, withSubtitles, enableDiarization, speakers, beam, names)
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
            {t.selectVideo}
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
                <p className="text-gray-600">{t.dragDrop}</p>
                <p className="text-sm text-gray-400 mt-2">
                  {t.supportedFormats}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Настройки */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t.language}
            </label>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="auto">{t.autoDetect}</option>
              <option value="ru">{t.language === 'Language' ? 'Russian' : 'Русский'}</option>
              <option value="en">{t.language === 'Language' ? 'English' : 'Английский'}</option>
              <option value="es">{t.language === 'Language' ? 'Spanish' : 'Испанский'}</option>
              <option value="fr">{t.language === 'Language' ? 'French' : 'Французский'}</option>
              <option value="de">{t.language === 'Language' ? 'German' : 'Немецкий'}</option>
              <option value="zh">{t.language === 'Language' ? 'Chinese' : 'Китайский'}</option>
              <option value="ja">{t.language === 'Language' ? 'Japanese' : 'Японский'}</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t.model}
            </label>
            <select
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="tiny">{t.modelTiny}</option>
              <option value="base">{t.modelBase}</option>
              <option value="small">{t.modelSmall}</option>
              <option value="medium">{t.modelMedium}</option>
              <option value="large">{t.modelLarge}</option>
            </select>
            {model === 'large' && (
              <p className="mt-1 text-xs text-orange-600">
                {t.modelLargeWarning}
              </p>
            )}
            {model === 'medium' && (
              <p className="mt-1 text-xs text-yellow-600">
                {t.modelMediumWarning}
              </p>
            )}
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
              {t.generateSubtitles}
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
              {t.speedMode}
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
              {t.enableDiarization}
            </span>
          </label>
          
          {enableDiarization && (
            <div className="ml-6 space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t.numSpeakers}
                </label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={numSpeakers}
                  onChange={(e) => setNumSpeakers(e.target.value)}
                  placeholder={t.autoDetect}
                  className="w-32 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t.speakerNames}
                </label>
                <div className="space-y-2">
                  {speakerNames.map((name, index) => (
                    <input
                      key={index}
                      type="text"
                      value={name}
                      onChange={(e) => {
                        const newNames = [...speakerNames]
                        newNames[index] = e.target.value
                        // Автоматически добавляем новое поле, если последнее заполнено
                        if (index === speakerNames.length - 1 && e.target.value.trim() !== '' && speakerNames.length < 5) {
                          newNames.push('')
                        }
                        setSpeakerNames(newNames)
                      }}
                      placeholder={t.speakerPlaceholder.replace('{num}', (index + 1).toString())}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                    />
                  ))}
                </div>
                <p className="mt-1 text-xs text-gray-500">
                  {t.speakerNamesHint}
                </p>
              </div>
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
              {t.processing}
            </span>
          ) : (
            t.convert
          )}
        </button>
      </form>
    </div>
  )
}

