# Comparative Research: Autonomous AI Agents (May 2026)

Research conducted 27/05/2026 to inform NEO architecture design.

## Agents Studied

### 1. Ruflo (ruvnet/ruflo v3.10.2)
- **Stars:** 55,647 | **License:** MIT | **Language:** TypeScript
- **Architecture:** Queen Coordinator Pattern with 15-agent hierarchy
- **Self-learning:** SONA (7 RL algorithms: PPO, A2C, DQN, Q-Learning, SARSA, Decision Transformer, Curiosity)
- **Memory:** HNSW vector DB (150x-12,500x faster than brute force), ReasoningBank pattern matching
- **Consensus:** Raft + Byzantine Fault Tolerance + Gossip protocols
- **Federation:** Zero-trust, mTLS, ed25519, PII-gated data flow
- **Strengths:** Most advanced self-learning of any open agent; real consensus algorithms; federation support
- **Limitations:** Alpha-quality (many alpha-tagged packages); TypeScript-only; aggressive versioning; Claude ecosystem lock-in

### 2. OpenClaw (openclaw/openclaw v2026.5.26)
- **Stars:** 375,003 | **License:** MIT | **Language:** TypeScript (2.16M LoC)
- **Architecture:** Gateway daemon (WebSocket) with plugin system, 136 bundled extensions
- **Memory:** File-based Markdown + SQLite/LanceDB/QMD + Dreaming consolidation
- **Providers:** 50+ LLM providers + voice/media providers
- **Channels:** 20+ messaging platforms (WhatsApp, Telegram, Discord, Slack, Signal, iMessage)
- **Strengths:** Massive ecosystem; dreaming memory; native multi-channel; companion apps (macOS/iOS/Android)
- **Limitations:** Enormous complexity (2.16M LoC, 6,862 open issues); Node.js requirement; steep config surface

### 3. Claude Code (Anthropic v2.1.152)
- **Architecture:** Native binary, three-phase agentic loop (Gather → Act → Verify)
- **Tools:** 31 built-in tools including LSP code intelligence
- **Teams:** Agent teams with inter-agent messaging
- **Sandbox:** OS-level (macOS Seatbelt / Linux bubblewrap)
- **Strengths:** Mature tooling; Plan mode; auto-memory; IDE integration (VS Code/JetBrains)
- **Limitations:** Closed source; Claude-only models; expensive (Anthropic API); sessions local to machine

### 4. Hermes Agent (Nous Research, current)
- **Architecture:** Python agent with skills, memory, cron, delegation
- **Brain:** 7 cognitive regions (Amygdala, Hippocampus, N. Accumbens, etc.) as no_agent cron scripts
- **Neural:** Triple neural network (NN-Brain, NN-Agent, NN-Shared) with feed-forward + backprop
- **Cortex:** Dual-hemisphere (Hermes DeepSeek V4 + Codex GPT-5.5)
- **Strengths:** Python ecosystem; skill-based learning; persistent memory; multi-profile
- **Limitations:** Brain is passive (cron-dependent); no RL; basic multi-agent; limited self-learning

## Key Insights for NEO

1. **Self-learning is the differentiator.** Ruflo's SONA is the only real RL implementation. NEO's SONA-lite can be simpler (Q-learning + pattern extraction) while still providing genuine learning.

2. **Memory sophistication matters.** OpenClaw's dreaming and Claude Code's auto-memory show that background consolidation is essential. NEO needs ChromaDB + dreaming.

3. **Python beats TypeScript for AI agents.** Both Ruflo and OpenClaw are massive TypeScript codebases. Python's ML ecosystem (scikit-learn, stable-baselines3, ChromaDB) makes self-learning natural.

4. **Ollama local is the cost killer.** All three competitors cost money per inference. NEO's Ollama-first approach with API fallback eliminates the main cost barrier.

5. **Architecture should be layered, not monolithic.** OpenClaw's plugin system is powerful but complex. NEO's 6-layer design with clean interfaces is easier to maintain and extend.
