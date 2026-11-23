# Radar Ofert – procedura jednego uruchomienia

Strona z wynikami: https://claude.ai/artifact/7iyh96yvH6nYmEmAFa4TF2 (baza `db` tego artefaktu).
Pracuj na gałęzi `claude/japanese-learning-app-zm128y`.

## 1. Pobierz nowe oferty
```
git fetch origin claude/japanese-learning-app-zm128y && git checkout claude/japanese-learning-app-zm128y && git pull --ff-only
python3 job-watcher/fetch.py --max-age-days 3
```
Wynik trafia do `job-watcher/nowe.json`. Jeśli 0 nowych ofert: przejdź od razu do kroku 4 (zapisz tylko `meta/stan`), bez powiadomienia.
Jeśli skrypt zgłosi BŁĄD dla serwisu, zanotuj go w `meta/stan.bledy`.

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
Kary: praca dorywcza/dodatkowa −10, brak stawki −5, odległość > 25 km −20. Ogłoszenia agencji o pracy za granicą z lokalizacją „Białystok” – traktuj jako zagraniczne.

`podsumowanie`: 1–2 zdania po polsku, konkretnie dlaczego taka ocena (np. „Twoje 16 mies. na produkcji w Smurfit Westrock pasuje wprost; jedyna niewiadoma to prawo jazdy kat. B.”).

## 3. Zapisz do bazy strony
Załaduj narzędzie `ArtifactData` (ToolSearch: `select:ArtifactData`). Jednym wywołaniem `action: "batch"` na `url: https://claude.ai/artifact/7iyh96yvH6nYmEmAFa4TF2` zapisz (`set`) każdą ofertę jako dokument `oferty/<id>` (np. `oferty/olx-1112498427`):
```json
{"tytul":"…","url":"…","zrodlo":"OLX","firma":"…","miejsce":"…","stawka":"…","dodano":"<ISO z nowe.json>",
 "znaleziono":"<ISO teraz>","ocena":72,"podsumowanie":"…",
 "wymagania":[{"t":"Doświadczenie na produkcji","s":"tak","n":"16 mies. Smurfit Westrock"},{"t":"Prawo jazdy kat. B","s":"?","n":"brak w CV – potwierdź"}],
 "status":""}
```
Przy dużej liczbie ofert dziel na kilka wywołań `batch` (np. po 25). Nowe dokumenty zapisuj bez `if_version`; jeśli batch odrzuci wpis, bo dokument już istnieje – pomiń tę ofertę (jest już oceniona, a użytkownik mógł zmienić jej status).
Na końcu zaktualizuj dokument `meta/stan`: najpierw `get` (`collection: "meta"`, `doc_id: "stan"`); jeśli istnieje – `set` z `if_version` równym odczytanej `version`, jeśli nie – `set` bez `if_version`. Treść: `{"ostatnie":"<ISO teraz>","nowych":<liczba>,"wysokich":<liczba ≥70>,"bledy":"<tekst lub pusty>"}`.
Sprzątanie (tylko gdy bieżąca godzina UTC to 5:xx–6:xx): `query` na `oferty` z `where: [["status","==",""]]`, `limit: 1000`; dokumenty z `znaleziono` starszym niż 30 dni usuń `batch`em `delete`, podając dla każdego `if_version` z odczytu.

## 4. Oznacz oferty jako widziane i zapisz
```
python3 job-watcher/fetch.py --mark-seen
git add job-watcher/seen.json && git commit -m "Radar: widziane oferty" && git push origin claude/japanese-learning-app-zm128y
```
(`nowe.json` nie commituj.) Jeśli push zostanie odrzucony: `git pull --rebase` i ponów.

## 5. Odpowiedź końcowa (to trafia do powiadomienia push)
- Jeśli są oferty z oceną ≥ 70: zacznij od „🔔 N nowych ofert z wysokimi szansami”, potem do 5 najlepszych w formacie `72 · Tytuł – Firma, stawka` + jedno zdanie dlaczego + link. Na końcu link do strony.
- Jeśli nie ma: jedno zdanie „Sprawdzono X nowych ofert, brak z wysokimi szansami.” – bez niczego więcej.
Nie wypisuj danych osobowych z CV.
