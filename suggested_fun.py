from pdf2image import convert_from_path
import pytesseract
import pandas as pd
import re

import cv2
import numpy as np
from datetime import datetime

# Define your category dictionary
category_dict = {
    'Shopping': ['ISHOP','AMAZON', 'EBAY', 'ALIEXPRESS', 'H M', 'ZARA', 'UNIQLO', 'CLIP', 'TAF', 'INTERES', 'IKA'],
    'Delivery Apps': ['RAPPI', 'UBER EATS', 'DIDI'],
    'Services': ['SELINA','MERPAGO','APPLE','TICKET','ATT','NETFLIX', 'HBO', 'YouTubePremium', 'AMAZON PRIME', 'Google Storage', 'TOTAL PLAY', 'SPORT CITY '],
    'Groseries': ['OXXO', '7 ELEVEN', 'CHEDRAUI', 'COSTCO', 'PETCO','WM EXPRESS'],
    'Restaurants': ['DP','MC DONALDS','STARBUCKS', 'IHOP', 'REST ROOFTOP', 'REST', 'UBER EATS', 'BIMBONT CAFETERIA', 'DOMINOS', 'HOOTERS'],
    'Transportation': ['UBER','UBER TRIP', 'GPO FLECHA AMARILLA', 'VIVA AEROBUS', 'GAS', 'GDF', 'TALISMAN'],
    'Business': ['PRISMA', 'OFFICE DEPOT', 'INST']
}
def classify_concepto(row):
    for category, keywords in category_dict.items():
        if any(keyword in row['concepto'] for keyword in keywords):
            return category
    return 'Other'
    
month_mapping = {
    'ENE': '01',
    'FEB': '02',
    'MAR': '03',
    'ABR': '04',
    'MAY': '05',
    'JUN': '06',
    'JUL': '07',
    'AGO': '08',
    'SEP': '09',
    'OCT': '10',
    'NOV': '11',
    'DIC': '12'
}

# Function to convert the date string to a date object
def convert_date(date_string):
    try:
        if ' ' in date_string:
            day, month_abbrev = date_string.split()
        else:
            day = date_string[:2]
            month_abbrev = date_string[2:]
            if day or month_abbrev not in month_mapping:
                return 0

        month = month_mapping[month_abbrev]
        date_string_formatted = f"2023-{month}-{day}"
        return datetime.strptime(date_string_formatted, '%Y-%m-%d').date()
    except Exception as e:
        print(f"Error: {e}")
        return None


def convert_pdf_to_image(file_path):
    images = convert_from_path(file_path)
    binary_images = []
    for image in images:
        image_np = np.array(image)
        gray_image = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
        ret, binary_image = cv2.threshold(gray_image, 127, 255, cv2.THRESH_BINARY)
        binary_images.append(binary_image)
    return binary_images

bank_patterns = {
    'Nu Bank': [r'Nu\s*México\s*Financiera'],
    'Santander': [r'Santander', r'SUPERLINEA'],
}

def identify_bank(text):
    for bank, patterns in bank_patterns.items():
        if any(re.search(pattern, text) for pattern in patterns):
            return bank
    return None


select_pattern = {
    'Nu Bank': r'(\d{1,2} [A-Z]{3})\s+(.*?)\s+\$\s*([\d,]+\.\d{2})',
    'Santander': r'(\b(?!00\b)(?:0[1-9]|1\d|2[0-9]|3[01])\s?[A-Z]{3}\b) (.*?) (\b\d{1,3}(?:,\d{3})*\.\d{2}\b)',
}

def extract_data_from_image(images):
    identified_bank = None
    data_list = []

    for binary_image in images:
        text = pytesseract.image_to_string(binary_image, lang='eng', config='--psm 6')

        # Identify the bank only if it has not been identified yet
        if identified_bank is None:
            identified_bank = identify_bank(text)
            if identified_bank is not None:
                print(f"Bank identified: {identified_bank}")
                #data_list.append({'Bank': identified_bank})
            else:
                print("Bank not identified")
                continue

        bank_match_pattern = select_pattern.get(identified_bank)
        if bank_match_pattern is None:
            print(f"No pattern found for bank: {identified_bank}")
            continue

        # Compile the pattern
        pattern = re.compile(bank_match_pattern)
        matches = re.findall(pattern, text)
        for date, concept, amount in matches:
            if concept.endswith('° '):
                continue
            else:
                data_list.append({'fecha': date, 'concepto': concept, 'monto': float(amount.replace(',', ''))})
    
    return identified_bank, data_list

def create_dataframe(data_list):
    df = pd.DataFrame(data_list)
    df = df.sort_values('monto', ascending=False)
    df['fecha'] = df['fecha'].apply(convert_date)
    df['category'] = ''
    df['category'] = df.apply(classify_concepto, axis=1)
    return df

def save_to_csv(df, file_name):
    df.to_csv(file_name, index=False)

def main():
    file = 'junio_u'
    binary_images = convert_pdf_to_image(f'{file}.pdf')
    data_list = extract_data_from_image(binary_images)
    df = create_dataframe(data_list)
    save_to_csv(df, f'csv/{file}.csv')
    print(df.head(20))

if __name__ == "__main__":
    main()
