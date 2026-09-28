"""
Supabase PostgreSQL Diagnostic & Migration Helper
Run this script to test your Supabase connection, verify tables, and sync curriculum data.

Usage:
    python backend/supabase_setup.py
"""

import os
import sys
from dotenv import load_dotenv

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

load_dotenv()


def test_and_sync_supabase():
    db_url = os.getenv("DATABASE_URL")
    print("==========================================================")
    print("SMART LAB — Supabase PostgreSQL Configuration & Sync")
    print("==========================================================")

    if not db_url or "postgresql" not in db_url and "postgres" not in db_url:
        print("[INFO] DATABASE_URL is not set to a PostgreSQL/Supabase URL.")
        print("To connect to Supabase:")
        print("1. Go to your Supabase Project Settings -> Database")
        print("2. Copy the URI / Connection String (Node/URI or Transaction Pooler)")
        print("   e.g. postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres")
        print("3. Set DATABASE_URL in your .env or backend/.env file.")
        print("\nCurrently using local zero-config SQLite database.")
        return

    print(f"[STATUS] Testing connection to DATABASE_URL: {db_url.split('@')[-1] if '@' in db_url else 'PostgreSQL'}...")

    try:
        from database import engine, init_db_and_seed, SessionLocal, Problem, User, TestCase, WriteUp, Exam, LabManual
        from sqlalchemy import text

        with engine.connect() as conn:
            res = conn.execute(text("SELECT current_database(), current_user, version()")).fetchone()
            print(f"[SUCCESS] Connected to Supabase!")
            print(f"  Database: {res[0]}")
            print(f"  User:     {res[1]}")
            print(f"  Version:  {res[2][:50]}...")

        print("\n[MIGRATION] Initializing database schema and seeding curriculum data on Supabase...")
        init_db_and_seed()

        db = SessionLocal()
        try:
            problem_count = db.query(Problem).count()
            user_count = db.query(User).count()
            testcase_count = db.query(TestCase).count()
            writeup_count = db.query(WriteUp).count()
            exam_count = db.query(Exam).count()
            manual_count = db.query(LabManual).count()

            print("\n[VERIFICATION] Supabase database contains:")
            print(f"  • Problems:    {problem_count}")
            print(f"  • Test Cases:  {testcase_count}")
            print(f"  • Users:       {user_count}")
            print(f"  • Write-Ups:   {writeup_count}")
            print(f"  • Exams:       {exam_count}")
            print(f"  • Lab Manuals: {manual_count}")
            print("\n[READY] Supabase is fully configured and ready for production!")
        finally:
            db.close()

    except Exception as e:
        print(f"\n[ERROR] Failed connecting to Supabase: {e}")
        print("Troubleshooting steps:")
        print("1. Ensure your database password does not contain unencoded special characters in the URL.")
        print("2. Use the Session Pooler (port 5432) or Transaction Pooler (port 6543) from Supabase settings.")
        print("3. Verify your IP / network allows outbound connections on port 5432/6543.")


if __name__ == "__main__":
    test_and_sync_supabase()
