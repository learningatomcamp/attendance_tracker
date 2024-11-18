import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import time
import numpy as np
from datetime import datetime
import File_handling as fl
from io import StringIO
import sqlite3
import re


# Function to create the database and table
def create_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Function to add a new user
def add_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
    conn.commit()
    conn.close()

# Function to verify user credentials
def verify_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
    user = c.fetchone()
    conn.close()
    return user

# Function to check password validity
def is_valid_password(password):
    # Minimum 8 characters long
    if len(password) < 8:
        return False
    
    # At least one uppercase letter
    if not re.search(r'[A-Z]', password):
        return False
    
    # At least one lowercase letter
    if not re.search(r'[a-z]', password):
        return False
    
    # At least one number
    if not re.search(r'[0-9]', password):
        return False
    
    # At least one special character
    if not re.search(r'[\W_]', password):
        return False
    
    return True

# Function to register a new user
def register_user(username, password):
    if not is_valid_password(password):
        st.sidebar.error("Password must be at least 8 characters long, include an uppercase letter, a lowercase letter, a number, and a special character.")
        return False
    
    try:
        add_user(username, password)
        st.sidebar.success("User registered successfully!")
        return True
    except sqlite3.IntegrityError:
        st.sidebar.error("Username already exists.")
        return False

# Initialize the database
create_db()

# Streamlit app
st.set_page_config(layout="wide")

# Login and Registration section
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.sidebar.title("Login or Register")
    
    option = st.sidebar.selectbox("Choose an option", ["Login", "Register"])
    
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    
    if option == "Login":
        if st.sidebar.button("Login"):
            user = verify_user(username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.sidebar.success("Login successful!")
            else:
                st.sidebar.error("Invalid username or password")
    
    if option == "Register":
        st.sidebar.info("Only logged-in users can register new users.")

if st.session_state.logged_in:
    st.sidebar.title(f"Welcome, {st.session_state.username}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.sidebar.success("You have been logged out.")
        st.experimental_rerun()

    st.title("Attendance Tracker")
    # Your existing Streamlit code goes here
    with open('ui.html', 'r') as f:
        html_content = f.read()
    components.html(html_content, height=100) 

    # accessing the api key here 
    GITHUB_TOKEN = st.secrets["GitHub"]["apikey"]
    REPO = "AzeemChaudhry/attendance_merger"
    BRANCH = "main"

    col1, col2 = st.columns(2)

    def parse_duration(duration_str):
        minutes = 0
        hours_match = re.search(r'(\d+)\s*hr', duration_str)
        minutes_match = re.search(r'(\d+)\s*min', duration_str)
        if hours_match:
            hours = int(hours_match.group(1))
            minutes += hours * 60
        if minutes_match:
            minutes += int(minutes_match.group(1))
        return minutes

    def main():
        # available files (can be changed later)
        menu = ["AI", "DS", "ML", "DA Gray", "DA Black", "DA White", "DS6", "DS7 Blue", "DS7 Green"]

        col1.subheader("Attendance")

        datafile = col1.file_uploader("Upload CSV", type=['csv'])
        # loading data if file is uploaded.
        if datafile is not None:
            df = pd.read_csv(datafile)
            col1.dataframe(df)  # confirming that the right file is uploaded
            # choosing from the daily file.
            choice = col1.selectbox("Course", menu)
            current_date = col1.date_input("Enter the date", format="DD-MM-YYYY")
            current_date_str = current_date.strftime("%d-%m-%Y")
            if st.button("Update") and choice is not None:
                # Define URLs for the online files
                urls = {
                    "DA Black": "DA%20Cohort%2001(Black)%20-%20Trackerrr.csv",
                    "DA Gray": "DA%20Cohort%2001(Gray)%20-%20Tracker%20-%20Attendence.csv",
                    "DA White": "DA%20Cohort%2001(White)%20-%20Tracker.csv",
                    "DS6": "DS%20Cohort%2006%20-%20Tracker.csv",
                    "DS7 Blue": "DS%20Cohort%2007(Blue)%20-%20Tracker.csv",
                    "DS7 Green": "DS%20Cohort%2007(Green)%20-%20Tracker.csv"
                }

                if choice in urls:
                    try:
                        file_path = urls[choice]
                        original_content, sha = fl.get_file_content(file_path)
                        original_df = pd.read_csv(StringIO(original_content))
                        if current_date_str in original_df.columns:
                            st.write(original_df.columns)
                            st.warning("The date already exists in the dataset.")
                            return
                        #######################processing the data######################
                        df["Name"] = (df['First name'] + df['Last name']).str.replace(' ', '').str.lower()
                        # making it lower case to avoid errors
                        original_df['Name_lower'] = original_df['Name'].str.replace(' ', '').str.lower()  # removing spaces

                        # updating the duration column for the time the student attended the class
                        df['duration'] = df['Duration'].apply(parse_duration)

                        original_df['duration'] = df['duration']
                        # updating the attendance with 1 for present and 0 for absent
                        original_df[current_date] = np.where(original_df['Name_lower'].isin(df[df['duration'] >= 45]['Name']), 1, 0)

                        # dropping the extra name column and keeping the original
                        original_df.drop(columns=['Name_lower'], inplace=True)
                        df.drop(columns=['duration'], inplace=True)
                        original_df.drop(columns=['duration'], inplace=True)
                        df.drop(columns=['Name'], inplace=True)

                        # Update the file on GitHub
                        updated_content = original_df.to_csv(index=False)
                        fl.update_file(file_path, updated_content, sha)

                        col1.dataframe(original_df)
                        st.success("Done ✔️")
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.error("Error: Could not find the course file")

    main()

    # Add new member section
    with st.sidebar.expander("Add a new member"):
        name2 = st.text_input("New Username")
        password2 = st.text_input("New Password", type="password")
        if st.button("Add New Member"):
            if password2 and name2:
                register_user(name2, password2)
