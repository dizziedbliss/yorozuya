"""One Telegram message per refresh run: the best new jobs, or nothing at all."""

import html
from typing import Any

import httpx


def build_message(new_jobs: list[dict[str, Any]], notify: dict[str, Any], *, site_url: str) -> str | None:
    bar = int(notify.get("telegram_min_score", 120))
    top_n = int(notify.get("top_n", 5))
    worth_it = sorted((j for j in new_jobs if j["score"] >= bar), key=lambda j: j["score"], reverse=True)
    if not worth_it:
        return None

    noun = "match" if len(worth_it) == 1 else "matches"
    lines = [f"✱ <b>{len(worth_it)} new {noun}</b> just dropped\n"]
    for job in worth_it[:top_n]:
        title = html.escape(job["title"])
        company = html.escape(job["company"])
        url = html.escape(job["apply_url"], quote=True)
        lines.append(f'<b>{job["score"]}</b> · <a href="{url}">{title}</a> @ {company}')
    if len(worth_it) > top_n:
        lines.append(f"\nand {len(worth_it) - top_n} more → {html.escape(site_url)}")
    else:
        lines.append(f"\n→ {html.escape(site_url)}")
    return "\n".join(lines)


def send_new_jobs(
    client: httpx.Client,
    token: str,
    chat_id: str,
    new_jobs: list[dict[str, Any]],
    notify: dict[str, Any],
    *,
    site_url: str,
) -> str:
    """Returns "sent" or "nothing new"; raises RuntimeError when Telegram says no."""
    text = build_message(new_jobs, notify, site_url=site_url)
    if text is None:
        return "nothing new"
    response = client.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "link_preview_options": {"is_disabled": True},
        },
    )
    body = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
    if response.status_code != 200 or not body.get("ok"):
        raise RuntimeError(
            f"Telegram said no (HTTP {response.status_code}): {body.get('description', 'no reason')}"
        )
    return "sent"
