# Agenda Multi-Fonte — MindCoach

## Fluxo de varredura (validado 26/05/2026)

1. **Gmail pessoal** (robertosantos.una@gmail.com) → IMAP direto
2. **Outlook trabalho** (robrsantos@voegol.com.br) → Brave CDP :9222
3. **Outlook pessoal** (robertosantos141@outlook.com) → Brave CDP :9222 + Desktop Daemon
4. **WhatsApp** → Edge CDP :9224

## Estrutura do arquivo agenda_scan.json

```json
{
  "last_scan": "ISO timestamp",
  "sources": ["gmail_pessoal", "outlook_trabalho", "whatsapp"],
  "commitments": [
    {
      "date": "YYYY-MM-DD",
      "time": "HH:MM ou null",
      "type": "consulta|terapia|treinamento|evento|prazo|webinar|voo",
      "title": "descrição curta",
      "description": "detalhes",
      "source": "gmail|whatsapp|outlook_trabalho|outlook_pessoal",
      "priority": "critical|high|medium|low",
      "recurring": "weekly_monday|null"
    }
  ],
  "pending_actions": [
    {"action": "descrição", "source": "...", "priority": "..."}
  ],
  "recurring": [
    {"type": "terapia|igreja", "title": "...", "schedule": "segundas 12:00|domingos"}
  ]
}
```

## Palavras-chave de busca

Português: reunião, consulta, médico, terapia, voo, escala, compromisso, agendamento, prazo, entrevista, igreja, evento, calendário, confirmado, agendado, cirurgia, atestado, homologação

Inglês: meeting, appointment, schedule, deadline, interview, training, flight, confirmed

## Notificar o app

```bash
python3 ~/.hermes/scripts/notify_app.py "📅 Agenda Atualizada" "N compromissos encontrados" info
```

## Deploy dos dados

Para rebuildar o data.json e fazer deploy no Cloud Run:
```bash
cd ~/.hermes/mindcoach-pro
bash build_data.sh
gcloud run deploy mindcoach --source=. --region=us-central1 --allow-unauthenticated --memory=512Mi --project=gen-lang-client-0455851315
```

## Pitfalls

- **Outlook web NÃO responde a CDP Input.dispatchKeyEvent** — usar Desktop Daemon + ydotool para busca/clique
- **Outlook corporativo e pessoal podem compartilhar tenant** — verificar qual conta está ativa
- **WhatsApp Web exibe apenas conversas recentes no DOM** — virtual scrolling, scrollar para carregar mais
- **Gmail IMAP search SINCE** funciona bem para intervalo de datas, mas limite a 200 emails por scan
