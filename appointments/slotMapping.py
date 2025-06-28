
import re
from django.db import connections
import difflib
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# ─── Config ──────────────────────────────────────

GLOBAL_TABLE = "available_slots"
GLOBAL_SLOT_FIELDS = ["doctor_id", "slot_date", "slot_time", "slot_duration", "is_booked"]
TRANSFORMER_MODEL = 'all-MiniLM-L6-v2'
SEMANTIC_THRESHOLD = 0.5
FUZZY_THRESHOLD = 0.6

MODEL = SentenceTransformer(TRANSFORMER_MODEL)

# ─── DB Helpers ───────────────────────────────────

def list_tables(db_alias: str) -> list[str]:
    vendor = connections[db_alias].vendor
    with connections[db_alias].cursor() as c:
        if vendor == 'postgresql':
            c.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
        else:
            c.execute("SHOW TABLES;")
        return [row[0] for row in c.fetchall()]

def get_columns(db_alias: str, table_name: str) -> list[str]:
    with connections[db_alias].cursor() as c:
        c.execute("SELECT column_name FROM information_schema.columns WHERE table_name = %s;", [table_name])
        return [row[0] for row in c.fetchall()]

# ─── Matching ─────────────────────────────────────

def token_match(target: str, candidates: list[str], min_overlap: float = 1.0) -> str | None:
    t_tokens = set(re.split(r'\W+', target.lower()))
    best, best_score = None, 0.0
    for c in candidates:
        c_tokens = set(re.split(r'\W+', c.lower()))
        if not t_tokens or not c_tokens:
            continue
        score = len(t_tokens & c_tokens) / len(t_tokens | c_tokens)
        if score > best_score:
            best_score, best = score, c
    return best if best_score >= min_overlap else None

def semantic_match(target: str, candidates: list[str], embeddings: np.ndarray | None = None, threshold: float = SEMANTIC_THRESHOLD) -> str | None:
    target = target.lower()
    candidates = [c.lower() for c in candidates]
    if embeddings is None or embeddings.shape[0] != len(candidates):
        embeddings = MODEL.encode(candidates, convert_to_tensor=True).cpu().numpy()
    t_emb = MODEL.encode([target], convert_to_tensor=True).cpu().numpy()
    sims = cosine_similarity(t_emb, embeddings)[0]
    idx  = int(np.argmax(sims))
    return candidates[idx] if sims[idx] >= threshold else None

def fuzzy_match(target: str, candidates: list[str], threshold: float = FUZZY_THRESHOLD) -> str | None:
    best, best_ratio = None, 0.0
    t = target.lower()
    for c in candidates:
        ratio = difflib.SequenceMatcher(None, t, c.lower()).ratio()
        if ratio > best_ratio:
            best_ratio, best = ratio, c
    return best if best_ratio >= threshold else None

# ─── Mapping Builder ──────────────────────────────

def build_appointment_mapping():
    hospitals = {
        "Hospital1": "hospital1_2lrw",
        "Hospital2": "hospital2",
        "Hospital3": "hospital3",
    }

    GAV = {"Global_Appointments": {}}

    for hosp_name, db_alias in hospitals.items():
        tables = list_tables(db_alias)

        table = token_match(GLOBAL_TABLE, tables) \
             or semantic_match(GLOBAL_TABLE, tables) \
             or fuzzy_match(GLOBAL_TABLE, tables)

        if not table:
            raise RuntimeError(f"Could not find table matching '{GLOBAL_TABLE}' in DB '{db_alias}'")

        cols = get_columns(db_alias, table)
        embeddings = MODEL.encode(cols, convert_to_tensor=True).cpu().numpy()

        col_map = {}
        report  = []
        for gf in GLOBAL_SLOT_FIELDS:
            col = token_match(gf, cols)
            tech = 'token' if col else None

            if not col:
                col = semantic_match(gf, cols, embeddings=embeddings)
                tech = 'semantic' if col else tech

            if not col:
                col = fuzzy_match(gf, cols)
                tech = 'fuzzy' if col else tech

            if not col:
                col, tech = f"/* no match for {gf} */", 'none'

            col_map[gf] = col
            report.append((gf, col, tech))

        GAV["Global_Appointments"][hosp_name] = {
            "available_slots_table": table,
            "available_slots_columns": col_map,
            "db": db_alias
        }

        # Display result
        # print(f"\n=== {hosp_name} (db={db_alias}, table={table}) ===")
        # print(f"{'field':<15}{'mapped_column':<25}{'technique'}")
        # print('-'*60)
        # for gf, col, tech in report:
        #     print(f"{gf:<15}{col:<25}{tech}")
        
    return GAV
