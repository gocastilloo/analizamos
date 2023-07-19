from fastapi import FastAPI, UploadFile, File
from typing import Union
from suggested_fun import convert_pdf_to_image, extract_data_from_image, create_dataframe, save_to_csv
import shutil

app = FastAPI()



@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/pdf")
async def post_pdf(pdf: UploadFile = File(...)):
    with open(pdf.filename, 'wb') as buffer:
        shutil.copyfileobj(pdf.file, buffer)
    binary_images = convert_pdf_to_image(pdf.filename)
    data_list = extract_data_from_image(binary_images)
    df = create_dataframe(data_list)
    save_to_csv(df, f'csv.csv')
    # Convert the DataFrame to a dictionary and then to JSON
    json_data = df.to_dict(orient="records")
    
    # Save the DataFrame as CSV if needed
    # save_to_csv(df, f'csv.csv')
    
    return {"filename": pdf.filename, "data": json_data}
