# AnketaWA

Tento repozitář obsahuje ukázkový projekt webové ankety vytvořený jako cvičení z předmětu WA (Webové aplikace). Systém umožňuje sbírat hlasy uživatelů v reálném čase.

## O projektu

Aplikace je postavena na:
- **Backend:** Python s využitím frameworku Flask
- **Frontend:** HTML, CSS, a čistý JavaScript (s využitím Chart.js pro vizualizaci výsledků)
- **Data:** Získávané hlasy a logy jsou ukládány do lokálních JSON a TXT souborů se zajištěním proti souběhu (`filelock`).
- **Bezpečnost:** Aplikace obsahuje vlastní ochranu proti opakovanému hlasování z jedné IP adresy a využívá hlavičky pro základní webové zabezpečení.

Cílem projektu je demonstrovat vytvoření kompletní full-stack aplikace, od responzivního designu frontendu po zpracování dat na serveru a navázání administrátorského rozhraní.

## Instalace a spuštění lokálně

Pokud si chceš projekt zprovoznit lokálně na svém počítači:

1. **Naklonuj tento repozitář:**
   ```bash
   git clone https://github.com/MonsterMarian/AnketaWA.git
   cd AnketaWA
   ```
2. **Vytvoř si virtuální prostředí a nainstaluj závislosti:**
   ```bash
   python -m venv venv
   # Aktivace (Windows):
   venv\Scripts\activate
   # nebo (Mac/Linux):
   source venv/bin/activate
   
   pip install -r requirements.txt
   ```
3. **Spusť aplikaci:**
   ```bash
   python flask_app.py
   ```
4. Aplikace by měla běžet na portu 5000: `http://127.0.0.1:5000`

## Nahlašování chyb

Prosím o **nahlašování chyb a problémů** (issues) přímo v sekci [Issues na GitHubu](https://github.com/MonsterMarian/AnketaWA/issues). Na základě hlášení budou zjednány případné opravy či vylepšení. Děkuji!
