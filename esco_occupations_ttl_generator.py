#!/usr/bin/env python3
"""
ESCO Occupations TTL Generator v1.0
Generiert eine saubere TTL-Datei aus ESCO v1.2.0 Occupations CSV-Daten

Berücksichtigt:
- Alle ESCO-Berufe (Occupations)
- ISCO-Gruppierungen
- Forschungsberufe (Research Occupations)
- Hierarchische Beziehungen

Verwendet w3id.org URIs für konsistente Referenzierung
"""

import csv
import os
import sys
from datetime import datetime
from typing import Dict, List, Set, Optional, Tuple
from urllib.parse import urlparse
import re

class ESCOOccupationsTTLGenerator:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.occupations = {}  # URI -> occupation data
        self.isco_groups = {}  # ISCO code -> group info
        self.collections = {
            'research': set()
        }
        self.stats = {
            'total_occupations': 0,
            'research_occupations': 0,
            'isco_groups': 0,
            'collections_processed': 0
        }
        
    def _detect_encoding(self, filepath: str) -> str:
        """Erkennt das Encoding einer Datei"""
        encodings_to_try = ['utf-8', 'utf-8-sig', 'cp1252', 'latin1', 'iso-8859-1']
            
        # Teste bekannte Encodings
        for encoding in encodings_to_try:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    content = f.read(1000)  # Teste ersten 1000 Zeichen
                    # Teste auf deutsche Umlaute
                    if 'ü' in content or 'ä' in content or 'ö' in content or 'ß' in content:
                        return encoding
                return encoding
            except UnicodeDecodeError:
                continue
                
        return 'utf-8'  # Default fallback
        
    def load_data(self):
        """Lädt alle relevanten ESCO Occupations CSV-Dateien"""
        print("[INFO] Loading ESCO Occupations data...")
        
        # Lade Hauptdaten
        self._load_occupations()
        
        # Lade Collections
        self._load_collections()
        
        print("[OK] Data loaded successfully!")
        self._print_loading_stats()
        
    def _load_occupations(self):
        """Lädt die Hauptdatei mit allen Berufen"""
        occupations_file = os.path.join(self.data_dir, 'occupations_de.csv')
        
        if not os.path.exists(occupations_file):
            raise FileNotFoundError(f"Occupations file not found: {occupations_file}")
            
        encoding = self._detect_encoding(occupations_file)
        print(f"[INFO] Using encoding {encoding} for occupations file")
        with open(occupations_file, 'r', encoding=encoding) as f:
            reader = csv.DictReader(f)
            for row in reader:
                uri = row['conceptUri'].strip()
                
                # Extrahiere UUID aus der URI
                uuid = self._extract_uuid_from_uri(uri)
                if not uuid:
                    continue
                    
                # Verarbeite Labels
                pref_label = row['preferredLabel'].strip()
                alt_labels = self._parse_alt_labels(row.get('altLabels', ''))
                
                # ISCO Gruppe
                isco_group = row.get('iscoGroup', '').strip()
                
                # Beschreibung/Definition
                description = row.get('description', '').strip()
                definition = row.get('definition', '').strip()
                scope_note = description or definition
                
                self.occupations[uuid] = {
                    'uri': uri,
                    'uuid': uuid,
                    'pref_label': pref_label,
                    'alt_labels': alt_labels,
                    'isco_group': isco_group,
                    'scope_note': scope_note,
                    'collections': []
                }
                
                # Sammle ISCO Gruppen
                if isco_group and isco_group not in self.isco_groups:
                    self.isco_groups[isco_group] = {
                        'code': isco_group,
                        'occupations': []
                    }
                
                if isco_group:
                    self.isco_groups[isco_group]['occupations'].append(uuid)
                
                self.stats['total_occupations'] += 1
                
        print(f"[OK] Loaded {self.stats['total_occupations']} occupations")
        
    def _load_collections(self):
        """Lädt spezielle Collections wie Research Occupations"""
        collections_info = [
            ('research', 'researchOccupationsCollection_de.csv')
        ]
        
        for collection_name, filename in collections_info:
            filepath = os.path.join(self.data_dir, filename)
            if not os.path.exists(filepath):
                print(f"[WARNING] Collection file not found: {filepath}")
                continue
                
            encoding = self._detect_encoding(filepath)
            with open(filepath, 'r', encoding=encoding) as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    uri = row['conceptUri'].strip()
                    uuid = self._extract_uuid_from_uri(uri)
                    if uuid and uuid in self.occupations:
                        self.collections[collection_name].add(uuid)
                        self.occupations[uuid]['collections'].append(collection_name)
                        count += 1
                        
                print(f"[OK] Loaded {count} {collection_name} occupations")
                if collection_name == 'research':
                    self.stats['research_occupations'] = count
                    
        self.stats['collections_processed'] = len([c for c in collections_info if os.path.exists(os.path.join(self.data_dir, c[1]))])
        self.stats['isco_groups'] = len(self.isco_groups)
        
    def _extract_uuid_from_uri(self, uri: str) -> Optional[str]:
        """Extrahiert UUID aus ESCO URI"""
        if not uri:
            return None
            
        # Pattern: http://data.europa.eu/esco/occupation/UUID
        match = re.search(r'/occupation/([a-f0-9-]+)$', uri)
        if match:
            return match.group(1)
            
        return None
        
    def _parse_alt_labels(self, alt_labels_str: str) -> List[str]:
        """Parst alternative Labels aus dem CSV-String"""
        if not alt_labels_str or alt_labels_str.strip() == '':
            return []
            
        # Split by newlines and clean
        labels = []
        for label in alt_labels_str.split('\n'):
            label = label.strip()
            if label and label not in labels:
                labels.append(label)
                
        return labels
        
    def _clean_text(self, text: str) -> str:
        """Bereinigt Text für TTL-Ausgabe"""
        if not text:
            return ""
            
        # Entferne problematische Zeichen
        text = text.replace('"', '\\"')  # Escape quotes
        text = text.replace('\n', ' ')   # Replace newlines with spaces
        text = text.replace('\r', ' ')   # Replace carriage returns
        text = re.sub(r'\s+', ' ', text) # Normalize whitespace
        
        return text.strip()
        
    def generate_ttl(self, output_file: str):
        """Generiert die TTL-Datei"""
        print(f"[INFO] Generating TTL file: {output_file}")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            # Header
            f.write('@base <http://w3id.org/openeduhub/vocabs/escoOccupations/> .\n')
            f.write('@prefix skos: <http://www.w3.org/2004/02/skos/core#> .\n')
            f.write('@prefix esco: <http://data.europa.eu/esco/occupation/> .\n')
            f.write('@prefix dct: <http://purl.org/dc/terms/> .\n')
            f.write('@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n')
            f.write('\n')
            
            # ConceptScheme
            f.write('<> a skos:ConceptScheme ;\n')
            f.write('    dct:title "ESCO Occupations - Generated from ESCO v1.2.0"@de ;\n')
            f.write('    dct:description "Saubere TTL-Datei generiert aus ESCO v1.2.0 Occupations CSV-Daten"@de ;\n')
            f.write(f'    dct:created "{datetime.now().strftime("%Y-%m-%d")}"^^xsd:date .\n')
            f.write('\n')
            
            # Schreibe alle Occupations
            count = 0
            for uuid, occupation in self.occupations.items():
                count += 1
                
                # Progress
                if count % 1000 == 0:
                    print(f"[INFO] Written {count} occupations...")
                
                f.write(f'<{uuid}> a skos:Concept ;\n')
                
                # prefLabel
                pref_label = self._clean_text(occupation['pref_label'])
                f.write(f'    skos:prefLabel "{pref_label}"@de ;\n')
                
                # altLabels
                for alt_label in occupation['alt_labels']:
                    alt_label_clean = self._clean_text(alt_label)
                    if alt_label_clean:
                        f.write(f'    skos:altLabel "{alt_label_clean}"@de ;\n')
                
                # exactMatch zu ESCO
                f.write(f'    skos:exactMatch esco:{uuid} ;\n')
                
                # Collections als Kommentar
                if occupation['collections']:
                    collections_str = ', '.join(occupation['collections'])
                    f.write(f'    # Collections: {collections_str}\n')
                
                # scopeNote
                if occupation['scope_note']:
                    scope_note = self._clean_text(occupation['scope_note'])
                    if scope_note:
                        f.write(f'    skos:scopeNote "{scope_note}"@de ;\n')
                
                # ISCO Group als Kommentar
                if occupation['isco_group']:
                    f.write(f'    # ISCO Group: {occupation["isco_group"]}\n')
                
                # inScheme
                f.write('    skos:inScheme <> .\n')
                f.write('\n')
                
            print(f"[OK] Written {count} occupations to TTL")
            
        print(f"[OK] TTL file generated: {output_file}")
        self._print_generation_stats(count)
        
    def _print_loading_stats(self):
        """Druckt Ladestatistiken"""
        print("\n" + "="*60)
        print("ESCO OCCUPATIONS DATA LOADING STATISTICS")
        print("="*60)
        print(f"Total occupations loaded:   {self.stats['total_occupations']:>6}")
        print(f"Research occupations:       {self.stats['research_occupations']:>6}")
        print(f"ISCO groups found:          {self.stats['isco_groups']:>6}")
        print(f"Collections processed:      {self.stats['collections_processed']:>6}")
        print()
        print("COLLECTION SIZES:")
        for name, collection in self.collections.items():
            print(f"  {name.capitalize():<12} : {len(collection)}")
        print("="*60)
        
    def _print_generation_stats(self, written_count: int):
        """Druckt Generierungsstatistiken"""
        print("\n" + "="*60)
        print("TTL GENERATION STATISTICS")
        print("="*60)
        print(f"Occupations written to TTL: {written_count:>6}")
        print(f"ESCO exactMatch refs:       {written_count:>6}")
        print(f"Using w3id.org URIs:        YES")
        print(f"Base URI:                   http://w3id.org/openeduhub/vocabs/escoOccupations/")
        print("="*60)

def main():
    if len(sys.argv) != 3:
        print("Usage: python esco_occupations_ttl_generator.py <data_directory> <output_file>")
        print("Example: python esco_occupations_ttl_generator.py \"ESCO dataset - v1.2.0 - classification - de - csv\" esco_occupations_v1.2.0.ttl")
        sys.exit(1)
        
    data_dir = sys.argv[1]
    output_file = sys.argv[2]
    
    if not os.path.exists(data_dir):
        print(f"[ERROR] Data directory not found: {data_dir}")
        sys.exit(1)
        
    try:
        generator = ESCOOccupationsTTLGenerator(data_dir)
        generator.load_data()
        generator.generate_ttl(output_file)
        
        print(f"\n[SUCCESS] ESCO Occupations TTL file generated successfully!")
        print(f"Output file: {output_file}")
        print("Ready for upload to Skills&More Streamlit application!")
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
