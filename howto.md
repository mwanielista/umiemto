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

Pracuj w checkoutcie zawierającym incremental analysis, na gałęzi zadania. Implementacja tej zmiany znajduje się na `feature/incremental-analysis` w `/private/tmp/eszkola-incremental-analysis`; aby korzystać z niej przed integracją, przejdź do tego worktree i zainstaluj narzędzie z jego katalogu. Jeśli zaczynasz niezależne zadanie, utwórz dla niego własną gałąź zgodnie z [workflow.md](workflow.md#branches-and-worktrees). Etapy zapisujące dokumenty i zatwierdzenia odrzucają `main`, `master` oraz detached HEAD. Nie zmieniaj gałęzi w katalogu używanym przez innego agenta.

Gałąź zadania musi zawierać implementację orkiestratora: `pyproject.toml`, źródła `orchestrator/*.py` i `config/pipeline.yaml`. Utwórz ją z wersji zawierającej te pliki lub zintegruj do niej gałąź orkiestratora zgodnie z zasadami repozytorium. Instalacja editable (`pip install -e .`) odczytuje źródła z bieżącego checkoutu; przełączenie na gałąź bez tych plików powoduje `ModuleNotFoundError: No module named 'orchestrator'`, nawet gdy polecenie `factory` pozostaje w `.venv/bin/`.

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
- `AGENTS.md`,
- `docs/business/product-decisions.yaml`.

Jeżeli nowe źródło jest osobnym dokumentem, dodaj jego ścieżkę do tej listy **przed rozpoczęciem przebiegu**. Samo utworzenie pliku nie dodaje go do skonfigurowanej listy źródeł.

Rejestr [product-decisions.yaml](docs/business/product-decisions.yaml) jest źródłem utrzymywanym przez właściciela biznesowego, Michała Wanielistę, a nie wynikiem BA. Początkowo jest pusty. Każda decyzja ma `id`, `status`, `decision`, `rationale`, `supersedes`, `source` i `date`; format oraz przykład opisuje [instrukcja rejestru](docs/business/README.md). Datę zapisz jako tekst, np. `"2026-10-06"`.

Aktualna jawna decyzja właściciela ma pierwszeństwo przed aktualnym źródłem biznesowym, starszym źródłem i poprzednim wygenerowanym BA. Decyzje `ACTIVE` zastępują sprzeczne historyczne ustalenia; wpis `SUPERSEDED` nie może samodzielnie tworzyć nowego blockera. Poprawność interpretacji nadal sprawdzają BA i człowiek podczas przeglądu. Wpisanie decyzji nie zatwierdza automatycznie BA ani SA.

Nie dodawaj wygenerowanych BA/SA, historii `.orchestrator/` ani artefaktów architektury do źródeł biznesowych. Aby usunąć źródło z analizy, usuń jego ścieżkę z konfiguracji. Brak pliku nadal wymienionego w konfiguracji jest błędem.

Uzgodnij, kto odpowiada za zatwierdzenie BA i SA. W czasie pracy agenta nie edytuj równolegle plików repozytorium ani nie uruchamiaj drugiego autora tych samych artefaktów. Orkiestrator wykrywa nieoczekiwane zmiany i zatrzymuje zapis propozycji.

## 3. Uruchom analizę biznesową

```bash
factory analyze
factory status
```

`analyze` automatycznie wybiera tryb:

| Tryb | Kiedy | Wynik |
| --- | --- | --- |
| `FULL` | Brak poprawnego baseline BA lub jawne `--full`. | Pełna propozycja, walidacja i bezpieczna serializacja YAML przed zapisem. |
| `INCREMENTAL` | Poprawny baseline i zmienione źródła/kontrakty/konfiguracja albo pytania wymagające rozstrzygnięcia. | Analiza impactu i patch JSON zamiast regeneracji całego BA. |
| `NOOP` | Znany snapshot i wejścia bez zmian, poprawny baseline, brak powodu do ponownej analizy. | Bez wywołania Codex, zmiany artefaktu i nowej rewizji. |

W trybie przyrostowym agent otrzymuje dokładne ID, rewizję i digest baseline, jego reprezentację, zmienione źródła oraz otwarte pytania. Nie otrzymuje całych niezmienionych źródeł ani zadania odtworzenia wszystkich wymagań. Zwraca wyłącznie structured JSON patch. Python sprawdza jego bazę i operacje, scala go na kopii danych, zwiększa rewizję, usuwa approval, waliduje wynik i generuje YAML przez `safe_dump`. Błędny patch nie zmienia canonical BA. Szczegóły opisuje [kontrakt incremental analysis](docs/requirements/incremental-analysis.md).

Każde źródło ma SHA-256 liczony z bajtów pliku. Snapshot pozwala rozróżnić źródła dodane, zmienione, usunięte i niezmienione; jest zachowany w provenance danej rewizji.

Istniejąca poprawna BA revision 5 bez historycznego snapshotu jest przyjmowana jako baseline bez zmiany jej bajtów, rewizji i digestu. Snapshot historyczny pozostaje `UNKNOWN`. Pierwszy incremental może otrzymać wszystkie aktualne źródła jako nieznany delta; nie dorabia historycznych hashy. Kolejne przebiegi korzystają ze znanego snapshotu.

Aby wymusić pełną analizę BA i późniejszego SA:

```bash
factory analyze --full
```

Niezakończony przebieg wymaga `resume` albo świadomego `reset` także przed `--full`. Po `DONE` lub `NOOP` można ponownie wykonać `analyze` bez resetu.

Przy `NOOP` status informuje o braku zmian źródeł i pokazuje `PIPELINE: NOOP`. Istniejąca rewizja BA pozostaje aktualna; nie oznacza to jej zatwierdzenia. Jeżeli chcesz kontynuować downstream, wykonaj `factory resume`: ponownie sprawdzi approval BA, następnie bramki SA i architektury.

Podczas wywołania agenta terminal co około dwie sekundy odświeża nazwę etapu, czas trwania i limit czasu (domyślnie 1800 sekund). Przykład:

```text
[factory] BA — analiza biznesowa | czas 00:24 | limit 1800s | Codex uruchomiony; oczekiwanie na wynik
```

W terminalu aktualizowana jest jedna linia; po przekierowaniu outputu kolejne aktualizacje są osobnymi liniami na stderr. Licznik potwierdza trwanie wywołania, nie procent ukończenia ani postęp myślenia modelu. Treści odpowiedzi i surowe logi Codex pozostają ukryte. `Ctrl+C` kończy proces Codex i jego grupę subprocessów; CLI wypisuje instrukcję odzyskania przerwanego przebiegu.

Wynik BA zostaje zapisany do:

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

SA może również działać przyrostowo: wykorzystuje poprzedni baseline i diff semantyczny zatwierdzonego BA. Historyczny BA input musi być dostępny w archiwum i mieć ważne zewnętrzne approval. Jeżeli nie da się go zweryfikować, SA wybiera FULL. Niezmieniony, aktualny SA może zostać użyty ponownie bez inference. Zmieniony SA otrzymuje nową rewizję i wymaga nowego zatwierdzenia; SA nigdy nie działa na niezatwierdzonym BA.

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

`status` pokazuje rzeczywiste rewizje, digests, stan zgód, tryb analizy i diff źródeł, pochodzenie SA, recenzje i wyniki walidatorów. `history` wyświetla zdarzenia zachowanych przebiegów.

Pliki diagnostyczne znajdują się w ignorowanym przez Git katalogu:

```text
.orchestrator/
├── state.json
├── approvals/
├── provenance/
│   ├── artifacts/
│   ├── sources/
│   ├── manifests/
│   └── approvals/
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

`provenance/` zachowuje dokładne bajty analiz i źródeł, snapshoty, tożsamość parent revision, wykorzystany BA oraz wycofane ID. Zatwierdzenie zachowuje powiązanie ze snapshotem mimo zmiany metadanych i digestu. Nie usuwaj tego archiwum, aby przyspieszyć analizę.

## 7. Wznowienie i rozwiązywanie problemów

| Stan lub komunikat | Co zrobić |
| --- | --- |
| `WAITING_FOR_BA_APPROVAL` | Przejrzyj BA, wykonaj `factory approve ba`, potem `factory resume`. |
| `WAITING_FOR_SA_APPROVAL` | Przejrzyj SA, wykonaj `factory approve sa`, potem `factory resume`. |
| `NOOP` | Nie ma potrzeby nowej analizy BA. Aby kontynuować istniejący pipeline, użyj `factory resume`; approvals nadal są wymagane. |
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
| `CODEX_TIMEOUT` / `CODEX_START_FAILED` / `CODEX_EXIT_FAILED` | Sprawdź limit, instalację, uwierzytelnienie i połączenie. Po rozwiązaniu przyczyny zresetuj zakończony błędem przebieg i uruchom analizę ponownie. Canonical baseline pozostaje zachowany. |
| `CODEX_INVALID_OUTPUT` / `INVALID_PATCH` / `INVALID_GENERATED_ARTIFACT` / `VALIDATION_FAILED` | Sprawdź powód odrzucenia propozycji; popraw przyczynę przed nowym przebiegiem. Nie wklejaj odrzuconej propozycji do canonical YAML. |
| `BASE_REVISION_MISMATCH` / `BASE_DIGEST_MISMATCH` | Patch nie odpowiada dokładnej bazie. Sprawdź równoległych autorów i aktualny baseline, następnie rozpocznij nowy przebieg. |

Jeżeli przerwanie zatwierdzania pozostawiło `APPROVED` bez zewnętrznego pliku approval, pipeline nie przejdzie dalej. Gdy plik dowodu nie istnieje, możesz ponownie wykonać `factory approve ba` lub `sa`, przejrzeć nowego kandydata i jawnie potwierdzić go. Istniejący nieważny dowód pozostaje niezmienny i wymaga nowej rewizji po świadomym odzyskaniu przebiegu.

Reset i ponowne rozpoczęcie:

```bash
factory reset
factory analyze
```

`reset` usuwa wyłącznie bieżący stan orkiestratora. Zachowuje źródła, BA, SA, architekturę, ADR, zgody, historię i provenance. Nie cofa wcześniejszych zmian w dokumentach. Poprzednie zgody pozostają przypisane do swoich dokładnych rewizji i digestów. Nowa materialna rewizja wymaga nowej zgody; NOOP nie tworzy rewizji ani zgody.

## 8. Kolejna zmiana biznesowa

Po zakończeniu poprzedniego przebiegu przygotuj nowe źródła na właściwej gałęzi, następnie:

```bash
factory analyze
factory approve ba --owner "Michał Wanielista"
factory resume
factory approve sa --owner "Michał Wanielista"
factory resume
factory status
```

Ten przykład zakłada zmianę źródeł i nowe analizy gotowe do przeglądu. Jeśli poprzedni przebieg nie jest zakończony, sprawdź go i wykonaj świadomy `factory reset` przed `analyze`. Przy braku zmian `analyze` wybierze NOOP; nie wykonuj wtedy automatycznie sekwencji nowych zatwierdzeń.

Przeglądaj obie analizy przed każdym zatwierdzeniem. Approval rewizji N nigdy nie zatwierdza N+1. Zmiana BA oznacza poprzedni SA jako stale; architektura wymaga aktualnego zatwierdzonego BA i odpowiadającego mu zatwierdzonego SA. Nawet zmiana formatowania zatwierdzonego YAML zmienia digest i unieważnia dotychczasową zgodę. Wprowadzaj decyzje w źródłach właściciela, zamiast ręcznie edytować wygenerowane analizy.

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
