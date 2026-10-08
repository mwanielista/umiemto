# eSzkola — kanoniczny wsad systemowy

**Status:** ACTIVE  
**Wersja:** 1.0  
**Zakres:** doprecyzowanie System Analysis dla MVP eSzkola  
**Business input:** zatwierdzona Business Analysis revision 6  
**Właściciel decyzji:** Michał Wanielista

> Ten dokument jest wejściem do System Analysis. Doprecyzowuje kwestie techniczno-systemowe wynikające z SA-Q-001–SA-Q-008. Nie zmienia zatwierdzonych wymagań biznesowych BA revision 6 i nie stanowi zatwierdzenia konkretnej rewizji System Analysis. W przypadku sprzeczności z zatwierdzoną BA obowiązuje BA, a sprzeczność ma zostać zgłoszona właścicielowi zamiast samodzielnie rozstrzygnięta przez SA.

## 1. Zasady interpretacji

1. Niniejszy dokument jest aktualnym źródłem decyzji systemowych dla zagadnień SA-Q-001–SA-Q-008.
2. Nie należy ponownie otwierać tych pytań wyłącznie z powodu starszych, sprzecznych lub niepełnych dokumentów.
3. Decyzje prawne, podatkowe i regulaminowe pozostają bramkami produkcyjnymi tam, gdzie wskazano to poniżej.
4. System Analyst nie wybiera technologii, bibliotek ani dostawców, jeżeli nie wynika to z obowiązujących ograniczeń repozytorium.
5. Wartości wskazane jako konfigurowalne nie powinny być zaszywane na stałe w domenie.

---

# SA-Q-001 — tożsamość, opiekunowie, uprawnienia i MFA

**Status:** RESOLVED

## Dostęp dziecka

Dziecko posiada własny dostęp edukacyjny, odrębny od konta opiekuna.

Dla MVP dziecko nie musi posiadać własnego adresu e-mail ani numeru telefonu. Opiekun główny tworzy dostęp dziecka i otrzymuje identyfikator/login dziecka. Hasło dziecka jest ustawiane lub resetowane przez uprawnionego opiekuna.

Dziecko nie może samodzielnie:
- dodawać lub usuwać opiekunów;
- zarządzać zgodami wymagającymi osoby dorosłej;
- dokonywać zakupów;
- zmieniać danych rozliczeniowych;
- odzyskiwać dostępu poprzez niezależny kanał wymagający potwierdzenia pełnoletności.

Odzyskanie dostępu dziecka wykonuje uprawniony opiekun. Administrator może wykonać ręczne odzyskanie wyłącznie po zweryfikowaniu uprawnienia opiekuna; operacja jest audytowana.

## Relacje opiekunów

Pierwszy poprawnie zweryfikowany opiekun przypisany do dziecka jest **opiekunem głównym**.

Opiekun główny może zaprosić dodatkowego opiekuna. Zaproszenie:
- wskazuje konkretne dziecko;
- trafia do konkretnej osoby;
- wymaga utworzenia lub użycia własnego konta opiekuna;
- wymaga przyjęcia zaproszenia;
- pozostawia historię nadania uprawnienia.

Dodatkowy opiekun nie może samodzielnie dodać kolejnego opiekuna.

Opiekun główny może odebrać dostęp opiekunowi dodatkowemu. Odebranie dostępu nie usuwa historycznych zdarzeń i zgód z audytu.

Zmiana opiekuna głównego wymaga:
- zgody obecnego opiekuna głównego, albo
- ręcznej decyzji uprawnionego administratora po weryfikacji podstawy zmiany.

W przypadku sporu pomiędzy opiekunami system może zablokować zmiany relacji do czasu ręcznego rozstrzygnięcia. System nie rozstrzyga automatycznie sporów rodzinnych ani prawnych.

Jeżeli wszyscy opiekunowie utracą dostęp, odzyskanie relacji wymaga ręcznej weryfikacji przez uprawnionego administratora.

