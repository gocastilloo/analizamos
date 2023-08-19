from fastapi import FastAPI, UploadFile, File
from typing import Union
from suggested_fun import convert_pdf_to_image, extract_data_from_image, create_dataframe, save_to_csv
import shutil
from tempfile import NamedTemporaryFile
import os

app = FastAPI()



@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/pdf")
async def post_pdf(pdf: UploadFile = File(...)):
    try:
        # Using a temporary file to avoid conflicts
        with NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            shutil.copyfileobj(pdf.file, temp_file)
            temp_file_name = temp_file.name

        binary_images = convert_pdf_to_image(temp_file_name)
        bank, data_list = extract_data_from_image(binary_images)
        df = create_dataframe(data_list)
        save_to_csv(df, f'csv.csv')
        
        # Convert the DataFrame to a dictionary and then to JSON
        json_data = df.to_dict(orient="records")
        
        # Cleaning up the temporary file
        os.remove(temp_file_name)
        
        return {"filename": pdf.filename, "bank": bank, "data": json_data}
    except Exception as e:
        # Gracefully handling any errors that might occur
        return {"error": str(e)}
