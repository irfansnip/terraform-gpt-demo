from dotenv import load_dotenv
import os
import subprocess
import requests

# Load OpenAI key
load_dotenv()
api_key = os.environ["OPENAI_API_KEY"]

# Run terraform plan locally
subprocess.run("terraform init -input=false -no-color", shell=True, check=True)
subprocess.run("terraform plan -out=tfplan.bin -no-color", shell=True, check=True)

# Convert plan to JSON
plan_json = subprocess.check_output("terraform show -json tfplan.bin", shell=True)

# Prepare GPT prompt
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

# Call GPT API
resp = requests.post(
    "https://api.openai.com/v1/responses",
    headers={"Authorization": f"Bearer {api_key}",
             "Content-Type": "application/json"},
    json={"model": "gpt-4o-mini", "input": prompt}
)

# Print GPT summary
print(resp.json()["output_text"])
