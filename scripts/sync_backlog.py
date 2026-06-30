import os
import json
import requests

# Load environment variables manually from .env if needed
def load_env():
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip()

load_env()

PAT = os.environ.get("GITHUB_PAT")
REPO = "britneyscripts/sleuthdata"

if not PAT:
    print("Error: GITHUB_PAT not found in environment variables or .env file.")
    exit(1)

# API headers
headers = {
    "Authorization": f"token {PAT}",
    "Accept": "application/vnd.github.v3+json"
}

# Fetch existing issues to avoid duplicates
existing_issues = set()
page = 1
print(f"Checking for existing issues in {REPO}...")
while True:
    url = f"https://api.github.com/repos/{REPO}/issues?state=all&per_page=100&page={page}"
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        print(f"Error fetching issues: {res.status_code} - {res.text}")
        break
    data = res.json()
    if not data:
        break
    for issue in data:
        existing_issues.add(issue["title"])
    page += 1

print(f"Found {len(existing_issues)} existing issues.")

# Load backlog
with open("backlog.json", "r") as f:
    backlog = json.load(f)

# Create issues
created_count = 0
for task in backlog:
    title = task["title"]
    if title in existing_issues:
        print(f"Skipping: '{title}' (already exists)")
        continue
        
    print(f"Creating issue: '{title}'...")
    issue_data = {
        "title": title,
        "body": task["body"],
        "labels": task["labels"]
    }
    
    url = f"https://api.github.com/repos/{REPO}/issues"
    res = requests.post(url, headers=headers, json=issue_data)
    if res.status_code == 201:
        print(f"Successfully created: '{title}'")
        created_count += 1
    else:
        print(f"Failed to create '{title}': {res.status_code} - {res.text}")

print(f"\nBacklog sync completed. Created {created_count} new issues.")
