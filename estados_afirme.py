import streamlit as st
import pandas as pd
import base64
from io import BytesIO

# Function to process the Afirme bank statement from CSV
def process_afirme_statement(uploaded_file):
    try:
        # Read the CSV file
        bank_data = pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"Error reading the Afirme CSV file: {e}")
        return None, 0

    # Select relevant columns
    relevant_columns = ['Concepto', 'Fecha (DD/MM/AA)', 'Referencia', 'Cargo', 'Abono', 'Saldo']
    bank_data = bank_data[relevant_columns]

    # Convert 'Cargo' and 'Abono' to numeric values
    # Ensure the columns are treated as strings before stripping unwanted characters
    bank_data['Cargo'] = pd.to_numeric(bank_data['Cargo'].astype(str).str.replace('$', '').str.replace(',', ''), errors='coerce')
    bank_data['Abono'] = pd.to_numeric(bank_data['Abono'].astype(str).str.replace('$', '').str.replace(',', ''), errors='coerce')

    # Initialize 'Comentarios' and 'Considerar' columns
    bank_data['Comentarios'] = ''
    bank_data['Considerar'] = 'si'  # Default to 'si'

    # Apply rules for 'Comentarios' and 'Considerar'
    bank_data.loc[bank_data['Concepto'] == 'DISPERSION DE FONDOS', ['Comentarios', 'Considerar']] = ['Nómina', 'si']
    bank_data.loc[bank_data['Concepto'].str.startswith('RECH-'), ['Comentarios', 'Considerar']] = ['Domiciliación rechazada', 'no']
    bank_data.loc[bank_data['Concepto'].str.contains('propias'), ['Comentarios', 'Considerar']] = ['Traspaso entre cuentas propias', 'no']

    # Calculate the sum of 'Abono' where 'Considerar' is 'si'
    abono_sum = bank_data[bank_data['Considerar'] == 'si']['Abono'].sum()

    return bank_data, abono_sum

# Function to process the Hey bank statement
def process_hey_statement(uploaded_file):
    # Read the CSV file
    bank_data = pd.read_csv(uploaded_file, skiprows=9)

    # Rename columns for consistency
    bank_data.columns = ['Fecha', 'Descripción', 'Referencia', 'Cargo', 'Abonos', 'Saldo', 'Clasificación']

    # Convert 'Abonos' to numeric values
    bank_data['Abonos'] = pd.to_numeric(bank_data['Abonos'].astype(str).str.replace('$', '').str.replace(',', ''), errors='coerce')

    # Initialize 'Comentarios' and 'Considerar' columns
    bank_data['Comentarios'] = ''
    bank_data['Considerar'] = 'si'  # Default to 'si'

    # Apply rules for 'Comentarios' and 'Considerar'
    bank_data.loc[bank_data['Descripción'].str.contains('TARJETA DE CREDITO B|propias|Ahorro', case=False, na=False), ['Comentarios', 'Considerar']] = ['Traspaso entre cuentas propias', 'no']
    bank_data.loc[bank_data['Descripción'].str.contains('recompensas', case=False, na=False), ['Comentarios', 'Considerar']] = ['recompensas', 'no']

    # Calculate the sum of 'Abonos' where 'Considerar' is 'si'
    abonos_sum = bank_data[bank_data['Considerar'] == 'si']['Abonos'].sum()

    return bank_data, abonos_sum

# Function to download data as Excel
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    processed_data = output.getvalue()
    return processed_data

# Streamlit application layout
st.title('Bank Statement Processor')

# File uploader for Afirme CSV
st.subheader('Afirme Bank Statement')
uploaded_file_afirme = st.file_uploader("Choose an Afirme CSV file", type=['csv'], key='afirme')

# Process Afirme CSV file
if uploaded_file_afirme is not None:
    cleaned_data_afirme, total_abono_afirme = process_afirme_statement(uploaded_file_afirme)
    if cleaned_data_afirme is not None:
        st.write(f"Total Income from Afirme: ${total_abono_afirme:,.2f}")

        # Download link for Afirme data
        if st.button('Download Afirme Data as Excel', key='download_afirme'):
            processed_data_afirme = to_excel(cleaned_data_afirme)
            b64_afirme = base64.b64encode(processed_data_afirme).decode()
            href_afirme = f'<a href="data:application/octet-stream;base64,{b64_afirme}" download="afirme_data.xlsx">Download Afirme Excel File</a>'
            st.markdown(href_afirme, unsafe_allow_html=True)

# File uploader for Hey
st.subheader('Hey Bank Statement')
uploaded_file_hey = st.file_uploader("Choose a Hey file", type=['csv'], key='hey')

# Process Hey file
if uploaded_file_hey is not None:
    cleaned_data_hey, total_abonos_hey = process_hey_statement(uploaded_file_hey)
    st.write(f"Total Income from Hey: ${total_abonos_hey:,.2f}")

    # Download link for Hey data
    if st.button('Download Hey Data as Excel', key='download_hey'):
        processed_data_hey = to_excel(cleaned_data_hey)
        b64_hey = base64.b64encode(processed_data_hey).decode()
        href_hey = f'<a href="data:application/octet-stream;base64,{b64_hey}" download="hey_data.xlsx">Download Hey Excel File</a>'
        st.markdown(href_hey, unsafe_allow_html=True)
