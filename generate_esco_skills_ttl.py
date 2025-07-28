#!/usr/bin/env python3
"""
ESCO Skills TTL Generator

Generiert eine TTL-Datei aus den originalen ESCO CSV-Daten,
die analog zur bestehenden escoSkills.ttl strukturiert ist.

Die Datei bildet die 4 ESCO Skill-Kategorien als Top-Level-Konzepte ab:
1. Fähigkeiten (Skills) - S
2. Querschnittsfähigkeiten und -kompetenzen (Transversal Skills) - T  
3. Kenntnisse (Knowledge) - K
4. Sprachliche Fähigkeiten und Kenntnisse (Language Skills) - L
"""

import pandas as pd
import os
from pathlib import Path
from datetime import datetime
import uuid

class ESCOSkillsTTLGenerator:
    def __init__(self, csv_folder_path, output_file="escoSkillsneu.ttl"):
        self.csv_folder = Path(csv_folder_path)
        self.output_file = output_file
        self.base_uri = "http://w3id.org/openeduhub/vocabs/escoSkills/"
        self.esco_base = "http://data.europa.eu/esco/skill/"
        
        # Top-Level Skill Categories (aus der bestehenden escoSkills.ttl)
        self.top_level_skills = {
            "335228d2-297d-4e0e-a6ee-bc6a8dc110d9": {
                "label": "Fähigkeiten",
                "type": "skills",
                "code": "S"
            },
            "04a13491-b58c-4d33-8b59-8fad0d55fe9e": {
                "label": "Querschnittsfähigkeiten und -kompetenzen", 
                "type": "transversal",
                "code": "T"
            },
            "c46fcb45-5c14-4ffa-abed-5a43f104bb22": {
                "label": "Kenntnisse",
                "type": "knowledge", 
                "code": "K"
            },
            "e35a5936-091d-4e87-bafe-f264e55bd656": {
                "label": "Sprachliche Fähigkeiten und Kenntnisse",
                "type": "language",
                "code": "L"
            }
        }
        
        # Datenstrukturen für Skills und Hierarchien
        self.skills_data = {}
        self.skill_groups = {}
        self.hierarchies = {}
        self.broader_relations = {}
        
    def load_csv_data(self):
        """Lädt alle relevanten CSV-Dateien"""
        print("Lade CSV-Dateien...")
        
        # Skills laden
        skills_file = self.csv_folder / "skills_de.csv"
        if skills_file.exists():
            self.skills_df = pd.read_csv(skills_file)
            print(f"Skills geladen: {len(self.skills_df)} Einträge")
        
        # Skill Groups laden  
        skill_groups_file = self.csv_folder / "skillGroups_de.csv"
        if skill_groups_file.exists():
            self.skill_groups_df = pd.read_csv(skill_groups_file)
            print(f"Skill Groups geladen: {len(self.skill_groups_df)} Einträge")
        
        # Skills Hierarchy laden
        hierarchy_file = self.csv_folder / "skillsHierarchy_de.csv"
        if hierarchy_file.exists():
            self.hierarchy_df = pd.read_csv(hierarchy_file)
            print(f"Skills Hierarchy geladen: {len(self.hierarchy_df)} Einträge")
        
        # Broader Relations laden
        broader_file = self.csv_folder / "broaderRelationsSkillPillar_de.csv"
        if broader_file.exists():
            self.broader_df = pd.read_csv(broader_file)
            print(f"Broader Relations geladen: {len(self.broader_df)} Einträge")
        
        # Transversal Skills Collection laden
        transversal_file = self.csv_folder / "transversalSkillsCollection_de.csv"
        if transversal_file.exists():
            self.transversal_df = pd.read_csv(transversal_file)
            print(f"Transversal Skills geladen: {len(self.transversal_df)} Einträge")
    
    def extract_uuid_from_uri(self, uri):
        """Extrahiert UUID aus ESCO URI"""
        if pd.isna(uri) or not uri:
            return None
        return uri.split('/')[-1]
    
    def build_skill_hierarchy(self):
        """Baut die Skill-Hierarchie aus den CSV-Daten auf"""
        print("Baue Skill-Hierarchie auf...")
        
        # Skills aus skills_de.csv verarbeiten
        for _, row in self.skills_df.iterrows():
            uri = row['conceptUri']
            uuid = self.extract_uuid_from_uri(uri)
            if uuid:
                self.skills_data[uuid] = {
                    'uri': uri,
                    'prefLabel': row['preferredLabel'],
                    'altLabels': row.get('altLabels', ''),
                    'description': row.get('description', ''),
                    'definition': row.get('definition', ''),
                    'scopeNote': row.get('scopeNote', ''),
                    'skillType': row.get('skillType', ''),
                    'reuseLevel': row.get('reuseLevel', ''),
                    'type': 'KnowledgeSkillCompetence'
                }
        
        # Skill Groups aus skillGroups_de.csv verarbeiten
        for _, row in self.skill_groups_df.iterrows():
            uri = row['conceptUri']
            uuid = self.extract_uuid_from_uri(uri)
            if uuid:
                self.skill_groups[uuid] = {
                    'uri': uri,
                    'prefLabel': row['preferredLabel'],
                    'code': row.get('code', ''),
                    'type': 'SkillGroup'
                }
        
        # Hierarchie aus skillsHierarchy_de.csv verarbeiten
        for _, row in self.hierarchy_df.iterrows():
            level0_uri = row['Level 0 URI']
            level0_uuid = self.extract_uuid_from_uri(level0_uri)
            
            if level0_uuid and level0_uuid in self.top_level_skills:
                # Level 1
                level1_uri = row.get('Level 1 URI')
                if pd.notna(level1_uri):
                    level1_uuid = self.extract_uuid_from_uri(level1_uri)
                    if level1_uuid:
                        if level0_uuid not in self.hierarchies:
                            self.hierarchies[level0_uuid] = {'narrower': set(), 'broader': None}
                        if level1_uuid not in self.hierarchies:
                            self.hierarchies[level1_uuid] = {'narrower': set(), 'broader': level0_uuid}
                        
                        self.hierarchies[level0_uuid]['narrower'].add(level1_uuid)
                        
                        # Level 2
                        level2_uri = row.get('Level 2 URI')
                        if pd.notna(level2_uri):
                            level2_uuid = self.extract_uuid_from_uri(level2_uri)
                            if level2_uuid:
                                if level2_uuid not in self.hierarchies:
                                    self.hierarchies[level2_uuid] = {'narrower': set(), 'broader': level1_uuid}
                                
                                self.hierarchies[level1_uuid]['narrower'].add(level2_uuid)
                                
                                # Level 3
                                level3_uri = row.get('Level 3 URI')
                                if pd.notna(level3_uri):
                                    level3_uuid = self.extract_uuid_from_uri(level3_uri)
                                    if level3_uuid:
                                        if level3_uuid not in self.hierarchies:
                                            self.hierarchies[level3_uuid] = {'narrower': set(), 'broader': level2_uuid}
                                        
                                        self.hierarchies[level2_uuid]['narrower'].add(level3_uuid)
        
        # Broader Relations aus broaderRelationsSkillPillar_de.csv verarbeiten
        for _, row in self.broader_df.iterrows():
            concept_uri = row['conceptUri']
            broader_uri = row['broaderUri']
            
            concept_uuid = self.extract_uuid_from_uri(concept_uri)
            broader_uuid = self.extract_uuid_from_uri(broader_uri)
            
            if concept_uuid and broader_uuid:
                if concept_uuid not in self.hierarchies:
                    self.hierarchies[concept_uuid] = {'narrower': set(), 'broader': broader_uuid}
                else:
                    self.hierarchies[concept_uuid]['broader'] = broader_uuid
                
                if broader_uuid not in self.hierarchies:
                    self.hierarchies[broader_uuid] = {'narrower': set(), 'broader': None}
                
                self.hierarchies[broader_uuid]['narrower'].add(concept_uuid)
    
    def get_transitive_broader(self, uuid):
        """Berechnet alle transitiven broader-Beziehungen für einen Skill"""
        broader_list = []
        current = uuid
        
        while current and current in self.hierarchies and self.hierarchies[current]['broader']:
            broader = self.hierarchies[current]['broader']
            if broader not in broader_list:  # Zyklen vermeiden
                broader_list.append(broader)
                current = broader
            else:
                break
        
        return broader_list
    
    def generate_ttl_header(self):
        """Generiert TTL-Header mit Namespaces und ConceptScheme"""
        header = f"""@base <{self.base_uri}> .
@prefix dct: <http://purl.org/dc/terms/> .
@prefix esco: <{self.esco_base}> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix isced: <http://data.europa.eu/esco/isced-f/> .
@prefix isothes: <http://purl.org/iso25964/skos-thes#> .

<> a skos:ConceptScheme  ;
    dct:title "ESCO Skills"@de ;
    skos:hasTopConcept"""
        
        # Top Concepts hinzufügen
        top_concepts = [f"<{uuid}>" for uuid in self.top_level_skills.keys()]
        header += ",\n        ".join([""] + top_concepts) + " .\n\n"
        
        return header
    
    def generate_concept_ttl(self, uuid, concept_data, is_top_level=False):
        """Generiert TTL für ein einzelnes Concept"""
        ttl = f"<{uuid}> a skos:Concept ;\n"
        
        # exactMatch zu ESCO
        if 'uri' in concept_data:
            esco_uri = concept_data['uri'].replace('http://data.europa.eu/esco/skill/', 'esco:')
            ttl += f"    skos:exactMatch {esco_uri} ;\n"
        
        # Hierarchie-Beziehungen
        if uuid in self.hierarchies:
            hierarchy = self.hierarchies[uuid]
            
            # narrower
            if hierarchy['narrower']:
                narrower_list = sorted(list(hierarchy['narrower']))
                narrower_refs = [f"<{n}>" for n in narrower_list]
                ttl += "    skos:narrower " + ",\n        ".join(narrower_refs) + " ;\n"
            
            # broader (nur für nicht-Top-Level)
            if not is_top_level and hierarchy['broader']:
                ttl += f"    skos:broader <{hierarchy['broader']}> ;\n"
                
                # broaderTransitive
                transitive_broader = self.get_transitive_broader(uuid)
                if transitive_broader:
                    broader_refs = [f"<{b}>" for b in transitive_broader]
                    ttl += "    skos:broaderTransitive " + ",\n        ".join(broader_refs) + " ;\n"
        
        # Labels
        if 'prefLabel' in concept_data and concept_data['prefLabel']:
            ttl += f'    skos:prefLabel "{concept_data["prefLabel"]}"@de ;\n'
        
        # Alternative Labels
        if 'altLabels' in concept_data and pd.notna(concept_data['altLabels']) and concept_data['altLabels']:
            alt_labels = str(concept_data['altLabels']).split('|')
            for alt_label in alt_labels:
                alt_label = alt_label.strip()
                if alt_label:
                    ttl += f'    skos:altLabel "{alt_label}"@de ;\n'
        
        # Definition (aus description Feld)
        if 'description' in concept_data and pd.notna(concept_data['description']) and concept_data['description']:
            # Escape quotes in definition text
            definition_text = str(concept_data['description']).replace('"', '\\"').replace('\n', ' ').strip()
            if definition_text:
                ttl += f'    skos:definition "{definition_text}"@de ;\n'
        
        # Scope Note (falls vorhanden)
        if 'scopeNote' in concept_data and pd.notna(concept_data['scopeNote']) and concept_data['scopeNote']:
            scope_note_text = str(concept_data['scopeNote']).replace('"', '\\"').replace('\n', ' ').strip()
            if scope_note_text:
                ttl += f'    skos:scopeNote "{scope_note_text}"@de ;\n'
        
        # Schema-Zugehörigkeit
        if is_top_level:
            ttl += "    skos:topConceptOf <> .\n\n"
        else:
            ttl += "    skos:inScheme <> .\n\n"
        
        return ttl
    
    def generate_ttl(self):
        """Generiert die komplette TTL-Datei"""
        print("Generiere TTL-Datei...")
        
        ttl_content = self.generate_ttl_header()
        
        # Top-Level Skills generieren
        for uuid, skill_info in self.top_level_skills.items():
            concept_data = {
                'prefLabel': skill_info['label'],
                'uri': f"{self.esco_base}{uuid}"
            }
            ttl_content += self.generate_concept_ttl(uuid, concept_data, is_top_level=True)
        
        # Alle anderen Skills und Skill Groups generieren
        all_concepts = {}
        all_concepts.update(self.skills_data)
        all_concepts.update(self.skill_groups)
        
        # Sortiert nach UUID für konsistente Ausgabe
        for uuid in sorted(all_concepts.keys()):
            if uuid not in self.top_level_skills:  # Top-Level bereits generiert
                concept_data = all_concepts[uuid]
                ttl_content += self.generate_concept_ttl(uuid, concept_data, is_top_level=False)
        
        return ttl_content
    
    def save_ttl(self, ttl_content):
        """Speichert TTL-Inhalt in Datei"""
        output_path = Path(self.output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(ttl_content)
        
        print(f"TTL-Datei gespeichert: {output_path.absolute()}")
        print(f"Dateigröße: {output_path.stat().st_size / 1024 / 1024:.2f} MB")
    
    def generate(self):
        """Hauptmethode: Generiert TTL aus ESCO CSV-Daten"""
        print("=== ESCO Skills TTL Generator ===")
        print(f"CSV-Ordner: {self.csv_folder}")
        print(f"Output-Datei: {self.output_file}")
        print()
        
        # CSV-Daten laden
        self.load_csv_data()
        
        # Hierarchie aufbauen
        self.build_skill_hierarchy()
        
        # TTL generieren
        ttl_content = self.generate_ttl()
        
        # TTL speichern
        self.save_ttl(ttl_content)
        
        # Statistiken
        print("\n=== Statistiken ===")
        print(f"Skills: {len(self.skills_data)}")
        print(f"Skill Groups: {len(self.skill_groups)}")
        print(f"Hierarchie-Beziehungen: {len(self.hierarchies)}")
        print(f"Top-Level Skills: {len(self.top_level_skills)}")


def main():
    """Hauptfunktion"""
    # Pfade definieren
    csv_folder = "ESCO dataset - v1.2.0 - classification - de - csv"
    output_file = "escoSkillsneu.ttl"
    
    # Generator erstellen und ausführen
    generator = ESCOSkillsTTLGenerator(csv_folder, output_file)
    generator.generate()


if __name__ == "__main__":
    main()
