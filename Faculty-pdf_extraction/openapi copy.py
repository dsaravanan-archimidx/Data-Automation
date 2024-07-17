import openai
import json
import os
import logging

# Set up logging
log_directory = r'Faculty\logs'
os.makedirs(log_directory, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(log_directory, 'app.log'),
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Set your OpenAI API key
openai.api_key = ""

# Function to count the names in each item
def count_names(data):
    name_counts = []
    for item in data:
        section_text = item.get('section', '')  # Extract 'section' value from JSON object
        lines = section_text.split('\n')
        count = 0
        for line in lines:
            if "Name:" in line:
                count += 1
        name_counts.append(count)
    return name_counts

# Ensure directory existence
def ensure_directory_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

# Function to sanitize strings
def sanitize_string(input_str):
    # Remove any invalid control characters
    return ''.join(c for c in input_str if c.isprintable())

# Function to convert unstructured data to structured JSON
def convert_to_json(data, name_counts, startkey, result_directory):
    # Create an empty list to store the structured data
    structured_data_list = []
    # Counter to keep track of the key
    key = 0
    # Ensure the result directory exists
    ensure_directory_exists(result_directory)
    # Iterate over the data and extract the structured data
    for i, unstructured_data in enumerate(data):
        try:
            key += 1
            if key < startkey:
                # Log the key
                logging.info(f"{key} - Skipped")
                continue
            
            # Define the desired JSON format
            desired_json_format = """
{
    "faculty_details": [
        {
            "department": " ",
            "faculty_members": [
                {
                    "name": " ",
                    "dob": " ",
                    "date_of_joining": " ",
                    "aicte_id": " ",
                    "phd_thesis_title": " ",
                    "year_of_starting": "",
                    "educational_qualification": [
                        {
                            "degree": " ",
                            "specialization": " ",
                            "college_name": " ",
                            "year_of_passing": " "
                        },
                        {
                            "degree": " ",
                            "specialization": " ",
                            "college_name": " ",
                            "year_of_passing": " "
                        },
                        {
                            "degree": " ",
                            "specialization": " ",
                            "college_name": " ",
                            "year_of_passing": " "
                        }
                    ],
                    "designation": " ",
                    "academic_experience": [
                        {
                            "current_position": " ",
                            "previous_position": " "
                        }
                    ]
                }
            ]
        }
    ]
}
            """
            
            # Define OpenAI parameters
            model = "gpt-3.5-turbo"
            prompt = f"Extract structured data from the following unstructured data and format it as JSON according to the provided structure. Ensure the JSON is valid and does not include comments or syntax errors:\n\nUnstructured Data:\n{unstructured_data}\n\nDesired JSON Format:\n{desired_json_format} and make sure to include all {name_counts[i]} faculty details present in the unstructured data."
            
            # Make the API call
            response = openai.ChatCompletion.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            
            # Extract the structured data
            structured_data = response.choices[0]['message']['content'].strip()
            # Sanitize the string to remove invalid control characters
            structured_data = sanitize_string(structured_data)
            
            # Sanitize and validate the JSON
            try:
                structured_data_dict = json.loads(structured_data)
                # Append the structured data to the list
                structured_data_list.append(structured_data_dict)
                # Save the structured data to a JSON file
                output_file_name = os.path.join(result_directory, f'structured_data_{key}.json')
                with open(output_file_name, 'w') as f:
                    json.dump(structured_data_dict, f, indent=4)
                logging.info(f"Structured data saved to '{output_file_name}'")
                # Create a text file log for each subject
                with open(os.path.join(result_directory, 'log.txt'), 'a') as f:
                    f.write(str(key) + '-' + 'Processed' + '\n')
            except json.JSONDecodeError as e:
                logging.error(f"Failed to decode JSON. Error: {e}")
                logging.error("Received data:")
                logging.error(structured_data)
                # Write to a JSON file
                failed_output_file_name = os.path.join(result_directory, f'failed_structured_data_{key}.json')
                failed_data = {"failed_data": structured_data}
                with open(failed_output_file_name, 'w') as f:
                    json.dump(failed_data, f, indent=4)
                # Create a text file log for each subject
                with open(os.path.join(result_directory, 'log.txt'), 'a') as f:
                    f.write(str(key) + '-' + 'Failed JSON Decode' + '\n')
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            # Create a text file log for each subject
            with open(os.path.join(result_directory, 'log.txt'), 'a') as f:
                f.write(str(key) + '-' + 'Failed - ' + str(e) + '\n')
    # Save the list of all structured data to a single JSON file
    output_file_name = os.path.join(result_directory, 'structured_data_all.json')
    with open(output_file_name, 'w') as f:
        json.dump(structured_data_list, f, indent=4)
    logging.info(f"All structured data saved to '{output_file_name}'")

# Function to process all extracted_text.json files in subdirectories
def process_all_extracted_text_files(base_directory):
    for root, dirs, files in os.walk(base_directory):
        for file in files:
            if file == 'extracted_text.json':
                file_path = os.path.join(root, file)
                logging.info(f"Processing file: {file_path}")
                with open(file_path, 'r') as json_file:
                    data = json.load(json_file)
                    # Get the counts
                    name_counts = count_names(data)
                    # Run the function and save the results in the current directory
                    convert_to_json(data, name_counts, startkey=0, result_directory=root)

# Base directory containing all subdirectories with extracted_text.json files
base_directory = 'Pdfs'

# Process all extracted_text.json files
process_all_extracted_text_files(base_directory)
