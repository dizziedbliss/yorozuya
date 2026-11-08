import { type ReactNode, useCallback, useRef, useState } from "react";
import { type ShowToast, ToastContext } from "./toast-context";

/** One toast at a time, bottom-left, announced to screen readers. */
export function ToastProvider({ children }: { children: ReactNode }) {
  const [content, setContent] = useState<ReactNode>(null);
  const [visible, setVisible] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout>>(undefined);
  const show = useCallback<ShowToast>((next) => {
    setContent(next);
    setVisible(true);
    clearTimeout(timer.current);
    timer.current = setTimeout(() => setVisible(false), 3400);
  }, []);
  return (
    <ToastContext value={show}>
      {children}
      <div className={`toast${visible ? " show" : ""}`} role="status" aria-live="polite" aria-label="Notifications">{content}</div>
    </ToastContext>
  );
}
