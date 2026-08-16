import { useCallback, useEffect, useState } from 'react';
import { flushSync } from 'react-dom';

type Theme = 'light' | 'dark';

type ToggleOrigin = {
  x: number;
  y: number;
};

type ViewTransitionDocument = Document & {
  startViewTransition?: (update: () => void) => {
    finished: Promise<unknown>;
  };
};

const THEME_STORAGE_KEY = 'amplinews-theme';

function getSavedTheme(): Theme {
  try {
    return window.localStorage.getItem(THEME_STORAGE_KEY) === 'dark' ? 'dark' : 'light';
  } catch {
    return 'light';
  }
}

export function useTheme() {
  const [theme, setTheme] = useState<Theme>(getSavedTheme);

  useEffect(() => {
    try {
      window.localStorage.setItem(THEME_STORAGE_KEY, theme);
    } catch {
      // The selected theme still works if browser storage is unavailable.
    }
  }, [theme]);

  const toggleTheme = useCallback((origin: ToggleOrigin) => {
    const nextTheme = theme === 'light' ? 'dark' : 'light';
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const transitionDocument = document as ViewTransitionDocument;

    if (prefersReducedMotion || !transitionDocument.startViewTransition) {
      setTheme(nextTheme);
      return;
    }

    const root = document.documentElement;
    root.dataset.themeTransition = 'reveal';
    root.style.setProperty('--theme-reveal-x', `${origin.x}px`);
    root.style.setProperty('--theme-reveal-y', `${origin.y}px`);

    try {
      const transition = transitionDocument.startViewTransition(() => {
        flushSync(() => setTheme(nextTheme));
      });

      void transition.finished
        .catch(() => undefined)
        .finally(() => {
          delete root.dataset.themeTransition;
          root.style.removeProperty('--theme-reveal-x');
          root.style.removeProperty('--theme-reveal-y');
        });
    } catch {
      delete root.dataset.themeTransition;
      root.style.removeProperty('--theme-reveal-x');
      root.style.removeProperty('--theme-reveal-y');
      setTheme(nextTheme);
    }
  }, [theme]);

  return { theme, toggleTheme };
}
