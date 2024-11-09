import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import random
import yaml
import streamlit_authenticator as stauth
from config import *
from database import *
from backup import ExerciseLogBackup

# Initialize database on first run
init_db()

# Load authentication config
with open('auth_config.yaml') as file:
    config = yaml.load(file, Loader=yaml.SafeLoader)

# Create authenticator
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# Add login widget
name, authentication_status, username = authenticator.login('Login', 'main')

if authentication_status == False:
    st.error('Username/password is incorrect')
    st.stop()
elif authentication_status == None:
    st.warning('Please enter your username and password')
    st.stop()

# If authenticated, continue with the app
st.sidebar.title(f'Welcome {name}!')
authenticator.logout('Logout', 'sidebar')

def main():
    st.set_page_config(
        page_title="Family Exercise Logger",
        page_icon="💪",
        layout="wide"
    )
    
    # Verify password before showing any content
    if not check_password():
        return
    
    # Main app content (only shown after correct password)
    st.title("Family Exercise Logger")
    
    # Sidebar navigation
    page = st.sidebar.selectbox(
        "Choose a page",
        ["Dashboard", "Log Exercise", "Goals Management", 
         "View History", "Progress Analysis", "Personal Bests", "Backup Data"]
    )
    
    # Add a date filter in sidebar for all pages
    start_date = st.sidebar.date_input(
        "Start Date",
        datetime.now() - timedelta(days=30),
        key="sidebar_start_date"
    )
    end_date = st.sidebar.date_input(
        "End Date",
        datetime.now(),
        key="sidebar_end_date"
    )
    
    # Show logout button in sidebar
    if st.sidebar.button("Logout"):
        st.session_state["password_correct"] = False
        st.experimental_rerun()
    
    if page == "Dashboard":
        show_dashboard(start_date, end_date)
    elif page == "Log Exercise":
        log_exercise()
    elif page == "Goals Management":
        manage_goals()
    elif page == "View History":
        view_history(start_date, end_date)
    elif page == "Backup Data":
        show_backup_page()
    elif page == "Progress Analysis":
        show_analysis(start_date, end_date)
    elif page == "Personal Bests":
        show_personal_bests()

def main():
    st.set_page_config(
        page_title="Family Exercise Logger",
        page_icon="💪",
        layout="wide"
    )
    
    # Verify password before showing any content
    if not check_password():
        return
    
    # Main app content (only shown after correct password)
    st.title("Family Exercise Logger")
    
    # Sidebar navigation
    page = st.sidebar.selectbox(
        "Choose a page",
        ["Dashboard", "Log Exercise", "Goals Management", 
         "View History", "Progress Analysis", "Personal Bests", "Backup Data"]
    )
    
    # Add a date filter in sidebar for all pages
    start_date = st.sidebar.date_input(
        "Start Date",
        datetime.now() - timedelta(days=30),
        key="sidebar_start_date"
    )
    end_date = st.sidebar.date_input(
        "End Date",
        datetime.now(),
        key="sidebar_end_date"
    )
    
    # Show logout button in sidebar
    if st.sidebar.button("Logout"):
        st.session_state["password_correct"] = False
        st.experimental_rerun()
    
    if page == "Dashboard":
        show_dashboard(start_date, end_date)
    elif page == "Log Exercise":
        log_exercise()
    elif page == "Goals Management":
        manage_goals()
    elif page == "View History":
        view_history(start_date, end_date)
    elif page == "Backup Data":
        show_backup_page()
    elif page == "Progress Analysis":
        show_analysis(start_date, end_date)
    elif page == "Personal Bests":
        show_personal_bests()

def show_dashboard(start_date, end_date):
    st.header("Dashboard")
    
    # Recent Achievements
    st.subheader("🏆 Recent Achievements")
    achievements_df = get_recent_achievements()
    if not achievements_df.empty:
        for _, achievement in achievements_df.iterrows():
            with st.expander(f"{achievement['family_member']} - "
                           f"{achievement['exercise_type']} Goal Achieved! "
                           f"({achievement['achievement_date']})"):
                st.write(f"**Goal:** {achievement['description']}")
                st.write(f"**Target:** {achievement['target_value']} {achievement['goal_type']}")
                st.write(f"**Achieved:** {achievement['achieved_value']} {achievement['goal_type']}")
                st.write("---")
                if achievement['notes']:
                    st.write(f"*{achievement['notes']}*")
    else:
        st.info("No recent achievements. Keep pushing towards your goals! 💪")
        
    # Get recent data
    df = get_exercises(start_date=start_date, end_date=end_date)
    
    if not df.empty:
        # Show summary statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Workouts", len(df))
        with col2:
            unique_exercises = len(df['exercise_type'].unique())
            st.metric("Different Exercises", unique_exercises)
        with col3:
            active_goals = len(get_goals(status='active'))
            st.metric("Active Goals", active_goals)
        
        # Recent activity summary
        st.subheader("Recent Activities")
        for _, row in df.iterrows():
            with st.expander(
                f"{row['family_member']} - {row['exercise_type']} "
                f"({row['date']})"
            ):
                if row['reps_per_set'] is not None:
                    st.write(f"Sets: {row['sets']}")
                    st.write(f"Reps per set: {row['reps_per_set']}")
                if row['seconds_per_set'] is not None:
                    st.write(f"Time per set: {row['seconds_per_set']} seconds")
                if row['feeling']:
                    st.write(f"Feeling: {row['feeling']}")
                if row['notes']:
                    st.write(f"Notes: {row['notes']}")
    else:
        st.info("No recent activities found for the selected date range.")

