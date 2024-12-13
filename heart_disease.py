import streamlit as st
import pandas as pd
import sqlite3

# Streamlit interface
st.title("Student Registration Portal")

# Step 1: Connect to SQLite database
conn = sqlite3.connect('student_database.db')
cursor = conn.cursor()

# Create tables for students and enrollments
cursor.execute('''
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    roll_no TEXT NOT NULL UNIQUE,
    department TEXT NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    duration TEXT NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    enrollment_date TEXT NOT NULL,
    FOREIGN KEY(student_id) REFERENCES students(id),
    FOREIGN KEY(course_id) REFERENCES courses(id)
)
''')
conn.commit()

# Step 2: Add a student
st.header("Register a Student")
name = st.text_input("Student Name")
roll_no = st.text_input("Roll Number")
department = st.text_input("Department")
if st.button("Add Student"):
    if name and roll_no and department:
        try:
            cursor.execute("INSERT INTO students (name, roll_no, department) VALUES (?, ?, ?)", (name, roll_no, department))
            conn.commit()
            st.success("Student registered successfully!")
        except sqlite3.IntegrityError:
            st.error("Roll number must be unique.")
    else:
        st.error("Please fill out all fields.")

# Step 3: Add a course
st.header("Add a Course")
course_name = st.text_input("Course Name")
course_duration = st.text_input("Course Duration")
if st.button("Add Course"):
    if course_name and course_duration:
        cursor.execute("INSERT INTO courses (name, duration) VALUES (?, ?)", (course_name, course_duration))
        conn.commit()
        st.success("Course added successfully!")
    else:
        st.error("Please fill out all fields.")

# Step 4: Enroll a student in a course
st.header("Enroll a Student in a Course")
students = pd.read_sql_query("SELECT * FROM students", conn)
courses = pd.read_sql_query("SELECT * FROM courses", conn)

if not students.empty and not courses.empty:
    student_id = st.selectbox("Select Student", students.apply(lambda x: f"{x['id']}: {x['name']} ({x['roll_no']})", axis=1))
    course_id = st.selectbox("Select Course", courses.apply(lambda x: f"{x['id']}: {x['name']} ({x['duration']})", axis=1))
    enrollment_date = st.date_input("Enrollment Date")

    if st.button("Enroll"):
        student_id = int(student_id.split(":")[0])
        course_id = int(course_id.split(":")[0])
        cursor.execute("INSERT INTO enrollments (student_id, course_id, enrollment_date) VALUES (?, ?, ?)", (student_id, course_id, enrollment_date))
        conn.commit()
        st.success("Enrollment successful!")
else:
    st.warning("Add students and courses before enrolling.")

# Step 5: View records
st.header("View Records")
view_option = st.selectbox("Select Table to View", ["Students", "Courses", "Enrollments"])
if view_option == "Students":
    st.dataframe(pd.read_sql_query("SELECT * FROM students", conn))
elif view_option == "Courses":
    st.dataframe(pd.read_sql_query("SELECT * FROM courses", conn))
else:
    st.dataframe(pd.read_sql_query(
        "SELECT enrollments.id, students.name AS student_name, students.roll_no, courses.name AS course_name, courses.duration, enrollments.enrollment_date "
        "FROM enrollments "
        "JOIN students ON enrollments.student_id = students.id "
        "JOIN courses ON enrollments.course_id = courses.id", conn
    ))

# Step 6: Delete records
st.header("Delete Records")
record_type = st.selectbox("Select Record Type to Delete", ["Student", "Course", "Enrollment"])
if record_type == "Student":
    student_id_to_delete = st.number_input("Enter Student ID", min_value=1)
    if st.button("Delete Student"):
        cursor.execute("DELETE FROM students WHERE id = ?", (student_id_to_delete,))
        conn.commit()
        st.success("Student record deleted.")
elif record_type == "Course":
    course_id_to_delete = st.number_input("Enter Course ID", min_value=1)
    if st.button("Delete Course"):
        cursor.execute("DELETE FROM courses WHERE id = ?", (course_id_to_delete,))
        conn.commit()
        st.success("Course record deleted.")
else:
    enrollment_id_to_delete = st.number_input("Enter Enrollment ID", min_value=1)
    if st.button("Delete Enrollment"):
        cursor.execute("DELETE FROM enrollments WHERE id = ?", (enrollment_id_to_delete,))
        conn.commit()
        st.success("Enrollment record deleted.")

# Close the connection
conn.close()