## Macierz uprawnień

### Opiekun
Ma dostęp wyłącznie do dzieci, do których posiada aktywną relację.

Może:
- widzieć harmonogram, materiały, wyniki, postęp i konsultacje dziecka;
- wykonywać czynności zakupowe;
- zarządzać wymaganymi zgodami w zakresie swojej roli;
- inicjować konsultację w imieniu dziecka zgodnie z SA-Q-003.

### Dziecko
Ma dostęp wyłącznie do własnych danych edukacyjnych i funkcji uczestnika.

### Nauczyciel
Ma dostęp wyłącznie do programów, grup i uczestników, do których jest przypisany albo do których otrzymał jawne uprawnienie.

Nie otrzymuje dostępu do danych rozliczeniowych opiekuna, jeżeli nie są potrzebne do realizacji jego obowiązków.

### Metodyk
Ma dostęp do treści, programów, kryteriów oceniania i danych potrzebnych do kontroli jakości.

Sama rola metodyka nie daje:
- prawa do zakupów i zwrotów;
- prawa do zarządzania relacjami opiekunów;
- prawa do ręcznego wyjątku progresji;
- pełnego dostępu do danych dziecka niezwiązanego z kontrolą jakości.

### Obsługa klienta
Może:
- odczytać dane potrzebne do obsługi sprawy;
- prowadzić sprawę organizacyjną;
- przygotować operację wymagającą decyzji administratora.

Nie może samodzielnie:
- nadać dostępu do dziecka po sporze;
- zmienić finalnego wyniku edukacyjnego;
- przyznać wyjątku progresji, jeżeli nie posiada odrębnego uprawnienia administratora.

### Administrator
Może wykonywać operacje administracyjne wymagane do obsługi uczestnictwa, płatności, zwrotów, relacji opiekunów, incydentów i moderacji.

Operacje uprzywilejowane są audytowane.

### Business Owner
Posiada uprawnienia biznesowe wynikające z zatwierdzonej BA, w tym możliwość audytowanego wyjątku progresji. Approval BA/SA pozostaje procesem orchestratora, a nie funkcją produktu.

## MFA

MFA jest obowiązkowe dla:
- nauczycieli;
- metodyków;
- obsługi klienta;
- administratorów;
- kont posiadających uprawnienia Business Owner w produkcie.

MFA nie jest obowiązkowe dla dziecka.

Dla opiekuna MFA jest opcjonalne w MVP, chyba że późniejsza decyzja bezpieczeństwa lub prawa ustanowi obowiązek.

## Odzyskiwanie MFA

Użytkownik uprzywilejowany odzyskuje MFA poprzez:
1. kod odzyskiwania, jeżeli został wcześniej wygenerowany; albo
2. ręczny proces odzyskania przeprowadzony przez uprawnionego administratora po dodatkowej weryfikacji tożsamości.

Administrator wykonujący recovery nie może zatwierdzać własnego odzyskania MFA.

Reset MFA:
- unieważnia poprzednią konfigurację;
- wymusza ponowną konfigurację MFA;
- tworzy wpis audytowy;
- może unieważnić aktywne sesje użytkownika.

---

# SA-Q-002 — późna płatność, utrata miejsca, zwroty i istotne pogorszenie

**Status:** RESOLVED

## Płatność po wygaśnięciu rezerwacji

Potwierdzona płatność zawsze jest wiązana z pierwotnym zamówieniem, nawet jeżeli rezerwacja miejsca wygasła.

Po otrzymaniu zweryfikowanej płatności po wygaśnięciu rezerwacji:

1. jeżeli pierwotne miejsce nadal jest dostępne, system może potwierdzić uczestnictwo;
2. jeżeli miejsce nie jest już dostępne, system **nie zapisuje automatycznie** dziecka do innej grupy;
3. zamówienie otrzymuje status wymagający rozstrzygnięcia;
4. opiekunowi proponuje się:
   - przeniesienie wpłaty na zaakceptowaną alternatywną grupę/edycję, albo
   - pełny zwrot wpłaty;
