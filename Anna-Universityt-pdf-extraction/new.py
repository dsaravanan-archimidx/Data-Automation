import os
import json
import openai
import time
from concurrent.futures import ThreadPoolExecutor
from requests.exceptions import ReadTimeout

# Set your OpenAI API key
openai.api_key = ""

def sanitize_string(input_str):
    # Remove any invalid control characters
    return ''.join(c for c in input_str if c.isprintable())

def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

def list_files_in_directory(directory):
    try:
        # List all files in the given directory
        files = os.listdir(directory)
        # Filter out directories, keeping only files
        files = [file for file in files if os.path.isfile(os.path.join(directory, file))]
        return files
    except Exception as e:
        print(f"An error occurred while listing files in the directory: {e}")
        return []

def convert_to_json(input_file, startkey=0):
    # Read the JSON file
    with open(input_file) as f:
        data = json.load(f)
    
    # Create the directory for output files
    base_name = os.path.splitext(input_file)[0]
    output_dir = base_name
    create_directory(output_dir)

    # Create an empty list to store the structured data
    structured_data_list = []
    # Counter to keep track of the key
    key = 0
    # Iterate over the data and extract the structured data
    for i in data:
        try:
            key += 1
            if key < startkey:
                # Log the key
                with open(os.path.join(output_dir, 'log.txt'), 'a') as f:
                    f.write(str(key) + '-' + 'Skipped' + '\n')
                continue
            # Define unstructured data
            unstructured_data = i
            # Define the desired JSON format
            desired_json_format = {
                "Syllabus": "string",
                "Semester": "string",
                "Course Code": "string",
                "Course Title": "string",
                "SDG NO": "string",
                "L": "integer",
                "T": "integer",
                "P": "integer",
                "C": "integer",
                "Objectives": ["string"],
                "Units": [
                    {
                        "Unit": "string",
                        "Title": "string",
                        "Periods": "integer",
                        "Content": "string"
                    }
                ],
                "Total Periods": "integer",
                "Textbooks": [
                    {
                        "Author": "string",
                        "Title": "string",
                        "Edition": "string",
                        "Publisher": "string",
                        "Location": "string",
                        "Year": "integer"
                    }
                ],
                "References": [
                    {
                        "Author": "string",
                        "Title": "string",
                        "Edition": "string",
                        "Publisher": "string",
                        "Reprint": "string"
                    }
                ],
                "Web References": ["string"],
                "Online Resources": ["string"]
            }
            # Define OpenAI parameters
            model = "gpt-3.5-turbo"
            prompt = f"Extract structured data from the following unstructured data and format it as JSON according to the provided structure. Ensure the JSON is valid and does not include comments or syntax errors:\n\nUnstructured Data:\n{unstructured_data}\n\nDesired JSON Format:\n{json.dumps(desired_json_format, indent=4)}"
            
            retry_count = 0
            max_retries = 5
            
            while retry_count < max_retries:
                try:
                    # Make the API call
                    response = openai.ChatCompletion.create(
                        model=model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.0,
                    )
                    # Extract the structured data
                    structured_data = response.choices[0]['message']['content'].strip()
                    # Sanitize the string to remove invalid control characters
                    structured_data = sanitize_string(structured_data)
                    # Sanitize and validate the JSON
                    structured_data_dict = json.loads(structured_data)
                    # Append the structured data to the list
                    structured_data_list.append(structured_data_dict)
                    # Save the structured data to a JSON file
                    output_file_name = os.path.join(output_dir, f'structured_data_{key}.json')
                    with open(output_file_name, 'w') as f:
                        json.dump(structured_data_dict, f, indent=4)
                    print(f"Structured data saved to '{output_file_name}'")
                    # Create a text file log for each subject
                    with open(os.path.join(output_dir, 'log.txt'), 'a') as f:
                        f.write(str(key) + '-' + 'Processed' + '\n')
                    break  # Exit the retry loop if successful
                except (openai.error.RateLimitError, openai.error.OpenAIError, ReadTimeout) as e:
                    print(f"Error occurred: {e}. Retrying in 1 second...")
                    retry_count += 1
                    time.sleep(1)
                except json.JSONDecodeError as e:
                    print("Failed to decode JSON. Error:", e)
                    print("Received data:")
                    print(structured_data)
                    # Write to a JSON file
                    failed_output_file_name = os.path.join(output_dir, f'failed_structured_data_{key}.json')
                    failed_data = {"failed_data": structured_data}
                    with open(failed_output_file_name, 'w') as f:
                        json.dump(failed_data, f, indent=4)
                    # Create a text file log for each subject
                    with open(os.path.join(output_dir, 'log.txt'), 'a') as f:
                        f.write(str(key) + '-' + 'Failed JSON Decode' + '\n')
                    break  # Exit the retry loop if JSON decode error occurs
                except Exception as e:
                    print("An error occurred:", e)
                    # Create a text file log for each subject
                    with open(os.path.join(output_dir, 'log.txt'), 'a') as f:
                        f.write(str(key) + '-' + 'Failed - ' + str(e) + '\n')
                    break  # Exit the retry loop if any other error occurs
        except Exception as e:
            print("An error occurred:", e)
            # Create a text file log for each subject
            with open(os.path.join(output_dir, 'log.txt'), 'a') as f:
                f.write(str(key) + '-' + 'Failed - ' + str(e) + '\n')
    
    # Save the list of all structured data to a single JSON file
    output_file_name = os.path.join(output_dir, 'structured_data_all.json')
    with open(output_file_name, 'w') as f:
        json.dump(structured_data_list, f, indent=4)
    print(f"All structured data saved to '{output_file_name}'")

def process_folder(folder_path):
    # Directory containing JSON files
    result_directory = os.path.join(folder_path, 'result')

    # Get the list of files
    file_list = list_files_in_directory(result_directory)

    # Print the list of files
    print(f"Files in '{result_directory}':")
    for file in file_list:
        print(file)

    # Filter for JSON files only
    json_files = [file for file in file_list if file.endswith('.json')]

    # Process each JSON file in the directory
    for json_file in json_files:
        input_file = os.path.join(result_directory, json_file)
        print(f"Processing file: {input_file}")
        startkey = 0  # Set the startkey value here if needed
        convert_to_json(input_file, startkey)

def process_all_folders(base_directory):
    with ThreadPoolExecutor() as executor:
        for root, dirs, files in os.walk(base_directory):
            if 'result' in dirs:
                folder_path = os.path.join(root)
                executor.submit(process_folder, folder_path)

# Base directory containing multiple folders
base_directory = 'Syllabus'

# Process all folders in parallel
process_all_folders(base_directory)
