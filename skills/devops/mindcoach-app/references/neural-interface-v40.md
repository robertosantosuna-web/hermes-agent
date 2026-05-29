# Neural Link Interface v40 Design Notes (26/05/2026)

## Architecture Decision: WebView over Native Compose

After 3 failed iterations of Kotlin Compose UI (rejected by user: "está uma merda", "não parece uma rede neural", "visualize antes de enviar"), migrated to WebView architecture:

- `MindCoachScreen.kt` = 5-line WebView wrapper
- All UI lives in `index.html` on Cloud Run
- Can be tested visually in browser before deployment
- APK loads the same URL → no recompile needed for UI changes

## Visual Elements (index.html)

### Canvas Layers
1. **Particle Background** (`#neural-bg`): 50 particles with connections, animated via requestAnimationFrame
2. **Brain Core** (`#brain-canvas`): Concentric rings, radial lines, orbiting dots, pulsating core

### Synapse Stream
- Color-coded cards: TRADE=gold, SIGNAL=green, WARN=red, THOUGHT=purple, COMMAND=cyan
- Flash animation on insert
- Dedup via `loadedKeys` Set
- Auto-poll every 8-30 seconds

### Command System
- Modal overlay with animated rings canvas
- Approve (gradient purple) / Reject (red outline) buttons
- Polls `/auth` every 8s
- Responds via `POST /auth {type:"command_response", id, action}`

### Chat
- Persistent input bar at bottom
- REST-only (POST /chat → poll GET /chat?since=N)
- Messages shown as "Roberto / Córtex" styled bubbles

## Color Palette
- Background: #020212
- Cards: rgba(8,8,40,.7)
- Accent: #7c3aed (purple)
- Cyan glow: #06b6d4
- Gold: #f59e0b
- Pink: #ec4899
- Text: #e0d8ff

## REST Endpoints Used
- `/auth` (GET/POST) — commands
- `/chat` (GET/POST) — messages
- `/outbox` (GET) — command responses
- `/data.json` (GET) — neural data
