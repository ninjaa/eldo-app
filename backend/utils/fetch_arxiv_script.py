import requests
import json


def fetch_arxiv_script(pdf_url, audience_type="high school", debug=False):
    prompt_id = "cc4860c3-c22a-419e-a071-11e178bb4b69"
    api_key = "sk-7PaL8YSTAJmc1hpFsLsMy4vVykWnqmY3yuuJwS7oAGahoSiRLl2SKi"

    # Execute the prompt with the PDF URL
    response = requests.post(f"https://app.wordware.ai/api/prompt/{prompt_id}/run",
                             json={"inputs": {"pdf_url": pdf_url,
                                              "audience_type": audience_type}},
                             headers={"Authorization": f"Bearer {api_key}"},
                             stream=True)

    # Ensure the request was successful
    if response.status_code == 200:
        for line in response.iter_lines():
            if line:
                content = json.loads(line.decode('utf-8'))
                value = content.get('value', {})
                # Assuming 'le_script' is part of the 'outputs' type in the streamed response
                if content.get('type') == "chunk" and content.get('value', {}).get('type') == "outputs":
                    le_script = content.get('value', {}).get(
                        'values', {}).get('le script', None)
                    if le_script is not None:
                        print("le_script:", le_script)
                        return le_script
                    else:
                        print("Key 'le_script' not found in the response.")
                        return False
    else:
        print(f"Failed to fetch data, status code: {response.status_code}")
        return False


# Example usage
fetch_arxiv_script("https://arxiv.org/pdf/2404.10636.pdf")
