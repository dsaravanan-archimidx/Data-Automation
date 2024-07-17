import os
import json
import pdfplumber
from concurrent.futures import ThreadPoolExecutor
import re
# Function to create directories if they do not exist
def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)
# Function to extract text from a PDF file between two keywords
def extract_text_between_keywords(pdf_file, start_keyword, end_keyword, output_dir, extracted_text_file, start_page=0):
    # Ensure the output directory exists
    create_directory(output_dir)
    semester_file_path = os.path.join(output_dir, 'semester_' + extracted_text_file)
    elective_file_path = os.path.join(output_dir, 'elective_' + extracted_text_file)
    with pdfplumber.open(pdf_file) as pdf:
        number_of_pages = len(pdf.pages)
        start_extraction = False
        end_extraction = False
        text_count = 0
        professional_elective = False
        semester_completed = False
        for page_number in range(start_page, number_of_pages):
            page = pdf.pages[page_number]
            text = page.extract_text()
            if start_keyword and start_keyword in text:
                start_extraction = True
                text_count += 1
            if end_keyword and end_keyword in text and start_extraction and text_count > 1 and page_number > 160:
                end_extraction = True
            if 'PROFESSIONAL ELECTIVES - I' in text and not professional_elective:
                professional_elective = True
                semester_completed = True
            if (not start_keyword or start_extraction) and not semester_completed:
                with open(semester_file_path, 'a', encoding='utf-8') as f:
                    f.write(text)
            if semester_completed:
                with open(elective_file_path, 'a', encoding='utf-8') as f:
                    f.write(text)
            if end_extraction:
                break
# Function to split text by multiple regex patterns and remove numbers before the letters in the matched patterns
def split_text_by_keywords(text, regex_patterns):
    pattern = '|'.join(regex_patterns)
    matches = re.finditer(pattern, text)
    indices = [match.start() for match in matches]
    splits = [text[i:j] for i, j in zip([0] + indices, indices + [None])]
    cleaned_splits = []
    for split in splits:
        for regex in regex_patterns:
            match = re.search(regex, split)
            if match:
                cleaned_split = re.sub(r'\b\d{2,3}([A-Z]{2}\d{4})\b', r'\1', split)
                cleaned_split = re.sub(r'\b\d{2,3}([A-Z]{3}\d{3})\b', r'\1', cleaned_split)
                cleaned_splits.append(cleaned_split)
                break
        else:
            cleaned_splits.append(split)
    return cleaned_splits
def process_pdf(pdf_file, start_keyword, end_keyword):
    pdf_path = os.path.join(syllabus_directory, pdf_file)
    output_dir = os.path.splitext(pdf_path)[0]  # Use PDF file name as the output directory name
    extracted_text_file = 'allsubjectscse.txt'
    start_page = 20
    extract_text_between_keywords(pdf_path, start_keyword, end_keyword, output_dir, extracted_text_file, start_page)
    # Ensure the extracted_text directory exists
    extracted_text_dir = os.path.join(output_dir, 'extracted_text')
    create_directory(extracted_text_dir)
    # Ensure the result directory exists
    result_dir = os.path.join(output_dir, 'result')
    create_directory(result_dir)
    # Read and split the extracted text if files exist
    semester_file_path = os.path.join(output_dir, 'semester_' + extracted_text_file)
    elective_file_path = os.path.join(output_dir, 'elective_' + extracted_text_file)
    # Move the extracted text files to the extracted_text directory if they exist
    if os.path.exists(semester_file_path):
        os.rename(semester_file_path, os.path.join(extracted_text_dir, 'semester_allsubjectscse.txt'))
    if os.path.exists(elective_file_path):
        os.rename(elective_file_path, os.path.join(extracted_text_dir, 'elective_allsubjectscse.txt'))
    # Update paths for reading
    semester_file_path = os.path.join(extracted_text_dir, 'semester_allsubjectscse.txt')
    elective_file_path = os.path.join(extracted_text_dir, 'elective_allsubjectscse.txt')
    # Process the extracted text if files exist
    result_semester = []
    semester_matched_sentences = []  # Variable to store matched sentences for semester
    if os.path.exists(semester_file_path):
        with open(semester_file_path, 'r', encoding='utf-8') as f:
            extracted_text = f.read()
        result_semester = split_text_by_keywords(extracted_text, [r'\b[A-Z]{2}\d{4}\b.*L T P C\b',
                                                                  r'\b[A-Z]{2}\d{4}\b.*L T P/S C\b',
                                                                  r'\b[A-Z]{3}\d{3}\b.*L T P C\b',
                                                                  r'\b[A-Z]{3}\d{3}\b.*L T P/S C\b',
                                                                  r'\b\d{2,3}[A-Z]{2}\d{4}\b.*L T P C\b',
                                                                  r'\b\d{2,3}[A-Z]{2}\d{4}\b.*L T P/S C\b',
                                                                  r'\b\d{2,3}[A-Z]{3}\d{3}\b.*L T P C\b',
                                                                  r'\b\d{2,3}[A-Z]{3}\d{3}\b.*L T P/S C\b'])
        # Append matched sentences to variable
        semester_matched_sentences += result_semester
    result_electives = []
    elective_matched_sentences = []  # Variable to store matched sentences for electives
    if os.path.exists(elective_file_path):
        with open(elective_file_path, 'r', encoding='utf-8') as f:
            extracted_text = f.read()
        result_electives = split_text_by_keywords(extracted_text, [r'PROFESSIONAL ELECTIVES'])
        # Append matched sentences to variable
        elective_matched_sentences += result_electives
    # Combine results and save to JSON if there is any data
    result = semester_matched_sentences + elective_matched_sentences
    if result_semester:
        semester_json_path = os.path.join(result_dir, 'semester.json')
        with open(semester_json_path, 'w', encoding='utf-8') as json_file:
            json.dump(result_semester, json_file, indent=4)
    if result_electives:
        electives_json_path = os.path.join(result_dir, 'electives.json')
        with open(electives_json_path, 'w', encoding='utf-8') as json_file:
            json.dump(result_electives, json_file, indent=4)
    if result:
        desired_json_format_path = os.path.join(extracted_text_dir, 'desired_json_format.json')
        with open(desired_json_format_path, 'w', encoding='utf-8') as json_file:
            json.dump(result, json_file, indent=4)
    print(f"All files for '{pdf_file}' saved in '{extracted_text_dir}' and '{result_dir}'")
    return semester_matched_sentences, elective_matched_sentences
def process_pdf_files_in_directory(directory, start_keyword, end_keyword):
    pdf_files = [f for f in os.listdir(directory) if f.endswith('.pdf')]
    with ThreadPoolExecutor() as executor:
        results = executor.map(lambda pdf_file: process_pdf(pdf_file, start_keyword, end_keyword), pdf_files)
    # Collect and process the results if needed
    all_semester_matched_sentences = []
    all_elective_matched_sentences = []
    for result in results:
        all_semester_matched_sentences.extend(result[0])
        all_elective_matched_sentences.extend(result[1])
    # Return the combined results
    return all_semester_matched_sentences, all_elective_matched_sentences
# Directory containing PDF files
syllabus_directory = 'Syllabus'
# Keywords to start and end extraction
start_keyword = ''
end_keyword = ''
# Process all PDF files in the directory in parallel
semester_results, elective_results = process_pdf_files_in_directory(syllabus_directory, start_keyword, end_keyword)
# You can now use semester_results and elective_results as needed