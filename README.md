# Yorozuya — a “I hate LinkedIn” job portal (v2)

Yorozuya is my personal job portal / playground project built because I *hate* LinkedIn and most job apps. Like, I hate using them, I hate them a lot.  

So I made my own thing: customizable, easy for **me** to fetch jobs and stay updated, without dealing with the usual job-app ass experience.

**Live:** https://yorozuya.dizziedbliss.lol  

> Heads-up: it's locked with a passphrase (it's a one-person club). First load can still take ~10s while Railway wakes up, but now there are loading lines to roast you while you wait.

---

## What it does (v2)

Two modes:

- **Fresher** (J✱B Search): hunts intern / fresher / new-grad roles in SRE, DevOps, platform, cloud,
  backend and fullstack, in Bengaluru, Chennai, India remote or remote anywhere.
    - Pulls from Greenhouse, Lever, Ashby, Workable, SmartRecruiters (~90 companies), plus JSearch
      (Google Jobs), Remotive, RemoteOK, Himalayas, Arbeitnow, and LinkedIn / Indeed / Naukri through
      JobSpy (no login, low volume, nobody gets banned).
    - Scores every job for *me* (role, level, location, and the tech in the JD vs my resume) and shows
      why it scored what it did.
    - Salary in ₹ LPA with a range slider (my zone: 4–10 LPA).
    - **Find HR**: emails in the posting → Hunter → a guessed hr@/careers@ that actually takes mail. If
      nothing turns up it says so.
    - **Email in Gmail** opens a pre-filled draft from my template. I hit send myself.
    - **Receipts** tracks everything I've applied to (applied → emailed → heard back → interview →
      offer, or rejected / ghosted), with a timeline per job and stats that roast me.
    - Refreshes every 6 hours on GitHub Actions and pings me on Telegram when something good shows up.
    - **Log (a real log)**: every refresh is a ring on a cut log. Click a ring to see what each board did.
- **Curated**: the original v1 thing. Live Greenhouse fetch from a few favourite companies (Discord,
  GitLab, Reddit and such), ranked for SRE-ish roles.

---

## How it runs

- **Frontend**: React 19 + Vite + TypeScript (strict), plain CSS. On **Vercel**.
- **API**: FastAPI + SQLAlchemy on **Railway** (Docker).
- **Database**: **Supabase** Postgres, migrations with Alembic.
- **Refresh worker**: a GitHub Actions cron every 6h (or "Run workflow" by hand).
- Details for working on it: [`CLAUDE.md`](./CLAUDE.md), [`backend/CLAUDE.md`](./backend/CLAUDE.md),
  [`frontend/CLAUDE.md`](./frontend/CLAUDE.md).

---

## Why it exists

- I wanted a job portal that matches *my* brain and lets me customize the experience.
- I’m using this app as a playground to experiment while I learn more:
    - DevOps
    - frontend
    - backend
    - basically everything

---

## DevOps / deployment stuff I’ve learned while building this

- **GitHub Actions**
- Deploying on:
    - **Railway** through **Docker**
    - **Vercel** too

---

## Roadmap (aka “I’ll make this less boring later”)

- [x]  Add a loading animation so it doesn’t look dead while Railway wakes up
- [x]  Update the UI (because current UI is boring as hell): it's a B/W poster now
- [ ]  Keep expanding companies + filters as I learn more and mess around
- [ ]  Edit the company list from Settings (needs a companies API)

---

## Known issues

- Railway's free tier sleeps, so the first request after a while is slow.
- Free quotas: JSearch is 200 requests/month (one query per refresh), Hunter is 50 searches/month (only
  on a Find HR click, cached per company).
- JobSpy scrapes LinkedIn / Indeed / Naukri without logging in; when a board blocks it, that run logs it
  as blocked and carries on.
- Curated still fetches its 17 boards live on every load (cached 10 minutes in the browser).
- The passphrase is a door, not security: one shared secret, no accounts. Fine for a site only I use.

---

## Notes / quirks

- This is personal. I’m not trying to be formal or impress anyone here.
- If it’s scuffed: yup, that’s the point. It’s a learning playground. idc.

---

## License

No “license” BS.

I don’t care if you steal my code or copy it or remix it or whatever — if it helps you, go for it.  

At most: don’t be an AH and pretend you wrote the whole thing from scratch, but honestly even that isn’t worth my energy.

---

## A tiny Gintama nod

It’s called **Yorozuya** because of course it is. Gintama brainrot stays on.

![some yorozuya gif](./frontend/src/assets/readme.gif)
