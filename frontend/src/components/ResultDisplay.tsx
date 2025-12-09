import { useState } from 'react'
import type { Translations } from '../locales/ru'

interface ResultDisplayProps {
  result: {
    text: string
    segments?: Array<{
      id: number
      start: number
      end: number
      text: string
      speaker?: string
    }>
    subtitles?: string
    format?: string
    language?: string
    speakers?: Record<string, string>
    num_speakers?: number
  }
  t: Translations
}

export default function ResultDisplay({ result, t }: ResultDisplayProps) {
  const [copied, setCopied] = useState(false)

  const copyToClipboard = () => {
    navigator.clipboard.writeText(result.text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const downloadText = () => {
    const blob = new Blob([result.text], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'transcription.txt'
    a.click()
    URL.revokeObjectURL(url)
  }

  const downloadSubtitles = (format: string) => {
    if (!result.subtitles) return
    
    const blob = new Blob([result.subtitles], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `subtitles.${format}`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="mt-6 bg-white rounded-lg shadow-lg p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold text-gray-800">{t.result}</h2>
        <div className="flex gap-4 items-center">
          {result.language && (
            <span className="text-sm text-gray-500">
              {t.languageLabel}: {result.language.toUpperCase()}
            </span>
          )}
          {result.num_speakers && result.num_speakers > 0 && (
            <span className="text-sm text-purple-600 font-medium">
              🎭 {t.speakers}: {result.num_speakers}
            </span>
          )}
        </div>
      </div>

      {/* Текст */}
      <div className="mb-4">
        <div className="flex justify-between items-center mb-2">
          <h3 className="text-lg font-semibold text-gray-700">{t.text}:</h3>
          <div className="space-x-2">
            <button
              onClick={copyToClipboard}
              className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded transition-colors"
            >
              {copied ? t.copied : t.copy}
            </button>
            <button
              onClick={downloadText}
              className="px-3 py-1 text-sm bg-blue-100 hover:bg-blue-200 rounded transition-colors"
            >
              {t.downloadTxt}
            </button>
          </div>
        </div>
        <div className="bg-gray-50 rounded-lg p-4 max-h-96 overflow-y-auto">
          <p className="text-gray-800 whitespace-pre-wrap">{result.text}</p>
        </div>
      </div>

      {/* Субтитры */}
      {result.subtitles && (
        <div className="mt-4">
          <div className="flex justify-between items-center mb-2">
            <h3 className="text-lg font-semibold text-gray-700">
              {t.subtitles}
            </h3>
            <button
              onClick={() => downloadSubtitles(result.format || 'srt')}
              className="px-3 py-1 text-sm bg-green-100 hover:bg-green-200 rounded transition-colors"
            >
              {result.format === 'srt' ? t.downloadSrt : t.downloadVtt}
            </button>
          </div>
          <div className="bg-gray-50 rounded-lg p-4 max-h-64 overflow-y-auto">
            <pre className="text-sm text-gray-700 whitespace-pre-wrap">
              {result.subtitles}
            </pre>
          </div>
        </div>
      )}

      {/* Информация о спикерах */}
      {result.speakers && Object.keys(result.speakers).length > 0 && (
        <div className="mt-4">
          <h3 className="text-lg font-semibold text-gray-700 mb-2">
            {t.textBySpeakers}
          </h3>
          <div className="space-y-3">
            {Object.entries(result.speakers).map(([speaker, text]) => (
              <div key={speaker} className="bg-purple-50 rounded-lg p-4 border border-purple-200">
                <div className="font-semibold text-purple-700 mb-2">{speaker}:</div>
                <div className="text-gray-800">{text}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Сегменты с временными метками */}
      {result.segments && result.segments.length > 0 && (
        <div className="mt-4">
          <h3 className="text-lg font-semibold text-gray-700 mb-2">
            {t.segmentsWithTimestamps}
          </h3>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {result.segments.map((segment) => (
              <div
                key={segment.id}
                className={`bg-gray-50 rounded p-3 text-sm ${segment.speaker ? 'border-l-4 border-purple-400' : ''}`}
              >
                <div className="text-gray-500 mb-1 flex justify-between">
                  <span>{formatTime(segment.start)} → {formatTime(segment.end)}</span>
                  {segment.speaker && (
                    <span className="text-purple-600 font-medium">{segment.speaker}</span>
                  )}
                </div>
                <div className="text-gray-800">{segment.text}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function formatTime(seconds: number): string {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

