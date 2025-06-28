import difflib
from django.db import connections
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import json

# Model for semantic similarity
MODEL = SentenceTransformer("all-MiniLM-L6-v2")

GLOBAL_DOCTOR_FIELDS = [
    "doctor_id",
    "full_name",
    "specialization",
    "hospital_name",
    "contact_info",
]

# Hospital DB configurations (no table names here now)
HOSPITAL_DBS = {
    "Hospital1": "hospital1_2lrw",
    "Hospital2": "hospital2",
    "Hospital3": "hospital3",
}


def list_tables(db_alias):
    vendor = connections[db_alias].vendor
    with connections[db_alias].cursor() as cursor:
        if vendor == 'postgresql':
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
        else:
            cursor.execute("SHOW TABLES;")
        return [row[0] for row in cursor.fetchall()]

def get_table_columns(db_alias, table):
    query = "SELECT column_name FROM information_schema.columns WHERE table_name = %s"
    with connections[db_alias].cursor() as cursor:
        cursor.execute(query, [table])
        return [row[0] for row in cursor.fetchall()]

def get_foreign_keys(db_alias, table_name):
    vendor = connections[db_alias].vendor
    if vendor == 'postgresql':
        query = """
        SELECT kcu.column_name, ccu.table_name, ccu.column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
          ON tc.constraint_name = kcu.constraint_name
         AND tc.constraint_schema = kcu.constraint_schema
        JOIN information_schema.constraint_column_usage AS ccu
          ON ccu.constraint_name = tc.constraint_name
         AND ccu.constraint_schema = tc.constraint_schema
        WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name = %s
        """
    elif vendor == 'mysql':
        query = """
        SELECT kcu.COLUMN_NAME, kcu.REFERENCED_TABLE_NAME, kcu.REFERENCED_COLUMN_NAME
        FROM information_schema.KEY_COLUMN_USAGE AS kcu
        WHERE kcu.TABLE_NAME = %s AND kcu.REFERENCED_TABLE_NAME IS NOT NULL AND kcu.CONSTRAINT_SCHEMA = DATABASE()
        """
    else:
        raise NotImplementedError("Unsupported DB vendor")

    with connections[db_alias].cursor() as cursor:
        cursor.execute(query, [table_name])
        return cursor.fetchall()

def find_name_pair(cols):
    name_cols = [c for c in cols if c.lower() in ("first_name", "last_name") or c.lower().endswith("_name")]
    if "first_name" in name_cols and "last_name" in name_cols:
        return "first_name", "last_name"
    if len(name_cols) >= 2:
        return name_cols[0], name_cols[1]
    return None

def best_match(global_field, local_cols, threshold=0.6):
    gf = global_field.lower()
    best, best_ratio = None, 0.0
    for col in local_cols:
        lc = col.lower()
        if gf in lc or lc in gf:
            return col
        ratio = difflib.SequenceMatcher(None, gf, lc).ratio()
        if ratio > best_ratio:
            best_ratio, best = ratio, col
    return best if best_ratio >= threshold else None

def semantic_table_match(target: str, candidates: list[str], threshold=0.5) -> str | None:
    if not candidates:
        return None
    target_emb = MODEL.encode([target], convert_to_tensor=True).cpu().numpy()
    candidate_embs = MODEL.encode(candidates, convert_to_tensor=True).cpu().numpy()
    sims = cosine_similarity(target_emb, candidate_embs)[0]
    idx = int(np.argmax(sims))
    return candidates[idx] if sims[idx] >= threshold else None

def build_gav_mapping():
    mapping = {"Global_Doctors": {}}
    for hospital, db in HOSPITAL_DBS.items():
        # Dynamically identify doctor table

        tables = list_tables(db)
        doctor_table = semantic_table_match("doctors", tables)
        # print(doctor_table)
        if not doctor_table:
            raise Exception(f"No doctor table found in {db}")

        local_cols = get_table_columns(db, doctor_table)
        fks = get_foreign_keys(db, doctor_table)

        col_map = {}
        confidence = {}

        for field in GLOBAL_DOCTOR_FIELDS:
            if field == "hospital_name":
                col_map[field] = f"'{hospital}'"
                confidence[field] = 1.0
                continue

            if field == "full_name":
                name_pair = find_name_pair(local_cols)
                if name_pair:
                    col_map[field] = f"CONCAT({name_pair[0]}, ' ', {name_pair[1]})"
                    confidence[field] = 0.95
                    continue

            best_local = best_match(field, local_cols)
            best_local_ratio = difflib.SequenceMatcher(None, field.lower(), best_local.lower()).ratio() if best_local else 0.0

            best_foreign = None
            best_foreign_ratio = 0.0

            for local_col, ref_table, _ in fks:
                ref_cols = get_table_columns(db, ref_table)
                ref_match = best_match(field, ref_cols)
                if ref_match:
                    ratio = difflib.SequenceMatcher(None, field.lower(), ref_match.lower()).ratio()
                    if ratio > best_foreign_ratio:
                        best_foreign = f"{ref_table}.{ref_match}"
                        best_foreign_ratio = ratio

            if best_foreign_ratio > best_local_ratio and best_foreign_ratio >= 0.6:
                col_map[field] = best_foreign
                confidence[field] = round(best_foreign_ratio, 2)
            elif best_local and best_local_ratio >= 0.6:
                col_map[field] = best_local
                confidence[field] = round(best_local_ratio, 2)
            else:
                col_map[field] = f"/* no match for {field} */"
                confidence[field] = 0.0

        joins = [
            f"JOIN {ref_table} ON {doctor_table}.{local_col} = {ref_table}.{ref_col}"
            for local_col, ref_table, ref_col in fks
        ]

        mapping["Global_Doctors"][hospital] = {
            "db": db,
            "table": doctor_table,
            "columns": col_map,
            "join": " ".join(joins) if joins else None,
        }
        
    return mapping
