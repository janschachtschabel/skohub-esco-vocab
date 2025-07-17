# ESCO TTL Generators

Dieses Repository enthält zwei spezialisierte Tools zur Generierung von TTL-Dateien aus ESCO v1.2.0 CSV-Daten für die Integration in Skills&More und andere SKOS-basierte Anwendungen.

## 📋 Übersicht

### Tools:
1. **`esco_skills_ttl_generator.py`** - Generiert TTL für ESCO Skills/Kompetenzen
2. **`esco_occupations_ttl_generator.py`** - Generiert TTL für ESCO Berufe/Occupations

### Datenquelle:
- **ESCO Portal**: https://esco.ec.europa.eu/de/use-esco/download
- **Version**: 1.2.0
- **Typ**: Classification (Inhalt)
- **Format**: CSV (Dateityp)
- **Sprache**: Deutsch (de)

---

## 🛠️ Tool 1: ESCO Skills TTL Generator

### Beschreibung:
Konvertiert ESCO v1.2.0 Skills/Kompetenzen CSV-Daten in saubere, SKOS-konforme TTL-Dateien.

### Eingabedateien:
```
ESCO dataset - v1.2.0 - classification - de - csv/
├── skills_de.csv                           # Hauptdatei mit allen Skills
├── transversalSkillsCollection_de.csv      # Transversale Skills
├── languageSkillsCollection_de.csv         # Sprachkompetenzen
├── digitalSkillsCollection_de.csv          # Digitale Skills
├── greenSkillsCollection_de.csv            # Grüne Skills
├── researchSkillsCollection_de.csv         # Forschungskompetenzen
└── broaderRelationsSkillPillar_de.csv      # Hierarchische Beziehungen
```

### Verwendung:
```bash
python esco_skills_ttl_generator.py "ESCO dataset - v1.2.0 - classification - de - csv" esco_skills_v1.2.0.ttl
```

### Ausgabe:
- **TTL-Datei**: Saubere SKOS-Struktur mit w3id.org URIs
- **Base URI**: `http://w3id.org/openeduhub/vocabs/escoSkills/`
- **Statistiken**: Detaillierte Übersicht über verarbeitete Daten

### Verarbeitete Daten:
- **Total Skills**: ~13.939
- **Transversal Skills**: 95
- **Language Skills**: 359
- **Digital Skills**: 1.284
- **Green Skills**: 591
- **Research Skills**: 40
- **Knowledge Items**: ~517

---

## 🏢 Tool 2: ESCO Occupations TTL Generator

### Beschreibung:
Konvertiert ESCO v1.2.0 Occupations/Berufe CSV-Daten in saubere, SKOS-konforme TTL-Dateien.

### Eingabedateien:
```
ESCO dataset - v1.2.0 - classification - de - csv/
├── occupations_de.csv                      # Hauptdatei mit allen Berufen
└── researchOccupationsCollection_de.csv    # Forschungsberufe
```

### Verwendung:
```bash
python esco_occupations_ttl_generator.py "ESCO dataset - v1.2.0 - classification - de - csv" esco_occupations_v1.2.0.ttl
```

### Ausgabe:
- **TTL-Datei**: Saubere SKOS-Struktur mit w3id.org URIs
- **Base URI**: `http://w3id.org/openeduhub/vocabs/escoOccupations/`
- **Statistiken**: Detaillierte Übersicht über verarbeitete Daten

### Verarbeitete Daten:
- **Total Occupations**: 3.039
- **Research Occupations**: 122
- **ISCO Groups**: 426 automatisch erkannt

---

## 📊 Gemeinsame Features

### SKOS-Struktur:
Beide Tools generieren vollständige SKOS-konforme TTL-Dateien mit:

```turtle
@base <http://w3id.org/openeduhub/vocabs/[escoSkills|escoOccupations]/> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix esco: <http://data.europa.eu/esco/[skill|occupation]/> .
@prefix dct: <http://purl.org/dc/terms/> .

<> a skos:ConceptScheme ;
    dct:title "ESCO [Skills|Occupations] - Generated from ESCO v1.2.0"@de ;
    dct:description "Saubere TTL-Datei generiert aus ESCO v1.2.0 CSV-Daten"@de ;
    dct:created "YYYY-MM-DD"^^xsd:date .

<uuid> a skos:Concept ;
    skos:prefLabel "Hauptbezeichnung"@de ;
    skos:altLabel "Alternative Bezeichnung"@de ;
    skos:exactMatch esco:uuid ;
    skos:scopeNote "Beschreibung/Definition"@de ;
    skos:inScheme <> .
```

### Encoding-Behandlung:
- **Robuste Encoding-Erkennung**: Automatische Erkennung von UTF-8, UTF-8-BOM, CP1252, Latin1
- **Deutsche Umlaute**: Korrekte Behandlung von ä, ö, ü, ß
- **Fallback-Mechanismus**: Mehrere Encoding-Versuche für maximale Kompatibilität

### Datenqualität:
- **URI-Konsistenz**: Einheitliche w3id.org URI-Struktur
- **ESCO-Referenzen**: `skos:exactMatch` zu originalen ESCO-URIs
- **Hierarchien**: Erhaltung aller SKOS-Beziehungen (broader, narrower, etc.)
- **Labels**: Vollständige Erhaltung von prefLabel und altLabel

