import streamlit as st
import pandas as pd
import requests
import os
import zipfile
from io import BytesIO


# Function to hit each endpoint and handle possible errors
def get_api_data(base_url):
    endpoints = {
        "categories": "api/categories",
        "category_1001": "api/categories/1001",
        "book_1001": "api/books/1001",
        "books_in_category": "api/categories/1001/books",
        "suggested_books": "api/categories/1001/suggested-books",
        "suggested_books_limit_2": "api/categories/1001/suggested-books?limit=2"
    }

    results = {}

    for key, endpoint in endpoints.items():
        full_url = f"{base_url}/{endpoint}"
        try:
            response = requests.get(full_url)
            response.raise_for_status()  # This will raise an HTTPError for bad responses (e.g., 404)
            results[key] = response.json()  # Store the JSON response
        except requests.exceptions.HTTPError as http_err:
            results[key] = f"HTTP Error: {http_err.response.status_code} {http_err.response.reason}"
        except requests.exceptions.RequestException as req_err:
            results[key] = f"Request Error: {str(req_err)}"

    return results


# Validation logic for the API responses
def validate_api_responses(api_data):
    validation_results = []

    # Rule 1: Check if there are at least 4 categories in the response
    categories = api_data.get("categories", [])
    if isinstance(categories, list) and len(categories) >= 4:
        validation_results.append("Pass: At least 4 categories returned.")
    else:
        validation_results.append("Fail: Less than 4 categories returned or invalid format.")

    # Rule 2: Validate the structure of category objects
    required_category_keys = ["categoryId", "name"]
    if isinstance(categories, list):
        for category in categories:
            if isinstance(category, dict) and all(key in category for key in required_category_keys):
                validation_results.append(f"Pass: Category {category.get('categoryId', 'Unknown')} structure is valid.")
            else:
                validation_results.append(f"Fail: Category structure is invalid or missing keys: {category}")
    else:
        validation_results.append("Fail: Categories response is not a list.")

    # Rule 3: Validate books in category
    books = api_data.get("books_in_category", [])
    if isinstance(books, list) and len(books) >= 4:
        validation_results.append("Pass: At least 4 books returned in category.")
    else:
        validation_results.append("Fail: Less than 4 books returned in category or invalid format.")

    # Rule 4: Validate suggested books
    suggested_books = api_data.get("suggested_books", [])
    if isinstance(suggested_books, list) and len(suggested_books) == 3:
        validation_results.append("Pass: 3 suggested books returned.")
    else:
        validation_results.append("Fail: Incorrect number of suggested books returned.")

    # Rule 5: Validate suggested books with limit=2
    suggested_books_limit_2 = api_data.get("suggested_books_limit_2", [])
    if isinstance(suggested_books_limit_2, list) and len(suggested_books_limit_2) == 2:
        validation_results.append("Pass: 2 suggested books returned with limit=2.")
    else:
        validation_results.append("Fail: Incorrect number of suggested books returned with limit=2.")

    return validation_results


# Convert complex objects (lists, dicts, errors) to strings before creating the DataFrame
def convert_to_string(data):
    if isinstance(data, (list, dict)):
        return str(data)
    return data


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
        # Memory buffer to hold zip file
        zip_buffer = BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for index, row in df.iterrows():
                student_name = row['student_name']  # Assuming the column name for student name
                base_url = row['base_url']  # Assuming the column name for base URL
                st.write(f"Processing for {student_name} at {base_url}...")

                # Get the API data for this student
                api_results = get_api_data(base_url)

                # Validate the API responses
                validation_results = validate_api_responses(api_results)

                # Determine if all tests passed
                if all("Pass" in result for result in validation_results):
                    final_grade = "Pass"
                else:
                    final_grade = "Fail"

                # Append the student's name, validation results, and final grade
                student_row = {
                    'student_name': student_name,
                    'api/categories': convert_to_string(api_results.get("categories", "N/A")),
                    'api/categories/1001': convert_to_string(api_results.get("category_1001", "N/A")),
                    'api/books/1001': convert_to_string(api_results.get("book_1001", "N/A")),
                    'api/categories/1001/books': convert_to_string(api_results.get("books_in_category", "N/A")),
                    'api/categories/1001/suggested-books': convert_to_string(api_results.get("suggested_books", "N/A")),
                    'api/categories/1001/suggested-books?limit=2': convert_to_string(
                        api_results.get("suggested_books_limit_2", "N/A")),
                    'Validation Results': "; ".join(validation_results),
                    'Final Grade': final_grade
                }

                student_results.append(student_row)

                # Create individual file for the student and add to zip
                student_file_content = f"Student Name: {student_name}\n"
                student_file_content += "=" * 50 + "\n"
                for key, value in student_row.items():
                    if key != 'student_name':
                        student_file_content += f"{key}:\n  {value}\n\n"

                zip_file.writestr(f"{student_name}.txt", student_file_content)

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

        # Save zip buffer and offer download
        zip_buffer.seek(0)
        st.download_button(
            label="Download All Files as Zip",
            data=zip_buffer,
            file_name="student_results.zip",
            mime="application/zip"
        )
