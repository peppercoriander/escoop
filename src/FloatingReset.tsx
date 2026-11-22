import { useEffect, useRef, useState } from 'react';
import type { PointerEvent } from 'react';
import styles from './App.module.css';

type Point = { x: number; y: number };
type Drag = { id: number; start: Point; origin: Point; moved: boolean };

export default function FloatingReset({ onReset }: { onReset: () => void }) {
  const button = useRef<HTMLButtonElement>(null);
  const drag = useRef<Drag | null>(null);
  const suppressClick = useRef(false);
  // A fresh page always starts in the upper-right corner. Do not persist drag coordinates.
  const [position, setPosition] = useState<Point | null>(null);
  const [dragging, setDragging] = useState(false);

  function clamp(point: Point): Point {
    const rect = button.current!.getBoundingClientRect();
    return {
      x: Math.max(8, Math.min(point.x, document.documentElement.clientWidth - rect.width - 8)),
      y: Math.max(8, Math.min(point.y, window.innerHeight - rect.height - 8)),
    };
  }
  useEffect(() => {
    const resize = () => setPosition(previous => previous ? clamp(previous) : null);
    window.addEventListener('resize', resize);
    return () => window.removeEventListener('resize', resize);
  }, []);

  function start(event: PointerEvent<HTMLButtonElement>) {
    if (event.button !== 0 || !event.isPrimary) return;
    const rect = event.currentTarget.getBoundingClientRect();
    suppressClick.current = false;
    drag.current = { id: event.pointerId, start: { x: event.clientX, y: event.clientY }, origin: { x: rect.left, y: rect.top }, moved: false };
    event.currentTarget.setPointerCapture(event.pointerId);
  }
  function move(event: PointerEvent<HTMLButtonElement>) {
    const current = drag.current;
    if (!current || current.id !== event.pointerId) return;
    const dx = event.clientX - current.start.x, dy = event.clientY - current.start.y;
    if (!current.moved && Math.hypot(dx, dy) < 6) return;
    current.moved = true;
    setDragging(true);
    setPosition(clamp({ x: current.origin.x + dx, y: current.origin.y + dy }));
  }
  function finish(event: PointerEvent<HTMLButtonElement>, cancelled = false) {
    if (!drag.current || drag.current.id !== event.pointerId) return;
    suppressClick.current = cancelled || drag.current.moved;
    drag.current = null;
    setDragging(false);
    if (event.currentTarget.hasPointerCapture(event.pointerId)) event.currentTarget.releasePointerCapture(event.pointerId);
  }
  return <button ref={button} id="reset" type="button"
    className={`${styles['reset']} ${styles['floating-reset']}`}
    style={position ? { left: position.x, top: position.y, right: 'auto', bottom: 'auto' } : undefined}
    data-dragging={dragging}
    aria-label="RESET：清除全部筛选并回到顶部"
    title="点击重置并回到顶部；按住拖动可调整位置"
    onPointerDown={start} onPointerMove={move} onPointerUp={event => finish(event)}
    onPointerCancel={event => finish(event, true)} onLostPointerCapture={event => finish(event, true)}
    onClick={event => {
      if (suppressClick.current && event.detail !== 0) { suppressClick.current = false; return; }
      suppressClick.current = false;
      onReset();
    }}>
    <span aria-hidden="true">↺</span> RESET <span aria-hidden="true">↑</span>
  </button>;
}
