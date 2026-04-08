import streamlit as st
import pandas as pd
import io

# Set page configuration
st.set_page_config(page_title="OMR Data Converter", layout="centered")

st.title("📝 OMR Format Converter")
st.write("Convert your wide-format test data into the long-format OMR Scoring Template.")

# File uploader
uploaded_file = st.file_uploader("Upload your 'Wide' format file (CSV or Excel)", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        # 1. Read the uploaded file
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.success("File uploaded successfully! Processing data...")

        # 2. Identify the fixed columns and question columns
        id_vars = ['SchoolID', 'StudentID', 'Grade', 'Subject']

        # Verify if expected ID columns exist
        missing_cols = [col for col in id_vars if col not in df.columns]
        if missing_cols:
            st.error(f"Missing expected columns in the uploaded file: {', '.join(missing_cols)}")
            st.stop()

        # Dynamically find all 'Q' columns (Q1, Q2, ..., Q40)
        q_cols = [col for col in df.columns if col.startswith('Q') and col[1:].isdigit()]

        # 3. Unpivot (Melt) the dataframe from Wide to Long
        df_long = pd.melt(df, id_vars=id_vars, value_vars=q_cols, var_name='Q#', value_name='A')

        # 4. Rename columns to match the target template
        df_long = df_long.rename(columns={
            'SchoolID': 'CentreID',
            'Grade': 'Class'
        })

        # 5. Clean and format the 'Q#' and 'A' columns
        # Remove the 'Q' from the question column to just keep the number
        df_long['Q#'] = df_long['Q#'].str.replace('Q', '')

        # Convert Answers to string, lowercase them, and strip whitespace
        df_long['A'] = df_long['A'].astype(str).str.strip().str.lower()

        # Apply specific coding rules:
        # Rule A: Unanswered/Blank becomes '88' (pandas reads blanks as 'nan')
        df_long.loc[df_long['A'].isin(['nan', 'none', '', 'null']), 'A'] = '88'

        # Rule B: Unclear responses (*) become '86'
        df_long.loc[df_long['A'] == '*', 'A'] = '86'

        # 6. Reorder and sort the final dataframe
        final_columns = ['CentreID', 'StudentID', 'Class', 'Subject', 'Q#', 'A']
        df_final = df_long[final_columns]

        # Sort by StudentID and then by Question number (convert Q# temporarily to integer for correct sorting)
        df_final['Q#_int'] = df_final['Q#'].astype(int)
        df_final = df_final.sort_values(by=['StudentID', 'Q#_int']).drop(columns=['Q#_int'])

        # Show a preview of the transformed data
        st.subheader("Data Preview (First 15 Rows)")
        st.dataframe(df_final.head(15), use_container_width=True)

        # 7. Create download button for the new CSV
        csv_buffer = df_final.to_csv(index=False).encode('utf-8')

        st.download_button(
            label="⬇️ Download Converted Format (CSV)",
            data=csv_buffer,
            file_name="converted_OMR_data.csv",
            mime="text/csv",
            type="primary"
        )

    except Exception as e:
        st.error(f"An error occurred during processing: {e}")