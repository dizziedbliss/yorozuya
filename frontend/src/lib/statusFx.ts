// Every status change gets its own reaction on the receipt line. All of it is skipped under reduced motion.
import { COPY } from "./copy";
import { burst, reducedMotion } from "./motion";
import type { Status } from "./types";

export type FxStatus = keyof typeof COPY.statusFx;
export const isFxStatus = (s: Status): s is FxStatus => s in COPY.statusFx;

/** Adds `el` to the body and removes it after `ms`. */
function flash(el: HTMLElement, ms: number): void {
  document.body.append(el);
  setTimeout(() => el.remove(), ms);
}

function restart(line: HTMLElement, cls: string): void {
  line.classList.remove(cls);
  void line.offsetWidth; // restart the animation if it's already on
  line.classList.add(cls);
  setTimeout(() => line.classList.remove(cls), 1400);
}

function floater(cls: string, text: string, x: number, y: number, frames: Keyframe[], duration: number): void {
  const el = document.createElement("span");
  el.className = cls;
  el.textContent = text;
  el.style.left = `${x}px`;
  el.style.top = `${y}px`;
  el.setAttribute("aria-hidden", "true");
  document.body.append(el);
  el.animate(frames, { duration, easing: "cubic-bezier(.5,0,.8,.4)" }).onfinish = () => el.remove();
}

function bigWord(status: FxStatus, word: string, ms: number): void {
  const el = document.createElement("div");
  el.className = `bigfx ${status}`;
  el.dataset.status = status;
  el.setAttribute("aria-hidden", "true");
  const b = document.createElement("b");
  b.textContent = word;
  el.append(b);
  flash(el, ms);
}

export function playStatusFx(status: FxStatus, line: HTMLElement): void {
  if (reducedMotion() || typeof line.animate !== "function") return;
  const r = line.getBoundingClientRect();

  if (status !== "interview" && status !== "offer") {
    const stamp = document.createElement("div");
    stamp.className = `fx-stamp ${status}`;
    stamp.textContent = COPY.statusFx[status].stamp;
    stamp.setAttribute("aria-hidden", "true");
    line.append(stamp);
    setTimeout(() => stamp.remove(), 2600);
  }

  switch (status) {
    case "applied":
      restart(line, "shake");
      burst(r.left + r.width / 2, r.top + r.height / 2);
      break;
    case "emailed":
      floater("plane", "✈", r.left + 20, r.top, [
        { transform: "translate(0,0) rotate(-20deg) scale(.6)", opacity: 1 },
        { transform: `translate(${innerWidth * 0.4}px, -${r.top + 80}px) rotate(-35deg) scale(1.4)`, opacity: 0 },
      ], 1100);
      break;
    case "heard_back": {
      restart(line, "glow");
      const bubble = document.createElement("div");
      bubble.className = "bubble";
      bubble.setAttribute("aria-hidden", "true");
      bubble.append(...Array.from({ length: 3 }, () => document.createElement("i")));
      bubble.style.left = `${Math.max(8, Math.min(innerWidth - 170, r.right - 140))}px`;
      bubble.style.top = `${Math.max(8, r.top - 42)}px`;
      flash(bubble, 2200);
      setTimeout(() => { bubble.textContent = "they replied!"; }, 900);
      break;
    }
    case "interview":
      bigWord("interview", "LOCK IN.", 1700);
      restart(document.body, "shakeall");
      break;
    case "offer":
      bigWord("offer", "OFFER.", 2700);
      for (let i = 0; i < 6; i++) setTimeout(() => burst(Math.random() * innerWidth, Math.random() * innerHeight * 0.7, 16), 300 + i * 180);
      break;
    case "rejected":
      restart(line, "tear");
      break;
    case "ghosted":
      restart(line, "ghostout");
      floater("ghosty", "👻", r.right - 70, r.top, [
        { transform: "translate(0,0)", opacity: 1 },
        { transform: "translate(30px,-120px)", opacity: 0 },
      ], 1600);
      break;
  }
}
