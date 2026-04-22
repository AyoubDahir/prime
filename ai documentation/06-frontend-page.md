# 06 — Frontend Page Deep Dive

The chat UI is a Frappe desk page — a standard Frappe extension point for adding custom pages to the desk interface.

## Files

```
prime/page/ai_assistant/
  ai_assistant.json    ← Page manifest (metadata, roles, module)
  ai_assistant.py      ← Empty Python controller (required by Frappe)
  ai_assistant.js      ← All UI logic
```

## ai_assistant.json — Page Manifest

```json
{
  "doctype": "Page",
  "module": "Prime",
  "name": "ai-assistant",
  "page_name": "ai-assistant",
  "title": "AI Assistant",
  "standard": "Yes",
  "roles": [
    {"role": "System Manager"},
    {"role": "Physician"},
    {"role": "Nurse"},
    {"role": "Receptionist"},
    {"role": "Main Cashier"},
    {"role": "Lab Technician"},
    {"role": "Pharmacy"}
  ]
}
```

**Key fields:**

- `name` / `page_name`: Must use hyphens, not underscores. This determines the URL: `/app/ai-assistant`
- `module: "Prime"`: Associates the page with the Prime app — required for Frappe to register it during `bench migrate`
- `standard: "Yes"`: Marks this as a framework page (not a custom user-created page) — required for deployment via fixtures
- `roles`: Frappe enforces this. Users without any of these roles cannot access the page. You can add or remove roles here without changing any other code.

## ai_assistant.py — Empty Controller

```python
(empty file)
```

Frappe requires a `.py` file alongside every page's `.js` and `.json`. Even if empty, it must exist. Without it, Frappe cannot load the page module.

## ai_assistant.js — The Chat UI

### Page Initialization

```javascript
frappe.pages["ai-assistant"].on_page_load = function (wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: "AI Assistant",
        single_column: true,
    });
```

`frappe.ui.make_app_page()` creates the standard Frappe page scaffold — title bar, breadcrumbs, action buttons area, and a `page.body` container. `single_column: true` removes the sidebar for a clean full-width layout.

`on_page_load` fires once when the user first navigates to the page. It does not re-fire on subsequent visits unless the page is explicitly destroyed.

### CSS Injection

```javascript
$(page.body).append('<style>...');
```

Styles are injected directly into `page.body` rather than a separate CSS file. This keeps the page self-contained and avoids needing to register a CSS file in `hooks.py`.

**Why no template literals?**
The Frappe page asset pipeline (used in `his.js` and `his.css` via `hooks.py`) has issues with ES6 template literals (backticks). To stay consistent with the existing codebase pattern — where all page JS uses string concatenation — no template literals are used in this file.

### HTML Structure

```javascript
$(page.body).append(
    '<div class="ai-wrap">'
    + '<div class="ai-messages" id="ai-msgs">...</div>'
    + '<div class="ai-footer">'
    + '<input type="text" class="form-control" id="ai-input" ...>'
    + '<button class="btn btn-primary" id="ai-send">Send</button>'
    + '</div>'
    + '</div>'
);
```

The layout is a flex column:
- `ai-wrap` — full height flex container
- `ai-messages` — scrollable message area (`flex: 1` grows to fill space)
- `ai-footer` — fixed-height input row at the bottom

Elements are found via `.find()` scoped to `page.body` to avoid conflicts with other pages:

```javascript
var $msgs  = $(page.body).find("#ai-msgs");
var $input = $(page.body).find("#ai-input");
var $send  = $(page.body).find("#ai-send");
```

### Conversation History

```javascript
var history = [];
```

The history is a JavaScript array stored in the closure of `on_page_load`. It persists as long as the page is open. Each element is a message object:

```javascript
// User message
{ "role": "user", "content": "How many patients today?" }

// AI reply
{ "role": "assistant", "content": "47 patients were registered today." }
```

The array is trimmed to 20 entries (10 exchanges) after each response:
```javascript
if (history.length > 20) {
    history = history.slice(history.length - 20);
}
```

This prevents the payload from growing indefinitely and keeps Claude's context within reasonable token limits.

### The send() Function

```javascript
function send() {
    var msg = $input.val().trim();
    if (!msg) return;
    $input.val("");
    appendMsg("user", msg);

    // Show thinking indicator
    var $thinking = $('<div class="ai-msg ai-msg-thinking">Thinking…</div>');
    $msgs.append($thinking);

    setLoading(true);

    frappe.call({
        method: "prime.api.ai.chat",
        args: {
            message: msg,
            history: JSON.stringify(history)
        },
        timeout: 120,   // 2 minutes — AI calls can be slow
        callback: function (r) {
            $thinking.remove();
            if (r.message) {
                appendMsg("bot", r.message.reply);
                history = r.message.history || [];
                ...
            }
            setLoading(false);
            $input.focus();
        },
        error: function () {
            $thinking.remove();
            appendMsg("bot", "Something went wrong. Please check the console and try again.");
            setLoading(false);
        }
    });
}
```

Key design decisions:
- `timeout: 120` — Claude API calls can take 10-30 seconds for complex multi-tool requests. The default Frappe timeout is 60s which would cut them off.
- `JSON.stringify(history)` — the history array is serialized to a string because `frappe.call()` sends args as a flat object, and nested arrays can have serialization issues.
- `$thinking` indicator — gives immediate feedback while the AI processes. Without it, the UI appears frozen.
- `setLoading(true)` — disables both input and button to prevent duplicate submissions.

### appendMsg()

```javascript
function appendMsg(role, text) {
    var cls = role === "user" ? "ai-msg ai-msg-user" : "ai-msg ai-msg-bot";
    var $m = $('<div></div>').addClass(cls).text(text);
    $msgs.append($m);
    $msgs.scrollTop($msgs[0].scrollHeight);
    return $m;
}
```

`.text(text)` (not `.html()`) is used intentionally — it escapes HTML characters, preventing XSS if the AI response contains any HTML-like strings. `scrollTop` auto-scrolls to the latest message after each append.

### Keyboard Shortcut

```javascript
$input.on("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) send();
});
```

Enter sends the message. Shift+Enter is reserved for future multi-line input support.
