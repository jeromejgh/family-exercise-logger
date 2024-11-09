# initialize_db.py
import os
import sqlite3
from database import init_db

def reset_database():
    """Reset the database by removing existing file and reinitializing"""
    db_path = 'data/exercise_log.db'
    
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Remove existing database if it exists
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print(f"Removed existing database: {db_path}")
        except Exception as e:
            print(f"Error removing database: {e}")
            return
    
    # Initialize new database
    try:
        init_db()
        
        # Verify tables were created
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # Get list of tables
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = c.fetchall()
        
        print("\nSuccessfully created tables:")
        for table in tables:
            print(f"- {table[0]}")
            
        conn.close()
        print("\nDatabase initialization complete!")
        
    except Exception as e:
        print(f"Error initializing database: {e}")

if __name__ == "__main__":
    reset_database()