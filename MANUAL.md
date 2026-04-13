# User Manual

## Ziel

Dieses Manual beschreibt, wie man das Projekt nach einem frischen `git clone` lokal startet und die App das erste Mal erfolgreich aufruft.
Die Anleitung ist auf den lokalen Entwicklungsstart mit Docker ausgelegt.

Außerdem wird hier beschrieben, wie die Anwendung zu verwenden ist.

## Voraussetzungen

Vor dem Start sollten diese Tools installiert sein:

- `git`
- `Docker Desktop` inklusive `docker compose`

Optional, aber hilfreich:

- ein OpenAI API Key, falls nicht mit lokalem Ollama gearbeitet werden soll

## 1. Repository klonen

```powershell
git clone <REPOSITORY_URL>
cd rag-llm
```

Falls das Projekt schon geklont wurde, reicht natürlich ein `cd` in den Projektordner.

## 2. Umgebungsvariablen anlegen

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
SMTP_HOST=mailhog
SMTP_PORT=
SMTP_USER=
SMTP_PASSWORD=
```

Hinweise:

- `APP_ENV=development` sorgt dafür, dass lokale Entwicklungslogik aktiv ist.
- Für Development ist `mailhog` die passende SMTP-Konfiguration, weil der Service in `docker-compose.dev.yml` bereits enthalten ist.
- `POCKETBASE_ADMIN_USERNAME` und `POCKETBASE_ADMIN_PASSWORD` werden von der App verwendet, um sich serverseitig gegen PocketBase zu authentifizieren.

## 3. Container bauen

Die Entwicklungsumgebung wird mit der Basisdatei und dem Dev-Override gebaut:

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml build
```

Der erste Build kann etwas dauern, weil unter anderem Python-Abhängigkeiten und Playwright installiert werden.

## 4. Container starten

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

Damit werden diese Services gestartet:

- `rag-app` auf Port `8501`
- `ollama` auf Port `11434`
- `pocketbase` auf Port `8080`
- `mailhog` auf Port `8025`

## 5. Lokales Ollama-Modell laden

Beim ersten Start ist in Ollama noch kein Modell vorhanden. Für den lokalen Betrieb muss deshalb mindestens ein Modell geladen werden, zum Beispiel `llama3.2`:

```powershell
docker exec -it ollama ollama pull llama3.2
```

Ohne diesen Schritt startet zwar die Umgebung, aber lokale Chat-Anfragen können nicht verarbeitet werden.

## 6. PocketBase-Superuser anlegen

Wenn `pocketbase-data` noch leer ist, muss einmalig ein PocketBase-Superuser erstellt werden:

```powershell
docker exec -it pocketbase /pb/pocketbase superuser create admin@example.com change_me_please
```

Wichtig:

- Die Zugangsdaten sollten zu `POCKETBASE_ADMIN_USERNAME` und `POCKETBASE_ADMIN_PASSWORD` aus der `.env` passen.
- Dieser Superuser ist für die serverseitige Verwaltung durch die App nötig.

## 7. App aufrufen

Nach dem Start ist die Anwendung hier erreichbar:

- App: `http://localhost:8501`
- PocketBase Admin UI: `http://127.0.0.1:8080/_/`
- MailHog UI: `http://127.0.0.1:8025`

Die eigentliche RAG-Seite ist direkt verfügbar. Login- und Admin-Funktionen hängen davon ab, ob in PocketBase passende Benutzer vorhanden sind.

## 8. Erste Funktionsprüfung

Wenn alles korrekt läuft, sollte Folgendes funktionieren:

1. `http://localhost:8501` öffnet die Streamlit-App.
2. `http://127.0.0.1:8080/_/` öffnet das PocketBase-Dashboard.
3. `http://127.0.0.1:8025` öffnet MailHog.
4. Der Befehl `docker ps` zeigt alle benötigten Container als laufend an.

## 9. Dokumente einspielen

Statische Dokumente können im Ordner `data/` abgelegt werden.

Bevorzugt in der App:
1. Dokumente als Adminuser in der Dokumentenverwaltung hochladen.
2. Den Index aufbauen bzw. aktualisieren.
3. Anschließend Fragen gegen den aufgebauten Index stellen.