5. brak decyzji klienta nie może zostać potraktowany jako automatyczna zgoda na inną grupę.

Ponowne dostarczenie tego samego potwierdzenia płatności nie tworzy drugiego uczestnictwa ani drugiego skutku finansowego.

## Wycena niezrealizowanej części

Dla MVP oferta może posiadać **plan rozliczeniowy** określający wartość poszczególnych elementów świadczenia. Suma wartości elementów musi być równa cenie brutto zakupionej usługi.

W przypadku częściowej realizacji:
- zrealizowane elementy nie podlegają automatycznie zwrotowi;
- niezrealizowana część jest sumą wartości niezrealizowanych elementów zapisanych w zakupionej wersji planu rozliczeniowego.

Jeżeli dla historycznej lub wyjątkowej oferty nie istnieje jednoznaczny plan rozliczeniowy, system nie wymyśla proporcji. Uprawniony administrator wprowadza kwotę zwrotu ręcznie zgodnie z zatwierdzoną polityką, a system zapisuje:
- kwotę;
- walutę;
- podstawę;
- osobę podejmującą decyzję;
- czas;
- uzasadnienie.

Kwota zwrotu nie może przekroczyć rzeczywiście zapłaconej kwoty pomniejszonej o wcześniejsze skuteczne zwroty.

Jeżeli usługa nie rozpoczęła się i nie może być wykonana na zakupionych warunkach, zwrot obejmuje całą zapłaconą kwotę za tę usługę.

## Istotne pogorszenie

System nie podejmuje samodzielnie decyzji prawnej, czy zmiana jest istotnym pogorszeniem.

Zmianę jako istotne pogorszenie może oznaczyć:
- uprawniony administrator odpowiedzialny za realizację usługi;
- Business Owner.

W przypadku sporu o kwalifikację decyzję końcową podejmuje Business Owner lub osoba formalnie uprawniona przez organizatora zgodnie z obowiązującą procedurą.

Za kandydatów do istotnego pogorszenia uznaje się w szczególności zmianę po zakupie dotyczącą:
- zmniejszenia zakupionego zakresu zajęć lub materiałów;
- skrócenia zakupionego okresu dostępu;
- istotnej zmiany efektów lub zakresu programu;
- zmiany kryteriów ukończenia/progresji na mniej korzystne dla już zapisanego uczestnika;
- istotnej zmiany harmonogramu wpływającej na możliwość udziału;
- zmiany formy realizacji na jakościowo inną.

Lista ta wspiera kwalifikację, ale nie zastępuje wymaganej decyzji osoby uprawnionej.

---

# SA-Q-003 — konsultacje

**Status:** RESOLVED

Opiekun może rozpocząć wątek konsultacyjny w imieniu dziecka.

Limit konsultacji jest wspólny dla dziecka i wszystkich jego uprawnionych opiekunów:
- maksymalnie jeden nowy wątek;
- na jedno aktywne uczestnictwo/program;
- w tygodniu od poniedziałku 00:00 do niedzieli 23:59;
- strefa `Europe/Warsaw`.

Odpowiedzi w istniejącym wątku nie zużywają kolejnego limitu.

„Dwa dni robocze” oznaczają poniedziałek–piątek z wyłączeniem dni ustawowo wolnych od pracy w Polsce. Termin liczy się od momentu utworzenia wątku.

Program jest aktywny dla konsultacji, jeżeli:
- uczestnictwo ma status aktywny;
- rozpoczął się okres dostępu;
- nie zakończył się okres dostępu do konsultacji wynikający z oferty/programu.

Wątek może zostać zamknięty przez nauczyciela lub uprawnionego administratora po rozwiązaniu sprawy albo zakończeniu uprawnionego okresu konsultacji.

Zamknięty wątek pozostaje w historii i nie jest usuwany przez zwykłego użytkownika.

