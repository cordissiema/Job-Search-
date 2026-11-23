# Radar Ofert – procedura jednego uruchomienia

Strona z wynikami: https://claude.ai/artifact/7iyh96yvH6nYmEmAFa4TF2 (baza `db` tego artefaktu).
Repozytorium (gałąź `claude/japanese-learning-app-zm128y`) służy TYLKO do odczytu – nic nie commituj i nie pushuj (sesje zadania nie mają prawa zapisu). Cały stan trzymamy w bazie strony.
Narzędzie bazy: `ArtifactData` (załaduj: ToolSearch `select:ArtifactData`), zawsze z `url: https://claude.ai/artifact/7iyh96yvH6nYmEmAFa4TF2`.

## 1. Pobierz nowe oferty
1. Odczytaj listę widzianych ofert: `ArtifactData` `get`, `collection: "meta"`, `doc_id: "widziane"`, `out_dir: "/tmp/radar"`. Zapamiętaj jej `version` (jeśli dokument nie istnieje – brak wersji).
2. Uruchom (ścieżkę pliku weź z wyniku `get`; jeśli dokumentu nie było, pomiń `--seen-file`):
```
python3 job-watcher/fetch.py --max-age-days 3 --seen-file /tmp/radar/meta/widziane.json
```
Wynik trafia do `job-watcher/nowe.json`. Jeśli 0 nowych ofert: przejdź od razu do kroku 4 (zapisz tylko `meta/stan`), bez powiadomienia.
Jeśli skrypt zgłosi BŁĄD dla serwisu, zanotuj go w `meta/stan.bledy`.

## 1b. Odczytaj oceny użytkownika (👍/👎) i zaktualizuj preferencje
Użytkownik ocenia oferty na stronie: pole `kciuk` = `1` (👍 podoba się), `-1` (👎 nie dla mnie), `0`/brak = bez oceny. Dodatkowe sygnały: `status: "aplikowalem"` (silnie pozytywny), `otwarto` (otworzył ogłoszenie – słaby pozytywny), `status: "ukryta"` (słaby negatywny).
1. `ArtifactData` `query` na `oferty` z `where: [["kciuk","==",1]]`, `limit: 300`, `out_dir: "/tmp/radar"`; tak samo dla `-1` i dla `["status","==","aplikowalem"]`. Wystarczą pola: `tytul`, `firma`, `miejsce`, `stawka`, `podsumowanie`, `wymagania`, `ocena`, `parametry` nie są zapisywane – wnioskuj z tytułu i wymagań.
2. Wyciągnij wzorce: jakie branże/stanowiska, rodzaje pracy (fizyczna/biurowa/z ludźmi), systemy (zmiany, noce, weekendy), wymiar etatu, stawki, lokalizacje, typy pracodawców (agencje pracy, sieci, małe firmy) użytkownik lubi, a jakie odrzuca. Zwróć uwagę na rozbieżności: 👎 przy wysokiej ocenie Radaru = Radar przecenia ten typ; 👍 przy niskiej = niedocenia.
3. Zapisz podsumowanie w dokumencie `meta/preferencje` (najpierw `get`, potem `set` z `if_version`, jeśli istnieje): `{"tekst":"<3–8 krótkich punktów po polsku, np. ‘+ magazyn i sortownie, także na zmiany’, ‘− przedstawiciel handlowy na prowizji’>","polubione":<liczba 👍>,"niepolubione":<liczba 👎>,"aplikowane":<liczba>,"aktualizacja":"<ISO teraz>"}`. Gdy ocen jest 0 – pomiń zapis.
Te wnioski MAJĄ PIERWSZEŃSTWO przed „Preferencjami” z profilu, gdy są ze sobą sprzeczne (profil to założenia, oceny to realne wybory użytkownika). Twardych wymagań (uprawnienia, wykształcenie) oceny nie zmieniają.

## 2. Oceń każdą ofertę względem profilu kandydata (podanego w treści zadania – NIE zapisuj go w repozytorium, jest publiczne)
Przeczytaj profil z treści zadania. Dla każdej oferty z `nowe.json`:

**Szybka selekcja po tytule i parametrach.** Gdy oferta oczywiście nie pasuje (zawód wymagający uprawnień/wykształcenia, których kandydat nie ma, praca za granicą, poza okolicą Białegostoku – patrz „Odrzucaj” w profilu): `ocena` 0–19, jedno zdanie w `podsumowanie`, `wymagania` = 1–3 kluczowe wymagania.

**Pełna analiza dla pozostałych.** Przeczytaj cały opis. Wypisz WSZYSTKIE wymagania pracodawcy (sekcje „Wymagania”, „Oczekujemy”, „Szukamy osoby, która…”, wymogi ukryte w tekście: prawo jazdy, książeczka sanepid, doświadczenie, język, dyspozycyjność, praca zmianowa, wykształcenie). Dla każdego ustal:
- `"tak"` – CV to potwierdza (podaj w `n` krótko czym, np. „16 mies. jako operator maszyn offsetowych”),
- `"nie"` – CV jednoznacznie temu przeczy lub wymóg jest twardy i kandydat go nie ma,
- `"?"` – CV o tym milczy (np. prawo jazdy, sanepid, dyspozycyjność) – w `n` napisz, co trzeba potwierdzić.
Cechy osobowe (komunikatywność, odpowiedzialność, szybka nauka) oceniaj na podstawie CV i doświadczenia – zwykle `"tak"`.