---

## 🔧 Nachbearbeitung mit TTL Cleaner

### Empfohlener Workflow:
```bash
# 1. Generiere Skills TTL
python esco_skills_ttl_generator.py "ESCO dataset - v1.2.0 - classification - de - csv" esco_skills_v1.2.0.ttl

# 2. Bereinige Skills TTL
python ttl_cleaner.py esco_skills_v1.2.0.ttl

# 3. Generiere Occupations TTL
python esco_occupations_ttl_generator.py "ESCO dataset - v1.2.0 - classification - de - csv" esco_occupations_v1.2.0.ttl

# 4. Bereinige Occupations TTL
python ttl_cleaner.py esco_occupations_v1.2.0.ttl
```

### TTL Cleaner Vorteile:
- **Duplikat-Entfernung**: Eliminiert doppelte Konzepte
- **Syntax-Korrektur**: Behebt TTL-Formatierungsfehler
- **URI-Normalisierung**: Standardisiert URI-Formate
- **Change-Log**: Vollständige Dokumentation aller Änderungen

---

## 📁 Ausgabedateien

### Skills Generator:
- `esco_skills_v1.2.0.ttl` - Rohdatei
- `esco_skills_v1.2.0_cleaned.ttl` - Bereinigte Datei (empfohlen)
- `esco_skills_v1.2.0_cleaned_changes.log` - Änderungsprotokoll

### Occupations Generator:
- `esco_occupations_v1.2.0.ttl` - Rohdatei
- `esco_occupations_v1.2.0_cleaned.ttl` - Bereinigte Datei (empfohlen)
- `esco_occupations_v1.2.0_cleaned_changes.log` - Änderungsprotokoll

---

## 🚀 Integration in Skills&More

### Upload-Prozess:
1. **TTL-Datei generieren** mit entsprechendem Generator
2. **Optional bereinigen** mit TTL Cleaner
3. **Upload in Streamlit-App** über TTL/SKOS Upload Tab
4. **Batch-Verarbeitung** mit konfigurierbarer Batch-Größe

### Kompatibilität:
- **SKOS-Standard**: Vollständige Unterstützung aller SKOS-Properties
- **Encoding**: UTF-8 mit deutschen Umlauten
- **URI-Schema**: Konsistente w3id.org URIs
- **Metadaten**: Dublin Core Terms für Versionierung

---

## 📋 Systemanforderungen

### Python-Abhängigkeiten:
```python
csv         # CSV-Verarbeitung
os          # Dateisystem-Operationen
sys         # System-Parameter
datetime    # Zeitstempel
typing      # Type Hints
urllib.parse # URI-Verarbeitung
re          # Regular Expressions
```

### Unterstützte Plattformen:
- **Windows**: Vollständig getestet
- **Linux**: Kompatibel
- **macOS**: Kompatibel

---

## 🐛 Troubleshooting

### Häufige Probleme:

#### 1. Encoding-Fehler:
```
UnicodeDecodeError: 'utf-8' codec can't decode...
```
**Lösung**: Tools verwenden automatische Encoding-Erkennung

#### 2. Fehlende CSV-Dateien:
```
FileNotFoundError: CSV file not found
```
**Lösung**: Überprüfen Sie den Pfad zum ESCO-Dataset-Ordner

#### 3. Speicher-Probleme:
```
MemoryError: Unable to allocate array
```
**Lösung**: Verarbeitung erfolgt streamweise, sollte nicht auftreten

### Support:
- **Logs**: Detaillierte Konsolen-Ausgabe während Verarbeitung
- **Statistiken**: Umfassende Übersicht über verarbeitete Daten
- **Change-Logs**: Vollständige Dokumentation aller Änderungen

---

## 📈 Statistiken-Beispiel

### Skills Generator Output:
```
============================================================
ESCO SKILLS DATA LOADING STATISTICS
============================================================
Total skills loaded:        13939
Transversal skills:            95
Language skills:              359
Digital skills:              1284
Green skills:                 591
Research skills:               40
Knowledge items:              517
Collections processed:          6
============================================================
```

### Occupations Generator Output:
```
============================================================
ESCO OCCUPATIONS DATA LOADING STATISTICS
============================================================
Total occupations loaded:     3039
Research occupations:          122
ISCO groups found:             426
Collections processed:           1
============================================================
```

---

## 📄 Lizenz

Dieses Tool verarbeitet ESCO-Daten, die unter der Creative Commons Attribution 4.0 International License stehen.

**ESCO-Datenquelle**: https://esco.ec.europa.eu/de/use-esco/download
**Version**: 1.2.0 (Classification, CSV, Deutsch)

---

## 🔄 Updates

### Version History:
- **v1.0**: Initiale Implementierung für Skills und Occupations
- **v1.1**: Verbesserte Encoding-Behandlung
- **v1.2**: Integration mit TTL Cleaner
- **v1.3**: Erweiterte Statistiken und Logging

### Geplante Features:
- **Mehrsprachigkeit**: Unterstützung für andere ESCO-Sprachen
- **Batch-Verarbeitung**: Automatisierte Pipeline
- **Validierung**: Erweiterte TTL-Syntax-Prüfung

---

**Für weitere Informationen und Support kontaktieren Sie mich.**
