import { useState } from 'react'
import VideoUploader from './components/VideoUploader'
import ResultDisplay from './components/ResultDisplay'
import { useLanguage } from './contexts/LanguageContext'
import './App.css'

function App() {
  const { language, setLanguage, t } = useLanguage()
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [progressMessage, setProgressMessage] = useState<string>('')

  const handleConvert = async (
    file: File, 
    language: string, 
    model: string, 
    withSubtitles: boolean,
    enableDiarization: boolean,
    numSpeakers: number | null,
    beamSize: number,
    speakerNames: string[],
    translateToEnglish: boolean
  ) => {
    console.log('=== НАЧАЛО КОНВЕРТАЦИИ ===')
    console.log('Файл:', file.name, 'Размер:', (file.size / 1024 / 1024).toFixed(2), 'MB')
    console.log('Настройки:', { language, model, withSubtitles, enableDiarization, numSpeakers, beamSize })
    
    if (!file) {
      console.error('ОШИБКА: Файл не передан в handleConvert!')
      setError('Файл не выбран')
      return
    }
    
    setLoading(true)
    setError(null)
    setResult(null)
    setProgressMessage('Подготовка к загрузке...')
    console.log('Состояние: loading = true')

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('language', language)
      formData.append('model', model)
      formData.append('beam_size', beamSize.toString())
      formData.append('enable_diarization', enableDiarization.toString())
      formData.append('translate_to_english', translateToEnglish.toString())
      if (numSpeakers !== null) {
        formData.append('num_speakers', numSpeakers.toString())
      }
      // Добавляем имена спикеров
      if (speakerNames.length > 0 && speakerNames.some(name => name.trim() !== '')) {
        formData.append('speaker_names', JSON.stringify(speakerNames.filter(name => name.trim() !== '')))
      }

      const endpoint = withSubtitles 
        ? '/api/convert-with-subtitles'
        : '/api/convert'
      
      // Определяем URL для API
      // В production (Hugging Face Spaces) используем относительный путь
      // В development используем полный URL
      const apiUrl = import.meta.env.VITE_API_URL || (
        window.location.hostname === 'localhost' 
          ? 'http://localhost:8000' 
          : '' // Относительный путь для production
      )
      const fullUrl = `${apiUrl}${endpoint}`
      console.log('Отправка запроса на:', endpoint)
      console.log('Полный URL:', fullUrl)
      console.log('Размер FormData:', formData.get('file') ? (formData.get('file') as File).size : 'нет файла')
      
      // Добавляем параметры для субтитров
      if (withSubtitles) {
        formData.append('include_speakers', enableDiarization.toString())
      }
      
      // Создаем AbortController для таймаута (10 минут для больших файлов)
      const controller = new AbortController()
      const timeoutId = setTimeout(() => {
        console.error('Таймаут запроса!')
        controller.abort()
      }, 600000) // 10 минут
      
      console.log('Начало загрузки файла...')
      const startTime = Date.now()
      
      // Пробуем прямой запрос к backend, если прокси не работает
      // Используем тот же API URL что и для конвертации
      const backendUrl = apiUrl + endpoint
      console.log('Пробуем прямой запрос к:', backendUrl)
      console.log('Размер FormData:', file.size, 'байт')
      
      // Тестовый запрос для проверки связи
      setProgressMessage('Проверка связи с сервером...')
      try {
        console.log('Проверка связи с backend...')
        const testController = new AbortController()
        const testTimeout = setTimeout(() => testController.abort(), 3000) // 3 секунды
        
        const testResponse = await fetch(`${apiUrl}/api/test`, {
          method: 'GET',
          signal: testController.signal,
          mode: 'cors' // Явно указываем CORS режим
        })
        
        clearTimeout(testTimeout)
        
        if (!testResponse.ok) {
          throw new Error(`HTTP ${testResponse.status}: ${testResponse.statusText}`)
        }
        
        const testData = await testResponse.json()
        console.log('✓ Backend доступен:', testData)
      } catch (testErr: any) {
        console.error('✗ Backend недоступен:', testErr)
        console.error('Детали ошибки:', {
          name: testErr.name,
          message: testErr.message,
          stack: testErr.stack
        })
        
        // Не блокируем запрос, просто предупреждаем
        console.warn('Продолжаем попытку отправки файла...')
        // setError('Не удается подключиться к серверу. Убедитесь, что backend запущен на порту 8000.')
        // setLoading(false)
        // return
      }
      
      console.log('Отправка основного запроса...')
      setProgressMessage('Загрузка файла на сервер...')
      const response = await fetch(backendUrl, {
        method: 'POST',
        body: formData,
        signal: controller.signal,
        mode: 'cors', // Явно указываем CORS режим
        // Не добавляем Content-Type - браузер сам установит с boundary для FormData
      })
      
      clearTimeout(timeoutId)
      const uploadTime = ((Date.now() - startTime) / 1000).toFixed(2)
      console.log(`Файл загружен за ${uploadTime} секунд`)
      console.log('Статус ответа:', response.status, response.statusText)

      if (!response.ok) {
        console.error('Ошибка ответа:', response.status)
        const errorData = await response.json().catch(() => ({ detail: 'Неизвестная ошибка' }))
        console.error('Детали ошибки:', errorData)
        throw new Error(errorData.detail || 'Ошибка при конвертации')
      }

      setProgressMessage('Обработка видео на сервере...')
      console.log('Получение данных ответа...')
      const data = await response.json()
      console.log('Данные получены:', {
        success: data.success,
        textLength: data.text?.length || 0,
        segmentsCount: data.segments?.length || 0
      })
      console.log('=== Конвертация завершена успешно ===')
      setProgressMessage('Завершено!')
      setResult(data)
    } catch (err: any) {
      console.error('=== ОШИБКА ===')
      console.error('Тип ошибки:', err.name)
      console.error('Сообщение:', err.message)
      console.error('Полная ошибка:', err)
      
      if (err.name === 'AbortError') {
        setError('Загрузка прервана из-за таймаута. Попробуйте файл меньшего размера или подождите.')
      } else if (err.message.includes('ERR_UPLOAD_FILE_CHANGED')) {
        setError('Файл был изменен во время загрузки. Пожалуйста, попробуйте снова.')
      } else {
        setError(err.message || 'Произошла ошибка при загрузке файла')
      }
    } finally {
      setLoading(false)
      console.log('Состояние загрузки: завершено')
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Кнопки переключения языка */}
        <div className="flex justify-end mb-4 gap-2">
          <button
            onClick={() => setLanguage('ru')}
            className={`px-4 py-2 rounded-lg shadow-sm transition-colors font-medium ${
              language === 'ru' 
                ? 'bg-blue-600 text-white' 
                : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
            }`}
            title="Переключить на русский"
          >
            RU
          </button>
          <button
            onClick={() => setLanguage('en')}
            className={`px-4 py-2 rounded-lg shadow-sm transition-colors font-medium ${
              language === 'en' 
                ? 'bg-blue-600 text-white' 
                : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
            }`}
            title="Switch to English"
          >
            EN
          </button>
        </div>

        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            {t.title}
          </h1>
          <p className="text-gray-600">
            {t.subtitle}
          </p>
        </header>

        <div className="max-w-4xl mx-auto">
          <VideoUploader 
            onConvert={handleConvert}
            loading={loading}
            t={t}
          />

          {loading && (
            <div className="mt-6 p-8 bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-xl shadow-2xl border-2 border-blue-400">
              <div className="flex items-center space-x-6">
                <svg className="animate-spin h-12 w-12 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <div className="flex-1">
                  <h3 className="text-2xl font-bold mb-2">
                    ⚙️ {t.processing}
                  </h3>
                  <p className="text-lg mb-4 opacity-90">
                    {progressMessage || (language === 'ru' ? 'Обработка файла на сервере. Это может занять несколько минут...' : 'Processing file on server. This may take several minutes...')}
                  </p>
                  <div className="bg-blue-300 rounded-full h-3 overflow-hidden shadow-inner">
                    <div className="bg-white h-3 rounded-full animate-pulse" style={{ width: '100%' }}></div>
                  </div>
                  <p className="text-sm mt-3 opacity-75">
                    {language === 'ru' ? 'Пожалуйста, не закрывайте страницу' : 'Please do not close this page'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {error && (
            <div className="mt-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg">
              {error}
            </div>
          )}

          {result && (
            <ResultDisplay result={result} t={t} />
          )}
        </div>
      </div>
    </div>
  )
}

export default App

