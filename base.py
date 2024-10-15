import streamlit as st
import pandas as pd
import requests


# Function to hit each endpoint and get the response
def get_api_data(base_url):
    endpoints = [
        "api/categories",
        "api/categories/1001",
        "api/books/1001",
        "api/categories/1001/books",
        "api/categories/1001/suggested-books",
        "api/categories/1001/suggested-books?limit=2"
    ]

    results = {}

    for endpoint in endpoints:
        full_url = f"{base_url}/{endpoint}"
        try:
            response = requests.get(full_url)
            response.raise_for_status()  # Check for HTTP errors
            results[endpoint] = response.text  # Storing response as text
        except requests.exceptions.RequestException as e:
            results[endpoint] = f"Error: {str(e)}"

    return results


# Streamlit app
st.title("Student API Grading App")

# File uploader to upload the CSV file
uploaded_file = st.file_uploader("Upload a CSV file with students' base URLs", type="csv")

if uploaded_file is not None:
    # Read the uploaded CSV file
    df = pd.read_csv(uploaded_file)

    st.write("CSV Data Preview:")
    st.dataframe(df)  # Display the dataframe

    # List to store all student results for table presentation
    student_results = []

    # Processing each student's base URL
    if st.button('Start Grading'):
        for index, row in df.iterrows():
            student_name = row['student_name']  # Assuming the column name for student name
            base_url = row['base_url']  # Assuming the column name for base URL
            st.write(f"Processing for {student_name} at {base_url}...")

            # Get the API data for this student
            api_results = get_api_data(base_url)

            # Append the student's name and results for each API endpoint
            student_row = {
                'student_name': student_name,
                'api/categories': api_results.get("api/categories", "N/A"),
                'api/categories/1001': api_results.get("api/categories/1001", "N/A"),
                'api/books/1001': api_results.get("api/books/1001", "N/A"),
                'api/categories/1001/books': api_results.get("api/categories/1001/books", "N/A"),
                'api/categories/1001/suggested-books': api_results.get("api/categories/1001/suggested-books", "N/A"),
                'api/categories/1001/suggested-books?limit=2': api_results.get(
                    "api/categories/1001/suggested-books?limit=2", "N/A")
            }

            student_results.append(student_row)

        # Convert the list of student results to a DataFrame for display
        results_df = pd.DataFrame(student_results)

        # Display the results table
        st.write("API Results for Students:")
        st.dataframe(results_df)

        # Option to download the results as a CSV file
        st.success("Grading Completed!")
        csv_output = results_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Results as CSV",
            data=csv_output,
            file_name="grading_results.csv",
            mime="text/csv"
        )
