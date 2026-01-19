# open_bim
Dieses Projekt versucht, IFC-Dateien aus BIM-Projekten zu lesen und zu schreiben.

## IFC Abfrage-Webanwendung

Eine Flask-basierte Webanwendung, mit der Sie IFC-Dateien hochladen und über eine intuitive Weboberfläche abfragen können. Beantworten Sie komplexe Fragen zu Ihren BIM-Daten ohne Code zu schreiben.

### Funktionen

Die Webanwendung bietet 9 umfassende Abfragekategorien, die alle Aspekte von IFC-Daten abdecken:

1. **Mengen & Kostenermittlung** - Elemente pro Geschoss oder gebäudeweit zählen
2. **Längen & Volumen** - Gesamtlängen von Rohren, Lüftungskanälen, Kabeln und Oberflächen berechnen
3. **Elementkontext** - Elemente in bestimmten Räumen oder Bauteilen finden
4. **Systemanalyse** - TGA-Systeme und elektrische Stromkreise analysieren
5. **Raum & Nutzung** - Flächen berechnen und Raumnutzungsmuster analysieren
6. **Konformitätsprüfung** - Prüfen, ob Elemente an erforderlichen Stellen vorhanden sind
7. **Installationsplanung** - Installationsarbeiten vor Ort koordinieren
8. **Wartung & Übergabe** - Wartbare Geräte und Verteilerpunkte lokalisieren
9. **Zusammengesetzte Abfragen** - Komplexe Abfragen mit mehreren Filtern

### Schnellstart

1. Abhängigkeiten installieren:
```bash
pip install -r requirements.txt
```

2. Flask-Anwendung starten:
```bash
python app.py
```

3. Öffnen Sie Ihren Browser und navigieren Sie zu:
```
http://localhost:5000
```

4. Laden Sie eine IFC-Datei hoch und beginnen Sie mit den Abfragen!

### Verwendung

1. **IFC-Datei hochladen**: Klicken Sie auf der Startseite auf "IFC-Datei auswählen" und laden Sie Ihre IFC-Datei hoch
2. **Abfragekategorie auswählen**: Wählen Sie aus 9 Kategorien in der Seitenleiste
3. **Abfrage konfigurieren**: Füllen Sie die Formularparameter für Ihre spezifische Frage aus
4. **Abfrage ausführen**: Klicken Sie auf "Abfrage ausführen", um Ergebnisse zu sehen
5. **Ergebnisse anzeigen**: Ergebnisse werden als Tabellen, Werte oder Konformitätsprüfungen angezeigt

### Beispielabfragen

- "Wie viele Steckdosen gibt es im Erdgeschoss?"
- "Was ist die Gesamtlänge der Trinkwasserleitungen?"
- "Wie viele Leuchten sind in Büroräumen installiert?"
- "Welches Geschoss hat die höchste Installationsdichte?"
- "Gibt es in jedem Büroraum Steckdosen?"

## Brüstungskanal Test-Programm (canal_test.py)

Ein spezialisiertes Test-Programm, das die Grenzen der ifcopenshell-API auslotet, indem es nach Brüstungskanälen (Parapet Channels) in IFC-Dateien sucht.

### Was ist ein Brüstungskanal?

Ein Brüstungskanal ist ein Kabelkanal oder Kabelträgersegment, das auf Brüstungshöhe (ca. 0,8-1,3m vom Boden) installiert wird. Diese werden häufig in Bürogebäuden verwendet, um Steckdosen und Datenkabel an den Wänden zu führen.

### Funktionen

- **Sucht nach IfcCableCarrierSegment-Objekten** in IFC-Dateien
- **Mehrere Erkennungsmethoden**:
  - Namensbasierte Erkennung (sucht nach "Brüstungskanal", "Brüstung", "parapet")
  - Höhenbasierte Erkennung (prüft Installationshöhe zwischen 0,8-1,3m)
  - Prüfung von Eigenschaften und Typ-Informationen
