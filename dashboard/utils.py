import json

def format_github_issue(bug_data: dict) -> str:
    """Formats bug analysis into GitHub Markdown format."""
    return f"""## 🐛 [{bug_data.get('priority', 'P2')}] {bug_data.get('bug_summary', 'Bug Report')}

**Category:** {bug_data.get('category', 'General')}  
**Severity:** `{bug_data.get('severity', 'Medium')}` | **Priority:** `{bug_data.get('priority', 'P2')}`  
**Affected Component:** `{bug_data.get('affected_component', 'Unknown')}`  
**AI Confidence:** {int(bug_data.get('confidence_score', 0.9) * 100)}%

---

### 🔍 Probable Root Cause
{bug_data.get('probable_root_cause', 'N/A')}

### 🛠️ Technical Breakdown
{bug_data.get('technical_analysis', 'N/A')}

### 💡 Suggested Fix
```typescript
{bug_data.get('suggested_fix', {}).get('code_snippet', '// No code patch provided')}
```

### ⚠️ Missing Information Required

{chr(10).join([f"- {item}" for item in bug_data.get('missing_information', [])])}
"""

def format_jira_issue(bug_data: dict) -> str:
    """Formats bug analysis into Jira Markup format."""
    return f"""h2. [{bug_data.get('priority', 'P2')}] {bug_data.get('bug_summary')}

*Category:* {bug_data.get('category')}
*Severity:* {bug_data.get('severity')}
*Priority:* {bug_data.get('priority')}
*Component:* {bug_data.get('affected_component')}

h3. Probable Root Cause
{bug_data.get('probable_root_cause')}

h3. Suggested Code Fix
{{code:javascript}}
{bug_data.get('suggested_fix', {}).get('code_snippet', '')}
{{code}}
"""