---

# SA-Q-004 — KPI, aktywna rodzina, równoczesne zajęcia i profil obciążenia

**Status:** RESOLVED

## Aktywna rodzina

Aktywna rodzina to konto/relacja rodzinna posiadająca co najmniej jedno dziecko, które w danym miesiącu:
- ma aktywne uczestnictwo w trwającym programie; albo
- posiada opłacone uczestnictwo, którego okres realizacji obejmuje dany miesiąc.

Rodzina jest liczona raz niezależnie od liczby dzieci i aktywnych programów.

## Równoczesne zajęcia

Jedne równoczesne zajęcia oznaczają jedno wystąpienie zajęć live, którego przedział czasowy nakłada się na przedział innych zajęć live.

Liczba uczestników w grupie nie zwiększa liczby równoczesnych zajęć.

## Profil obciążenia MVP

Minimalny test zdolności MVP obejmuje:
- co najmniej 100 aktywnych rodzin;
- co najmniej 10 równoczesnych zajęć;
- równoczesne korzystanie z logowania, paneli, harmonogramu, materiałów, prac, wyników i podstawowych operacji administracyjnych.

Dla typowych synchronicznych operacji użytkownika celem testowym jest:
- p95 czasu odpowiedzi backendu do 2 sekund;
- p99 do 5 sekund;
- udział błędów technicznych poniżej 1% w okresie testu.

Operacje długotrwałe, generowanie raportów i integracje asynchroniczne nie muszą spełniać limitu 2 sekund, ale użytkownik powinien otrzymać jednoznaczne potwierdzenie przyjęcia operacji.

## Główny opiekun dla KPI

Dla ankiety i raportowania opiekunem głównym jest osoba posiadająca status głównego opiekuna w chwili zakończenia mierzonego uczestnictwa.

Zmiana głównego opiekuna nie tworzy drugiej ankiety dla tego samego uczestnictwa.

## Deduplikacja klienta dla kontynuacji

Jednostką kwalifikacji KPI kontynuacji jest:

`opiekun kupujący + dziecko + zakończone uczestnictwo + logiczna kontynuacja`

Jedno dziecko może tworzyć osobną kwalifikację dla kolejnego etapu. Kilka dzieci jednego opiekuna może tworzyć odrębne kwalifikacje.

Wielokrotne wyświetlenie lub udostępnienie tej samej kontynuacji nie tworzy kolejnych kwalifikacji.

Zakup liczy się do okna 60 dni, jeżeli zweryfikowana płatność nastąpiła nie później niż do końca 60. dnia od daty kwalifikacji. Granice dnia liczone są w `Europe/Warsaw`.

---

# SA-Q-005 — dostępność, RTO, RPO i test odtworzenia

**Status:** RESOLVED

## Pomiar dostępności 99,5%

Dostępność jest mierzona dla funkcji wskazanych w zatwierdzonej BA.

Pomiar odbywa się w rozdzielczości jednej minuty.

Minuta jest uznana za niedostępną dla danej krytycznej funkcji, jeżeli syntetyczna kontrola podstawowego procesu zakończy się niepowodzeniem w dwóch kolejnych próbach wykonanych w tej minucie lub stan aplikacji jednoznacznie potwierdza blokującą awarię.

Częściowa awaria jest traktowana jako niedostępność, jeżeli uniemożliwia wykonanie podstawowego procesu użytkownika w objętym zakresie, nawet jeśli pozostała część aplikacji odpowiada.

Planowane prace serwisowe są wyłączone wyłącznie zgodnie z zatwierdzoną regułą wcześniejszego powiadomienia.

Raport dostępności przechowuje:
- okres pomiaru;
- całkowity czas objęty pomiarem;
- czas wyłączony jako prawidłowo zapowiedziane prace;
- czas niedostępności;
- funkcję/proces objęty awarią;
- źródło dowodu pomiarowego.

## RTO

