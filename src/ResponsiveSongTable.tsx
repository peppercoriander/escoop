import { useLayoutEffect, useRef, useState, type ReactNode } from 'react';
import styles from './App.module.css';

export default function ResponsiveSongTable({ children, hidden }: { children: ReactNode; hidden: boolean }) {
  const viewportRef = useRef<HTMLDivElement>(null);
  const tableRef = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(1);

  useLayoutEffect(() => {
    const viewport = viewportRef.current!;
    const table = tableRef.current!;
    const fit = (width: number) => {
      if (width > 0) {
        const minimumWidth = parseFloat(getComputedStyle(table).minWidth);
        setScale(Math.min(1, width / minimumWidth));
      }
    };
    fit(viewport.getBoundingClientRect().width);
    const observer = new ResizeObserver(([entry]) => fit(entry.contentRect.width));
    observer.observe(viewport);
    return () => observer.disconnect();
  }, []);

  return <div ref={viewportRef} className={styles['table-viewport']} hidden={hidden}>
    <div ref={tableRef} className={styles['table-container']} style={{ zoom: scale }} role="region" aria-label="歌曲站位结果表格">
      {children}
    </div>
  </div>;
}
