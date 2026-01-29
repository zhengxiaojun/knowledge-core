#!/usr/bin/env python3
"""
Database initialization script.
Creates all tables defined in sql_models.py
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.sql_models import init_db
from app.core.config import settings


def main():
    print("=" * 60)
    print("Database Initialization Script")
    print("=" * 60)
    print(f"Database URI: {settings.sqlalchemy_database_uri}")
    print("\nCreating all tables...")

    try:
        init_db()
        print("\n✓ Database initialization completed successfully!")
        print("\nTables created:")
        print("  - requirement_raw")
        print("  - requirement_std")
        print("  - test_point")
        print("  - test_case")
        print("  - defect")
        print("  - generation_task")
        print("  - generation_result")
        print("  - requirements (legacy)")
        print("  - knowledge_bases (legacy)")
        print("  - tasks (legacy)")
        print("\n" + "=" * 60)
    except Exception as e:
        print(f"\n✗ Database initialization failed: {e}")
        print("\nPlease check:")
        print("  1. MySQL server is running")
        print("  2. Database credentials are correct in .env file")
        print("  3. Database 'vx_knowledge' exists")
        print("\n" + "=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()