- **Detaillierte Terminalausgabe** mit allen Analyseschritten
- **Testet verschiedene IFC-Element-Typen**:
  - IfcCableCarrierSegment (Kabelträgersegmente)
  - IfcCableSegment (Kabelsegmente)
  - IfcBuildingElementProxy (generische Elemente)
  - IfcFlowSegment (Fließsegmente)
- **Dokumentiert API-Grenzen und -Erkenntnisse**

### Verwendung

```bash
# Mit spezifischer IFC-Datei
python canal_test.py pfad/zur/datei.ifc

# Sucht automatisch nach IFC-Dateien im aktuellen Verzeichnis
python canal_test.py

# Hilfe anzeigen
python canal_test.py --help
```

### Beispielausgabe

```
======================================================================
PARAPET CHANNEL (BRÜSTUNGSKANAL) ANALYSIS
======================================================================

Analyzing file: beispiel.ifc

✓ Successfully opened IFC file
  IFC Schema: IFC4
  Project Name: Bürogebäude

----------------------------------------------------------------------
ANALYSIS STRATEGY:
----------------------------------------------------------------------
1. Search IfcCableCarrierSegment objects
2. Check names for 'Brüstungskanal' or 'parapet' keywords
3. Check height properties (parapet range: 0.8-1.3m)
4. Also check IfcCableSegment and generic elements
----------------------------------------------------------------------

======================================================================
SEARCHING FOR CABLE CARRIER SEGMENTS (IfcCableCarrierSegment)
======================================================================

Found 15 IfcCableCarrierSegment objects in total.

--- Cable Carrier #1 ---
  ID: 12345
  Name: Brüstungskanal-BK-01
  ✓ Name contains parapet keywords!
  Installation Height: 1.100 m
  ✓ Height is within parapet range (0.8-1.3m)!
  
  >>> POTENTIAL PARAPET CHANNEL DETECTED! <<<

...

======================================================================
SUMMARY: PARAPET CHANNEL DETECTION RESULTS
======================================================================

Total parapet channel candidates found: 3

1. ID: 12345
   Name: Brüstungskanal-BK-01
   Height: 1.100 m
   Detected by: Name keywords, Height range

...
```

### Zweck

Dieses Programm wurde entwickelt, um:
- Die Möglichkeiten und Grenzen der ifcopenshell-API zu testen
- Zu zeigen, wie spezifische Objekttypen in IFC-Dateien gefunden werden können
- Verschiedene Erkennungsstrategien für BIM-Objekte zu demonstrieren
- Als Beispiel für spezialisierte IFC-Analysetools zu dienen

## IFC-Datei-Analyser (Kommandozeile)

Ein Python-Skript, das die ifcopenshell-API verwendet, um IFC-Dateien (Industry Foundation Classes) zu lesen und zu analysieren. Das Skript zählt verschiedene BIM-Objekte wie Wände, Türen, Fenster, Decken, Träger, Stützen und mehr.

### Funktionen

- **Erkennt automatisch IFC-Dateien** im aktuellen Verzeichnis (zeigt vollständige Dateipfade an)
- **Liest IFC-Dateien** nur mit der ifcopenshell-API
- **Schnellübersicht** gängiger BIM-Objekttypen:
  - Wände, Türen, Fenster, Decken, Träger, Stützen
  - Treppen, Dächer, Räume, Möbel und mehr
- **Umfassende Produktauflistung** - Zeigt ALLE IfcProduct-Typen organisiert nach Kategorie:
  - **Tragende Elemente**: Wände, Träger, Stützen, Decken, Fundamente usw.
  - **TGA & HLK**: Kanäle, Rohre, Pumpen, Ventile, Kessel, Kühler usw.
  - **Elektrik & Beleuchtung**: Lampen, Leuchten, Sensoren, Kabel, Steckdosen usw.
  - **Sanitär**: Sanitäre Endgeräte, Abflussendgeräte usw.
  - **Sensoren & Steuerungen**: Sensoren, Aktoren, Alarme, Steuergeräte usw.
  - **Ausstattung & Geräte**: Möbel, medizinische Geräte, Audio-/Videogeräte usw.
  - **Transport**: Transportelemente
  - **Und weitere Kategorien...**
