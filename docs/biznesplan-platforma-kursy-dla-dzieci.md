# eSzkola --- kanoniczny wsad biznesowy

**Status:** ACTIVE\
**Wersja:** 2.0\
**Rynek startowy:** Polska\
**Właściciel biznesowy / Product Owner / Requirements Owner:** Michał
Wanielista

> Ten dokument jest aktualnym źródłem decyzji biznesowych eSzkola.
> Zastępuje wcześniejsze sprzeczne wersje biznesplanu, historyczne
> odpowiedzi Q-001--Q-016, przykłady i założenia w zakresie, w którym są
> z nim sprzeczne. Nie zatwierdza automatycznie żadnej rewizji ani
> digestu BA/SA.

## 1. Pierwszeństwo źródeł

W razie sprzeczności obowiązuje kolejno:

1.  późniejsza jawna decyzja Michała Wanielisty;
2.  niniejszy dokument;
3.  aktualny `AGENTS.md` w zakresie procesu i odpowiedzialności;
4.  inne aktualne źródła biznesowe właściciela;
5.  starsze źródła biznesowe;
6.  wcześniejsze wygenerowane BA i SA.

BA/SA są artefaktami analitycznymi, nie źródłami nowych decyzji
biznesowych. Nie trzeba odzyskiwać historycznej sekcji „Aktualizacja
decyzji biznesowych Q-001--Q-014". Brak starego pliku nie może
samodzielnie tworzyć BLOCKER-a, jeżeli aktualne źródła rozstrzygają
temat.

Wszystkie wcześniejsze zapisy sprzeczne z tym dokumentem są
**SUPERSEDED**. Dotyczy to szczególnie założeń: obowiązkowych 4 lekcji,
jednej klasy/wieku, obowiązkowego egzaminu, globalnego warunku
zaliczenia poprzedniego modułu, płatnych kolejnych poprawek, poprawek
jako źródła przychodu, automatycznych uprawnień metodyka do obchodzenia
progresji oraz traktowania historycznych rekomendacji technologicznych
jako wymagań biznesowych.

Nowy BLOCKER może powstać tylko przy rzeczywistej nierozstrzygalnej
sprzeczności aktualnych źródeł albo braku decyzji koniecznej do
jednoznacznego przejścia do następnego etapu.

## 2. Cel i model produktu

eSzkola to platforma edukacyjna dla dzieci, opiekunów i nauczycieli.
Umożliwia tworzenie, publikowanie, sprzedaż i realizację
konfigurowalnych programów edukacyjnych online oraz monitorowanie
postępu.

Podstawowy proces:
`program → zapis i płatność → nauka → ocena/postęp → ukończenie → kontynuacja`.

Platforma nie jest ograniczona do jednego przedmiotu, wieku, klasy ani
struktury programu. Rynek startowy to Polska. Początkowe przedmioty mogą
obejmować matematykę, angielski i niemiecki, lecz model nie może być do
nich technicznie ograniczony.

## 3. Role

### Opiekun

Tworzy konto i profil dziecka, dokonuje zakupów, zarządza wymaganymi
zgodami, widzi harmonogram, obecności, postępy, wyniki i raporty,
otrzymuje komunikaty organizacyjne oraz korzysta z procesów
reklamacji/rezygnacji. Możliwe jest powiązanie więcej niż jednego
opiekuna z dzieckiem.

### Dziecko / uczestnik

Korzysta z przypisanych programów, materiałów, zajęć, zadań, treningów,
testów/egzaminów i konsultacji. Nie dokonuje samodzielnie zakupów ani
czynności wymagających osoby dorosłej.

### Nauczyciel

Może tworzyć programy, prowadzić przypisane programy/grupy, zarządzać
zajęciami i obecnością, udostępniać materiały, oceniać, prowadzić
konsultacje i raportować postęp zgodnie z uprawnieniami.

### Metodyk

Wspiera jakość programów, treści i oceniania zgodnie z uprawnieniami.
Sama rola metodyka nie daje prawa do ręcznego obchodzenia progresji.

### Administrator

Obsługuje uprawnione procesy organizacyjne, użytkowników, grupy,
płatności, zwroty, incydenty, moderację i operacje administracyjne.
Operacje uprzywilejowane są audytowalne.

### Właściciel biznesowy

Michał Wanielista jest jedyną osobą ostatecznie zatwierdzającą decyzje
biznesowe, zakres produktu, wymagania oraz konkretne rewizje BA/SA.

## 4. Program edukacyjny

