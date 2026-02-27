import subprocess
import json
import os
import requests

def get_diff():
    result = subprocess.run(
        ["git", "diff", f"origin/{os.environ['GITHUB_BASE_REF']}...HEAD"],
        capture_output=True, text=True
    ).stdout
    lines = result.split('\n')
    if len(lines) > 6000:
        lines = lines[:6000]
        lines.append('\n...truncated...')
    return lines.join('\n')



def run_claude(prompt: str) -> str:
    result = subprocess.run(
        ["claude", "--print", prompt],
        capture_output=True, text=True
    )
    return result.stdout

def post_review(body: str, comments: list):
    """Post a review to the Github PR"""
    repo = os.environ["GITHUB_REPOSITORY"]
    pr_number = os.environ['GITHUB_EVENT_NUMBER']
    token = os.environ['GH_TOKEN']

    headers = {
        'Authorization': f"Bearer {token}",
        'Accept': 'application/vnd.github+json'
    }

    requests.post(
        f"https://api.github.com/repos/{repo}/pulls/{pr_number}/reviews",
        headers=headers,
        json={
            "body": body,
            "event": "COMMENT",
            "comments": comments
        }
    )

def main():
    diff = get_diff()

    if not diff.strip():
        print("No diff found, skipping reviews")
        return
    
    import asyncio

    async def run_claude_async(prompt):
        proc = await asyncio.create_subprocess_exec(
            "claude", "--print", prompt,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        return stdout.decode()
    
    async def run_all_critics():
        critics = {
            "security": f"""
You are a security expert reviewing a PR diff.
Find vulnerabilities, exposed secrets, injection risks and the like.PendingDeprecationWarning

Diff:
{diff}

Return JSON only in the following form:
{{"issues": [{{"severity": "high/medium/low", "description": "...", "file": "...", line=0}}]}}
""",
            "correctness": f"""
You are a senior engineer reviewing a PR diff.
Find bugs, logic errors, unhandled edge cases.

Diff:
{diff}

Return JSON only in the following form:
{{"issues": [{{"severity": "high/medium/low", "description": "...", "file": "...", "line": 0}}]}}
""",
"performance": f"""
You are a performance engineer reviewing a PR diff.
Find inefficiencies, unecessary allocations, unoptimized SQL queries, blocking calls.

Diff:
{diff}

Return JSON only in the following form:
{{"issues": [{{"severity" "high/medium/low", "description", "...", "file": "...", "line": 0}}]}}
"""
        }

        results = await asyncio.gather(*[run_claude_async(prompt) for prompt in critics.values()])
        return dict(zip(critics.keys(), results))
    
    reviews = asyncio.run(run_all_critics())

    all_issues = []
    for critic, raw in reviews.items():
        try:
            import re
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            data = json.loads(match.group())
            for issue in data.get('issues', []):
                issue['critic'] = critic
                all_issues.append(issue)
        except:
            pass
        
    high_severity = [i for i in all_issues if i['severity'] == 'high']
    med_severity = [i for i in all_issues if i['severity'] == 'medium']
    low_severity = [i for i in all_issues if i['severity'] == 'low']

    body = "## 🤖 AI Code Review\n\n"
    
    if high_severity:
        body += "### 🔴 High Priority\n"
        for issue in high_severity:
            body += f"- **[{issue['critic']}]** {issue['description']}\n"
    
    if med_severity:
        body += "\n### 🟡 Medium Priority\n"
        for issue in med_severity:
            body += f"- **[{issue['critic']}]** {issue['description']}\n"
    
    if low_severity:
        body += "\n### 🟢 Suggestions\n"
        for issue in low_severity:
            body += f"- **[{issue['critic']}]** {issue['description']}\n"
    
    if not all_issues:
        body += "✅ No issues found!"
    
    # Build inline comments for specific file/line issues
    inline_comments = [
        {
            "path": issue["file"],
            "line": issue["line"],
            "body": f"**[{issue['critic']} - {issue['severity']}]** {issue['description']}"
        }
        for issue in all_issues
        if issue.get("file") and issue.get("line")
    ]
    
    post_review(body, inline_comments)
    print("Review posted!")



