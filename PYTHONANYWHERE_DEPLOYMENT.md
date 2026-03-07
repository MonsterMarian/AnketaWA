# Návod na nasazení na PythonAnywhere

Tento návod popisuje, jak krok za krokem nasadit aplikaci AnketaWA na webový hosting PythonAnywhere zdarma.

## 1. Příprava účtu
1. Zaregistrujte se (nebo se přihlaste) na [PythonAnywhere](https://www.pythonanywhere.com/).
2. Po přihlášení přejděte na záložku **Web** a klikněte na **Add a new web app**.
3. Při výběru frameworku zvolte **Flask** a vaši preferovanou verzi Pythonu (např. Python 3.10).
4. Do cesty projektu (např. `/home/vasejmeno/mysite`) můžete nechat defaultní cestu, případně si ji přejmenovat na `/home/vasejmeno/AnketaWA`. Rozbalte, vytvořte a dokončete inicializaci webu.

## 2. Nahrání souborů
Přejděte na záložku **Files**. Abyste nemuseli nahrávat soubory po jednom, doporučujeme na vašem PC vytvořit `.zip` archiv ze složky projektu, ten nahrát a v konzoli na PythonAnywhere rozbalit.

Pokud nahráváte ručně nebo používáte GitHub, na serveru **musí být tyto soubory a složky**:

- `flask_app.py` (hlavní kód aplikace)
- `config.py` (nastavení aplikace)
- `requirements.txt` (seznam knihoven)
- Složka `templates/` (a všechny HTML soubory uvnitř)
- Složka `static/` (a všechny CSS/JS/SVG soubory uvnitř)
- Složka `data/` se vytvoří sama po prvním spuštění (nebo si ji předpřipravte prázdnou).

## 3. Instalace závislostí
1. V záložce **Consoles** si otevřete nový **Bash** terminál.
2. Běžte do složky vašeho projektu:
   ```bash
   cd /home/vasejmeno/AnketaWA
   ```
   *(nahraďte `vasejmeno/AnketaWA` vaší reálnou cestou)*
3. Nainstalujte potřebné závislosti ze souboru:
   ```bash
   pip3 install --user -r requirements.txt
   ```

## 4. Propojení aplikace (WSGI konfigurace)
Základní webová aplikace PythonAnywhere by mohla očekávat jiný název souboru. Aby věděla, že má brát náš `flask_app.py`:

1. Vraťte se do záložky **Web**.
2. V sekci **Code** najděte položku **WSGI configuration file** a klikněte na odkaz.
3. Upravte kód tak, aby nahoře v importech bylo správně vloženo vaše Flask app:
   ```python
   import sys
   # Přidejte cestu k vašemu projektu
   path = '/home/vasejmeno/AnketaWA'
   if path not in sys.path:
       sys.path.append(path)

   # Importujte vaši Flask instanci
   from flask_app import app as application
   ```
   *Poznámka: Nezapomeňte smazat nebo zakomentovat ostatní ukázkový kód z toho souboru, např. ten se standardním `flask_app` nebo `hello_world`.*

## 5. Spuštění a Reload
1. Uložte změny v editoru WSGI souboru.
2. Běžte opět zpět na záložku **Web** a klikněte na velké zelené tlačítko **Reload vasejmeno.pythonanywhere.com**.
3. Otevřete si odkaz na vaši webovou stránku a anketa by tam měla běžet plně funkční!
