# database.py
import sqlite3
import pandas as pd
import json
from datetime import datetime, date
from typing import Optional, List, Dict, Union, Any, Tuple
import numpy as np
import os

def init_db():
    """Initialize the database with all necessary tables."""
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    conn = sqlite3.connect('data/exercise_log.db')
    c = conn.cursor()
    
    # Exercises table
    c.execute('''
        CREATE TABLE IF NOT EXISTS exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            family_member TEXT NOT NULL,
            date DATE NOT NULL,
            exercise_type TEXT NOT NULL,
            sets INTEGER,
            reps_per_set TEXT,  -- JSON string array
            seconds_per_set TEXT,  -- JSON string array
            notes TEXT,
            feeling TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(family_member, date, exercise_type, created_at)
        )
    ''')
    
    # Goals table
    c.execute('''
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            family_member TEXT NOT NULL,
            exercise_type TEXT NOT NULL,
            goal_type TEXT NOT NULL,
            target_value REAL NOT NULL,
            current_value REAL DEFAULT 0,
            start_date DATE NOT NULL,
            target_date DATE,
            status TEXT DEFAULT 'active',
            description TEXT,
            achievement_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Goal Progress table
    c.execute('''
        CREATE TABLE IF NOT EXISTS goal_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal_id INTEGER NOT NULL,
            date DATE NOT NULL,
            value REAL NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (goal_id) REFERENCES goals (id)
        )
    ''')
    
    # Personal Bests table
    c.execute('''
        CREATE TABLE IF NOT EXISTS personal_bests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            family_member TEXT NOT NULL,
            exercise_type TEXT NOT NULL,
            measurement_type TEXT NOT NULL,
            value REAL NOT NULL,
            date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(family_member, exercise_type, measurement_type)
        )
    ''')
    
    # Achievements table
    c.execute('''
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal_id INTEGER,
            family_member TEXT NOT NULL,
            achievement_date DATE NOT NULL,
            exercise_type TEXT NOT NULL,
            goal_type TEXT NOT NULL,
            target_value REAL NOT NULL,
            achieved_value REAL NOT NULL,
            description TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (goal_id) REFERENCES goals (id)
        )
    ''')
    
    # Create indices for better performance
    c.execute('CREATE INDEX IF NOT EXISTS idx_exercises_family_member ON exercises(family_member)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_exercises_date ON exercises(date)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_goals_family_member ON goals(family_member)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_achievements_date ON achievements(achievement_date)')
    
    conn.commit()
    conn.close()

# In database.py

def add_exercise(
    family_member: str,
    date: Union[str, date],
    exercise_type: str,
    sets: Optional[int] = None,
    reps_per_set: Optional[List[int]] = None,
    seconds_per_set: Optional[List[int]] = None,
    notes: Optional[str] = None,
    feeling: Optional[str] = None
) -> Tuple[int, List[Dict]]:  # Now returns both ID and achievements
    """
    Add a new exercise entry to the database.
    
    Returns:
        Tuple containing (exercise_id, list of achievements)
    """
    conn = sqlite3.connect('data/exercise_log.db')
    c = conn.cursor()
    
    try:
        # Convert lists to JSON strings
        reps_json = json.dumps(reps_per_set) if reps_per_set else None
        seconds_json = json.dumps(seconds_per_set) if seconds_per_set else None
        
        # Insert exercise record
        c.execute('''
            INSERT INTO exercises (
                family_member, date, exercise_type, sets,
                reps_per_set, seconds_per_set, notes, feeling
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (family_member, date, exercise_type, sets,
              reps_json, seconds_json, notes, feeling))
        
        exercise_id = c.lastrowid
        
        # Update personal bests
        if reps_per_set:
            max_reps = max(reps_per_set)
            update_personal_best(c, family_member, exercise_type, 'reps', max_reps, date)
        
        if seconds_per_set:
            max_time = max(seconds_per_set)
            update_personal_best(c, family_member, exercise_type, 'time', max_time, date)
        
        # Check and update goals, get achievements
        achievements = update_goals_for_exercise(
            c, family_member, exercise_type, date, reps_per_set, seconds_per_set
        )
        
        conn.commit()
        return exercise_id, achievements
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def update_goals_for_exercise(
    cursor: sqlite3.Cursor,
    family_member: str,
    exercise_type: str,
    date: Union[str, date],
    reps_per_set: Optional[List[int]],
    seconds_per_set: Optional[List[int]]
) -> List[Dict]:
    """
    Update goals and return list of achievements.
    
    Returns:
        List of achievement dictionaries
    """
    achievements = []
    
    cursor.execute('''
        SELECT id, goal_type, target_value, current_value, description 
        FROM goals 
        WHERE family_member = ? 
        AND exercise_type = ? 
        AND status = 'active'
    ''', (family_member, exercise_type))
    
    active_goals = cursor.fetchall()
    
    for goal_id, goal_type, target_value, current_value, description in active_goals:
        new_value = None
        
        if goal_type == 'max_reps' and reps_per_set:
            new_value = max(reps_per_set)
        elif goal_type == 'total_reps' and reps_per_set:
            new_value = sum(reps_per_set)
        elif goal_type == 'max_time' and seconds_per_set:
            new_value = max(seconds_per_set)
        elif goal_type == 'total_time' and seconds_per_set:
            new_value = sum(seconds_per_set)
        
        if new_value and new_value >= target_value and current_value < target_value:
            # Record achievement
            cursor.execute('''
                INSERT INTO achievements (
                    goal_id, family_member, achievement_date, 
                    exercise_type, goal_type, target_value,
                    achieved_value, description
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (goal_id, family_member, date, exercise_type, 
                  goal_type, target_value, new_value, description))
            
            achievements.append({
                'goal_id': goal_id,
                'description': description,
                'target_value': target_value,
                'achieved_value': new_value,
                'exercise_type': exercise_type,
                'goal_type': goal_type
            })
        
        if new_value and new_value > current_value:
            # Update goal progress
            cursor.execute('''
                INSERT INTO goal_progress (goal_id, date, value, notes)
                VALUES (?, ?, ?, ?)
            ''', (goal_id, date, new_value, 
                  "🎉 Goal Achieved!" if new_value >= target_value else f"New best: {new_value}"))
            
            # Update goal status
            cursor.execute('''
                UPDATE goals 
                SET current_value = ?,
                    status = CASE WHEN ? >= target_value THEN 'achieved' ELSE status END,
                    achievement_date = CASE WHEN ? >= target_value THEN ? ELSE NULL END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (new_value, new_value, new_value, date if new_value >= target_value else None, goal_id))
    
    return achievements