def celebrate_achievement(achievement):
    """Display a celebratory message for achieved goals"""
    st.balloons()  # Streamlit's built-in celebration
    
    # Create a festive celebration card
    with st.container():
        st.markdown("""
            <style>
                .celebration-card {
                    background-color: #FFD700;
                    padding: 20px;
                    border-radius: 10px;
                    text-align: center;
                    margin: 20px 0;
                    animation: pulse 2s infinite;
                }
                @keyframes pulse {
                    0% { transform: scale(1); }
                    50% { transform: scale(1.05); }
                    100% { transform: scale(1); }
                }
            </style>
            """, unsafe_allow_html=True)
        
        st.markdown(f"""
            <div class="celebration-card">
                <h1>🎉 Congratulations! 🎉</h1>
                <h2>Goal Achieved!</h2>
                <p>{achievement['description']}</p>
                <h3>Target: {achievement['target_value']} {achievement['goal_type']}</h3>
                <h3>Achieved: {achievement['achieved_value']} {achievement['goal_type']}</h3>
            </div>
            """, unsafe_allow_html=True)
        
        # Add motivational quote
        quotes = [
            "Success is not final, failure is not fatal: it is the courage to continue that counts.",
            "The only way to do great work is to love what you do.",
            "Believe you can and you're halfway there.",
            "You're making incredible progress! Keep pushing forward!",
            "Every rep counts, every second matters - you're proving that today!",
            "This is just the beginning of what you can achieve!",
            "Hard work pays off - and you just proved it!",
            "From goal to achievement - you made it happen!",
            "Your dedication is inspiring!",
            "What an achievement! Time to set new heights!"
        ]
        st.write(f"💭 *{random.choice(quotes)}*")
        
        # Show achievement options
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Share Achievement"):
                # Generate shareable image/text
                share_text = f"I just achieved my goal of {achievement['target_value']} {achievement['goal_type']} in {achievement['exercise_type']}! 💪"
                st.code(share_text, language=None)
                st.info("Text copied to clipboard! Share your success with friends and family!")
        
        with col2:
            if st.button("Set New Goal"):
                st.session_state.page = "Goals Management"
                st.session_state.show_new_goal = True

def log_exercise():
    st.header("Log Exercise")
    
    col1, col2 = st.columns(2)
    
    with col1:
        family_member = st.selectbox("Family Member", FAMILY_MEMBERS)
        date = st.date_input("Date", datetime.now(), key="log_exercise_date")
        exercise_type = st.selectbox("Exercise", list(EXERCISE_TYPES.keys()))
        
    with col2:
        st.write(f"**Description:** {EXERCISE_TYPES[exercise_type]['description']}")
        num_sets = st.number_input("Number of Sets", min_value=1, value=1)
    
    # Dynamic form based on exercise type
    measurements = EXERCISE_TYPES[exercise_type]['measurements']
    
    reps_per_set = None
    seconds_per_set = None
    
    if 'reps' in measurements:
        st.subheader("Reps per Set")
        reps_per_set = []
        cols = st.columns(num_sets)
        for i, col in enumerate(cols):
            with col:
                reps = col.number_input(f"Set {i+1}", min_value=0, value=0, key=f"reps_set_{i}")
                reps_per_set.append(reps)
    
    if 'time' in measurements:
        st.subheader("Seconds per Set")
        seconds_per_set = []
        cols = st.columns(num_sets)
        for i, col in enumerate(cols):
            with col:
                seconds = col.number_input(f"Set {i+1} (seconds)", min_value=0, value=0, key=f"seconds_set_{i}")
                seconds_per_set.append(seconds)
    
    feeling = st.select_slider(
        "How did it feel?",
        options=['Very Easy', 'Easy', 'Moderate', 'Hard', 'Very Hard']
    )
    
    notes = st.text_area("Notes (optional)")
    
    if st.button("Save Exercise"):
        try:
            # Save exercise and check for achievements
            exercise_id, achievements = add_exercise(
                family_member=family_member,
                date=date,
                exercise_type=exercise_type,
                sets=num_sets,
                reps_per_set=reps_per_set,
                seconds_per_set=seconds_per_set,
                notes=notes,
                feeling=feeling
            )
            
            # Celebrate any achievements
            if achievements:
                for achievement in achievements:
                    celebrate_achievement(achievement)
            else:
                st.success("Exercise logged successfully!")
                
                # Show progress towards goals
                active_goals = get_goals(family_member=family_member, status='active')
                if not active_goals.empty:
                    st.write("Progress towards goals:")
                    for _, goal in active_goals.iterrows():
                        if goal['exercise_type'] == exercise_type:
                            progress = (goal['current_value'] / goal['target_value']) * 100
                            st.progress(min(progress / 100, 1.0))
                            st.write(f"{goal['description']}: {goal['current_value']}/{goal['target_value']} "
                                    f"({progress:.1f}% complete)")
        except Exception as e:
            st.error(f"Error saving exercise: {str(e)}")

