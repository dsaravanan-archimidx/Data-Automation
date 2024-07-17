import pdfplumber
import json
import os

# Function to extract text from a PDF file between two keywords
def extract_text_between_keywords(pdf_file, start_keyword, end_keyword, start_page=0):
    extracted_text = ''
    with pdfplumber.open(pdf_file) as pdf:
        number_of_pages = len(pdf.pages)
        start_extraction = False
        end_extraction = False
        text_count = 0
        for page_number in range(start_page, number_of_pages):
            page = pdf.pages[page_number]
            text = page.extract_text()
            if start_keyword in text:
                start_extraction = True
                text_count += 1
            if end_keyword in text and start_extraction and text_count > 1 and page_number > 160:
                end_extraction = True
            if start_extraction:
                extracted_text += text
            if end_extraction:
                break
    return extracted_text

# Function to split text by a keyword
def split_text_by_keyword(text, keyword):
    return text.split(keyword) if keyword in text else [text]

# Function to ensure directory existence
def ensure_directory_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

# Extract text from the PDF
pdf_file = 'srisairamengg (1).pdf'
start_keyword = 'Name of the Degree & Course'
end_keyword = 'concepts of basics of Number'
start_page = 2
extracted_text = extract_text_between_keywords(pdf_file, start_keyword, end_keyword, start_page)

# Save the total extracted text to a file
extracted_text_file = 'Faculty/extracted_text/extract_txt.txt'
ensure_directory_exists('Faculty/extracted_text')
with open(extracted_text_file, 'w', encoding='utf-8', errors='ignore') as f:
    f.write(extracted_text)

# Split the extracted text
result = split_text_by_keyword(extracted_text, start_keyword)

# Save the combined result as a single JSON list
output_file = 'Faculty/extracted_text/all_faculty.json'
with open(output_file, 'w', encoding='utf-8', errors='ignore') as json_file:
    json.dump(result, json_file, indent=4)
