"""Terminal heartbeat without displaying agent output or claiming model progress."""
import sys


LABELS = {"business-analyst": "BA — analiza biznesowa", "system-analyst": "SA — analiza systemowa",
          "architect": "Architektura", "architect-reviewer": "Recenzja architektury"}


class ConsoleProgress:
    def __init__(self, stream=None):
        self.stream = stream if stream is not None else sys.stderr

    def __call__(self, agent, elapsed, timeout, status="running"):
        label = LABELS.get(agent, agent)
        seconds = int(elapsed)
        duration = f"{seconds // 60:02d}:{seconds % 60:02d}"
        messages = {"running": "Codex uruchomiony; oczekiwanie na wynik",
                    "finished": "Odebrano wynik Codex; sprawdzanie odpowiedzi",
                    "failed": "Wywołanie Codex zakończone błędem",
                    "timeout": "Przekroczono limit czasu; zakończono proces",
                    "interrupted": "Przerwano; zakończono proces Codex"}
        line = f"[factory] {label} | czas {duration} | limit {timeout:g}s | {messages[status]}"
        interactive = self.stream.isatty()
        prefix = "\r\033[K" if interactive else ""
        suffix = "" if interactive and status == "running" else "\n"
        self.stream.write(prefix + line + suffix)
        self.stream.flush()