Nauczyciel publikuje konfigurowalny program. Nie ma globalnie narzuconej
klasy, wieku, liczby modułów, liczby lekcji, długości lekcji, wielkości
grupy, obowiązkowego egzaminu, globalnego progu zaliczenia ani jednego
sposobu ukończenia/progresji.

Program może definiować: nazwę, opis, przedmiot, grupę docelową,
rekomendowany wiek/klasę/poziom, wymagania wejściowe, efekty uczenia
się, etapy/moduły, lekcje, terminy, czas trwania, liczebność, materiały,
zadania, treningi, testy, egzaminy, kryteria oceniania, kryteria
ukończenia, progresję, cenę, zasady dostępu i rekomendowaną kontynuację.

Model „4 lekcje + egzamin" jest dopuszczalnym wariantem
programu/pilotażu, a nie strukturą całej platformy.

## 5. Publikacja i wersjonowanie

Program może być wersją roboczą i zostać opublikowany. Opublikowana
wersja musi być identyfikowalna. Dla uczestnictwa musi dać się ustalić
wersję programu, według której realizowano usługę. Zmiana programu nie
może niejawnie i retroaktywnie zmieniać istotnych warunków już
zakupionej usługi.

## 6. Cena, waluta i zakup

MVP sprzedaje wyłącznie w PLN. Cena jest konfigurowalna per
oferta/program. Kwota ma jawną walutę. Inne waluty są poza MVP, ale
model nie powinien uniemożliwiać ich późniejszego dodania.

Opiekun dokonuje zakupu. Przed zakupem zna ofertę, cenę brutto i istotne
warunki realizacji. Nieopłacona rezerwacja miejsca może być utrzymywana
maksymalnie 24 godziny. Po skutecznej płatności uczestnictwo jest
potwierdzone.

VAT, dokumenty sprzedażowe, finalne zasady odstąpienia/reklamacji i
podatki wymagają przeglądu przed sprzedażą produkcyjną i nie blokują SA.

## 7. Ukończenie

Egzamin nie jest globalnie obowiązkowy. Kryteria ukończenia definiuje
konkretna wersja programu/etapu i mogą obejmować wymagane lekcje,
zadania, wynik, test/egzamin, frekwencję lub inne jawne kryteria.

Jeśli program nie ma egzaminu ani dodatkowych kryteriów, ukończenie
następuje po realizacji wszystkich elementów oznaczonych jako wymagane.
Ukończenie nie oznacza automatycznie opanowania wszystkich efektów,
jeśli program nie ustanawia takiego kryterium.

## 8. Progresja i wyjątki

Nie ma globalnego obowiązku zdania egzaminu lub ukończenia poprzedniego
modułu przed przejściem dalej. Progresja jest konfigurowana dla wersji
programu i może nie być blokowana.

Wyjątek od skonfigurowanej progresji może przyznać: - nauczyciel
przypisany do prowadzenia danego programu/grupy; - uprawniony
administrator; - właściciel biznesowy.

Nauczyciel nie musi być autorem programu. Sama rola metodyka nie daje
tego uprawnienia. Wyjątek musi rejestrować osobę, uczestnika,
program/etap, czas i uzasadnienie.

## 9. Testy, egzaminy i poprawki

Program może posiadać test/egzamin i konfigurować próg, wymagania,
sposób oceny i inne zasady.

**Wszystkie poprawki i kolejne próby zaliczenia są bezpłatne.**

Zapisy o pierwszej darmowej poprawce, kolejnych za 100 PLN netto i
poprawkach jako źródle przychodu są SUPERSEDED.

Przy uzasadnionym podejrzeniu niesamodzielności wynik otrzymuje status
wymagający ręcznej weryfikacji i nie jest finalny. Weryfikuje uprawniony
nauczyciel lub administrator. Decyzja, osoba, czas i uzasadnienie są
audytowalne.

## 10. Zajęcia, zmiany i nieobecności

O zmianie terminu, odwołaniu lub istotnej zmianie organizacyjnej
uczestnik i opiekun są informowani przez platformę bez zbędnej zwłoki.
MVP nie ustanawia dodatkowego globalnego SLA.

Przy nieobecności nauczyciela organizator zapewnia zastępstwo albo nowy
termin. Przy awarii uniemożliwiającej zajęcia organizator zapewnia nowy
termin. Nieobecność uczestnika na prawidłowo zrealizowanych zajęciach
nie daje automatycznego prawa do zwrotu.

## 11. Frekwencja

Frekwencja uczestnika =
`obecności na zrealizowanych zajęciach live / zajęcia live, które powinny zostać zrealizowane dla uczestnika`.

