import { useState } from 'react'
import VideoUploader from './components/VideoUploader'
import ResultDisplay from './components/ResultDisplay'
import './App.css'

function App() {
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleConvert = async (
    file: File, 
    language: string, 
    model: string, 
    withSubtitles: boolean,
    enableDiarization: boolean,
    numSpeakers: number | null,
    beamSize: number
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
    console.log('Состояние: loading = true')

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('language', language)
      formData.append('model', model)
      formData.append('beam_size', beamSize.toString())
      formData.append('enable_diarization', enableDiarization.toString())
      if (numSpeakers !== null) {
        formData.append('num_speakers', numSpeakers.toString())
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
      const apiUrl = import.meta.env.VITE_API_URL || (
        window.location.hostname === 'localhost' 
          ? 'http://localhost:8000' 
          : ''
      )
      const backendUrl = apiUrl + endpoint
      console.log('Пробуем прямой запрос к:', backendUrl)
      console.log('Размер FormData:', file.size, 'байт')
      
      // Тестовый запрос для проверки связи
      try {
        console.log('Проверка связи с backend...')
        const testController = new AbortController()
        const testTimeout = setTimeout(() => testController.abort(), 3000) // 3 секунды
        
        const apiUrl = import.meta.env.VITE_API_URL || (
          window.location.hostname === 'localhost' 
            ? 'http://localhost:8000' 
            : ''
        )
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

      console.log('Получение данных ответа...')
      const data = await response.json()
      console.log('Данные получены:', {
        success: data.success,
        textLength: data.text?.length || 0,
        segmentsCount: data.segments?.length || 0
      })
      console.log('=== Конвертация завершена успешно ===')
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
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            Видео в текст конвертер
          </h1>
          <p className="text-gray-600">
            Конвертируйте видео в текст с помощью AI
          </p>
        </header>

        <div className="max-w-4xl mx-auto">
          <VideoUploader 
            onConvert={handleConvert}
            loading={loading}
          />

          {error && (
            <div className="mt-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg">
              {error}
            </div>
          )}

          {result && (
            <ResultDisplay result={result} />
          )}
        </div>
      </div>
    </div>
  )
}

export default App