def view_history(start_date, end_date):
    st.header("Exercise History")
    
    # Filters
    col1, col2 = st.columns(2)
    
    with col1:
        member_filter = st.selectbox(
            "Family Member",
            ["All"] + FAMILY_MEMBERS,
            key="history_member_filter"
        )
    
    # Get filtered data
    df = get_exercises(
        family_member=member_filter if member_filter != "All" else None,
        start_date=start_date,
        end_date=end_date
    )
    
    if not df.empty:
        # Display as a table
        st.dataframe(
            df[['date', 'family_member', 'exercise_type', 'sets', 'feeling', 'notes']],
            hide_index=True
        )
        
        # Show detailed views in expanders
        for _, row in df.iterrows():
            with st.expander(f"Details - {row['exercise_type']} on {row['date']}"):
                if row['reps_per_set'] is not None:
                    st.write(f"Reps per set: {row['reps_per_set']}")
                if row['seconds_per_set'] is not None:
                    st.write(f"Seconds per set: {row['seconds_per_set']}")
                if row['notes']:
                    st.write(f"Notes: {row['notes']}")
    else:
        st.info("No exercises found for the selected filters.")

def show_analysis(start_date, end_date):
    st.header("Progress Analysis")
    
    # Filter controls
    col1, col2 = st.columns(2)
    with col1:
        member_filter = st.selectbox(
            "Family Member",
            ["All"] + FAMILY_MEMBERS,
            key="analysis_member_filter"
        )
    
    df = get_exercises(
        family_member=member_filter if member_filter != "All" else None,
        start_date=start_date,
        end_date=end_date
    )
    
    if not df.empty:
        # Exercise distribution
        st.subheader("Exercise Distribution")
        fig = px.pie(
            df,
            names='exercise_type',
            title="Exercise Type Distribution"
        )
        st.plotly_chart(fig)
        
        # Progress over time
        st.subheader("Progress Over Time")
        for exercise_type in df['exercise_type'].unique():
            exercise_df = df[df['exercise_type'] == exercise_type]
            
            # For exercises measured in reps
            if 'reps' in EXERCISE_TYPES[exercise_type]['measurements']:
                max_reps = []
                dates = []
                
                for _, row in exercise_df.iterrows():
                    if row['reps_per_set']:
                        max_reps.append(max(row['reps_per_set']))
                        dates.append(row['date'])
                
                if max_reps:
                    progress_df = pd.DataFrame({
                        'date': dates,
                        'max_reps': max_reps
                    })
                    
                    fig = px.line(
                        progress_df,
                        x='date',
                        y='max_reps',
                        title=f"{exercise_type} - Max Reps Progress"
                    )
                    st.plotly_chart(fig)
    else:
        st.info("No data available for the selected filters.")

def show_personal_bests():
    st.header("Personal Bests")
    
    pbs_df = get_personal_bests()
    
    if not pbs_df.empty:
        for member in FAMILY_MEMBERS:
            member_pbs = pbs_df[pbs_df['family_member'] == member]
            if not member_pbs.empty:
                st.subheader(f"{member}'s Personal Bests")
                
                for _, pb in member_pbs.iterrows():
                    st.write(
                        f"**{pb['exercise_type']}** - "
                        f"{pb['value']} {pb['measurement_type']} "
                        f"({pb['date']})"
                    )
                st.write("---")
    else:
        st.info("No personal bests recorded yet.")

