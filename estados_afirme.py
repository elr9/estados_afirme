import streamlit as st
import pandas as pd
import base64
from io import BytesIO

# Function to process the Excel file
def process_bank_statement(uploaded_file):
    # Read the Excel file
    bank_data = pd.read_excel(uploaded_file, header=7)

    # Select relevant columns
    relevant_columns = ['Concepto', 'Fecha', 'Referencia', 'Cargo', 'Abono', 'Saldo']
    bank_data = bank_data[relevant_columns]

    # Convert 'Cargo' and 'Abono' to numeric values
    bank_data['Cargo'] = pd.to_numeric(bank_data['Cargo'].str.replace('$', '').str.replace(',', ''), errors='coerce')
    bank_data['Abono'] = pd.to_numeric(bank_data['Abono'].str.replace('$', '').str.replace(',', ''), errors='coerce')

    # Initialize 'Comentarios' and 'Considerar' columns
    bank_data['Comentarios'] = ''
    bank_data['Considerar'] = 'si' # Default to 'si'

    # Apply rules for 'Comentarios' and 'Considerar'
    bank_data.loc[bank_data['Concepto'] == 'DISPERSION DE FONDOS', ['Comentarios', 'Considerar']] = ['Nómina', 'si']
    bank_data.loc[bank_data['Concepto'].str.startswith('RECH-'), ['Comentarios', 'Considerar']] = ['Domiciliación rechazada', 'no']
    bank_data.loc[bank_data['Concepto'].str.contains('propias'), ['Comentarios', 'Considerar']] = ['Traspaso entre cuentas propias', 'no']

    # Calculate the sum of 'Abono' where 'Considerar' is 'si'
    abono_sum = bank_data[bank_data['Considerar'] == 'si']['Abono'].sum()

    return bank_data, abono_sum

# Function to download data as Excel
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    processed_data = output.getvalue()
    return processed_data


# Streamlit application layout
st.title('Bank Statement Processor')

# File uploader
uploaded_file = st.file_uploader("Choose a file", type=['xlsx'])

if uploaded_file is not None:
    # Process the file
    cleaned_data, total_abono = process_bank_statement(uploaded_file)

    # Display results
    st.write(f"Total Sum of 'Abono': ${total_abono:,.2f}")

    # Download link for cleaned data
    if st.button('Download Cleaned Data as Excel'):
        processed_data = to_excel(cleaned_data)
        b64 = base64.b64encode(processed_data).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="cleaned_data.xlsx">Download Excel File</a>'
        st.markdown(href, unsafe_allow_html=True)
