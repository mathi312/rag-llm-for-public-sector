# User Manual

## Ziel

Dieses Manual beschreibt, wie das Projekt nach einem frischen `git clone` lokal gestartet wird, wie die Anwendung verwendet wird und welche typischen Betriebs- und Fehlerfälle zu beachten sind.

Die Anleitung ist auf den lokalen Entwicklungsstart mit Docker ausgelegt.

## Voraussetzungen

Vor dem Start sollten diese Tools installiert sein:

- `git`
- `Docker Desktop` inklusive `docker compose`

Optional, aber hilfreich:

- ein OpenAI API Key, falls nicht mit lokalem Ollama gearbeitet werden soll

### Empfohlene Systemressourcen

- mindestens `8 GB RAM`
- empfohlen `16 GB RAM`, wenn lokale Modelle über Ollama verwendet werden
- mindestens `10 GB` freier Speicherplatz für Images, Container, Indizes und Modelle

## 1. Repository klonen

```powershell
git clone <REPOSITORY_URL>
cd <geklonter-ordner>
```

Falls das Projekt schon geklont wurde, reicht ein `cd` in den Projektordner.

## 2. Projektstruktur in Kürze

Für den lokalen Start sind vor allem diese Dateien und Ordner wichtig:

- `docker-compose.yml`: Basisdefinition der Services
- `docker-compose.dev.yml`: lokale Entwicklungsports und MailHog
- `.env.example`: Vorlage für lokale Umgebungsvariablen
- `data/`: statische Dokumente für den Index
- `faiss_index/`: gespeicherter Vektorindex
- `logs/`: erzeugte Logdateien
- `pocketbase-data/`: persistente PocketBase-Daten
- `pocketbase/pb_migrations/`: versionierte PocketBase-Migrationen

## 3. Umgebungsvariablen anlegen

Die App erwartet eine lokale `.env`-Datei. Am einfachsten ist es, die Vorlage zu kopieren:

```powershell
cp .env.example .env
```

Danach die `.env` anpassen.

### Empfohlene Werte für die lokale Entwicklung

```env
APP_ENV=development
POCKETBASE_ADMIN_USERNAME=<email>
POCKETBASE_ADMIN_PASSWORD=<passwort>
SMTP_HOST=
SMTP_PORT=
SMTP_USER=
SMTP_PASSWORD=
```

### Bedeutung der wichtigsten Variablen

- `APP_ENV=development` aktiviert die lokale Entwicklungslogik.
- `POCKETBASE_ADMIN_USERNAME` und `POCKETBASE_ADMIN_PASSWORD` werden von der App verwendet, um sich serverseitig gegen PocketBase zu authentifizieren.
- `SMTP_HOST` und `SMTP_PORT` werden lokal mit MailHog nicht benötigt.
- `SMTP_USER` und `SMTP_PASSWORD` werden lokal mit MailHog nicht benötigt.

### Welche Werte sind Pflicht?

Für einen funktionsfähigen lokalen Start mit PocketBase und MailHog sind diese Variablen Pflicht:

- `APP_ENV`
- `POCKETBASE_ADMIN_USERNAME`
- `POCKETBASE_ADMIN_PASSWORD`
- `SMTP_HOST`
- `SMTP_PORT`

Für den lokalen OpenAI-Betrieb ist kein zusätzlicher `.env`-Eintrag nötig. Der OpenAI API Key wird in der App im Administrationsbereich eingegeben.

## 4. Container bauen