Zajęcia odwołane przez organizatora i niezrealizowane nie wchodzą do
mianownika. Przełożone liczy się jeden raz.

Agregowana frekwencja =
`łączna liczba obecności / łączna liczba możliwych obecności na zrealizowanych zajęciach`.

## 12. Konsultacje

Dla aktywnego programu uczestnik może utworzyć jeden nowy wątek
konsultacyjny tygodniowo. Tydzień: `Europe/Warsaw`,
poniedziałek--niedziela. Limit nie przechodzi na kolejny tydzień.
Odpowiedzi w istniejącym wątku nie zużywają nowego limitu.

Komunikacja odbywa się na platformie, jest audytowalna/moderowalna i
widoczna dla uprawnionego opiekuna. Docelowy czas odpowiedzi
nauczyciela: maksymalnie 2 dni robocze. Wideokonsultacja 1:1 może być
osobnym produktem.

## 13. Materiały i postęp

Program może udostępniać materiały, zadania i treningi. Opiekun widzi
adekwatne informacje o obecności, realizacji wymaganych elementów,
wynikach i raportach.

Czas dostępu do materiałów może być konfigurowany przez ofertę/program.
Brak jednej globalnej wartości nie jest blockerem --- SA ma przewidzieć
możliwość konfiguracji.

## 14. Zmiana zakupionych warunków i zwroty

Istotna zmiana pogarszająca zakupione warunki wymaga akceptacji
opiekuna. Jeśli nie zostanie zaakceptowana i pierwotna realizacja jest
niemożliwa, organizator oferuje zaakceptowaną alternatywę albo zwrot za
niezrealizowaną część usługi. Jeśli świadczenie nie rozpoczęło się i nie
może zostać wykonane na zakupionych warunkach, zwrot obejmuje całą
zapłaconą kwotę za tę usługę.

Finalne zasady konsumenckie podlegają przeglądowi prawnemu.

## 15. Opiekun, bezpieczeństwo dzieci i nauczyciele

Osoba tworząca konto opiekuna oświadcza, że jest pełnoletnia, jest
uprawniona do działania wobec dziecka i podaje prawdziwe informacje.
Finalna treść oświadczeń/zgód zostanie zweryfikowana prawnie.

Komunikacja nauczyciela z dzieckiem dotycząca usługi odbywa się przez
kontrolowane kanały. Brak publicznych profili dzieci i otwartego
kontaktu niepowiązanych użytkowników. Obowiązuje minimalizacja danych.

Lekcje nie są domyślnie nagrywane. Ewentualne nagrywanie wymaga osobnego
celu, podstawy prawnej, dostępu, retencji i informacji dla uczestników.

Przed pracą z dziećmi nauczyciel przechodzi wymagane prawem weryfikacje,
dostarcza wymagane dokumenty/oświadczenia, poznaje standardy ochrony
małoletnich i zasady komunikacji oraz przechodzi szkolenia
bezpieczeństwa i platformy. Szczegół prawny/organizacyjny jest bramką
przed produkcją, nie blockerem SA.

## 16. Podstawowe funkcje MVP

MVP obejmuje co najmniej: - rejestrację/logowanie opiekuna; - profil
dziecka; - katalog ofert; - zapis, zakup i status płatności; -
harmonogram i dostęp do informacji potrzebnych do udziału w zajęciach; -
materiały, zadania i przesyłanie odpowiedzi; - testy/egzaminy, jeśli
program je przewiduje; - wyniki, postęp i raporty; - panel opiekuna,
uczestnika i nauczyciela; - podstawowe funkcje administracyjne; -
konsultacje asynchroniczne; - powiadomienia transakcyjne; - role,
uprawnienia i audyt.

Programy matematyczne wymagają obsługi treści matematycznych, w tym
wzorów/równań.

## 17. KPI MVP / pilota

Cele: - ukończenie ≥ 70%; - kontynuacja ≥ 60% kwalifikujących się
klientów w 60 dni; - agregowana frekwencja ≥ 80%; - średnia satysfakcja
opiekunów ≥ 4,2/5.

### Ukończenie

Mianownik: uczestnicy, którzy rozpoczęli mierzony program/etap. Licznik:
uczestnicy ze statusem ukończenia według kryteriów swojej wersji
programu.

### Kontynuacja

Klient kwalifikuje się, jeśli dziecko ukończyło wymagany etap, istnieje
opublikowana płatna logiczna kontynuacja i uczestnik spełnia jej warunki
wejściowe.

