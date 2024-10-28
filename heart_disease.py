import streamlit as st
import numpy as np
import pandas as pd
import sqlite3
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

# Streamlit interface
st.title("Heart Disease Prediction App")

# Initialize session state for prediction if not already done
if 'prediction' not in st.session_state:
    st.session_state.prediction = None

# Upload CSV
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
if uploaded_file is not None:
    heart_data = pd.read_csv(uploaded_file)
    st.write("Data Preview:")
    st.dataframe(heart_data.head())

    # Step 1: Connect to SQLite database and load the data
    conn = sqlite3.connect('heart_disease.db')
    cursor = conn.cursor()
    
    # Create table for heart disease data
    create_table_query = '''
    CREATE TABLE IF NOT EXISTS heart_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        age INTEGER,
        sex INTEGER,
        cp INTEGER,
        trestbps INTEGER,
        chol INTEGER,
        fbs INTEGER,
        restecg INTEGER,
        thalach INTEGER,
        exang INTEGER,
        oldpeak REAL,
        slope INTEGER,
        ca INTEGER,
        thal INTEGER,
        target INTEGER
    )
    '''
    cursor.execute(create_table_query)
    conn.commit()

    # Insert data into the SQL table
    heart_data.to_sql('heart_data', conn, if_exists='replace', index=False)
    st.write("Data successfully imported into the database.")

    # Step 2: Train the Model
    df = pd.read_sql_query("SELECT * FROM heart_data", conn)
    X = df.drop(columns='target', axis=1).values
    Y = df['target'].values

    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, stratify=Y, random_state=2)
    
    model = LogisticRegression(max_iter=200)
    model.fit(X_train, Y_train)

    train_accuracy = accuracy_score(Y_train, model.predict(X_train))
    test_accuracy = accuracy_score(Y_test, model.predict(X_test))
    
    st.write(f"Training Accuracy: {train_accuracy}")
    st.write(f"Test Accuracy: {test_accuracy}")

    # Step 3: Predict heart disease based on user input
    st.header("Predict Heart Disease")
    age = st.number_input("Age", min_value=1, max_value=120, value=30)
    sex = st.selectbox("Sex (0 = Female, 1 = Male)", [0, 1])
    cp = st.selectbox("Chest Pain Type (0, 1, 2, 3)", [0, 1, 2, 3])
    trestbps = st.number_input("Resting Blood Pressure", min_value=80, max_value=200, value=120)
    chol = st.number_input("Cholesterol Level", min_value=100, max_value=400, value=150)
    fbs = st.selectbox("Fasting Blood Sugar > 120 mg/dl (1 = True, 0 = False)", [0, 1])
    restecg = st.selectbox("Rest ECG (0, 1, 2)", [0, 1, 2])
    thalach = st.number_input("Max Heart Rate Achieved", min_value=50, max_value=250, value=140)
    exang = st.selectbox("Exercise Induced Angina (1 = Yes, 0 = No)", [0, 1])
    oldpeak = st.number_input("ST Depression Induced by Exercise", min_value=0.0, max_value=10.0, value=1.0)
    slope = st.selectbox("Slope of the Peak Exercise ST Segment (0, 1, 2)", [0, 1, 2])
    ca = st.selectbox("Number of Major Vessels (0-3)", [0, 1, 2, 3])
    thal = st.selectbox("Thal (1 = Normal, 2 = Fixed Defect, 3 = Reversable Defect)", [1, 2, 3])

    if st.button("Predict"):
        input_data = np.array([age, sex, cp, trestbps, chol, fbs, restecg, thalach, exang, oldpeak, slope, ca, thal]).reshape(1, -1)
        st.session_state.prediction = model.predict(input_data)  # Store prediction in session state

        if st.session_state.prediction[0] == 0:
            st.success("The person does not have heart disease.")
        else:
            st.warning("The person has heart disease.")

    # Step 4: Save predictions in SQL
    if st.button("Save Prediction"):
        if st.session_state.prediction is not None:  # Ensure prediction is made before saving
            predicted = int(st.session_state.prediction[0])  # Get the predicted value
            
            # Insert into predictions table
            cursor.execute("CREATE TABLE IF NOT EXISTS predictions (id INTEGER PRIMARY KEY AUTOINCREMENT, predicted INTEGER)")
            cursor.execute("INSERT INTO predictions (predicted) VALUES (?)", (predicted,))
            conn.commit()
            st.write("Prediction saved to the database.")
        else:
            st.error("Please make a prediction before saving.")

    # Step 5: Display predictions from the database
    if st.button("Show Predictions"):
        prediction_df = pd.read_sql_query("SELECT * FROM predictions", conn)
        st.write(prediction_df)

    # Step 6: Data Filtering
    st.header("Filter Data")
    age_filter = st.number_input("Filter Age", min_value=1, max_value=120)
    filtered_data = pd.read_sql_query(f"SELECT * FROM heart_data WHERE age > {age_filter}", conn)
    st.write(filtered_data)

    # Step 7: Update Records
    st.header("Update Record")
    record_id = st.number_input("Enter Record ID to Update", min_value=1, step=1)
    new_target = st.selectbox("New Target Value (0 or 1)", [0, 1])

    if st.button("Update Record"):
        try:
            # Attempt to update the record in the database
            cursor.execute("UPDATE heart_data SET target = ? WHERE id = ?", (new_target, record_id))
            
            # Commit the changes to the database
            conn.commit()
            
            # Check if any rows were affected
            if cursor.rowcount > 0:
                st.success("Record updated successfully.")
            else:
                st.warning("No record found with the specified ID.")

        except sqlite3.Error as e:
            st.error(f"An error occurred while updating the record: {e}")
        finally:
            pass

    # Step 8: Aggregate Data
    st.header("Aggregate Data")
    agg_query = "SELECT target, AVG(chol) as avg_chol FROM heart_data GROUP BY target"
    agg_data = pd.read_sql_query(agg_query, conn)
    st.write(agg_data)

    # Close the database connection
    conn.close()

