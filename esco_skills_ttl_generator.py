#!/usr/bin/env python3
"""
ESCO TTL Generator v1.0
Generiert eine saubere TTL-Datei aus ESCO v1.2.0 CSV-Daten

Berücksichtigt:
- Querschnittsfähigkeiten (Transversal Skills)
- Fähigkeiten (Skills/Competences) 
- Sprachliche Fähigkeiten (Language Skills)
- Kenntnisse (Knowledge)

Verwendet die gleichen w3id.org URIs wie escoSkills.ttl
"""

import csv
import os
import sys
from datetime import datetime
from typing import Dict, List, Set, Optional, Tuple
from urllib.parse import urlparse
import re

class ESCOTTLGenerator:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.skills = {}  # URI -> skill data
        self.skill_groups = {}  # URI -> group data
        self.broader_relations = {}  # child_uri -> parent_uri
        self.collections = {
            'transversal': set(),
            'language': set(),
            'digital': set(),
            'green': set(),
            'research': set()
        }
        self.stats = {
            'total_skills': 0,
            'transversal_skills': 0,
            'language_skills': 0,
            'knowledge_items': 0,
            'skill_competences': 0,
            'broader_relations': 0,
            'collections_processed': 0
        }
        
    def _detect_encoding(self, filepath: str) -> str:
        """Erkennt das Encoding einer Datei"""
        encodings_to_try = ['utf-8-sig', 'utf-8', 'latin1', 'cp1252', 'iso-8859-1']
            
        # Teste bekannte Encodings
        for encoding in encodings_to_try:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    f.read(1000)  # Teste ersten 1000 Zeichen
                return encoding
            except UnicodeDecodeError:
                continue
                
        return 'utf-8'  # Default fallback
        
    def load_data(self):
        """Lädt alle relevanten ESCO CSV-Dateien"""
        print("[INFO] Loading ESCO data...")
        
        # 1. Skills laden
        self._load_skills()
        
        # 2. Skill Groups laden
        self._load_skill_groups()
        
        # 3. Hierarchie-Beziehungen laden
        self._load_broader_relations()
        
        # 4. Spezielle Collections laden
        self._load_collections()
        
        print(f"[OK] Data loaded successfully!")
        self._print_loading_stats()
        
    def _load_skills(self):
        """Lädt skills_de.csv"""
        skills_file = os.path.join(self.data_dir, 'skills_de.csv')
        if not os.path.exists(skills_file):
            raise FileNotFoundError(f"Skills file not found: {skills_file}")
            
        encoding = self._detect_encoding(skills_file)
        print(f"[INFO] Using encoding {encoding} for skills file")
        with open(skills_file, 'r', encoding=encoding) as f:
            reader = csv.DictReader(f)
            for row in reader:
                uri = row['conceptUri'].strip()
                
                # Nur KnowledgeSkillCompetence berücksichtigen
                if row['conceptType'] != 'KnowledgeSkillCompetence':
                    continue
                    
                skill_data = {
                    'uri': uri,
                    'concept_type': row['conceptType'],
                    'skill_type': row.get('skillType', ''),
                    'reuse_level': row.get('reuseLevel', ''),
                    'preferred_label': row['preferredLabel'].strip(),
                    'alt_labels': self._parse_alt_labels(row.get('altLabels', '')),
                    'description': row.get('description', '').strip(),
                    'definition': row.get('definition', '').strip(),
                    'scope_note': row.get('scopeNote', '').strip(),
                    'status': row.get('status', ''),
                    'modified_date': row.get('modifiedDate', ''),
                    'in_scheme': self._parse_in_scheme(row.get('inScheme', ''))
                }
                
                self.skills[uri] = skill_data
                self.stats['total_skills'] += 1
                
                # Statistiken nach Typ
                if skill_data['skill_type'] == 'knowledge':
                    self.stats['knowledge_items'] += 1
                elif skill_data['skill_type'] == 'skill/competence':
                    self.stats['skill_competences'] += 1
                    
                # Statistiken nach Reuse Level
                if skill_data['reuse_level'] == 'transversal':
                    self.stats['transversal_skills'] += 1
                    
    def _load_skill_groups(self):
        """Lädt skillGroups_de.csv"""
        groups_file = os.path.join(self.data_dir, 'skillGroups_de.csv')
        if not os.path.exists(groups_file):
            print(f"[WARNING] Skill groups file not found: {groups_file}")
            return
            
        encoding = self._detect_encoding(groups_file)
        with open(groups_file, 'r', encoding=encoding) as f:
            reader = csv.DictReader(f)
            for row in reader:
                uri = row['conceptUri'].strip()
                
                group_data = {
                    'uri': uri,
                    'concept_type': row['conceptType'],
                    'preferred_label': row['preferredLabel'].strip(),
                    'alt_labels': self._parse_alt_labels(row.get('altLabels', '')),
                    'description': row.get('description', '').strip(),
                    'code': row.get('code', '').strip(),
                    'status': row.get('status', ''),
                    'in_scheme': self._parse_in_scheme(row.get('inScheme', ''))
                }
                
                self.skill_groups[uri] = group_data
                
    def _load_broader_relations(self):
        """Lädt broaderRelationsSkillPillar_de.csv"""
        relations_file = os.path.join(self.data_dir, 'broaderRelationsSkillPillar_de.csv')
        if not os.path.exists(relations_file):
            print(f"[WARNING] Broader relations file not found: {relations_file}")
            return
            
        encoding = self._detect_encoding(relations_file)
        with open(relations_file, 'r', encoding=encoding) as f:
            reader = csv.DictReader(f)
            for row in reader:
                child_uri = row['conceptUri'].strip()
                parent_uri = row['broaderUri'].strip()
                
                self.broader_relations[child_uri] = parent_uri
                self.stats['broader_relations'] += 1
                
    def _load_collections(self):
        """Lädt spezielle Skill Collections"""
        collections_files = {
            'transversal': 'transversalSkillsCollection_de.csv',
            'language': 'languageSkillsCollection_de.csv',
            'digital': 'digitalSkillsCollection_de.csv',
            'green': 'greenSkillsCollection_de.csv',
            'research': 'researchSkillsCollection_de.csv'
        }
        
        for collection_name, filename in collections_files.items():
            filepath = os.path.join(self.data_dir, filename)
            if not os.path.exists(filepath):
                print(f"[WARNING] Collection file not found: {filepath}")
                continue
                
            encoding = self._detect_encoding(filepath)
            with open(filepath, 'r', encoding=encoding) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    uri = row['conceptUri'].strip()
                    self.collections[collection_name].add(uri)
                    
                    # Spezielle Zählung für Language Skills
                    if collection_name == 'language':
                        self.stats['language_skills'] += 1
                        
            self.stats['collections_processed'] += 1
            print(f"[OK] Loaded {len(self.collections[collection_name])} {collection_name} skills")
            
    def _parse_alt_labels(self, alt_labels_str: str) -> List[str]:
        """Parst alternative Labels"""
        if not alt_labels_str or alt_labels_str.strip() == '':
            return []
        
        # Split by | and clean
        labels = [label.strip() for label in alt_labels_str.split('|')]
        return [label for label in labels if label]
        
    def _parse_in_scheme(self, in_scheme_str: str) -> List[str]:
        """Parst inScheme URIs"""
        if not in_scheme_str or in_scheme_str.strip() == '':
            return []
            
        # Split by comma and clean
        schemes = [scheme.strip() for scheme in in_scheme_str.split(',')]
        return [scheme for scheme in schemes if scheme and scheme.startswith('http')]
        
    def _convert_to_w3id_uri(self, esco_uri: str) -> str:
        """Konvertiert ESCO URI zu w3id.org Format"""
        if not esco_uri.startswith('http://data.europa.eu/esco/skill/'):
            return esco_uri
            
        # Extrahiere UUID
        uuid = esco_uri.replace('http://data.europa.eu/esco/skill/', '')
        
        # Konvertiere zu w3id.org Format
        w3id_uri = f"http://w3id.org/openeduhub/vocabs/escoSkills/{uuid}"
        return w3id_uri
        
    def _get_relative_uri(self, full_uri: str) -> str:
        """Konvertiert zu relativer URI für TTL Output"""
        if full_uri.startswith('http://w3id.org/openeduhub/vocabs/escoSkills/'):
            uuid = full_uri.replace('http://w3id.org/openeduhub/vocabs/escoSkills/', '')
            return f"<{uuid}>"
        return f"<{full_uri}>"
        
    def generate_ttl(self, output_file: str):
        """Generiert die TTL-Datei"""
        print(f"[INFO] Generating TTL file: {output_file}")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            # Header schreiben
            self._write_ttl_header(f)
            
            # ConceptScheme schreiben
            self._write_concept_scheme(f)
            
            # Skills schreiben
            self._write_skills(f)
            
        print(f"[OK] TTL file generated: {output_file}")
        self._print_generation_stats()
        
    def _write_ttl_header(self, f):
        """Schreibt TTL Header mit @base und Prefixes"""
        f.write("@base <http://w3id.org/openeduhub/vocabs/escoSkills/> .\n")
        f.write("@prefix skos: <http://www.w3.org/2004/02/skos/core#> .\n")
        f.write("@prefix esco: <http://data.europa.eu/esco/skill/> .\n")
        f.write("@prefix dct: <http://purl.org/dc/terms/> .\n")
        f.write("@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n")
        f.write("\n")
        
    def _write_concept_scheme(self, f):
        """Schreibt ConceptScheme Definition"""
        f.write("<> a skos:ConceptScheme ;\n")
        f.write('    dct:title "ESCO Skills - Generated from ESCO v1.2.0"@de ;\n')
        f.write('    dct:description "Saubere TTL-Datei generiert aus ESCO v1.2.0 CSV-Daten"@de ;\n')
        f.write(f'    dct:created "{datetime.now().strftime("%Y-%m-%d")}"^^xsd:date ;\n')
        f.write('    skos:hasTopConcept <335228d2-297d-4e0e-a6ee-bc6a8dc110d9> .\n')
        f.write("\n")
        
    def _write_skills(self, f):
        """Schreibt alle Skills als SKOS Concepts"""
        written_count = 0
        
        for uri, skill in self.skills.items():
            # Konvertiere zu w3id.org URI
            w3id_uri = self._convert_to_w3id_uri(uri)
            relative_uri = self._get_relative_uri(w3id_uri)
            
            # Concept Definition
            f.write(f"{relative_uri} a skos:Concept ;\n")
            
            # Preferred Label
            pref_label = self._escape_ttl_string(skill['preferred_label'])
            f.write(f'    skos:prefLabel "{pref_label}"@de ;\n')
            
            # Alternative Labels
            for alt_label in skill['alt_labels']:
                if alt_label:
                    escaped_alt = self._escape_ttl_string(alt_label)
                    f.write(f'    skos:altLabel "{escaped_alt}"@de ;\n')
            
            # ESCO exactMatch
            esco_uuid = uri.replace('http://data.europa.eu/esco/skill/', '')
            f.write(f'    skos:exactMatch esco:{esco_uuid} ;\n')
            
            # Broader Relations
            if uri in self.broader_relations:
                broader_uri = self.broader_relations[uri]
                broader_w3id = self._convert_to_w3id_uri(broader_uri)
                broader_relative = self._get_relative_uri(broader_w3id)
                f.write(f'    skos:broader {broader_relative} ;\n')
            
            # Collection Memberships
            collections_found = []
            for collection_name, collection_uris in self.collections.items():
                if uri in collection_uris:
                    collections_found.append(collection_name)
            
            if collections_found:
                f.write(f'    # Collections: {", ".join(collections_found)}\n')
            
            # Definition/Description als scopeNote
            if skill['definition']:
                definition = self._escape_ttl_string(skill['definition'])
                f.write(f'    skos:scopeNote "{definition}"@de ;\n')
            elif skill['description']:
                description = self._escape_ttl_string(skill['description'])
                f.write(f'    skos:scopeNote "{description}"@de ;\n')
            
            # inScheme
            f.write('    skos:inScheme <> .\n')
            f.write("\n")
            
            written_count += 1
            
            # Progress
            if written_count % 1000 == 0:
                print(f"[INFO] Written {written_count} skills...")
                
        print(f"[OK] Written {written_count} skills to TTL")
        
    def _escape_ttl_string(self, text: str) -> str:
        """Escaped Strings für TTL Format"""
        if not text:
            return ""
            
        # Entferne führende/nachfolgende Whitespace
        text = text.strip()
        
        # Escape Anführungszeichen und Backslashes
        text = text.replace('\\', '\\\\')
        text = text.replace('"', '\\"')
        text = text.replace('\n', '\\n')
        text = text.replace('\r', '\\r')
        text = text.replace('\t', '\\t')
        
        return text
        
    def _print_loading_stats(self):
        """Druckt Lade-Statistiken"""
        print("\n" + "="*60)
        print("ESCO DATA LOADING STATISTICS")
        print("="*60)
        print(f"Total skills loaded:        {self.stats['total_skills']:,}")
        print(f"Knowledge items:            {self.stats['knowledge_items']:,}")
        print(f"Skill/Competences:          {self.stats['skill_competences']:,}")
        print(f"Transversal skills:         {self.stats['transversal_skills']:,}")
        print(f"Language skills:            {self.stats['language_skills']:,}")
        print(f"Broader relations:          {self.stats['broader_relations']:,}")
        print(f"Collections processed:      {self.stats['collections_processed']}")
        print("\nCOLLECTION SIZES:")
        for name, collection in self.collections.items():
            print(f"  {name.capitalize():12}: {len(collection):,}")
        print("="*60)
        
    def _print_generation_stats(self):
        """Druckt Generierungs-Statistiken"""
        print("\n" + "="*60)
        print("TTL GENERATION STATISTICS")
        print("="*60)
        print(f"Skills written to TTL:      {len(self.skills):,}")
        print(f"ESCO exactMatch refs:       {len(self.skills):,}")
        print(f"Broader relations:          {len(self.broader_relations):,}")
        print(f"Using w3id.org URIs:        YES")
        print(f"Base URI:                   http://w3id.org/openeduhub/vocabs/escoSkills/")
        print("="*60)


def main():
    if len(sys.argv) < 2:
        print("Usage: python esco_ttl_generator.py <esco_csv_directory> [output_file]")
        print("Example: python esco_ttl_generator.py 'ESCO dataset - v1.2.0 - classification - de - csv'")
        sys.exit(1)
        
    data_dir = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "esco_skills_clean.ttl"
    
    if not os.path.exists(data_dir):
        print(f"[ERROR] Data directory not found: {data_dir}")
        sys.exit(1)
        
    try:
        # Generator erstellen
        generator = ESCOTTLGenerator(data_dir)
        
        # Daten laden
        generator.load_data()
        
        # TTL generieren
        generator.generate_ttl(output_file)
        
        print(f"\n[SUCCESS] ESCO TTL file generated successfully!")
        print(f"Output file: {output_file}")
        print(f"Ready for upload to Skills&More Streamlit application!")
        
    except Exception as e:
        print(f"[ERROR] Failed to generate TTL: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