Okno 60 dni zaczyna się od późniejszej daty: ukończenia bieżącego etapu
albo udostępnienia możliwości zakupu kontynuacji. Brak odpowiedniej
oferty wyłącza klienta z mianownika.

### Satysfakcja

Ankieta po zakończeniu mierzonego programu/etapu. Jedna odpowiedź od
opiekuna głównego na uczestnictwo. Skala 1--5. Raport: średnia, liczba
wysłanych ankiet, liczba odpowiedzi, response rate.

## 18. NFR i ciągłość

MVP ma obsługiwać początkowo co najmniej 100 aktywnych rodzin i 10
równocześnie trwających zajęć. Model nie powinien wymagać fundamentalnej
przebudowy domeny, aby dojść do około 10 000 aktywnych rodzin i 200
równoczesnych zajęć.

Cel dostępności: **99,5% miesięcznie**.\
RPO: **maks. 24 h**.\
RTO: **maks. 4 h**.\
WCAG 2.2 AA: cel projektowy.

Wymagane są adekwatne: kontrola dostępu, audyt uprzywilejowanych
działań, backup, monitoring i ochrona danych.

## 19. Zakres dostępności 99,5%

Pomiar obejmuje funkcje kontrolowane przez eSzkola: -
logowanie/uwierzytelnienie; - katalog; - zakup i zapis; - panel opiekuna
i uczestnika; - podstawowe funkcje nauczyciela; - harmonogram; -
udostępnienie linku/informacji do zajęć; - materiały; - oddawanie
prac; - wyniki i raporty; - progresję; - konsultacje.

Awaria blokująca podstawowy proces wchodzi do pomiaru. Zapowiedziane
prace serwisowe mogą być wyłączone, jeśli użytkowników poinformowano co
najmniej 24 h wcześniej.

Awaria zewnętrznego dostawcy wideokonferencji nie jest automatycznie
niedostępnością eSzkola, jeśli funkcje kontrolowane przez eSzkola
działają. Szczegółową techniczną metodę pomiaru określa SA/architektura.

## 20. Powiadomienia i audyt

Platforma wspiera powiadomienia co najmniej o zakupie/płatności,
zapisie, istotnej zmianie lub odwołaniu zajęć i ważnych zdarzeniach
realizacji programu.

Audyt obejmuje co najmniej zmiany uprawnień, wyjątki progresji,
weryfikację niesamodzielności, istotne operacje administracyjne i
moderację wymagającą rozliczalności. Log powinien wskazywać kto, co i
kiedy zrobił oraz --- gdy wymagane --- dlaczego.

## 21. Kwestie prawne/podatkowe --- NON_BLOCKER dla SA

Przed właściwą bramką produkcyjną trzeba zatwierdzić m.in.: VAT,
dokumentowanie sprzedaży, regulamin, odstąpienia/reklamacje, politykę
prywatności, retencję, prawa osób, treść zgód/oświadczeń, prawne
kontrole nauczycieli, procedury ochrony małoletnich i ewentualną DPIA.

Nie są to BLOCKER-y dla SA, jeśli nie uniemożliwiają zaprojektowania
systemu. BA/SA nie mogą samodzielnie ustanawiać finalnego prawa,
podatków lub treści regulaminów.

## 22. Technologia i architektura

Historyczne rekomendacje Angular, Java/Spring Boot, PostgreSQL, S3,
Redis, modularny monolit, mikroserwisy, konkretny operator płatności lub
dostawca wideokonferencji nie są wymaganiami biznesowymi tylko dlatego,
że występowały w biznesplanie.

Dobór technologii należy do właściwego etapu SA/architektury zgodnie z
`AGENTS.md` i workflow.

## 23. Poza MVP

Poza obowiązkowym MVP pozostają, o ile późniejsza decyzja nie stanowi
inaczej: - natywna aplikacja mobilna; - własne WebRTC; - marketplace
nauczycieli; - publiczne profile dzieci; - otwarty czat między
uczniami; - decyzje o dziecku podejmowane wyłącznie przez AI; - wiele
walut; - mikroserwisy jako wymóg biznesowy; - zaawansowany AI tutor; -
rozpoznawanie odręcznych równań.

## 24. Hipotezy walidacyjne, nie wymagania globalne

Cztery lekcje, grupa 4--6 osób, cena 299/399/499 PLN, matematyka, klasy
5--6 i konkretny czas lekcji mogą być parametrami eksperymentu/pilotażu,
ale nie są globalnymi ograniczeniami platformy.

BA ma odróżniać hipotezy biznesowe od wymagań produktu.

## 25. Model przychodowy