**Ocena 0–100 = szansa na zaproszenie na rozmowę**, nie atrakcyjność oferty:
- 80–100: spełnia wszystkie twarde wymagania, ma pokrewne doświadczenie, oferta „bez doświadczenia / przyuczymy” lub doświadczenie wprost pasuje.
- 60–79: spełnia większość, braki miękkie lub do szybkiego uzupełnienia.
- 40–59: realna szansa, ale istotne `"?"` lub jeden brak.
- 20–39: wyraźne braki.
- 0–19: nie spełnia twardych wymogów / wykluczone preferencjami.
**Korekta wg ocen użytkownika (krok 1b):** oferta bardzo podobna do polubionych/aplikowanych (to samo stanowisko lub branża i podobne warunki) +10 do +20; podobna do 👎 −15 do −30. Gdy korekta zadziałała, dopisz to w `podsumowanie` (np. „Podobna do ofert, które oznaczyłeś 👍 (sortownie).”).
Kary: praca dorywcza/dodatkowa −10, brak stawki −5, odległość > 25 km −20. Ogłoszenia agencji o pracy za granicą z lokalizacją „Białystok” – traktuj jako zagraniczne.

`podsumowanie`: 1–2 zdania po polsku, konkretnie dlaczego taka ocena (np. „Twoje 16 mies. na produkcji w Smurfit Westrock pasuje wprost; jedyna niewiadoma to prawo jazdy kat. B.”).

## 3. Zapisz do bazy strony
Załaduj narzędzie `ArtifactData` (ToolSearch: `select:ArtifactData`). Jednym wywołaniem `action: "batch"` na `url: https://claude.ai/artifact/7iyh96yvH6nYmEmAFa4TF2` zapisz (`set`) każdą ofertę jako dokument `oferty/<id>` (np. `oferty/olx-1112498427`):
```json
{"tytul":"…","url":"…","zrodlo":"OLX","firma":"…","miejsce":"…","stawka":"…","dodano":"<ISO z nowe.json>",
 "znaleziono":"<ISO teraz>","ocena":72,"podsumowanie":"…",
 "wymagania":[{"t":"Doświadczenie na produkcji","s":"tak","n":"16 mies. Smurfit Westrock"},{"t":"Prawo jazdy kat. B","s":"?","n":"brak w CV – potwierdź"}],
 "status":"","kciuk":0}
```
Przy dużej liczbie ofert dziel na kilka wywołań `batch` (np. po 25). Nowe dokumenty zapisuj bez `if_version`; jeśli batch odrzuci wpis, bo dokument już istnieje – pomiń tę ofertę (jest już oceniona, a użytkownik mógł zmienić jej status).
Na końcu zaktualizuj dokument `meta/stan`: najpierw `get` (`collection: "meta"`, `doc_id: "stan"`); jeśli istnieje – `set` z `if_version` równym odczytanej `version`, jeśli nie – `set` bez `if_version`. Treść: `{"ostatnie":"<ISO teraz>","nowych":<liczba>,"wysokich":<liczba ≥70>,"bledy":"<tekst lub pusty>"}`.
Sprzątanie (tylko gdy bieżąca godzina UTC to 5:xx–6:xx): `query` na `oferty` z `where: [["status","==",""]]`, `limit: 1000`; dokumenty z `znaleziono` starszym niż 30 dni i bez `kciuk` (brak lub 0) usuń – ocenione kciukiem zostają na zawsze jako dane o preferencjach; `batch`em `delete`, podając dla każdego `if_version` z odczytu.

## 4. Oznacz oferty jako widziane
```
python3 job-watcher/fetch.py --mark-seen --seen-file /tmp/radar/meta/widziane.json --seen-out /tmp/radar/widziane-nowe.json
```
Potem `ArtifactData` `set`, `collection: "meta"`, `doc_id: "widziane"`, `file_path: "/tmp/radar/widziane-nowe.json"`, z `if_version` = wersja z kroku 1 (bez `if_version`, jeśli dokumentu nie było). Jeśli zapis odrzuci zmiana wersji – ponów krok 1 (`get`) i ten krok raz.
Rób to ZAWSZE, gdy były nowe oferty – inaczej następne uruchomienie oceni je ponownie.

## 5. Odpowiedź końcowa (to trafia do powiadomienia push)
- Jeśli są oferty z oceną ≥ 70: zacznij od „🔔 N nowych ofert z wysokimi szansami”, potem do 5 najlepszych w formacie `72 · Tytuł – Firma, stawka` + jedno zdanie dlaczego + link. Na końcu link do strony.
- Jeśli nie ma: jedno zdanie „Sprawdzono X nowych ofert, brak z wysokimi szansami.” – bez niczego więcej.
Nie wypisuj danych osobowych z CV.
