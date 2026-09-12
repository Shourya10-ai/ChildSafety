import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "local_dev.db")
print(f"Connecting to {db_path}...")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

def add_col_if_missing(table, column, col_type):
    cursor.execute(f"PRAGMA table_info({table})")
    existing = [r[1] for r in cursor.fetchall()]
    if column not in existing:
        print(f"Adding {column} to {table}...")
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")

add_col_if_missing("cases", "sla_deadline", "DATETIME")
add_col_if_missing("cases", "sla_breached", "BOOLEAN DEFAULT 0")
add_col_if_missing("cases", "sla_tier", "VARCHAR(30) DEFAULT 'STANDARD'")
add_col_if_missing("cases", "escalation_level", "INTEGER DEFAULT 0")

add_col_if_missing("sos_events", "is_silent_duress", "BOOLEAN DEFAULT 0")
add_col_if_missing("sos_events", "routed_to_alternate_adults_only", "BOOLEAN DEFAULT 0")

add_col_if_missing("adult_child_links", "is_alternate_trusted_adult", "BOOLEAN DEFAULT 0")
add_col_if_missing("adult_child_links", "nomination_status", "VARCHAR(30) DEFAULT 'APPROVED'")
add_col_if_missing("adult_child_links", "relationship_label", "VARCHAR(100)")
add_col_if_missing("adult_child_links", "vetted_by_moderator_id", "CHAR(32)")
add_col_if_missing("adult_child_links", "vetted_at", "DATETIME")
add_col_if_missing("adult_child_links", "vetting_notes", "TEXT")

conn.commit()
print("Migration completed successfully!")

for table in ["cases", "sos_events", "adult_child_links"]:
    cursor.execute(f"PRAGMA table_info({table})")
    cols = [r[1] for r in cursor.fetchall()]
    print(f"{table} columns: {cols}")

conn.close()