RTO rozpoczyna się w chwili wcześniejszego z:
- automatycznego wykrycia krytycznej awarii przez monitoring;
- ręcznego potwierdzenia krytycznej awarii przez uprawnioną obsługę.

RTO kończy się, gdy podstawowe funkcje objęte awarią zostały przywrócone i przez co najmniej 15 kolejnych minut przechodzą wymagane kontrole zdrowia.

## RPO

RPO jest mierzone względem najnowszego trwałego zdarzenia biznesowego, które powinno być możliwe do odzyskania.

Test określa różnicę pomiędzy:
- czasem ostatnich poprawnie zapisanych danych przed awarią;
- najnowszym stanem możliwym do odtworzenia z backupu.

Różnica nie może przekroczyć 24 godzin.

## Zakres testu odtworzenia

Test odtworzenia obejmuje co najmniej:
- konta i relacje opiekun–dziecko;
- programy i opublikowane wersje;
- oferty, grupy i harmonogram;
- uczestnictwa;
- zamówienia, płatności i zwroty;
- zgody i oświadczenia;
- zadania, przesłane odpowiedzi, próby i wyniki;
- konsultacje;
- pliki przechowywane jako część usługi;
- audyt wymagany do rozliczalności.

Test nie kończy się na samym uruchomieniu aplikacji. Po odtworzeniu należy zweryfikować spójność danych i podstawowe procesy użytkownika.

---

# SA-Q-006 — prawo, podatki, retencja i procedury

**Status:** RESOLVED jako decyzja systemowa / pozostaje bramką produkcyjną**

System Analysis nie ustala samodzielnie finalnych:
- podstaw prawnych;
- tekstów zgód i oświadczeń;
- okresów retencji;
- procedur praw osób;
- umów z procesorami;
- stawek VAT;
- dokumentów sprzedaży;
- terminów reklamacyjnych;
- dokumentów wymaganych od nauczycieli;
- procedur ochrony małoletnich;
- procedur incydentów prawnych.

Dla MVP system ma jednak umożliwiać ich późniejsze wdrożenie bez zmiany podstawowego modelu domenowego.

W szczególności:
- zgody/oświadczenia są wersjonowane;
- akceptacja przechowuje wersję, osobę i czas;
- polityki retencji są konfigurowalne;
- VAT/stawka podatkowa nie jest globalnie zaszyta;
- dokument sprzedażowy jest powiązany z zamówieniem;
- status reklamacji/sprawy administracyjnej jest możliwy do śledzenia;
- przygotowanie nauczyciela do pracy z dziećmi może być oznaczane na podstawie zatwierdzonych kontroli;
- procedury ręcznej oceny i incydentów mogą być realizowane jako kontrolowane procesy z audytem.

Brak finalnego tekstu prawnego nie blokuje SA ani architektury. Blokuje uruchomienie odpowiedniej funkcji produkcyjnej, jeżeli przepisy lub zatwierdzona polityka tego wymagają.

---

# SA-Q-007 — pliki, walidacja, retry, diagnostyka i alerty

**Status:** RESOLVED

## Pliki w MVP

Dopuszczalne formaty:
- PDF;
- JPG/JPEG;
- PNG;
- WEBP;
- DOCX.

Maksymalny rozmiar pojedynczego pliku: **20 MB**.

Maksymalnie **5 plików** w pojedynczym przesłaniu zadania lub wiadomości.

Niedozwolone są pliki wykonywalne, skrypty i archiwa jako zwykłe załączniki użytkownika.

Walidacja pliku obejmuje:
- rozszerzenie;
- deklarowany MIME type;
- rozpoznanie rzeczywistego typu/magic bytes;
- rozmiar;
- kontrolę złośliwej zawartości;
- sprawdzenie uprawnienia do zasobu.

Plik niezweryfikowany pozostaje niedostępny dla innych użytkowników do czasu zakończenia kontroli.

## Retry integracji

