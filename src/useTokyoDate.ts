import { useEffect, useState } from 'react';
import { tokyoDate, millisecondsUntilTokyoMidnight } from './lib/song-data.mjs';

/** Refresh at midnight and when returning to a tab that may have been asleep. */
export default function useTokyoDate() {
  const [today, setToday] = useState(() => tokyoDate());
  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>;
    const refresh = () => {
      clearTimeout(timer);
      setToday(tokyoDate());
      timer = setTimeout(refresh, millisecondsUntilTokyoMidnight() + 50);
    };
    refresh();
    window.addEventListener('focus', refresh);
    document.addEventListener('visibilitychange', refresh);
    return () => {
      clearTimeout(timer);
      window.removeEventListener('focus', refresh);
      document.removeEventListener('visibilitychange', refresh);
    };
  }, []);
  return today;
}