## 10. Nützliche Befehle

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

## 11. Typische Probleme

### App startet, aber lokale Antworten funktionieren nicht

Wahrscheinlich wurde noch kein Ollama-Modell geladen.

Lösung:

```powershell
docker exec -it ollama ollama pull llama3.2
```

### PocketBase-Fehler beim App-Start

Oft passen die Admin-Zugangsdaten in `.env` nicht zu dem existierenden PocketBase-Superuser.

Prüfen:

- stimmen `POCKETBASE_ADMIN_USERNAME` und `POCKETBASE_ADMIN_PASSWORD`?
- wurde der Superuser in PocketBase wirklich mit diesen Daten angelegt?

### Mail-Versand funktioniert lokal nicht

Für die Entwicklungsumgebung sollten in `.env` diese Werte gesetzt sein:

```env
APP_ENV=development
SMTP_HOST=mailhog
SMTP_PORT=1025
```

### Ports sind schon belegt

Wenn `8501`, `8080`, `8025` oder `11434` lokal bereits verwendet werden, müssen die belegenden Prozesse beendet oder die Port-Mappings in den Compose-Dateien angepasst werden.

## 12. Kurzfassung

Wer nur die Minimalversion braucht, kommt mit diesen Schritten ans Ziel:

1. Repo klonen und in den Ordner wechseln.
2. `.env.example` nach `.env` kopieren und Werte setzen.
3. `docker compose -f docker-compose.yml -f docker-compose.dev.yml build`
4. `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d`
5. `docker exec -it ollama ollama pull llama3.2`
6. Falls nötig: `docker exec -it pocketbase /pb/pocketbase superuser create <mail> <passwort>`
7. `http://localhost:8501` im Browser öffnen.


# Verwendung der Applikation

## 1. Pocketbase

### 1.1. Accounts verwalten

Sobald ein Superuser für Pocketbase erstellt wurde, ist es möglich in Pocketbase Benutzerkonten für die RAG-LLM Anwendung anzulegen. In der Benutzerverwaltung können die Benutzer ebenfalls bearbeitet und gelöscht werden.

## 2. RAG-LLM Anwendung

### 2.1. Sidenav

Die Sidenav stellt Informationen und Funktionen bezüglich des Chatbots zu Verfügung. Hierbei wird zwischen Allgemein und Administration unterschieden.

#### 2.1.1. Allgemein

Im allgemeinen Bereich den eigenen Loginstatus einzusehen, einen Ausweis hochzuladen und einen Report zu generieren.

#### 2.1.2. Administration

Im Administrationsbereich ist es möglich das LLM-Modell zu ändern. Außerdem sieht man Informationen zu den indexierten und existierenden Dokumenten. Hier kann auch der Inhalt einer Webseite indexiert werden. Zudem kann der Index neu gebaut werden.

### 2.2. Hauptansicht

In der Hauptansicht sieht man einen chatähnlichen Aufbau. Über das Inputfeld auf der unteren Seite können Fragen an den digitalen Assistenten gestellt werden. Über den Button `generate questions` können neue vorgefertigte Fragen generiert werden. Über den Button `new chat` wird ein neuer Chat bereitgestellt.

### 2.3. Authentifizierung

Auf der oberen Leiste kann man sich unter `user -> login` in der Anwendung anmelden. Hierzu verwendet man die in Pocketbase angelegten Benutzerdaten.

### 2.4. Adminseiten

Als Administrator hat man Zugang zu Adminseiten.

#### 2.4.1. Dokumentenmanager

Im Dokumentenmanager können Dokumente hochgeladen, bearbeitet, angesehen und gelöscht werden. Für ein Dokument kann angegeben werden, ob ein Ausweis für dieses hochgeladen werden soll. Wenn ein Dokument bearbeitet wird, kann es durch ein neueres Dokument ausgetauscht werden. Hierbei wird das Dokument auf Unterschiede geprüft. Wenn das Dokument identisch ist, kann es nicht aktualisiert werden. In der Dokumentenauflistung können vorgefertigte Fragen aus dem Kontext generiert werden.

#### 2.4.2. Logmanager

Im Logmanager können tägliche Logs eingesehen werden. Diese können auch heruntergeladen werden.