Operacje muszą być projektowane idempotentnie tam, gdzie istnieje możliwość ponowienia lub duplikacji zdarzenia.

Dla wywołań wychodzących, które można bezpiecznie ponowić:
- pierwsza próba jest natychmiastowa;
- retry po około 1 minucie;
- kolejne po około 5 minutach;
- kolejne po około 15 minutach;
- po wyczerpaniu automatycznych prób zdarzenie przechodzi do obsługi ręcznej / kolejki błędów.

Nie ponawia się automatycznie operacji, których nie można bezpiecznie wykonać idempotentnie.

Webhooki i callbacki dostawców mogą być dostarczane wielokrotnie; powtórzenie tego samego zdarzenia nie może powielać skutków biznesowych.

## Diagnostyka

Techniczne logi diagnostyczne MVP są przechowywane domyślnie przez **30 dni**, o ile późniejsza zatwierdzona polityka nie wymaga innego okresu.

Audyt biznesowy i bezpieczeństwa ma osobną politykę retencji i nie jest automatycznie usuwany po 30 dniach.

Logi nie przechowują:
- haseł;
- sekretów;
- tokenów uwierzytelniających;
- pełnych danych kart;
- niepotrzebnych wrażliwych danych dzieci.

## Alerty

Alert krytyczny powstaje co najmniej, gdy:
- podstawowy proces jest niedostępny przez 5 kolejnych minut;
- trzy kolejne próby krytycznej integracji kończą się niepowodzeniem;
- występuje trwały błąd zapisu lub odczytu danych biznesowych;
- monitoring wykrywa istotny wzrost błędów autoryzacji, płatności lub dostępu do plików.

Progi alertów powinny być konfigurowalne bez zmiany kodu domenowego.

---

# SA-Q-008 — ekonomika pilota

**Status:** RESOLVED

Ekonomika pilota jest decyzją biznesową i nie jest automatycznym gate'em funkcjonalnym platformy.

MVP ma dostarczać dane pozwalające policzyć co najmniej:
- przychód ze sprzedaży;
- zwroty;
- liczbę płatnych uczestnictw;
- wykorzystanie miejsc;
- liczbę kontynuacji;
- dane potrzebne do zestawienia kosztów zmiennych poza systemem.

System nie musi w MVP prowadzić pełnego P&L, księgowości zarządczej ani automatycznie podejmować decyzji `GO/NO-GO`.

Dla pilota przyjmuje się następujące biznesowe kryteria pomocnicze:
- marża kontrybucyjna na programie/grupie powinna być dodatnia;
- docelowo relacja `LTV/CAC >= 3`;
- docelowo koszt pozyskania klienta powinien zwracać się nie później niż po pierwszych 1–2 zakupionych programach.

Budżet konkretnego pilota jest zatwierdzany osobno przez Business Owner przed jego rozpoczęciem i nie jest stałą systemową.

Brak zatwierdzonej konkretnej kwoty budżetu nie blokuje System Analysis ani architektury.

---

# Podsumowanie statusów

- SA-Q-001: RESOLVED
- SA-Q-002: RESOLVED
- SA-Q-003: RESOLVED
- SA-Q-004: RESOLVED
- SA-Q-005: RESOLVED
- SA-Q-006: RESOLVED jako decyzja systemowa; szczegóły pozostają bramkami produkcyjnymi
- SA-Q-007: RESOLVED
- SA-Q-008: RESOLVED

Po uwzględnieniu tego dokumentu System Analyst powinien zaktualizować `system-analysis.yaml`, usunąć blokadę wynikającą z SA-Q-001 i SA-Q-002 oraz oznaczyć SA-Q-001–SA-Q-008 jako rozwiązane w zakresie opisanym powyżej.

Niniejszy dokument nie stanowi approval konkretnej rewizji SA. Po wygenerowaniu nowej rewizji wymagane jest jej osobne zatwierdzenie przez Michała Wanielistę poprzez mechanizm orchestratora.