def show_backup_page():
    st.header("Backup Data")
    
    st.write("""
    Create backups of your exercise data in multiple formats:
    - **SQLite (.db)**: Complete database backup for system restore
    - **CSV (.zip)**: Spreadsheet-friendly format for data analysis
    - **JSON**: Structured format for data interoperability
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Create SQLite Backup"):
            with st.spinner("Creating SQLite backup..."):
                backup = ExerciseLogBackup()
                path = backup.create_sqlite_backup()
                st.success(f"SQLite backup created: {path}")

    with col2:
        if st.button("Create CSV Backup"):
            with st.spinner("Creating CSV backup..."):
                backup = ExerciseLogBackup()
                path = backup.create_csv_backup()
                st.success(f"CSV backup created: {path}")

    with col3:
        if st.button("Create JSON Backup"):
            with st.spinner("Creating JSON backup..."):
                backup = ExerciseLogBackup()
                path = backup.create_json_backup()
                st.success(f"JSON backup created: {path}")

    if st.button("Create Full Backup (All Formats)"):
        with st.spinner("Creating full backup in all formats..."):
            backup = ExerciseLogBackup()
            paths = backup.create_full_backup()
            
            st.success("Full backup created successfully!")
            st.write("Backup files created:")
            for format, path in paths.items():
                st.write(f"- {format.upper()}: {path}")

    # Show existing backups
    st.subheader("Existing Backups")
    if os.path.exists('backups'):
        backups = os.listdir('backups')
        if backups:
            for backup_file in sorted(backups, reverse=True):
                with st.expander(backup_file):
                    file_path = os.path.join('backups', backup_file)
                    st.write(f"Created: {datetime.fromtimestamp(os.path.getctime(file_path))}")
                    st.write(f"Size: {os.path.getsize(file_path) / 1024:.1f} KB")
        else:
            st.info("No backups found")
    else:
        st.info("No backups directory found")

def manage_goals():
    st.header("Goals Management")
    
    tab1, tab2 = st.tabs(["Active Goals", "Set New Goal"])
    
    with tab1:
        show_active_goals()
    
    with tab2:
        set_new_goal()

def show_active_goals():
    st.subheader("Active Goals")
    
    goals_df = get_goals()
    
    if not goals_df.empty:
        for member in FAMILY_MEMBERS:
            member_goals = goals_df[goals_df['family_member'] == member]
            if not member_goals.empty:
                st.write(f"**{member}'s Goals**")
                
                for _, goal in member_goals.iterrows():
                    with st.expander(f"{goal['exercise_type']} - {goal['goal_type']}"):
                        progress = (goal['current_value'] / goal['target_value']) * 100
                        st.progress(min(progress / 100, 1.0))
                        st.write(f"Target: {goal['target_value']}")
                        st.write(f"Current: {goal['current_value']}")
                        
                        if goal['target_date']:
                            days_left = (pd.to_datetime(goal['target_date']) - pd.Timestamp.now()).days
                            st.write(f"Days remaining: {max(0, days_left)}")
                        
                        if st.button("Archive Goal", key=f"archive_{goal['id']}"):
                            update_goal_status(goal['id'], 'archived')
                            st.experimental_rerun()
    else:
        st.info("No active goals found.")

def set_new_goal():
    st.subheader("Set New Goal")
    
    col1, col2 = st.columns(2)
    
    with col1:
        family_member = st.selectbox("Family Member", FAMILY_MEMBERS, key="new_goal_member")
        exercise_type = st.selectbox("Exercise Type", list(EXERCISE_TYPES.keys()), key="new_goal_exercise")
        goal_type = st.selectbox(
            "Goal Type",
            EXERCISE_TYPES[exercise_type]['valid_goals'],
            key="new_goal_type"
        )
    
    with col2:
        target_value = st.number_input(
            f"Target Value ({GOAL_TYPES[goal_type]['unit']})",
            min_value=1,
            value=1,
            key="new_goal_target"
        )
        start_date = st.date_input("Start Date", datetime.now(), key="new_goal_start")
        has_target_date = st.checkbox("Set target date?", key="new_goal_has_target")
    
    if has_target_date:
        target_date = st.date_input(
            "Target Date",
            datetime.now() + timedelta(days=30),
            key="new_goal_target_date"
        )
    else:
        target_date = None
    
    description = st.text_area(
        "Description (optional)",
        key="new_goal_description",
        placeholder="Describe your goal and why you want to achieve it..."
    )
    
    if st.button("Create Goal", key="new_goal_submit"):
        add_goal(
            family_member=family_member,
            exercise_type=exercise_type,
            goal_type=goal_type,
            target_value=target_value,
            start_date=start_date,
            target_date=target_date,
            description=description
        )
        st.success("Goal created successfully!")

if __name__ == "__main__":
    main()
