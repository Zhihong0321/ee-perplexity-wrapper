import requests
import json

# UUID for News Rewriter
NEWS_REWRITER_UUID = "6b8829ad-4c17-4a45-ac67-db3b017c2be6"

url = "https://ee-perplexity-wrapper-production.up.railway.app/api/query_sync"
params = {
    'q': 'research this news headline - Anwar Political Sec in trouble',
    'account_name': 'zhihong0321@gmail',
    'collection_uuid': NEWS_REWRITER_UUID
}

print("Fetching full answer...")
response = requests.get(url, params=params, timeout=120)
data = response.json()

# Extract the final answer text
if 'text' in data:
    text_content = data['text']
    # If it's a list of steps, get the final answer from the last step
    if isinstance(text_content, list):
        for step in reversed(text_content):
            if step.get('step_type') == 'FINAL':
                final_answer_json = step['content']['answer']
                # The answer itself is a JSON string inside a JSON string
                try:
                    parsed_answer = json.loads(final_answer_json)
                    # Sometimes it's doubly encoded if the LLM output raw JSON text
                    if isinstance(parsed_answer, str): # Handle double encoding if present
                         try:
                             parsed_answer = json.loads(parsed_answer)
                         except:
                             pass
                    print(json.dumps(parsed_answer, indent=2))
                except Exception as e:
                    print("Could not parse inner JSON, raw text:")
                    print(final_answer_json)
                break
    else:
        print(text_content)
else:
    print("No text found in response.")
