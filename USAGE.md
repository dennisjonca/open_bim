# IFC Abfrage-Tool - Bedienungsanleitung

## Erste Schritte

### Installation

1. Repository klonen:
```bash
git clone https://github.com/dennisjonca/open_bim.git
cd open_bim
```

2. Abhängigkeiten installieren:
```bash
pip install -r requirements.txt
```

### Anwendung ausführen

**Entwicklungsmodus:**
```bash
python app.py
```

**Produktionsmodus:**
```bash
# Umgebungsvariablen setzen
export SECRET_KEY="your-secure-random-key-here"
export FLASK_DEBUG="false"

# Einen Produktions-WSGI-Server verwenden
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

3. Öffnen Sie Ihren Browser und navigieren Sie zu:
```
http://localhost:5000
```

## Verwendung der Weboberfläche

### Schritt 1: Eine IFC-Datei hochladen

1. Klicken Sie auf der Startseite auf "IFC-Datei auswählen"
2. Wählen Sie Ihre IFC-Datei aus (muss die Erweiterung .ifc oder .IFC haben)
3. Klicken Sie auf "Datei hochladen"
4. Warten Sie auf die Validierung - Sie werden zur Abfrage-Oberfläche weitergeleitet

### Schritt 2: Eine Abfragekategorie auswählen

Die Oberfläche bietet 9 Abfragekategorien:

1. **Mengen & Kostenermittlung** - Elemente pro Geschoss oder gesamt zählen
2. **Längen & Volumen** - Materialmengen berechnen
3. **Elementkontext** - Elemente an bestimmten Orten finden
4. **Systemanalyse** - TGA-Systeme und Stromkreise analysieren
5. **Raum & Nutzung** - Raumflächen und Nutzung analysieren
6. **Konformität** - Prüfen, ob Elemente an erforderlichen Stellen vorhanden sind
7. **Planung** - Bereiche mit hoher Dichte für Installation identifizieren
8. **Wartung** - Geräte lokalisieren, die Wartung erfordern
9. **Zusammengesetzte Abfragen** - Komplexe Abfragen mit mehreren Filtern

### Schritt 3: Ihre Abfrage konfigurieren

Jede Kategorie hat spezifische Abfrageoptionen. Zum Beispiel:

**Mengen & Kostenermittlung:**
- Elementtyp auswählen (Steckdosen, Türen, Fenster usw.)
- Zwischen "nach Geschoss" oder "gesamt" Zählung wählen

**Zusammengesetzte Abfragen:**
- Elementtyp auswählen
- Optional nach Geschoss filtern (z.B. "Obergeschoss")
- Optional nach Raumtyp filtern (z.B. "Büro")

### Schritt 4: Ausführen und Ergebnisse anzeigen

1. Füllen Sie die Abfrageparameter aus
2. Klicken Sie auf "Abfrage ausführen"
3. Ergebnisse erscheinen unten in einem von drei Formaten:
   - **Wert**: Einzelnes numerisches Ergebnis mit Einheiten
   - **Tabelle**: Mehrere Datenzeilen
   - **Konformität**: Bestanden/Nicht bestanden Status mit Details

## Beispielabfragen

### Beispiel 1: Steckdosen pro Geschoss zählen

1. Gehen Sie zu "Mengen & Kostenermittlung"
2. Abfrage auswählen: "Nach Geschoss zählen"
3. Elementtyp: "Steckdosen"
4. Klicken Sie auf "Abfrage ausführen"

**Ergebnis:** Tabelle mit Anzahl der Steckdosen pro Geschoss

### Beispiel 2: Gesamte Rohrlänge

1. Gehen Sie zu "Längen & Volumen"
2. Abfrage auswählen: "Gesamtlänge"
3. Elementtyp: "Rohre"
4. Klicken Sie auf "Abfrage ausführen"

**Ergebnis:** Gesamtlänge in Metern

### Beispiel 3: Steckdosen in Büroräumen

1. Gehen Sie zu "Elementkontext"
2. Abfrage auswählen: "Elemente im Raumtyp"
3. Elementtyp: "Steckdosen"
4. Raumtyp: "Büro"
5. Klicken Sie auf "Abfrage ausführen"

**Ergebnis:** Anzahl der Steckdosen in Büroräumen

### Beispiel 4: Konformitätsprüfung

1. Gehen Sie zu "Konformität"
2. Abfrage auswählen: "Elemente in allen Räumen prüfen"
3. Elementtyp: "Steckdosen"
4. Raumtyp: "Büro"
5. Klicken Sie auf "Abfrage ausführen"

**Ergebnis:** Zeigt, ob alle Büroräume Steckdosen haben

### Beispiel 5: Zusammengesetzte Abfrage

1. Gehen Sie zu "Zusammengesetzte Abfragen"
2. Abfrage auswählen: "Gefilterte Elementanzahl"
3. Elementtyp: "Steckdosen"
4. Geschossfilter: "Obergeschoss"
5. Raumtypfilter: "Büro"
6. Klicken Sie auf "Abfrage ausführen"

**Ergebnis:** Anzahl der Steckdosen in Büroräumen im Obergeschoss

## Ergebnisse verstehen

### Wertergebnisse
Zeigt eine einzelne Zahl mit Einheiten:
```
Gesamt Steckdosen: 156 Elemente
```

### Tabellenergebnisse
Zeigt mehrere Zeilen:
```
Geschoss            | Anzahl
--------------------|-------
Erdgeschoss         | 45
Obergeschoss        | 52
Zweites Geschoss    | 38
```

### Konformitätsergebnisse
Zeigt Bestanden/Nicht bestanden Status:
```
✓ Alle Räume haben Elemente
Gesamt Büroräume: 25
Räume mit Steckdosen: 25
Räume ohne Steckdosen: 0
```

## Tipps und Best Practices

### Abfrage-Performance
- Beginnen Sie mit einfachen Abfragen, um Ihre Daten zu verstehen
- Verwenden Sie Filter, um Ergebnisse einzugrenzen
- Einige Abfragen können bei großen IFC-Dateien Zeit benötigen

### Datenqualität
Die Qualität der Ergebnisse hängt von Ihrer IFC-Datei ab:
- **Elementklassifizierung**: Elemente sollten ordnungsgemäß klassifiziert sein (nicht alle Proxys)
- **Geschosszuordnung**: Elemente sollten Geschossen zugeordnet sein
- **Systemdaten**: TGA-Elemente sollten für Systemabfragen Systemen zugeordnet sein
- **Räumliche Beziehungen**: Elemente sollten in Räumen enthalten oder referenziert sein

### Fehlerbehebung

**Abfrage gibt keine Daten zurück:**
- Prüfen Sie, ob Elemente dieses Typs in Ihrer IFC-Datei existieren
- Prüfen Sie, ob Elemente ordnungsgemäß Geschossen/Räumen zugeordnet sind
- Versuchen Sie die Abfrage "Elemente pro Geschoss", um zu sehen, was verfügbar ist

**Elemente werden als "Nicht zugeordnet" angezeigt:**
- Elemente sind möglicherweise keinem Geschoss in Ihrem BIM-Modell zugeordnet
- Prüfen Sie räumliche Beziehungen in Ihrem BIM-Authoring-Tool

**Systemabfragen geben nichts zurück:**
- TGA-Elemente sind möglicherweise in Ihrem Modell keinen Systemen zugeordnet
- Verwenden Sie Ihr BIM-Authoring-Tool, um Systeme zu erstellen und zuzuordnen

## Kommandozeilen-Alternative

Für Batch-Verarbeitung oder Skripting verwenden Sie den ursprünglichen Analyser:
```bash
# IFC-Datei im selben Verzeichnis platzieren
python analyze_ifc.py
```

Dies bietet detaillierte Konsolenausgabe mit allen verfügbaren Daten.

## Sicherheitshinweise

### Für Produktions-Deployment

1. **Setzen Sie immer einen sicheren SECRET_KEY:**
```bash
export SECRET_KEY="$(python -c 'import os; print(os.urandom(24).hex())')"
```

2. **Debug-Modus deaktivieren:**
```bash
export FLASK_DEBUG="false"
```

3. **Verwenden Sie einen Produktions-WSGI-Server** (nicht den integrierten Flask-Server):
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

4. **Richten Sie ordnungsgemäße Dateiberechtigungen** für das Upload-Verzeichnis ein

5. **Erwägen Sie das Hinzufügen von Authentifizierung** bei öffentlichem Deployment

6. **Richten Sie HTTPS ein** mit einem Reverse-Proxy (nginx, Apache)

7. **Begrenzen Sie Upload-Dateigrößen** (bereits auf 100 MB gesetzt)

## Support

Für Probleme oder Fragen:
- Prüfen Sie die README.md für allgemeine Informationen
- Überprüfen Sie das ursprüngliche analyze_ifc.py für detaillierte IFC-Analyse
- Konsultieren Sie die ifcopenshell-Dokumentation für IFC-Schema-Details
