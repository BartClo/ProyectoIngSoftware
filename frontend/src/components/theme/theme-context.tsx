// theme-context.tsx
import React, { createContext, useState, useEffect, useContext } from 'react';

type ThemeMode = 'light' | 'dark' | 'system';
type FontSize = 'small' | 'medium' | 'large';

interface ThemeContextType {
  theme: ThemeMode;
  fontSize: FontSize;
  setTheme: (theme: ThemeMode) => void;
  setFontSize: (fontSize: FontSize) => void;
}

const defaultThemeContext: ThemeContextType = {
  theme: 'light',
  fontSize: 'medium',
  setTheme: () => {},
  setFontSize: () => {},
};

// Crear el contexto
export const ThemeContext = createContext<ThemeContextType>(defaultThemeContext);

// Hook personalizado para usar el tema
export const useTheme = () => useContext(ThemeContext);

// Provider del tema
export const ThemeProvider: React.FC<{children: React.ReactNode}> = ({ children }) => {
  // Intentar cargar la configuración desde localStorage
  const [theme, setThemeState] = useState<ThemeMode>(() => {
    const savedTheme = localStorage.getItem('theme') as ThemeMode;
    return savedTheme || 'light';
  });
  
  const [fontSize, setFontSizeState] = useState<FontSize>(() => {
    const savedFontSize = localStorage.getItem('fontSize') as FontSize;
    return savedFontSize || 'medium';
  });

  // Función para cambiar el tema y guardarlo en localStorage
  const setTheme = (newTheme: ThemeMode) => {
    setThemeState(newTheme);
    localStorage.setItem('theme', newTheme);
  };

  // Función para cambiar el tamaño de fuente y guardarlo en localStorage
  const setFontSize = (newFontSize: FontSize) => {
    setFontSizeState(newFontSize);
    localStorage.setItem('fontSize', newFontSize);
  };

  // Aplicar el tema cuando cambia
  useEffect(() => {
    const applyTheme = () => {
      // Eliminar todas las clases de tema anteriores
      document.documentElement.classList.remove('theme-light', 'theme-dark');
      
      // Determinar qué tema aplicar
      let activeTheme = theme;
      
      if (theme === 'system') {
        // Detectar preferencia del sistema
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        activeTheme = prefersDark ? 'dark' : 'light';
      }
      
      // Aplicar el tema
      document.documentElement.classList.add(`theme-${activeTheme}`);
    };

    applyTheme();
    
    // Listener para cambios en preferencias del sistema
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = () => {
      if (theme === 'system') {
        applyTheme();
      }
    };
    
    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [theme]);

  // Aplicar el tamaño de fuente cuando cambia
  useEffect(() => {
    // Eliminar todas las clases de tamaño anteriores
    document.documentElement.classList.remove('font-small', 'font-medium', 'font-large');
    
    // Aplicar el nuevo tamaño
    document.documentElement.classList.add(`font-${fontSize}`);
  }, [fontSize]);

  return (
    <ThemeContext.Provider value={{ theme, fontSize, setTheme, setFontSize }}>
      {children}
    </ThemeContext.Provider>
  );
};