- **Geschossbasierte Organisation** - Zeigt Produkte sortiert nach Gebäudeetagen:
  - Zeigt Produkte für jede Etage an (Keller, Erdgeschoss, Obergeschoss usw.)
  - Sortiert nach Höhe von niedrigster bis höchster
  - Zeigt Höhenwerte für jede Etage
  - Enthält Gesamtzahlen pro Etage und Gesamtsumme
  - **Erweiterte räumliche Beziehungserkennung** für bessere Geschosszuordnung:
    - Prüft `IfcRelContainedInSpatialStructure` (direkte Zugehörigkeit)
    - Prüft `IfcRelReferencedInSpatialStructure` (oft für TGA/Steckdosen verwendet)
    - Prüft `IfcRelAggregates` (räumliche Dekomposition)
    - Durchläuft Räume, um übergeordnete Geschosse zu finden
- **Analyse nicht zugeordneter Objekte** - Hilft zu diagnostizieren, warum Objekte keine Geschosszuordnung haben:
  - Zeigt, welche Objekte räumliche Beziehungen haben, aber keine Geschosszuordnung
  - Zeigt, welche Objekte überhaupt keine räumlichen Beziehungen haben
  - Zeigt die Arten der gefundenen Beziehungen zur Fehlersuche
  - Gibt Empfehlungen zur Behebung von Zuordnungen in BIM-Authoring-Tools
- **TGA-Systemorganisation** - Zeigt Produkte organisiert nach TGA-Systemen:
  - Zeigt elektrische Stromkreise mit allen angeschlossenen Geräten (Steckdosen, Leuchten usw.)
  - Zeigt HLK-Systeme mit ihren Komponenten (Pumpen, Ventile, Endgeräte usw.)
  - Listet Sanitärsysteme und ihre Verbindungen auf
  - Identifiziert TGA-Produkte, die keinem System zugeordnet sind
  - Hilft, Systemkonnektivität und -organisation zu verstehen
  - Verwendet `IfcSystem`, `IfcElectricalCircuit` und `IfcDistributionSystem` Beziehungen
- **Zeigt Projektinformationen** und IFC-Schemaversion an
- **Sortiert nach Anzahl** innerhalb jeder Kategorie für einfache Analyse

### Installation

1. Installieren Sie Python 3.6 oder höher
2. Installieren Sie die erforderlichen Abhängigkeiten:

```bash
pip install -r requirements.txt
```

### Verwendung

1. Platzieren Sie Ihre IFC-Datei(en) im selben Verzeichnis wie `analyze_ifc.py`
2. Führen Sie das Skript aus:

```bash
python analyze_ifc.py
```

Oder machen Sie es ausführbar und führen Sie es direkt aus:

```bash
chmod +x analyze_ifc.py
./analyze_ifc.py
```

### Beispielausgabe