Die Entwicklungsumgebung wird mit der Basisdatei und dem Dev-Override gebaut:

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml build
```

Der erste Build kann etwas dauern, weil unter anderem Python-Abhängigkeiten und Playwright installiert werden.

## 5. Container starten

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

Damit werden diese Services gestartet:

- `rag-app` auf Port `8501`
- `ollama` auf Port `11434`
- `pocketbase` auf Port `8080`
- `mailhog` auf Port `8025`

## 6. Lokales Ollama-Modell laden

Beim ersten Start ist in Ollama noch kein Modell vorhanden. Für den lokalen Betrieb muss deshalb mindestens ein Modell geladen werden, zum Beispiel `llama3.2`:

```powershell
docker exec -it ollama ollama pull llama3.2
```

Ohne diesen Schritt startet zwar die Umgebung, aber lokale Chat-Anfragen können nicht verarbeitet werden.

Alternativ können auch andere in der App auswählbare lokale Modelle geladen werden, zum Beispiel:

- `llama3`
- `mistral`

## 7. PocketBase-Superuser anlegen

Wenn `pocketbase-data` noch leer ist, muss einmalig ein PocketBase-Superuser erstellt werden:

```powershell
docker exec -it pocketbase /pb/pocketbase superuser create admin@example.com change_me_please
```

Wichtig:

- Die Zugangsdaten sollten zu `POCKETBASE_ADMIN_USERNAME` und `POCKETBASE_ADMIN_PASSWORD` aus der `.env` passen.
- Dieser Superuser ist für die serverseitige Verwaltung durch die App nötig.
- Zusätzlich können in PocketBase normale Benutzerkonten für die Anwendung angelegt werden.

## 8. App aufrufen

Nach dem Start ist die Anwendung hier erreichbar:

- App: `http://localhost:8501`
- PocketBase Admin UI: `http://127.0.0.1:8080/_/`
- MailHog UI: `http://127.0.0.1:8025`

## 9. Erste Funktionsprüfung

Wenn alles korrekt läuft, sollte Folgendes funktionieren:

1. `http://localhost:8501` öffnet die Streamlit-App.
2. `http://127.0.0.1:8080/_/` öffnet das PocketBase-Dashboard.
3. `http://127.0.0.1:8025` öffnet MailHog.
4. Der Befehl `docker ps` zeigt alle benötigten Container als laufend an.
5. In der App lässt sich die Seite `User -> Login` aufrufen.

## 10. Anmeldung und Rollen

Die Anwendung kennt zwei relevante Rollen:

- normale Benutzer
- Administratoren

### Normale Benutzer

Normale Benutzer können sich anmelden und die Chatfunktionen der Anwendung verwenden. In der Sidebar sehen sie nur den Bereich `General`.

### Administratoren

Administratoren sehen zusätzlich:

- den Sidenav Bereich `Administration`
- die oberen Navigationseinträge für den Dokumentenmanager
- die oberen Navigationseinträge für den Logmanager

### Login

Die Anmeldung erfolgt über den oberen Navigationseintrag `User -> Login`. Hierzu werden die in PocketBase angelegten Benutzerdaten verwendet.

Nach erfolgreichem Login werden adminbezogene Seiten und Funktionen nur dann sichtbar, wenn das Benutzerkonto Adminrechte besitzt.

## 11. Verwendung der Applikation

## 11.1. PocketBase

### Accounts verwalten

Sobald ein Superuser für PocketBase erstellt wurde, ist es möglich, in PocketBase Benutzerkonten für die RAG-LLM-Anwendung anzulegen. In der Benutzerverwaltung können die Benutzer ebenfalls bearbeitet und gelöscht werden.

## 11.2. RAG-LLM-Anwendung

### Sidebar

Die Sidebar stellt Informationen und Funktionen bezüglich des Chatbots zur Verfügung. Hierbei wird zwischen `General` und `Administration` unterschieden.

#### General

Im Bereich `General` ist es möglich:

- den eigenen Loginstatus einzusehen
- einen Ausweis hochzuladen
- einen Report zu generieren

#### Administration

Der Bereich `Administration` ist nur für eingeloggte Admins sichtbar. Dort ist es möglich:

- den KI-Provider zu wählen
- das Modell zu ändern
- statische Dokumente aus `data/` einzubeziehen
- temporäre Dokumente hochzuladen
- Webseiteninhalte per URL hinzuzufügen
- den Index neu aufzubauen oder einen bestehenden Index weiterzuverwenden

### Hauptansicht

In der Hauptansicht sieht man einen chatähnlichen Aufbau. Über das Eingabefeld am unteren Seitenrand können Fragen an den digitalen Assistenten gestellt werden.

Zusätzlich stehen diese Funktionen zur Verfügung:

- `New Questions`: lädt neue vorgefertigte Fragen
- `New chat`: startet einen neuen Chat, ohne den bestehenden Index zu löschen

### Quellen und Antworten

Antworten können mit Quellenhinweisen dargestellt werden. Die eingeblendeten Quellbuttons öffnen den zugehörigen Kontextinhalt.

### Ausweis hochladen