Podstawowym źródłem przychodu jest sprzedaż płatnych programów/ofert. W
przyszłości możliwe są pakiety, oferta indywidualna premium, dodatkowe
konsultacje 1:1 i B2B.

**Poprawki i kolejne próby zaliczenia są bezpłatne i nie są źródłem
przychodu.**

## 26. Ryzyka i walidacja

Monitorowane ryzyka: zbyt duży system przed walidacją, nierówny poziom
uczestników, słaba jakość programów, brak nauczycieli, kontakt poza
platformą, wyciek danych dzieci, sezonowość, słaba ekonomika pozyskania,
niska retencja, nadużycia oceniania i zależność od pojedynczych
osób/dostawców.

Preferowany start to mały płatny pilotaż weryfikujący popyt, jakość,
ukończenie, frekwencję, satysfakcję, efekt edukacyjny, koszt obsługi,
ekonomię i kontynuację.

## 27. Zamknięcie Q-016

Q-016 jest **RESOLVED**.

Niniejszy dokument jednoznacznie rozstrzyga: wyjątki progresji i rolę
metodyka, PLN w MVP, kwalifikację do kontynuacji i start okna 60 dni,
ukończenie bez egzaminu, frekwencję, ankietę, zakres 99,5%, zmianę
zakupionych warunków, podejrzenie niesamodzielności, powiadomienia o
zmianach zajęć, oświadczenie opiekuna i wymagania wobec nauczyciela.

Nie należy tworzyć kolejnego BLOCKER-a wyłącznie dlatego, że historyczna
rewizja BA lub starszy biznesplan zawierały inne lub bardziej
szczegółowe ustalenie.

## 28. Gotowość do dalszej analizy

W zakresie, w którym Q-001--Q-015 dotyczyły tematów obecnie
jednoznacznie opisanych tutaj, obowiązuje niniejszy dokument. Q-016 ma
status RESOLVED.

Kwestie prawne, podatkowe, retencyjne i proceduralne mogą pozostać
NON_BLOCKER, jeśli nie uniemożliwiają SA.

Ten dokument jest wystarczającym aktualnym wsadem biznesowym do
przygotowania BA, a po zatwierdzeniu konkretnej rewizji BA --- SA. Nie
jest jednak approval konkretnego artefaktu. Approval nadal odbywa się
przez orchestrator, np.:

`factory approve ba --owner "Michał Wanielista"`

------------------------------------------------------------------------

# Załącznik A --- szablon programu

**Nazwa:**\
**Opis:**\
**Przedmiot:**\
**Grupa docelowa:**\
**Rekomendowany wiek/klasa/poziom:**\
**Wymagania wejściowe:**\
**Efekty uczenia się:**\
**Etapy/moduły:**\
**Lekcje i terminy:**\
**Czas trwania:**\
**Materiały:**\
**Zadania/trening:**\
**Test/egzamin (opcjonalny):**\
**Kryteria oceny:**\
**Kryteria ukończenia:**\
**Warunki progresji:**\
**Rekomendowana kontynuacja:**\
**Cena brutto:**\
**Waluta:** PLN\
**Minimalna/maksymalna liczba uczestników:**\
**Czas dostępu do materiałów:**\
**Dodatkowe zasady:**

# Załącznik B --- bramki przed produkcją

-   [ ] regulamin i warunki sprzedaży;
-   [ ] polityka prywatności;
-   [ ] VAT i dokumentowanie sprzedaży;
-   [ ] odstąpienia, reklamacje i zwroty;
-   [ ] zgody/oświadczenia opiekuna;
-   [ ] standardy ochrony małoletnich;
-   [ ] weryfikacja nauczycieli;
-   [ ] retencja danych;
-   [ ] umowy z dostawcami;
-   [ ] procedura incydentów;
-   [ ] backup i test odtworzenia;
-   [ ] monitoring i alerty;
-   [ ] testy bezpieczeństwa/uprawnień;
-   [ ] proces sytuacji wyjątkowych;
-   [ ] dashboard KPI.

# Załącznik C --- jawnie SUPERSEDED

Nie obowiązują: - „każdy program ma dokładnie 4 lekcje"; - „każdy
program ma obowiązkowy egzamin"; - „zaliczenie poprzedniego modułu jest
globalnym warunkiem kolejnego"; - „pierwsza poprawka jest darmowa,
kolejne kosztują 100 PLN netto"; - „płatne poprawki są źródłem
przychodu"; - „metodyk z samej roli może odblokować progresję"; -
„produkt jest globalnie ograniczony do klas 5--6"; - „technologie z
historycznego biznesplanu są wymaganiami biznesowymi".
