# Wireframe - Webová Anketa

Tento dokument obsahuje vizuální a strukturní návrh (wireframe) uživatelského rozhraní aplikace.

## 1. Koncepční schéma (Mermaid UI Flow)
Diagram ukazuje, jak jsou prvky na stránce uspořádány a jak se mění stav UI.

```mermaid
graph TD
    subgraph "Hlavní kontejner (Card)"
        H1[Nadpis: Otázka o záložkách]
        
        subgraph "Hlasovací Blok"
            R1(Option 1: 0-5)
            R2(Option 2: 6-20)
            R3(Option 3: 21+)
            R4(Option 4: Můj prohlížeč taje)
            B1[Tlačítko: Odeslat hlas]
            B2[Link: Zobrazit výsledky bez hlasování]
        end

        subgraph "Blok Výsledků (Schovaný defaultně)"
            P1[Progress Bar 1 + Počet hlasů]
            P2[Progress Bar 2 + Počet hlasů]
            P3[Progress Bar 3 + Počet hlasů]
            P4[Progress Bar 4 + Počet hlasů]
            B3[Tlačítko: Zpět k hlasování]
            B4[Tlačítko: Reset (Admin)]
        end
        
        F1[Patička: Copyright + Link O anketě]
    end

    B1 --> Blok_Výsledků
    B2 --> Blok_Výsledků
    B3 --> Hlasovací_Blok
```

## 2. Detailní popis prvků

### Hlavní stránka (`index.html`)
*   **Šablona**: Glassmorphism karta uprostřed obrazovky.
*   **Interaktivita**: 
    *   Výběr pomocí custom stylizovaných radio buttonů (celá plocha řádku je klikatelná).
    *   Přechody mezi hlasováním a výsledky jsou řešeny pomocí JavaScriptu (přepínání `display: block/none`) pro okamžitou odezvu bez refreshování stránky.
*   **Výsledky**: Dynamické progress bary, kde šířka odpovídá procentuálnímu podílu hlasů.

### Stránka O anketě (`about.html`)
*   **Obsah**: Čistý textový layout v podobné kartě jako hlavní stránka.
*   **Navigace**: Výrazné tlačítko "Zpět na hlavní stránku".

### Responzivita
*   Aplikace je navržena jako **Mobile-First**. Na mobilu se karta roztáhne na celou šířku, na desktopu zůstane centrovaný box o šířce 600px.

---

## 3. Wireframe - Resetovací Dialog
Při kliknutí na "Resetovat" se neotevírá nová stránka, ale systémové okno `prompt()`, které vyžaduje zadání tokenu. To zajišťuje maximální jednoduchost pro administrátora.