Im Bereich `General` kann ein Ausweisbild hochgeladen werden. Falls der Typ des Ausweises nicht automatisch erkannt wird, kann er manuell ausgewählt werden.

### Report erzeugen

Über `Print Report` wird ein Gesprächsreport erzeugt. Falls der Drucker nicht verfügbar ist, kann der Report alternativ per E-Mail versendet werden.

Im lokalen Entwicklungsmodus wird der Versand über MailHog abgewickelt.

## 11.3. Dokumentenmanager

Als Administrator hat man Zugriff auf eine eigene Seite für den Dokumentenmanager.

Im Dokumentenmanager können Dokumente:

- hochgeladen
- bearbeitet
- angesehen
- gelöscht

Zusätzlich kann für ein Dokument angegeben werden, welche Ausweisarten dafür benötigt werden. Für vorhandene Dokumente können außerdem vorgefertigte Fragen aus dem Dokumentkontext generiert werden.

## 11.4. Logmanager

Als Administrator hat man Zugriff auf eine eigene Seite für den Logmanager.

Im Logmanager können tägliche Logs:

- eingesehen
- heruntergeladen
- gelöscht

## 12. Dokumente und Index-Workflow

Die Anwendung arbeitet mit einem Vektorindex. Dokumente können auf drei Arten in die Wissensbasis eingebracht werden:

- als statische Dateien im Ordner `data/`
- als temporäre Uploads in der App
- als Webseiteninhalte über URL-Eingabe

### Wichtiger Ablauf

Nach jeder relevanten Änderung an den Dokumentquellen sollte der Index neu aufgebaut oder aktualisiert werden.

Typischer Ablauf:

1. Dokumente in `data/` ablegen oder in der App hochladen.
2. Optional URLs im Bereich `Administration` hinzufügen.
3. In der App `Build / Update Index` ausführen.
4. Erst danach Fragen an den Assistenten stellen.

### Wann muss der Index neu gebaut werden?

Ein Neuaufbau ist insbesondere nötig:

- nach neu hinzugefügten Dokumenten
- nach geänderten Dokumenten
- nach neu hinzugefügten URLs
- nach einem Wechsel des Providers oder Embedding-Modells

## 13. Lokaler Betrieb mit Ollama

Für den reinen lokalen Betrieb wird `Local (Ollama)` als Provider verwendet.

Empfohlener Ablauf:

1. Modell in Ollama laden, zum Beispiel `llama3.2`.
2. In der Anwendung als Provider `Local (Ollama)` wählen.
3. Ein verfügbares lokales Modell auswählen.
4. Den Index aufbauen.
5. Chat verwenden.

## 14. Betrieb mit OpenAI

Die Anwendung kann alternativ mit OpenAI verwendet werden.

### Voraussetzungen

- gültiger OpenAI API Key
- Adminrechte in der Anwendung, damit der Bereich `Administration` sichtbar ist

### Ablauf

1. In der Anwendung den Bereich `Administration` öffnen.
2. Als Provider `OpenAI` auswählen.
3. Den OpenAI API Key im Eingabefeld eintragen.
4. Ein Modell auswählen.
5. Den Index neu aufbauen, damit Embeddings und Modellkonfiguration konsistent sind.

Hinweis:

- Wenn von `Local (Ollama)` auf `OpenAI` oder zurück gewechselt wird, sollte der Index neu aufgebaut werden.

## 15. Persistenz und Datenablage

Die lokale Entwicklungsumgebung speichert Daten an mehreren Stellen:

- `data/`: statische Eingabedokumente
- `faiss_index/`: persistierter Suchindex
- `logs/`: Logdateien der Anwendung
- `pocketbase-data/`: PocketBase-Datenbank und Dateien
- Docker Volume `ollama_data`: lokal geladene Ollama-Modelle

Das bedeutet:

- Nach einem Container Neustart bleiben diese Daten erhalten.
- Bei einem kompletten Löschen dieser Ordner oder Volumes müssen Teile der Umgebung neu aufgebaut werden.

## 16. PocketBase Migrationen

PocketBase Migrationen liegen im Ordner `pocketbase/pb_migrations/`.

