import argparse
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()


def read_text_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


def fetch_arxiv_script(input_data, audience_type="high school", debug=False):
    if input_data.startswith("http"):
        prompt_id = "ee826b07-7786-4fa3-9173-f9c69283fed2"
        inputs = {"pdf_url": input_data, "audience_type": audience_type}
    else:
        prompt_id = "cc4860c3-c22a-419e-a071-11e178bb4b69"
        document_text = read_text_file(input_data)
        inputs = {"input_document_text": document_text,
                  "audience_type": audience_type}

    api_key = os.getenv("WORDWARE_API_KEY")
    print(inputs)
    # Execute the prompt with the appropriate input
    response = requests.post(f"https://app.wordware.ai/api/prompt/{prompt_id}/run",
                             json={"inputs": inputs},
                             headers={"Authorization": f"Bearer {api_key}"},
                             stream=True)

    print(response.status_code)

    # Process the response
    if response.status_code == 200:
        for line in response.iter_lines():
            if line:
                content = json.loads(line.decode('utf-8'))
                print(content)
                if content.get('type') == "chunk" and content.get('value', {}).get('type') == "outputs":
                    le_script = content.get('value', {}).get(
                        'values', {}).get('le_script', None)
                    if le_script is not None:
                        print("le_script:", le_script)
                        return le_script
                    else:
                        print("Key 'le_script' not found in the response.")
                        return False
    else:
        print(f"Failed to fetch data, status code: {response.status_code}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch script from arXiv or text file.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--pdf-url", type=str, help="URL of the PDF document.")
    group.add_argument("--file-path", type=str,
                       help="Path to the text file containing document content.")
    parser.add_argument("--audience-type", type=str, default="high school",
                        help="Audience type for the script.")  # Added audience-type as an optional argument

    args = parser.parse_args()

    if args.pdf_url:
        fetch_arxiv_script(args.pdf_url, args.audience_type)
    elif args.file_path:
        fetch_arxiv_script(args.file_path, args.audience_type)
