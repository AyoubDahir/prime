# 09 — Troubleshooting

## Error: "anthropic package is not installed"

**Message:** `anthropic package is not installed. Run: bench pip install anthropic`

**Cause:** The Docker image was built before `anthropic` was added to `requirements.txt`, or `bench pip install` was not run.

**Fix (temporary — live server):**
```bash
kubectl exec -it erpnext-dev-gunicorn-<pod> -n erpnext-dev -- \
  bench pip install anthropic
kubectl exec -it erpnext-dev-worker-default-<pod> -n erpnext-dev -- \
  bench pip install anthropic
```

**Fix (permanent — GitOps):**
Ensure `requirements.txt` contains `anthropic>=0.40.0` and trigger a full image rebuild by changing `CACHE_BUSTER` in `erpnext-build/Dockerfile`.

---

## Error: "anthropic_api_key is not set in site_config.json"

**Cause:** The API key was never configured on the server.

**Fix:**
```bash
kubectl exec -it erpnext-dev-gunicorn-<pod> -n erpnext-dev -- \
  bench --site alihsans.com set-config anthropic_api_key "sk-ant-YOUR-KEY-HERE"
```

To verify it's set:
```bash
kubectl exec -it erpnext-dev-gunicorn-<pod> -n erpnext-dev -- \
  bench --site alihsans.com execute \
  "import frappe; frappe.connect(); print(bool(frappe.conf.get('anthropic_api_key')))"
```

---

## Page Not Found at /app/ai-assistant

**Cause:** `bench migrate` has not run since the page was added.

**Check if the page exists in DB:**
```bash
kubectl exec -it erpnext-dev-gunicorn-<pod> -n erpnext-dev -- \
  bench --site alihsans.com execute \
  "import frappe; frappe.connect(); print(frappe.db.exists('Page', 'ai-assistant'))"
```

If it prints `None`, migrate is needed:
```bash
kubectl exec -it erpnext-dev-gunicorn-<pod> -n erpnext-dev -- \
  bench --site alihsans.com migrate
```

The ArgoCD PreSync job runs migrate automatically on every deployment, so this should only be needed if you're testing locally or migrate was skipped.

---

## "You don't have permission to access this page"

**Cause:** The logged-in user's role is not in the `roles` list in `ai_assistant.json`.

**Fix:** Add the role to `prime/page/ai_assistant/ai_assistant.json`:
```json
"roles": [
  {"role": "System Manager"},
  {"role": "Your New Role"}
]
```

Commit, push, and trigger a rebuild. Or patch directly on the server:
```bash
kubectl exec -it erpnext-dev-gunicorn-<pod> -n erpnext-dev -- \
  bench --site alihsans.com execute \
  "import frappe; frappe.connect(); \
   page = frappe.get_doc('Page', 'ai-assistant'); \
   page.append('roles', {'role': 'Your New Role'}); \
   page.save(); frappe.db.commit(); print('done')"
```

---

## AI Gives Wrong Answers / Wrong Doctype

**Cause:** The doctype, field name, or business rule is missing from the system prompt.

**Debug — check what Claude called:**
Add logging to `_execute_tool()`:
```python
def _execute_tool(tool_name, tool_input):
    frappe.logger().info("AI tool call: {} {}".format(tool_name, json.dumps(tool_input)))
    ...
```

Then check logs:
```bash
kubectl logs -n erpnext-dev erpnext-dev-gunicorn-<pod> --tail=50 | grep "AI tool call"
```

**Fix:** Add the missing doctype or rule to `_build_system_prompt()` in `prime/api/ai.py`. No migration needed — changes take effect immediately.

---

## AI Calls the Wrong Tool (e.g., query_data instead of aggregate_data)

**Cause:** The tool `description` field is not specific enough about when to use it.

**Fix:** Make the descriptions more distinct. For example:

```python
# Too vague:
"description": "Get data from the system"

# Better:
"description": (
    "Fetch a LIST of records. Use when the user wants to SEE records "
    "('show me', 'list', 'find'). Do NOT use for counts or totals — "
    "use aggregate_data for those."
)
```

---

## Request Times Out

**Cause:** The Anthropic API took longer than the `timeout` setting (120 seconds). This can happen for complex multi-tool chains.

**Fix Option 1:** Increase the timeout in `ai_assistant.js`:
```javascript
frappe.call({
    ...
    timeout: 180,   // 3 minutes
    ...
})
```

**Fix Option 2:** Use a faster model for simple requests:
```python
model="claude-sonnet-4-6"   # faster, cheaper
```

---

## Tool Returns a Permission Error

**Message in chat:** "Your role does not have permission to access [DocType]"

**Cause:** The logged-in user's Frappe role does not have read permission on the queried doctype.

**Fix:** Grant the role read permission on the doctype in Frappe:
`Settings → Role Permissions Manager → [DocType] → Add role`

This is correct behavior — the AI respects Frappe permissions exactly like any other page.

---

## History Causes API Errors (Invalid Tool Use Blocks)

**Cause:** Old tool_use message blocks with stale IDs were sent back to Claude. The Anthropic API rejects these.

**The code already handles this** by filtering out non-text messages from history:
```python
for m in parsed:
    if isinstance(m.get("content"), str):   # only text messages
        messages.append(m)
```

If you see Anthropic API errors mentioning `tool_use_id`, ensure this filter is in place.

---

## Checking Anthropic API Status and Usage

Monitor API usage at: **console.anthropic.com**

To check if the API key is valid:
```python
import anthropic
client = anthropic.Anthropic(api_key="sk-ant-...")
response = client.messages.create(
    model="claude-opus-4-7",
    max_tokens=10,
    messages=[{"role": "user", "content": "Hi"}]
)
print(response.content)
```

Common API errors:
- `401 Unauthorized` — wrong API key
- `429 Rate Limited` — too many requests (throttle or upgrade plan)
- `529 Overloaded` — Anthropic service issue, retry after a few seconds
