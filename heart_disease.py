import streamlit as st
import pandas as pd
import sqlite3

# Streamlit interface
st.title("Student Database Management System")

# Step 1: Connect to SQLite database
conn = sqlite3.connect('student_database.db')
cursor = conn.cursor()

# Create tables for students, courses, and enrollments
cursor.execute('''
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    FOREIGN KEY(student_id) REFERENCES students(id),
    FOREIGN KEY(course_id) REFERENCES courses(id)
)
''')
conn.commit()

# Step 2: Add a student
st.header("Add a Student")
name = st.text_input("Student Name")
email = st.text_input("Student Email")
if st.button("Add Student"):
    if name and email:
        try:
            cursor.execute("INSERT INTO students (name, email) VALUES (?, ?)", (name, email))
            conn.commit()
            st.success("Student added successfully!")
        except sqlite3.IntegrityError:
            st.error("Email must be unique.")
    else:
        st.error("Please enter both name and email.")

# Step 3: Add a course
st.header("Add a Course")
course_name = st.text_input("Course Name")
if st.button("Add Course"):
    if course_name:
        cursor.execute("INSERT INTO courses (name) VALUES (?)", (course_name,))
        conn.commit()
        st.success("Course added successfully!")
    else:
        st.error("Please enter a course name.")

# Step 4: Enroll a student in a course
st.header("Enroll a Student in a Course")
students = pd.read_sql_query("SELECT * FROM students", conn)
courses = pd.read_sql_query("SELECT * FROM courses", conn)

if not students.empty and not courses.empty:
    student_id = st.selectbox("Select Student", students["id"].apply(lambda x: f"{x}: {students[students['id'] == x]['name'].values[0]}").tolist(), format_func=lambda x: x.split(": ")[1])
    course_id = st.selectbox("Select Course", courses["id"].apply(lambda x: f"{x}: {courses[courses['id'] == x]['name'].values[0]}").tolist(), format_func=lambda x: x.split(": ")[1])

    if st.button("Enroll"):
        cursor.execute("INSERT INTO enrollments (student_id, course_id) VALUES (?, ?)", (student_id.split(": ")[0], course_id.split(": ")[0]))
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
        "SELECT enrollments.id, students.name AS student_name, courses.name AS course_name FROM enrollments "
        "JOIN students ON enrollments.student_id = students.id "
        "JOIN courses ON enrollments.course_id = courses.id", conn
    ))

# Step 6: Export data
if st.button("Export Data to CSV"):
    students_df = pd.read_sql_query("SELECT * FROM students", conn)
    courses_df = pd.read_sql_query("SELECT * FROM courses", conn)
    enrollments_df = pd.read_sql_query("SELECT * FROM enrollments", conn)

    students_df.to_csv("students.csv", index=False)
    courses_df.to_csv("courses.csv", index=False)
    enrollments_df.to_csv("enrollments.csv", index=False)

    st.success("Data exported to students.csv, courses.csv, and enrollments.csv")

# Step 7: Delete records
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
