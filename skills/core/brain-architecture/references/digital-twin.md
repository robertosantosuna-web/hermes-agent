# Digital Twin — Arquitetura Completa

Documento completo: `~/.hermes/architecture/digital-twin.md` (15KB)

## Dispositivos Mapeados

| Dispositivo | Dados | API | Status |
|------------|-------|-----|--------|
| 📱 Smartphone | Digital Wellbeing, Location, Notificações | UsageStatsManager, Google Takeout | Futuro |
| ⌚ Smartwatch | HRV, Sono, Passos, Stress | Health Connect, Samsung Health SDK | Futuro |
| 🥽 VR | Eye tracking, Atenção, Postura | Meta SDK | Futuro |
| 💻 PC | Browser, Sistema, Logs | psutil, CDP | ✅ Atual |
| 📧 Email | Volume, Tom, Remetentes | himalaya, IMAP | ✅ Atual |

## Camadas de Coaching
- N1 — Consciência: Relatórios passivos ("Você fez X")
- N2 — Nudge: Sugestão no momento certo ("São 23:30, você está no Instagram há 40min")
- N3 — Intervenção: Bloqueio ativo + redirecionamento
