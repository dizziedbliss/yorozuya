import { type RefObject, useEffect } from "react";

export const reducedMotion = (): boolean =>
  typeof matchMedia === "function" && matchMedia("(prefers-reduced-motion: reduce)").matches;

/** A burst of ✱ from a point, for "you did a thing" moments. */
export function burst(x: number, y: number, count = 12): void {
  if (reducedMotion() || typeof document.body.animate !== "function") return;
  for (let i = 0; i < count; i++) {
    const s = document.createElement("span");
    s.className = "spark";
    s.textContent = "✱";
    s.style.left = `${x}px`;
    s.style.top = `${y}px`;
    document.body.append(s);
    const a = Math.random() * Math.PI * 2;
    const d = 60 + Math.random() * 90;
    s.animate(
      [
        { transform: "translate(-50%,-50%) scale(.4)", opacity: 1 },
        { transform: `translate(calc(-50% + ${Math.cos(a) * d}px), calc(-50% + ${Math.sin(a) * d}px)) rotate(${Math.random() * 360}deg)`, opacity: 0 },
      ],
      { duration: 700 + Math.random() * 300, easing: "cubic-bezier(.2,.8,.2,1)" },
    ).onfinish = () => s.remove();
  }
}

/** Moves every [data-depth] element inside `root` with scroll and pointer, each at its own depth. */
export function useParallax(root: RefObject<HTMLElement | null>, deps: readonly unknown[] = []): void {
  useEffect(() => {
    const el = root.current;
    if (!el || reducedMotion()) return;
    const layers = [...el.querySelectorAll<HTMLElement>("[data-depth]")];
    let mx = 0;
    let my = 0;
    let frame = 0;
    const paint = () => {
      frame = 0;
      for (const layer of layers) {
        const d = Number(layer.dataset.depth);
        layer.style.transform = `translate3d(${mx * d * 40}px, ${scrollY * d + my * d * 30}px, 0)`;
      }
    };
    const ask = () => { if (!frame) frame = requestAnimationFrame(paint); };
    const move = (e: PointerEvent) => { mx = e.clientX / innerWidth - 0.5; my = e.clientY / innerHeight - 0.5; ask(); };
    addEventListener("scroll", ask, { passive: true });
    addEventListener("pointermove", move, { passive: true });
    paint();
    return () => {
      removeEventListener("scroll", ask);
      removeEventListener("pointermove", move);
      cancelAnimationFrame(frame);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- re-scan layers when the caller's content changes
  }, deps);
}
