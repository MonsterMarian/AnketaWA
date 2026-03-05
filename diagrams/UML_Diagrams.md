# UML Diagramy - Dokumentace

Tento dokument obsahuje detailní UML diagramy pro aplikaci Anketa.

## 1. Class Diagram (Třídní schéma)
Diagram popisuje statickou strukturu backendu a vztahy mezi moduly.

```mermaid
classDiagram
    class FlaskApp {
        <<Singleton>>
        +run()
        +index() : render_template
        +about() : render_template
        +get_results() : JSON
        +vote(option_id) : JSON
        +reset(token) : JSON
    }
    class VoteStore {
        +VOTE_FILE: String
        +load_votes() : Map[String, Int]
        +save_votes(votes: Map) : void
    }
    class Config {
        +RESET_TOKEN: String
        +QUESTIONS: Map
        +VOTE_FILE: String
    }
    FlaskApp ..> VoteStore : "volá persistence layer"
    FlaskApp ..> Config : "načítá nastavení"
    VoteStore ..> Config : "používá cestu k souboru"
```

## 2. Sequence Diagram (Hlasovací proces)
Diagram ukazuje časovou souslednost zpráv při odesílání hlasu.

```mermaid
sequenceDiagram
    autonumber
    actor U as Uživatel (Prohlížeč)
    participant C as app.js
    participant S as app.py (Flask)
    participant D as votes.json

    U->>C: Výběr možnosti + Klik na "Odeslat"
    C->>S: POST /api/vote (JSON payload)
    activate S
    S->>S: Validace dat
    S->>D: Čtení aktuálních dat
    D-->>S: JSON data
    S->>S: Aktualizace počítadla
    S->>D: Zápis nových dat
    S-->>C: Response 200 OK (Nové stavy)
    deactivate S
    C->>U: Překreslení UI (Progress bars)
```

## 3. Workflow Diagram (Reset hlasování)
Zabezpečený proces vymazání výsledků.

```mermaid
sequenceDiagram
    actor A as Administrátor
    participant C as app.js
    participant S as app.py
    
    A->>C: Klikne na "Resetovat"
    C->>A: Prompt "Zadejte token"
    A-->>C: Token string
    C->>S: POST /api/reset (Header: Auth)
    alt Token je správný
        S->>S: Reset na nuly
        S-->>C: 200 OK + Nulová data
        C->>A: Alert "Vynulováno"
    else Token je chybný
        S-->>C: 401 Unauthorized
        C->>A: Alert "Nesprávný token"
    end
```