Wenn Collections oder Regeln im PocketBase Dashboard geändert werden, sollte anschließend eine Snapshot Migration erzeugt werden:

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec pocketbase /pb/pocketbase migrate collections
```

Empfohlener Ablauf im Team:

1. Schema oder Regeln im PocketBase Dashboard ändern.
2. Den Befehl `migrate collections` ausführen.
3. Die neu erzeugte Datei in `pocketbase/pb_migrations/` committen.
4. Container neu starten oder neu bauen, falls nötig.

Auf einer frischen Umgebung mit leerem `pocketbase-data` werden offene Migrationen beim Start automatisch angewendet.

## 17. Tests

Für das Projekt existieren Unit- und Integrationstests.

### Unit-Tests ausführen

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile unit-test run --rm rag-app-test
```

### Integrationstests ausführen

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile integration-test run --rm rag-app-integration-test
```

### Test-Coverage erzeugen

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml run --rm --entrypoint "" rag-app-test python -m coverage run -m pytest tests/unit
docker compose -f docker-compose.yml -f docker-compose.dev.yml run --rm --entrypoint "" rag-app-test python -m coverage report -m
docker compose -f docker-compose.yml -f docker-compose.dev.yml run --rm --entrypoint "" rag-app-test python -m coverage html
```

Dabei wird ein Ordner `coverage_html_report/` erzeugt.

## 18. Nützliche Befehle

### Logs ansehen

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f
```

### Umgebung stoppen

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml down
```

### Umgebung neu bauen und starten

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml down
docker compose -f docker-compose.yml -f docker-compose.dev.yml build --no-cache
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

## 19. Typische Probleme

### App startet, aber lokale Antworten funktionieren nicht

Wahrscheinlich wurde noch kein Ollama-Modell geladen.

Lösung:

```powershell
docker exec -it ollama ollama pull llama3.2
```

### Kein Chat möglich, weil kein Index vorhanden ist

Wenn noch kein Index gebaut wurde, kann die App keine Dokumentfragen beantworten.

Lösung:

1. Dokumente bereitstellen.
2. Im Bereich `Administration` `Build / Update Index` ausführen.

### PocketBase-Fehler beim App-Start

Oft passen die Admin-Zugangsdaten in `.env` nicht zu dem existierenden PocketBase Superuser.

Prüfen:

- stimmen `POCKETBASE_ADMIN_USERNAME` und `POCKETBASE_ADMIN_PASSWORD`?
- wurde der Superuser in PocketBase wirklich mit diesen Daten angelegt?

### Login funktioniert nicht

Mögliche Ursachen:

- der Benutzer wurde in PocketBase noch nicht angelegt
- E-Mail oder Passwort sind falsch
- der Benutzer ist kein Admin, obwohl Adminfunktionen erwartet werden

### Adminfunktionen fehlen

Wenn `Administration`, Dokumentenmanager oder Logmanager nicht sichtbar sind, ist das Konto entweder:

- nicht eingeloggt
- kein Adminkonto

### Mail Versand funktioniert lokal nicht

Für die Entwicklungsumgebung sollten in `.env` diese Werte gesetzt sein:

```env
APP_ENV=development
```

Zusätzlich sollte geprüft werden, ob MailHog läuft und unter `http://127.0.0.1:8025` erreichbar ist.

### OpenAI funktioniert nicht

Mögliche Ursachen:

- kein API Key eingetragen
- ungültiger API Key
- Provider wurde gewechselt, aber der Index wurde nicht neu aufgebaut

### Ports sind schon belegt

Wenn `8501`, `8080`, `8025` oder `11434` lokal bereits verwendet werden, müssen die belegenden Prozesse beendet oder die Port-Mappings in den Compose Dateien angepasst werden.

## 20. Kurzfassung

Wer nur die Minimalversion braucht, kommt mit diesen Schritten ans Ziel:

1. Repo klonen und in den Ordner wechseln.
2. `.env.example` nach `.env` kopieren und Werte setzen.
3. `docker compose -f docker-compose.yml -f docker-compose.dev.yml build`
4. `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d`
5. `docker exec -it ollama ollama pull llama3.2`
6. Falls nötig: `docker exec -it pocketbase /pb/pocketbase superuser create <mail> <passwort>`
7. `http://localhost:8501` im Browser öffnen.
8. Als Admin anmelden.
9. Dokumente bereitstellen und `Build / Update Index` ausführen.
10. Danach den Chat verwenden.
