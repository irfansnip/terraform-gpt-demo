import requests
from dotenv import load_dotenv
import os
import subprocess
import json

load_dotenv()
api_key = os.environ["OPENAI_API_KEY"]

# Run Terraform plan (you already did this, just making sure)
subprocess.run("terraform init -input=false -no-color", shell=True, check=True)
subprocess.run("terraform plan -out=tfplan.bin -no-color", shell=True, check=True)

# Get JSON of plan
plan_json = subprocess.check_output("terraform show -json tfplan.bin", shell=True)

# Prepare prompt
prompt = f"""
Summarize this Terraform plan.
Sections:
1. High-level summary
2. Risks (security, cost, deletions)
3. Suggested fixes
4. Changelog

Plan JSON (truncated):
{plan_json[:8000]}
"""

# OpenAI API call
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

data = {
    "model": "gpt-4o-mini",
    "input": prompt
}

response = requests.post("https://api.openai.com/v1/responses", headers=headers, data=json.dumps(data))

resp_json = response.json()

# The correct way to get output text from the new Responses API
# It may be nested under resp_json['output'][0]['content'][0]['text']
try:
    output_text = resp_json["output"][0]["content"][0]["text"]
    print(output_text)
except (KeyError, IndexError):
    print("Error: Could not extract text from OpenAI response")
    print(json.dumps(resp_json, indent=2))