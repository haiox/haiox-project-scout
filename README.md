# Haiox Project Scout 🔭

> **A real-time contract radar and prototype generator that lives inside Telegram.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Telegram Bot](https://img.shields.io/badge/Telegram-Interactive%20UI-26A5E4.svg?style=flat&logo=telegram&logoColor=white)](https://telegram.org)
[![Pytest](https://img.shields.io/badge/pytest-38%20passed-brightgreen.svg?style=flat&logo=pytest&logoColor=white)]()
[![Architecture](https://img.shields.io/badge/Design-Microkernel%20%7C%20In--Memory%20Cache-8A2BE2.svg?style=flat)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat)](LICENSE)

---

## 💡 Why I Built This

Most freelance bots just dump raw, unvetted links into a chat channel until your phone explodes with notifications. You spend hours sifting through $5 junk projects and copy-pasting generic bids that clients ignore.

**Haiox Project Scout takes a completely different approach:**
1. **Filters ruthlessly:** Scrapes Freelancer.com, Upwork, and RemoteOK, strips out scams and low-ball commodity bids, and verifies the client's actual technical needs.
2. **Generates working code before you bid:** Using an AST-backed Python generator (`Haiox Genesis`), it spins up a tested, working proof-of-concept in seconds.
3. **Stays out of your way:** Instead of spamming endless new messages, it uses a single **Interactive Carousel Deal Deck** in Telegram that you can flip through like cards (`Previous` / `Next` / `Dismiss`).

---

## 🏛 Architecture & Execution Flow

```
+-----------------------------------------------------------------------------------+
|                        HAIOX PROJECT SCOUT ARCHITECTURE v1.2.0                    |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  [ Ingestion Hub ] ---> [ Quality Gatekeeper ] ---> [ Target Ground Truth Probe ] |
|  - Freelancer.com       - Anti-Phishing             - Tech Stack Fingerprinting   |
|  - Upwork RSS           - USD Normalization         - WAF / Public API Detection  |
|  - RemoteOK API         - Country Blacklist         - Latency Benchmarks          |
|  - Custom Extensible    - Technical Keywords                                      |
|                                |                                                  |
|                                v                                                  |
|                   [ Genesis Prototype Synthesis ]                                 |
|                   - AST-Verified Code Generation (ast.parse)                      |
|                   - 3-Sentence Pain-Killer Proposal                               |
|                   - Responsive Dark Glassmorphic HTML Reports                     |
|                                |                                                  |
|                                v                                                  |
|                   [ Fast In-Memory Cache (Sub-2ms) ]                              |
|                   - Ring-Buffer Storage (Capacity: 500)                           |
|                   - Pre-Warmed Multi-Discipline Seeds (0ms boot)                  |
|                   - 4-Tier Smart Fallback Guarantee                               |
|                                |                                                  |
|                                v                                                  |
|           +----------------------------------------------------+                  |
|           |       Interactive Paged Deal Deck (Telegram UI)    |                  |
|           |                                                    |                  |
|           |  🎴 Deal 1 of 5 | FREELANCER                      |                  |
|           |  📌 High-Speed E-Commerce Product Scraper          |                  |
|           |  💰 Budget: $450 USD | ⭐️ Score: 95/100            |                  |
|           |                                                    |                  |
|           |  [ ◀️ Previous ]      [ Card 1 / 5 ]      [ Next ▶️ ]|                  |
|           |  [ ⚡ Approve & Copy ]      [ 💻 View Genesis Code ]|                  |
|           |  [ 🎯 Ground Truth ]        [ 🌐 Open Project ]    |                  |
|           |  [ ❌ Dismiss ]             [ 🔄 Refresh Deals ]   |                  |
|           +----------------------------------------------------+                  |
|                                                                                   |
+-----------------------------------------------------------------------------------+
```

---

## 🌟 Key Features

1. **Interactive Paged Deal Deck (Zero Chat Clutter):**
   - Single-message mutating carousel powered by Telegram inline buttons (`editMessageText`).
   - Effortless navigation with `[ ◀️ Previous ] [ Card 1 / N ] [ Next ▶️ ]`.
   - Atomic dismiss actions that slide the next opportunity forward in real time.

2. **Sub-Millisecond In-Memory Cache with Smart Fallback Guarantee:**
   - Ultra-fast retrieval (< 2ms) from `GLOBAL_OPPORTUNITY_CACHE`.
   - **4-Tier Fallback Hierarchy:** Strict Match -> Platform Relaxation -> Budget Floor Relaxation -> Top Trending Contracts. Guarantees users never see an empty screen.

3. **Pre-Warmed Zero-Cold-Start Ingestion:**
   - Multi-discipline seeds across Python, AI/LLMs, React/Next.js, Mobile Flutter, and SQL Data Analytics loaded on boot.
   - Background daemon continuously captures all verified opportunities down to $15 without keyword bias.

4. **100% International English Multi-Tenant SaaS Interface:**
   - Interactive 4-step onboarding wizard (`/start`): Skills -> Platforms -> Budget Floor -> Alert Mode.
   - Per-user isolated profile state (`user_profiles.json`).

5. **Genesis Solution Blueprints via HTML Document Delivery:**
   - Bypasses Telegram's 4096-character limit by compiling responsive, dark glassmorphic HTML documents sent via `sendDocument`.
   - Includes 3-phase milestone roadmaps and 1-click clipboard code copy.

---

## 🧪 Test Verification

Comprehensive test suite verifying microkernel drivers, AST generation, quality gatekeepers, and carousel navigation:
```bash
pytest tests/ -v
```
**Result:** 38 / 38 unit and integration tests passing in 0.97s.

---

## 🚀 Quickstart

1. **Clone & Configure:**
   ```bash
   cp .env.example .env
   # Set TELEGRAM_BOT_TOKEN and ADMIN_CHAT_ID
   ```
2. **Run Dual-Engine Runner:**
   ```bash
   python -u run_bot.py
   ```
3. **Launch in Telegram:**
   - Search for your configured bot handle (e.g., `@HaioxScoutBot`).
   - Send `/start` to run the 4-step wizard or `/search` to browse matching deals immediately.

---

## 🛡 License & Author
Engineered by **haiox** ([@haioxlab](https://x.com/haioxlab)). Part of the **Haiox Ecosystem**.
