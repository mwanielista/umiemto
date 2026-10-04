# Jak używać orkiestratora eSzkola

Orkiestrator uruchamiasz poleceniem `factory` w terminalu. Prowadzi analizę biznesową (BA), analizę systemową (SA), aktualizację architektury, niezależną recenzję i walidację. BA i SA wymagają Twojego jawnego zatwierdzenia. Przebieg kończy się na architekturze; nie implementuje aplikacji.

## 1. Przygotowanie

Potrzebujesz Python 3.11 lub nowszego oraz zainstalowanego i uwierzytelnionego Codex CLI. Wywołania agentów wymagają dostępu do usługi Codex. Poniższe przykłady używają Python 3.12.

Przejdź do repozytorium i sprawdź gałąź oraz bieżące zmiany:

```bash
cd /Users/mwanielista/git/eszkola
git status --short
git branch --show-current
```

Pracuj na gałęzi zadania, np. istniejącej `feature/analysis-orchestrator`. Jeśli zaczynasz niezależne zadanie, utwórz dla niego własną gałąź zgodnie z [workflow.md](workflow.md#branches-and-worktrees). Etapy zapisujące dokumenty i zatwierdzenia odrzucają `main`, `master` oraz detached HEAD. Nie zmieniaj gałęzi w katalogu używanym przez innego agenta.

Zainstaluj narzędzie jednorazowo w środowisku wirtualnym:

```bash
python3.12 -m venv .venv
.venv/bin/pip install -e .
source .venv/bin/activate
factory --help
```

W każdym nowym terminalu aktywuj środowisko ponownie:

```bash
cd /Users/mwanielista/git/eszkola
source .venv/bin/activate
```

Możesz też wywoływać `.venv/bin/factory` bez aktywowania środowiska. Z innego katalogu podaj repozytorium przed nazwą komendy:

```bash
/Users/mwanielista/git/eszkola/.venv/bin/factory \
  --root /Users/mwanielista/git/eszkola status
```

## 2. Przygotuj źródła biznesowe

Zaktualizuj dokumenty zawierające nowe wymagania lub decyzje biznesowe. Lista źródeł znajduje się w `business_sources` w [config/pipeline.yaml](config/pipeline.yaml). Obecnie obejmuje:

- `docs/biznesplan-platforma-kursy-dla-dzieci.md`,
- `docs/szablon-programu-edukacyjnego-modul-4-zajecia.md`,
- `AGENTS.md`.

Jeżeli nowe źródło jest osobnym dokumentem, dodaj jego ścieżkę do tej listy **przed rozpoczęciem przebiegu**. Samo utworzenie pliku nie dodaje go do skonfigurowanej listy źródeł.

Uzgodnij, kto odpowiada za zatwierdzenie BA i SA. W czasie pracy agenta nie edytuj równolegle plików repozytorium ani nie uruchamiaj drugiego autora tych samych artefaktów. Orkiestrator wykrywa nieoczekiwane zmiany i zatrzymuje zapis propozycji.

## 3. Uruchom analizę biznesową

```bash
factory analyze
factory status
```

`analyze` tworzy nowy przebieg i uruchamia Business Analyst. Agent przygotowuje propozycję, którą kod orkiestratora sprawdza przed zapisaniem do:

```text
docs/requirements/business-analysis.yaml
```

Poprawna analiza gotowa do przeglądu zatrzymuje pipeline na:

```text
PIPELINE: WAITING_FOR_BA_APPROVAL
```

Otwórz dokument BA i sprawdź zakres, wymagania BR, źródła, kryteria akceptacji, założenia oraz pytania. `READY_FOR_REVIEW` oznacza gotowość do oceny, a nie zatwierdzenie. Otwarte pytania `BLOCKER` zatrzymują dalszy przebieg.

## 4. Zatwierdź BA i uruchom SA

Po przeglądzie zatwierdź BA jako wyznaczony właściciel:

```bash
factory approve ba --owner "Imię i nazwisko właściciela biznesowego"
```

Komenda pokazuje rewizję, SHA-256, liczbę wymagań i pytań oraz pełną treść kandydata z metadanymi zatwierdzenia. Przeczytaj wyświetloną treść. Aby zatwierdzić dokładnie te bajty, wpisz `y` i Enter. Enter bez `y` anuluje operację.

Zatwierdzanie działa tylko w interaktywnym terminalu. Nazwa podana w `--owner` jest deklaracją operatora, nie weryfikacją jego tożsamości. Bez `--owner` zapisywana jest etykieta `BUSINESS_OWNER`.

Następnie uruchom kolejny etap:

```bash
factory resume
factory status
```

System Analyst otrzyma dokładną tożsamość zatwierdzonego BA i przygotuje:

```text
docs/requirements/system-analysis.yaml
```

Pipeline zatrzyma się na `WAITING_FOR_SA_APPROVAL`. SA zapisuje wykorzystany BA w `business_input`: identyfikator artefaktu, rewizję i digest.

## 5. Zatwierdź SA i uruchom architekturę

Sprawdź wymagania FR/NFR, ich powiązania z BR, kryteria akceptacji, pokrycie wymagań biznesowych i pytania. Następnie:

```bash
factory approve sa --owner "Imię i nazwisko właściciela wymagań"
factory resume
factory status
```

Tak jak przy BA, potwierdź wyświetloną treść wpisując `y`. Domyślna etykieta właściciela SA to `REQUIREMENTS_OWNER`.

Po zatwierdzeniu SA orkiestrator automatycznie:

1. sprawdza obie zgody i zgodność SA z BA,
2. zapisuje baseline architektury i stan Git,
3. uruchamia Architect,
4. oblicza zmiany względem baseline, uwzględniając wcześniejsze niezacommitowane pliki,
5. uruchamia niezależnego Architect Reviewer,
6. przekazuje odrzucone uwagi Architectowi do poprawy — maksymalnie trzy recenzje,
7. po pozytywnej recenzji uruchamia obowiązkowe walidatory architektury.

Sukces oznacza:

```text
PIPELINE: DONE
```

`DONE` dotyczy zatwierdzonych analiz i sprawdzonej architektury. Nie oznacza wdrożenia, implementacji aplikacji ani scalenia gałęzi do `main`.

## 6. Podgląd stanu i dowodów

```bash
factory status
factory history
```

`status` pokazuje rzeczywiste rewizje, digests, stan zgód, pochodzenie SA, recenzje i wyniki walidatorów. `history` wyświetla zdarzenia zachowanych przebiegów.

Pliki diagnostyczne znajdują się w ignorowanym przez Git katalogu:

```text
.orchestrator/
├── state.json
├── approvals/
└── runs/<run-id>/
    ├── run.json
    ├── events.jsonl
    ├── architecture-baseline.json
    ├── architecture-diff.json
    ├── architecture-review.yaml
    ├── architecture-review-1.yaml
    ├── reviewed-architecture.json
    └── validation-results.json
```

Pliki architektury i walidacji pojawiają się dopiero po osiągnięciu odpowiednich etapów. Kolejne recenzje mają własne numerowane pliki. W `validation-results.json` znajdziesz komendę, kod wyjścia i output każdego wykonanego walidatora.

## 7. Wznowienie i rozwiązywanie problemów

| Stan lub komunikat | Co zrobić |
| --- | --- |
| `WAITING_FOR_BA_APPROVAL` | Przejrzyj BA, wykonaj `factory approve ba`, potem `factory resume`. |
| `WAITING_FOR_SA_APPROVAL` | Przejrzyj SA, wykonaj `factory approve sa`, potem `factory resume`. |
| Brak lub nieważna zgoda | Sprawdź rewizję i digest. Samo ustawienie `APPROVED` w YAML nie wystarcza. Zmiana zatwierdzonej treści wymaga nowej rewizji i zgody. |
| `BLOCKED` | Rozstrzygnij pytania z odpowiedzialnymi właścicielami i zapisz rzeczywiste decyzje w źródłach. Następnie zresetuj stan i rozpocznij nową analizę. |
| `FAILED` | Przeczytaj `Reason`, historię i wyniki walidacji. Usuń przyczynę, potem zresetuj stan i uruchom analizę ponownie. |
| `HUMAN_REQUIRED` po trzech recenzjach | Sprawdź dokładne uwagi recenzenta i uzgodnij rozwiązanie. Automatyczne poprawki już się nie powtórzą. Po rozwiązaniu problemu rozpocznij nowy przebieg. |
| Przerwany proces z zapisanym `RUNNING` | `resume` przejdzie do `HUMAN_REQUIRED`. Sprawdź pliki i historię przed resetem; etap nie zostanie automatycznie powtórzony. |
| `STALE` lub zmienione źródła/config | Zapisz zamierzone zmiany, następnie rozpocznij nowy przebieg. SA musi ponownie odpowiadać aktualnemu zatwierdzonemu BA. |
| Aktywny inny kontroler | Poczekaj na zakończenie drugiej instancji `factory` w tym samym worktree. |
| `Run already exists` | Użyj `resume` dla bieżącego przebiegu albo świadomie zresetuj go przed nowym `analyze`. |
| `factory: command not found` | Aktywuj `.venv` lub użyj `.venv/bin/factory`. |
| Błąd wykonania Codex | Sprawdź lokalną instalację, uwierzytelnienie, dostęp sieciowy i obsługę wymaganych flag. Adapter nie zapisuje surowego outputu dostawcy w logach. |

Reset i ponowne rozpoczęcie:

```bash
factory reset
factory analyze
```

`reset` usuwa wyłącznie bieżący stan orkiestratora. Zachowuje źródła, BA, SA, architekturę, ADR, zgody i historię. Nie cofa wcześniejszych zmian w dokumentach. Poprzednie zgody pozostają przypisane do swoich rewizji; nowa analiza musi zwiększyć rewizję i uzyskać nową zgodę.

## 8. Kolejna zmiana biznesowa

Po zakończeniu poprzedniego przebiegu przygotuj nowe źródła na właściwej gałęzi, następnie:

```bash
factory reset
factory analyze
factory approve ba
factory resume
factory approve sa
factory resume
factory status
```

Przeglądaj obie analizy przed każdym zatwierdzeniem. Nawet zmiana formatowania zatwierdzonego YAML zmienia digest i unieważnia dotychczasową zgodę.

## 9. Sprawdzenie instalacji

Testy bez wywołań LLM:

```bash
python -m unittest discover -s tests -v
python docs/architecture/validation/check_baseline.py --self-test
```

Opcjonalny smoke test rzeczywistych ról Codex:

```bash
python -m orchestrator.smoke --timeout 120
```

Smoke test wywołuje usługę Codex i sprawdza transport oraz załadowanie instrukcji czterech ról. Nie tworzy BA/SA ani zatwierdzeń i nie sprawdza jakości pełnej analizy biznesowej.

Więcej informacji o kontraktach, zabezpieczeniach i konfiguracji: [docs/orchestrator.md](docs/orchestrator.md).
