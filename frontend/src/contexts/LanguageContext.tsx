import { createContext, useContext, useState, ReactNode } from 'react'
import { ru } from '../locales/ru'
import { en } from '../locales/en'

type Language = 'ru' | 'en'
type Translations = typeof ru

interface LanguageContextType {
  language: Language
  setLanguage: (lang: Language) => void
  t: Translations
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined)

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguage] = useState<Language>(() => {
    // Сохраняем выбор языка в localStorage
    const saved = localStorage.getItem('language') as Language
    return saved === 'en' || saved === 'ru' ? saved : 'ru'
  })

  const translations: Record<Language, Translations> = {
    ru,
    en
  }

  const handleSetLanguage = (lang: Language) => {
    setLanguage(lang)
    localStorage.setItem('language', lang)
  }

  return (
    <LanguageContext.Provider value={{ language, setLanguage: handleSetLanguage, t: translations[language] }}>
      {children}
    </LanguageContext.Provider>
  )
}

export function useLanguage() {
  const context = useContext(LanguageContext)
  if (context === undefined) {
    throw new Error('useLanguage must be used within a LanguageProvider')
  }
  return context
}

