# AnketaWA

Tento repozitář obsahuje ukázkový projekt webové ankety vytvořený jako cvičení pro předmět **Webové aplikace (WA)**. Systém umožňuje sbírat hlasy uživatelů v reálném čase.

Aplikace je aktuálně **hostovaná v produkci na platformě PythonAnywhere**.

## O projektu

Aplikace je postavena na:
- **Backend:** Python s využitím frameworku Flask
- **Frontend:** HTML, CSS, a čistý JavaScript (s využitím Chart.js pro vizualizaci výsledků)
- **Data:** Získávané hlasy a logy jsou ukládány do lokálních JSON a TXT souborů se zajištěním proti souběhu (`filelock`).
- **Bezpečnost:** Aplikace obsahuje vlastní ochranu proti opakovanému hlasování z jedné IP adresy a využívá hlavičky pro základní webové zabezpečení.

Cílem projektu je demonstrovat vytvoření kompletní full-stack aplikace, od responzivního designu frontendu po zpracování dat na serveru a navázání administrátorského rozhraní.

## Nahlašování chyb

Prosím o **nahlašování chyb a problémů** (issues) přímo v sekci [Issues na GitHubu](https://github.com/MonsterMarian/AnketaWA/issues). Na základě hlášení budou zjednány případné opravy či vylepšení. Děkuji!
