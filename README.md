# Haiox Project Scout (دیده‌بان هوشمند پروژه‌ها) v1.2.0

> **Autonomous Real-Time Contract Reconnaissance, AST Prototype Synthesis & Interactive Deal Deck for Telegram**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Architecture](https://img.shields.io/badge/architecture-Microkernel%20%2F%20Dual--Engine-green.svg)]()
[![Tests Passing](https://img.shields.io/badge/tests-38%20passed-brightgreen.svg)]()
[![UI Status](https://img.shields.io/badge/Telegram%20UI-100%25%20English%20SaaS-purple.svg)]()

---

## ⚡ Overview

**Haiox Project Scout** is an autonomous reconnaissance platform engineered to bridge the gap between high-value freelance opportunities and verified software prototypes. It continuously ingests contract postings across **Freelancer.com, Upwork, RemoteOK, and custom developer feeds**, validates quality and client reputation, probes target URLs for technical ground truth, generates AST-verified executable Python prototypes, and surfaces opportunities via a high-velocity **Interactive Paged Deal Deck** inside Telegram.

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
**Result:** 38 / 38 unit and integration tests passing in 1.25s.

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
Engineered by **AIrash (آیرش)** for **Hatef Ghanei (@haioxlab)**. Part of the **Haiox Autonomous Ecosystem**.
