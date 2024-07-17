import os
import pdfplumber
import json
import re

# Function to create directories if they do not exist
def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

# Function to extract text from a PDF file between two keywords
def extract_text_between_keywords(pdf_file, start_keyword, end_keyword, split_keyword, output_dir, extracted_text_file, start_page=0):
    # Ensure the output directory exists
    create_directory(output_dir)
    output_file_path = os.path.join(output_dir, extracted_text_file)

    with pdfplumber.open(pdf_file) as pdf:
        number_of_pages = len(pdf.pages)
        start_extraction = False
        extracted_sections = []
        current_section = []

        for page_number in range(start_page, number_of_pages):
            page = pdf.pages[page_number]
            text = page.extract_text()

            if start_keyword in text and not start_extraction:
                start_extraction = True
                start_index = text.find(start_keyword) + len(start_keyword)
                current_section.append(text[start_index:].strip())
            elif start_extraction:
                if end_keyword and end_keyword in text:
                    end_index = text.find(end_keyword)
                    current_section.append(text[:end_index].strip())
                    extracted_sections.append('\n'.join(current_section).strip())
                    break
                else:
                    parts = text.split(split_keyword)
                    for i, part in enumerate(parts):
                        if i == 0 and current_section:
                            current_section.append(part.strip())
                        else:
                            if current_section:
                                extracted_sections.append('\n'.join(current_section).strip())
                            current_section = [split_keyword + part.strip()]
                    if end_keyword == "" and page_number == number_of_pages - 1:  # When end_keyword is empty and it's the last page
                        extracted_sections.append('\n'.join(current_section).strip())
                        break

        if current_section:
            extracted_sections.append('\n'.join(current_section).strip())

        # Remove exact duplicates from extracted_sections
        unique_sections = list(dict.fromkeys(extracted_sections))

        # Structure sections into a JSON format
        structured_data = [{'section': section} for section in unique_sections]

        # Save the structured data to a JSON file
        with open(output_file_path, 'w', encoding='utf-8') as json_file:
            json.dump(structured_data, json_file, ensure_ascii=False, indent=4)

    return unique_sections

# Function to process a single PDF and save extracted and split text
def process_pdf(pdf_file, start_keyword, end_keyword, split_keyword):
    pdf_path = os.path.join(syllabus_directory, pdf_file)
    output_dir = os.path.splitext(pdf_path)[0]  # Use PDF file name as the output directory name
    extracted_text_file = 'extracted_text.json'
    start_page = 0

    # Extract text between keywords
    extracted_sections = extract_text_between_keywords(pdf_path, start_keyword, end_keyword, split_keyword, output_dir, extracted_text_file, start_page)

    # Ensure the extracted_text directory exists
    extracted_text_dir = os.path.join(output_dir, 'extracted_text')
    create_directory(extracted_text_dir)

    # Ensure the result directory exists
    result_dir = os.path.join(output_dir, 'result')
    create_directory(result_dir)

    # Move the extracted text file to the extracted_text directory
    extracted_text_path = os.path.join(output_dir, extracted_text_file)
    if os.path.exists(extracted_text_path):
        os.rename(extracted_text_path, os.path.join(extracted_text_dir, extracted_text_file))

    # Process the extracted text
    result_sections = []
    if extracted_sections:
        for section in extracted_sections:
            split_sections = section.split(split_keyword)
            result_sections.extend(split_sections)

    # Save split sections to a JSON file
    result_json_path = os.path.join(result_dir, 'result.json')
    with open(result_json_path, 'w', encoding='utf-8') as json_file:
        json.dump(result_sections, json_file, ensure_ascii=False, indent=4)

    print(f"All files for '{pdf_file}' saved in '{extracted_text_dir}' and '{result_dir}'")
    return result_sections

# Function to process all PDF files in a directory
def process_pdf_files_in_directory(directory, start_keyword, end_keyword, split_keyword):
    pdf_files = [f for f in os.listdir(directory) if f.endswith('.pdf')]
    all_sections = []

    for pdf_file in pdf_files:
        sections = process_pdf(pdf_file, start_keyword, end_keyword, split_keyword)
        all_sections.extend(sections)

    return all_sections

# Directory containing PDF files
syllabus_directory = 'Pdfs'
# Keywords to start and end extraction
start_keyword = 'List of Faculty Members'
end_keyword = ''  # Consider the last page if end_keyword is not given
split_keyword = 'Name of the Degree & Course'

# Process all PDF files in the directory
all_results = process_pdf_files_in_directory(syllabus_directory, start_keyword, end_keyword, split_keyword)
print("Processing complete.")