```
============================================================
IFC File Analyzer using ifcopenshell
============================================================

Found 1 IFC file(s) in current directory:
Current directory: /path/to/your/directory

  1. /path/to/your/directory/example.ifc

============================================================
Analyzing IFC file: /path/to/your/directory/example.ifc
============================================================

IFC Schema: IFC4

File Information:
  Project Name: Sample Building
  Description: Example IFC file

============================================================
Object Count Summary:
============================================================

  IfcWall                       :    45
  IfcDoor                       :    12
  IfcWindow                     :    18
  IfcSlab                       :     8
  IfcBeam                       :    24
  IfcColumn                     :    16

  Total IfcBuildingElement      :   150
  Total IfcProduct              :   180

============================================================
Total Specific Objects Counted: 123
============================================================

============================================================
All Products by Category:
============================================================

Electrical & Lighting (450 items):
------------------------------------------------------------
  IfcLightFixture                         :   300
  IfcSensor                               :   100
  IfcLamp                                 :    50

Structural Elements (125 items):
------------------------------------------------------------
  IfcBeam                                 :    80
  IfcWall                                 :    45

... (more categories) ...

============================================================
Total Products Across All Categories: 4500
============================================================

============================================================
Products by Floor/Storey:
============================================================

Basement (Elevation: -3.50m) - 234 items:
------------------------------------------------------------
  IfcWall                                 :    89
  IfcColumn                               :    45
  IfcPipeSegment                          :    45
  IfcSlab                                 :    25
  IfcPump                                 :    18
  IfcSpace                                :    12

Ground Floor (Elevation: 0.00m) - 1245 items:
------------------------------------------------------------
  IfcWall                                 :   345
  IfcFurniture                            :   234
  IfcLightFixture                         :   123
  IfcWindow                               :    89
  IfcColumn                               :    78
  IfcDoor                                 :    67
  ... (more products) ...

First Floor (Elevation: 3.50m) - 1523 items:
------------------------------------------------------------
  IfcWall                                 :   456
  IfcFurniture                            :   312
  IfcLightFixture                         :   145
  IfcWindow                               :   112
  ... (more products) ...

... (more floors) ...

Unassigned - 245 items:
------------------------------------------------------------
  IfcOutlet                               :   156
  IfcLightFixture                         :    45
  IfcSensor                               :    32
  IfcSpace                                :    12

============================================================
Total Products Across All Floors: 4500
============================================================

============================================================
Analyzing Unassigned Objects:
============================================================

Checking spatial relationships for unassigned objects...
This can help identify if objects are related to spaces that
aren't properly linked to storeys.

Objects with spatial relationships but no storey assignment:
------------------------------------------------------------
  IfcOutlet                               :   156
    → Referenced in IfcSpace
  IfcLightFixture                         :    45
    → Referenced in IfcSpace
  IfcSensor                               :    32
    → Referenced in IfcSpace

Objects with NO spatial relationships:
------------------------------------------------------------
  IfcSpace                                :    12

Recommendation:
  • Objects 'Contained in' or 'Referenced in' IfcSpace should have
    their spaces properly linked to an IfcBuildingStorey
  • Objects with no spatial relationships may need to be assigned
    to a space or storey in your BIM authoring tool
============================================================

============================================================
Products by MEP System:
============================================================

This shows how products are organized into systems such as
electrical circuits, HVAC systems, plumbing systems, etc.

Circuit A-01 (IfcElectricalCircuit) - 45 items:
------------------------------------------------------------
  IfcOutlet                               :    32
  IfcLightFixture                         :     8
  IfcSwitchingDevice                      :     5

Circuit A-02 (IfcElectricalCircuit) - 38 items:
------------------------------------------------------------
  IfcOutlet                               :    28
  IfcLightFixture                         :     7
  IfcSwitchingDevice                      :     3

HVAC Zone 1 (IfcDistributionSystem) - 156 items:
------------------------------------------------------------
  IfcAirTerminal                          :    89
  IfcDuctSegment                          :    45
  IfcDamper                               :    22

Domestic Cold Water (IfcDistributionSystem) - 67 items:
------------------------------------------------------------
  IfcPipeSegment                          :    45
  IfcValve                                :    15
  IfcSanitaryTerminal                     :     7

============================================================
Total Products in Systems: 306
============================================================

============================================================
MEP Products Not Assigned to Systems:
============================================================

Found 89 MEP products not assigned to any system:

  IfcOutlet                               :    45
  IfcLightFixture                         :    23
  IfcSensor                               :    21

Recommendation:
  • Assign MEP elements to appropriate systems in your BIM authoring tool
  • Systems help track electrical circuits, HVAC zones, plumbing networks, etc.
============================================================
```

### Anforderungen

- Python 3.6+
- ifcopenshell >= 0.7.0

### Hinweise

- Das Skript sucht nach Dateien mit `.ifc` oder `.IFC` Erweiterungen
- Mehrere IFC-Dateien im Verzeichnis werden alle analysiert
- Das Skript verwendet nur die ifcopenshell-API (keine anderen Abhängigkeiten)
