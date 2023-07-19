from pdf2image import convert_from_path
import pytesseract
import pandas as pd
import re

import cv2
import numpy as np
from datetime import datetime

file = 'junio_u'
# Define your category dictionary
category_dict = {
    'Shopping': ['ISHOP','AMAZON', 'EBAY', 'ALIEXPRESS', 'H M', 'ZARA', 'UNIQLO', 'CLIP', 'TAF', 'INTERES'],
    'Delivery Apps': ['RAPPI', 'UBER EATS', 'DIDI'],
    'Services': ['SELINA','MERPAGO','APPLE','TICKET','ATT','NETFLIX', 'HBO', 'YouTubePremium', 'AMAZON PRIME', 'Google Storage', 'TOTAL PLAY', 'SPORT CITY '],
    'Groseries': ['OXXO', '7 ELEVEN', 'CHEDRAUI', 'COSTCO', 'PETCO','WM EXPRESS'],
    'Restaurants': ['DP','MC DONALDS','STARBUCKS', 'IHOP', 'REST ROOFTOP', 'REST', 'UBER EATS', 'BIMBONT CAFETERIA', 'DOMINOS', 'HOOTERS'],
    'Transportation': ['UBER','UBER TRIP', 'GPO FLECHA AMARILLA', 'VIVA AEROBUS', 'GAS', 'GDF', 'TALISMAN'],
    'Business': ['PRISMA', 'OFFICE DEPOT', 'INST']
    # Add as many categories and keywords as needed
}

def classify_concepto(row):
    for category, keywords in category_dict.items():
        if any(keyword in row['concepto'] for keyword in keywords):
            return category
    return 'Other'

# Create a mapping for the month abbreviations
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
    
# Convert the PDF into images
images = convert_from_path(f'edc/{file}.pdf')
im = []
for image in images:
    image_np = np.array(image)
    gray_image = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
    ret, binary_image = cv2.threshold(gray_image, 127, 255, cv2.THRESH_BINARY)

    im.append(binary_image)

data_list = []  # List to store the data

# Loop over the images and apply OCR to each one
for i in range(len(im)):
    text = pytesseract.image_to_string(im[i], lang='eng', config='--psm 4')
    # Regex pattern for the date, concept, and amount
    #pattern = r'(\b\d{2} \w{3}\b) (.*?)(\b\d{1,3}(?:\,\d{3})*(?:\.\d{2})?\b)'
    pattern = r'(\b(?!00\b)(?:0[1-9]|1\d|2[0-9]|3[01])\s?[A-Z]{3}\b) (.*?) (\b\d{1,3}(?:,\d{3})*\.\d{2}\b)'


    # Find all matches for the pattern
    matches = re.findall(pattern, text)
    # Unpack the matches into separate lists
    for date, concept, amount in matches:
        # If the concept ends with "°", omit this line
        if concept.endswith('° '):
            continue
        else:
            data_list.append({'fecha': date, 'concepto': concept, 'monto': float(amount.replace(',', ''))})
# Create a DataFrame with the data
df = pd.DataFrame(data_list)
df = df.sort_values('monto', ascending=False)
df['fecha'] = df['fecha'].apply(convert_date)
df['category'] = ''
df['category'] = df.apply(classify_concepto, axis=1)
# Write the DataFrame to a CSV file
df.to_csv(f'csv/{file}.csv', index=False)

print(df.head(20))