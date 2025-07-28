#!/usr/bin/env python3
"""
ESCO Occupations Enhanced TTL Generator

Generiert eine vollständige SKOS TTL-Datei aus den ESCO-Berufe-CSV-Dateien mit:
- Berufsbeschreibungen (skos:definition)
- Alternative Labels (skos:altLabel) 
- Versteckte Labels (skos:hiddenLabel)
- Anwendungsbereich (skos:scopeNote)
- Regulierungshinweise (skos:note)
- Vollständige ISCO-Hierarchie

Autor: Enhanced TTL Generator für ESCO Occupations
"""

import pandas as pd
import uuid
from pathlib import Path
import re

def escape_ttl_string(text):
    """Escape special characters for TTL format"""
    if pd.isna(text) or text == "":
        return ""
    text = str(text)
    # Escape backslashes first
    text = text.replace('\\', '\\\\')
    # Escape quotes
    text = text.replace('"', '\\"')
    # Escape newlines and tabs
    text = text.replace('\n', '\\n')
    text = text.replace('\r', '\\r')
    text = text.replace('\t', '\\t')
    return text

def process_multiline_labels(labels_text):
    """Process multiline label text into list of labels"""
    if pd.isna(labels_text) or labels_text == "":
        return []
    
    # Split by newlines and clean up
    labels = [label.strip() for label in str(labels_text).split('\n') if label.strip()]
    return labels

def get_local_uri(esco_uri):
    """Convert ESCO URI to local UUID-based URI"""
    # Extract identifier from ESCO URI and generate consistent UUID
    if pd.isna(esco_uri):
        return str(uuid.uuid4())
    
    # Use the last part of the URI as seed for UUID generation
    uri_parts = str(esco_uri).split('/')
    if len(uri_parts) > 0:
        seed = uri_parts[-1]
        # Generate UUID from seed for consistency
        namespace = uuid.UUID('12345678-1234-5678-1234-123456789abc')
        return str(uuid.uuid5(namespace, seed))
    
    return str(uuid.uuid4())

def get_transitive_broader_relations(isco_code, isco_groups_by_code, broader_relations_df):
    """Get all transitive broader relations for an ISCO code"""
    relations = []
    current_code = str(isco_code)
    
    while current_code in isco_groups_by_code:
        # Find broader relation
        broader_row = broader_relations_df[broader_relations_df['conceptUri'] == isco_groups_by_code[current_code]['conceptUri']]
        if not broader_row.empty:
            broader_uri = broader_row.iloc[0]['broaderUri']
            relations.append(broader_uri)
            
            # Find the code for the broader URI
            broader_code = None
            for code, group in isco_groups_by_code.items():
                if group['conceptUri'] == broader_uri:
                    broader_code = code
                    break
            
            if broader_code:
                current_code = broader_code
            else:
                break
        else:
            break
    
    return relations

