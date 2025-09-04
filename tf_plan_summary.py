import subprocess
import os
from dotenv import load_dotenv
import requests
import json

load_dotenv()
api_key = os.environ.get("OPENAI_API_KEY")

# -------------------------------
# Step 1: Generate Terraform plan
# -------------------------------
print("Generating Terraform plan...")
subprocess.run("terraform init -input=false -no-color", shell=True, check=True)
subprocess.run("terraform plan -out=tfplan.bin -no-color", shell=True, check=True)

# Get JSON version of plan
plan_json = subprocess.check_output("terraform show -json tfplan.bin", shell=True)
plan_data = json.loads(plan_json)

# -------------------------------
# Step 2: Prepare GPT prompt
# -------------------------------
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

# -------------------------------
# Step 3: Call OpenAI API (if key available)
# -------------------------------
output_text = ""

if api_key:
    print("Calling OpenAI API...")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "gpt-4o-mini",
        "input": prompt
    }

    try:
        response = requests.post(
            "https://api.openai.com/v1/responses",
            headers=headers,
            data=json.dumps(data)
        )
        resp_json = response.json()
        # Extract text safely
        output_text = resp_json["output"][0]["content"][0]["text"]
    except Exception as e:
        print(f"OpenAI API failed: {e}")
        output_text = ""

# -------------------------------
# Step 4: Fallback to dynamic mock GPT summary
# -------------------------------
if not output_text:
    print("Using dynamic mock GPT summary (demo mode)...\n")
    
    # Count resources
    resources = plan_data.get("resource_changes", [])
    num_resources = len(resources)
    resource_types = set(r.get("type") for r in resources)
    
    # Build a realistic summary
    high_level = f"High-Level Summary:\n- {num_resources} resource(s) will be created\n"
    risks = "- Risks:\n"
    fixes = "- Suggested Fixes:\n"
    changelog = "- Changelog:\n"
    
    for r in resources:
        name = r.get("name")
        rtype = r.get("type")
        action = r.get("change", {}).get("actions", ["create"])[0]
        changelog += f"+ {rtype}.{name} ({action})\n"
        # Example simple risk detection
        if rtype == "aws_s3_bucket":
            risks += f"  - S3 bucket \"{name}\" may be public\n"
            fixes += f"  - Set {name} ACL to private\n"
        if rtype == "aws_instance":
            risks += f"  - EC2 instance \"{name}\" may lack encrypted volumes\n"
            fixes += f"  - Enable encrypted EBS volume for {name}\n"
    
    output_text = f"{high_level}\n{risks}\n{fixes}\n{changelog}"

# -------------------------------
# Step 5: Print final summary
# -------------------------------
print(output_text)