def update_personal_best(
    cursor: sqlite3.Cursor,
    family_member: str,
    exercise_type: str,
    measurement_type: str,
    value: float,
    date: Union[str, date]
) -> None:
    """Update personal best if the new value is higher."""
    cursor.execute('''
        INSERT INTO personal_bests (
            family_member, exercise_type, measurement_type, value, date
        ) VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(family_member, exercise_type, measurement_type)
        DO UPDATE SET
            value = CASE WHEN excluded.value > value THEN excluded.value ELSE value END,
            date = CASE WHEN excluded.value > value THEN excluded.date ELSE date END
    ''', (family_member, exercise_type, measurement_type, value, date))

def get_exercises(
    family_member: Optional[str] = None,
    start_date: Optional[Union[str, date]] = None,
    end_date: Optional[Union[str, date]] = None,
    exercise_type: Optional[str] = None
) -> pd.DataFrame:
    """
    Retrieve exercise records with optional filtering.
    
    Returns:
        DataFrame containing exercise records
    """
    conn = sqlite3.connect('data/exercise_log.db')
    
    query = 'SELECT * FROM exercises WHERE 1=1'
    params = []
    
    if family_member:
        query += ' AND family_member = ?'
        params.append(family_member)
    if start_date:
        query += ' AND date >= ?'
        params.append(start_date)
    if end_date:
        query += ' AND date <= ?'
        params.append(end_date)
    if exercise_type:
        query += ' AND exercise_type = ?'
        params.append(exercise_type)
    
    query += ' ORDER BY date DESC, created_at DESC'
    
    df = pd.read_sql_query(query, conn, params=params)
    
    # Parse JSON columns
    if not df.empty:
        df['reps_per_set'] = df['reps_per_set'].apply(
            lambda x: json.loads(x) if x else None
        )
        df['seconds_per_set'] = df['seconds_per_set'].apply(
            lambda x: json.loads(x) if x else None
        )
    
    conn.close()
    return df