def main():
    # Pfad zum CSV-Ordner
    csv_folder = Path("ESCO dataset - v1.2.0 - classification - de - csv")
    
    if not csv_folder.exists():
        print(f"[ERROR] CSV-Ordner nicht gefunden: {csv_folder}")
        return
    
    print("[INFO] Lade ESCO-Berufe-Daten...")
    
    # Lade CSV-Dateien
    occupations_df = pd.read_csv(csv_folder / "occupations_de.csv")
    isco_groups_df = pd.read_csv(csv_folder / "ISCOGroups_de.csv")
    broader_relations_df = pd.read_csv(csv_folder / "broaderRelationsOccPillar_de.csv")
    
    print(f"[OK] {len(occupations_df)} ESCO-Berufe geladen")
    print(f"[OK] {len(isco_groups_df)} ISCO-Gruppen geladen")
    print(f"[OK] {len(broader_relations_df)} Hierarchie-Beziehungen geladen")
    
    # Erstelle Lookup-Dictionary für ISCO-Gruppen
    isco_groups_by_code = {}
    for _, group in isco_groups_df.iterrows():
        isco_groups_by_code[str(group['code'])] = group
    
    # Finde Top-Level-Gruppen (die keine broader-Relation haben)
    top_level_groups = []
    for _, group in isco_groups_df.iterrows():
        has_broader = not broader_relations_df[broader_relations_df['conceptUri'] == group['conceptUri']].empty
        if not has_broader:
            top_level_groups.append(group)
    
    print(f"[INFO] Generiere erweiterte TTL-Datei: escoOccupationsEnhanced.ttl")
    
    # TTL Header
    ttl_content = """@base <http://w3id.org/openeduhub/vocabs/escoOccupations/> .
@prefix dct: <http://purl.org/dc/terms/> .
@prefix esco: <http://data.europa.eu/esco/> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .

<> a skos:ConceptScheme ;
    dct:title "ESCO Occupations (Enhanced)"@de ;"""
    
    # Add top concepts
    if top_level_groups:
        ttl_content += "\n    skos:hasTopConcept "
        top_concept_uris = [f"<{get_local_uri(group['conceptUri'])}>" for group in top_level_groups]
        ttl_content += ",\n    ".join(top_concept_uris)
        ttl_content += " .\n"
    
    print("[INFO] Schreibe Top-Level ISCO-Gruppen...")
    
    # Write top-level ISCO groups
    for group in top_level_groups:
        group_uri = get_local_uri(group['conceptUri'])
        ttl_content += f"\n<{group_uri}> a skos:Concept ;\n"
        ttl_content += f"    skos:prefLabel \"{escape_ttl_string(group['preferredLabel'])}\"@de ;\n"
        ttl_content += f"    skos:exactMatch <{group['conceptUri']}> ;\n"
        
        # Add narrower relations
        narrower_groups = []
        for _, rel in broader_relations_df.iterrows():
            if rel['broaderUri'] == group['conceptUri']:
                narrower_groups.append(get_local_uri(rel['conceptUri']))
        
        if narrower_groups:
            ttl_content += f"    skos:narrower "
            ttl_content += ", ".join([f"<{uri}>" for uri in narrower_groups])
            ttl_content += " ;\n"
        
        ttl_content += f"    skos:topConceptOf <> .\n"
    
    print("[INFO] Schreibe ISCO-Gruppen-Hierarchie...")
    
    # Write all other ISCO groups
    top_level_uris = {group['conceptUri'] for group in top_level_groups}
    for _, group in isco_groups_df.iterrows():
        if group['conceptUri'] in top_level_uris:
            continue  # Already written
        
        group_uri = get_local_uri(group['conceptUri'])
        ttl_content += f"\n<{group_uri}> a skos:Concept ;\n"
        ttl_content += f"    skos:prefLabel \"{escape_ttl_string(group['preferredLabel'])}\"@de ;\n"
        ttl_content += f"    skos:exactMatch <{group['conceptUri']}> ;\n"
        
        # Add description if available
        if not pd.isna(group.get('description', '')) and group.get('description', '').strip():
            ttl_content += f"    skos:definition \"{escape_ttl_string(group['description'])}\"@de ;\n"
        
        # Add narrower relations (occupations and sub-groups)
        narrower_items = []
        
        # Find narrower ISCO groups
        for _, rel in broader_relations_df.iterrows():
            if rel['broaderUri'] == group['conceptUri']:
                narrower_items.append(get_local_uri(rel['conceptUri']))
        
        # Find occupations in this group
        group_occupations = occupations_df[occupations_df['iscoGroup'] == group['code']]
        for _, occ in group_occupations.iterrows():
            narrower_items.append(get_local_uri(occ['conceptUri']))
        
        if narrower_items:
            ttl_content += f"    skos:narrower "
            ttl_content += ", ".join([f"<{uri}>" for uri in narrower_items])
            ttl_content += " ;\n"
        
        # Add broader relation
        broader_row = broader_relations_df[broader_relations_df['conceptUri'] == group['conceptUri']]
        if not broader_row.empty:
            broader_uri = get_local_uri(broader_row.iloc[0]['broaderUri'])
            ttl_content += f"    skos:broader <{broader_uri}> ;\n"
            
            # Add broaderTransitive relations
            transitive_relations = get_transitive_broader_relations(group['code'], isco_groups_by_code, broader_relations_df)
            if transitive_relations:
                ttl_content += f"    skos:broaderTransitive "
                ttl_content += ", ".join([f"<{get_local_uri(uri)}>" for uri in transitive_relations])
                ttl_content += " ;\n"
        
        ttl_content += f"    skos:inScheme <> .\n"
    
    print("[INFO] Schreibe ESCO-Berufe mit allen verfügbaren Informationen...")
    
    # Write ESCO occupations with enhanced information
    for _, occupation in occupations_df.iterrows():
        occupation_uri = get_local_uri(occupation['conceptUri'])
        
        ttl_content += f"\n<{occupation_uri}> a skos:Concept ;\n"
        ttl_content += f"    skos:prefLabel \"{escape_ttl_string(occupation['preferredLabel'])}\"@de ;\n"
        
        # Add alternative labels
        alt_labels = process_multiline_labels(occupation.get('altLabels', ''))
        if alt_labels:
            for alt_label in alt_labels:
                if alt_label and alt_label != occupation['preferredLabel']:  # Avoid duplicates
                    ttl_content += f"    skos:altLabel \"{escape_ttl_string(alt_label)}\"@de ;\n"
        
        # Add hidden labels
        hidden_labels = process_multiline_labels(occupation.get('hiddenLabels', ''))
        if hidden_labels:
            for hidden_label in hidden_labels:
                if hidden_label:
                    ttl_content += f"    skos:hiddenLabel \"{escape_ttl_string(hidden_label)}\"@de ;\n"
        
        # Add definition (description)
        if not pd.isna(occupation.get('description', '')) and occupation.get('description', '').strip():
            ttl_content += f"    skos:definition \"{escape_ttl_string(occupation['description'])}\"@de ;\n"
        
        # Add scope note
        if not pd.isna(occupation.get('scopeNote', '')) and occupation.get('scopeNote', '').strip():
            ttl_content += f"    skos:scopeNote \"{escape_ttl_string(occupation['scopeNote'])}\"@de ;\n"
        
        # Add regulated profession note
        if not pd.isna(occupation.get('regulatedProfessionNote', '')) and occupation.get('regulatedProfessionNote', '').strip():
            # Only add meaningful notes, skip generic URLs
            reg_note = occupation['regulatedProfessionNote']
            if not reg_note.startswith('http://data.europa.eu/esco/regulated-professions/unregulated'):
                ttl_content += f"    skos:note \"{escape_ttl_string(reg_note)}\"@de ;\n"
        
        # Add ESCO exact match
        ttl_content += f"    skos:exactMatch <{occupation['conceptUri']}> ;\n"
        
        # Add broader relation to ISCO group
        isco_group_code = str(occupation['iscoGroup'])
        if isco_group_code in isco_groups_by_code:
            isco_group_uri = get_local_uri(isco_groups_by_code[isco_group_code]['conceptUri'])
            ttl_content += f"    skos:broader <{isco_group_uri}> ;\n"
            
            # Add broaderTransitive relations
            transitive_relations = get_transitive_broader_relations(isco_group_code, isco_groups_by_code, broader_relations_df)
            if transitive_relations:
                ttl_content += f"    skos:broaderTransitive "
                ttl_content += ", ".join([f"<{get_local_uri(uri)}>" for uri in transitive_relations])
                ttl_content += " ;\n"
        
        ttl_content += f"    skos:inScheme <> .\n"
    
    # Schreibe TTL-Datei
    output_file = "escoOccupationsEnhanced.ttl"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(ttl_content)
    
    print(f"[OK] Erweiterte TTL-Datei generiert: {output_file}")
    
    # Statistiken
    print("\n" + "="*60)
    print("ESCO OCCUPATIONS ENHANCED TTL GENERATION REPORT")
    print("="*60)
    print(f"ESCO-Berufe verarbeitet: {len(occupations_df)}")
    print(f"ISCO-Gruppen verarbeitet: {len(isco_groups_df)}")
    print(f"Top-Level-Gruppen: {len(top_level_groups)}")
    print(f"Hierarchie-Beziehungen: {len(broader_relations_df)}")
    
    # Zähle verfügbare Zusatzinformationen
    descriptions_count = len(occupations_df[occupations_df['description'].notna() & (occupations_df['description'] != '')])
    alt_labels_count = len(occupations_df[occupations_df['altLabels'].notna() & (occupations_df['altLabels'] != '')])
    hidden_labels_count = len(occupations_df[occupations_df['hiddenLabels'].notna() & (occupations_df['hiddenLabels'] != '')])
    scope_notes_count = len(occupations_df[occupations_df['scopeNote'].notna() & (occupations_df['scopeNote'] != '')])
    
    print(f"\nZusätzliche Informationen:")
    print(f"Berufsbeschreibungen (skos:definition): {descriptions_count}")
    print(f"Alternative Labels (skos:altLabel): {alt_labels_count}")
    print(f"Versteckte Labels (skos:hiddenLabel): {hidden_labels_count}")
    print(f"Anwendungsbereiche (skos:scopeNote): {scope_notes_count}")
    print("="*60)
    
    print(f"\n[SUCCESS] ESCO Occupations Enhanced TTL erfolgreich generiert!")
    print(f"Output-Datei: {output_file}")

if __name__ == "__main__":
    main()