def get_personal_bests(
    family_member: Optional[str] = None,
    exercise_type: Optional[str] = None
) -> pd.DataFrame:
    """Retrieve personal bests with optional filtering."""
    conn = sqlite3.connect('data/exercise_log.db')
    
    query = 'SELECT * FROM personal_bests WHERE 1=1'
    params = []
    
    if family_member:
        query += ' AND family_member = ?'
        params.append(family_member)
    if exercise_type:
        query += ' AND exercise_type = ?'
        params.append(exercise_type)
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def add_goal(
    family_member: str,
    exercise_type: str,
    goal_type: str,
    target_value: float,
    start_date: Union[str, date],
    target_date: Optional[Union[str, date]] = None,
    description: Optional[str] = None
) -> int:
    """Add a new goal to the database."""
    conn = sqlite3.connect('data/exercise_log.db')
    c = conn.cursor()
    
    try:
        c.execute('''
            INSERT INTO goals (
                family_member, exercise_type, goal_type, target_value,
                start_date, target_date, description
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (family_member, exercise_type, goal_type, target_value,
              start_date, target_date, description))
        
        goal_id = c.lastrowid
        conn.commit()
        return goal_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_goals(
    family_member: Optional[str] = None,
    status: str = 'active'
) -> pd.DataFrame:
    """Retrieve goals with optional filtering."""
    conn = sqlite3.connect('data/exercise_log.db')
    
    query = 'SELECT * FROM goals WHERE status = ?'
    params = [status]
    
    if family_member:
        query += ' AND family_member = ?'
        params.append(family_member)
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def get_goal_progress(goal_id: int) -> pd.DataFrame:
    """Retrieve progress history for a specific goal."""
    conn = sqlite3.connect('data/exercise_log.db')
    df = pd.read_sql_query('''
        SELECT * FROM goal_progress 
        WHERE goal_id = ?
        ORDER BY date
    ''', conn, params=[goal_id])
    conn.close()
    return df

def get_recent_achievements(days: int = 30) -> pd.DataFrame:
    """Get recent achievements within the specified number of days."""
    conn = sqlite3.connect('data/exercise_log.db')
    
    query = '''
        SELECT * FROM achievements 
        WHERE achievement_date >= date('now', ?)
        ORDER BY achievement_date DESC, created_at DESC
    '''
    
    df = pd.read_sql_query(
        query,
        conn,
        params=[f'-{days} days']
    )
    
    conn.close()
    return df

def get_achievements_summary(family_member: Optional[str] = None) -> Dict[str, Any]:
    """Get summary statistics for achievements."""
    conn = sqlite3.connect('data/exercise_log.db')
    
    query = '''
        SELECT 
            COUNT(*) as total_achievements,
            COUNT(DISTINCT exercise_type) as unique_exercises,
            COUNT(DISTINCT date(achievement_date)) as achievement_days,
            MAX(achievement_date) as last_achievement,
            family_member
        FROM achievements
    '''
    
    if family_member:
        query += ' WHERE family_member = ?'
        query += ' GROUP BY family_member'
        df = pd.read_sql_query(query, conn, params=[family_member])
    else:
        query += ' GROUP BY family_member'
        df = pd.read_sql_query(query, conn)
    
    conn.close()
    
    if df.empty:
        return {}
    
    return {
        row['family_member']: {
            'total_achievements': row['total_achievements'],
            'unique_exercises': row['unique_exercises'],
            'achievement_days': row['achievement_days'],
            'last_achievement': row['last_achievement']
        }
        for _, row in df.iterrows()
    }

def update_goal_status(goal_id: int, status: str) -> None:
    """Update the status of a goal (active/achieved/archived)."""
    conn = sqlite3.connect('data/exercise_log.db')
    c = conn.cursor()
    
    try:
        c.execute('''
            UPDATE goals 
            SET status = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (status, goal_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def delete_goal(goal_id: int) -> None:
    """Delete a goal and its progress records."""
    conn = sqlite3.connect('data/exercise_log.db')
    c = conn.cursor()
    
    try:
        # Delete goal progress first (foreign key constraint)
        c.execute('DELETE FROM goal_progress WHERE goal_id = ?', (goal_id,))
        # Delete the goal
        c.execute('DELETE FROM goals WHERE id = ?', (goal_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def update_goals_for_exercise(cursor, family_member, exercise_type, date, reps_per_set, seconds_per_set):
    """Enhanced goal update function with achievement celebration"""
    achievements = []  # Track achievements in this session
    
    cursor.execute('''
        SELECT id, goal_type, target_value, current_value, description 
        FROM goals 
        WHERE family_member = ? 
        AND exercise_type = ? 
        AND status = 'active'
    ''', (family_member, exercise_type))
    
    active_goals = cursor.fetchall()
    
    for goal_id, goal_type, target_value, current_value, description in active_goals:
        new_value = None
        was_achieved = False
        
        if goal_type == 'max_reps' and reps_per_set:
            new_value = max(reps_per_set)
        elif goal_type == 'total_reps' and reps_per_set:
            new_value = sum(reps_per_set)
        elif goal_type == 'max_time' and seconds_per_set:
            new_value = max(seconds_per_set)
        elif goal_type == 'total_time' and seconds_per_set:
            new_value = sum(seconds_per_set)
        
        if new_value and new_value >= target_value and current_value < target_value:
            was_achieved = True
            
            # Record achievement
            cursor.execute('''
                INSERT INTO achievements (
                    goal_id, family_member, achievement_date, 
                    exercise_type, goal_type, target_value,
                    achieved_value, description
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (goal_id, family_member, date, exercise_type, 
                  goal_type, target_value, new_value, description))
            
            achievements.append({
                'goal_id': goal_id,
                'description': description,
                'target_value': target_value,
                'achieved_value': new_value,
                'exercise_type': exercise_type,
                'goal_type': goal_type
            })
        
        if new_value and new_value > current_value:
            # Update goal progress
            cursor.execute('''
                INSERT INTO goal_progress (goal_id, date, value, notes)
                VALUES (?, ?, ?, ?)
            ''', (goal_id, date, new_value, 
                  "🎉 Goal Achieved!" if was_achieved else f"New best: {new_value}"))
            
            # Update goal status
            cursor.execute('''
                UPDATE goals 
                SET current_value = ?,
                    status = CASE WHEN ? >= target_value THEN 'achieved' ELSE status END,
                    achievement_date = CASE WHEN ? >= target_value THEN ? ELSE NULL END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (new_value, new_value, new_value, date if was_achieved else None, goal_id))
    
    return achievements

def get_exercise_summary(
    family_member: Optional[str] = None,
    start_date: Optional[Union[str, date]] = None,
    end_date: Optional[Union[str, date]] = None
) -> Dict[str, Any]:
    """Get summary statistics for exercises."""
    df = get_exercises(family_member, start_date, end_date)
    
    if df.empty:
        return {}
    
    summary = {
        'total_exercises': len(df),
        'exercise_types': df['exercise_type'].value_counts().to_dict(),
        'dates': {
            'first': df['date'].min(),
            'last': df['date'].max()
        }
    }
    
    return summary