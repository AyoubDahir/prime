# 01 — Overview

## What Was Built

A natural language AI assistant embedded directly inside the Alihsan Hospital Management System Frappe desk. Hospital staff open a chat page, type a question or instruction in plain English, and the AI either answers with live data from the database or performs the requested action in the system.

## The Problem It Solves

Without this assistant, a receptionist who wants to know "how many patients were seen today" has to:
1. Navigate to the Patient Appointment list
2. Apply a date filter
3. Count or export the results

With the assistant, they type that sentence and get the answer instantly. The same applies to creating records, checking invoices, or looking up patient history — it all becomes a conversation.

## Two Core Capabilities

### 1. Question Answering from Live Data

The user asks a question. The AI understands it, translates it into a database query against the correct Frappe doctype, fetches the result, and replies in natural language.

**Examples:**
- "How many patients were registered this month?" → queries `Patient` doctype with date filter → "47 patients were registered this month."
- "What is the total outstanding amount on unpaid invoices?" → queries `Sales Invoice` with `outstanding_amount > 0` → "The total outstanding is $12,450."
- "Show me today's open appointments" → queries `Patient Appointment` filtered by today's date and status=Open → returns a formatted list.

### 2. Action Execution from Instructions

The user gives an instruction. The AI understands it as an action, asks for confirmation, then creates or updates the record in Frappe and confirms what was done.

**Examples:**
- "Register a patient named Ayoub, male, age 25" → AI summarizes the action, user confirms → creates `Patient` record → "Patient registered: PAT-00456."
- "Update appointment APP-00012 status to Scheduled" → updates the record → "Appointment APP-00012 updated."

## Why This Approach (No Training Required)

A common misconception is that you need to "train" the AI on your system. This is not how it works here.

Claude (the AI model by Anthropic) already understands language perfectly. What it needs to answer questions about *your specific system* is two things:

1. **Tools** — Python functions it can call to query your database or perform actions
2. **Context** — A description of your doctypes, field names, and business rules

Both are provided at runtime. No machine learning, no datasets, no fine-tuning. When you change a business rule, you update one line in the system prompt. When you add a new doctype, you add one tool or extend the system prompt.

## Technology Stack

| Layer | Technology | Role |
|-------|-----------|------|
| AI Model | Claude claude-opus-4-7 (Anthropic) | Understands language, decides what to do |
| AI Protocol | Tool Use (function calling) | Structured bridge between language and code |
| Backend | Python (Frappe whitelist) | Executes queries and actions against the DB |
| Database Access | `frappe.get_list`, `frappe.get_doc`, `frappe.db.sql` | Live data, permissions enforced automatically |
| Frontend | Frappe Desk Page (JavaScript + jQuery) | Chat UI inside the hospital system |
| Package | `anthropic` Python SDK | Calls the Claude API |

## What Makes It Safe

- **No direct database access from the AI.** The AI cannot write SQL. It calls Python functions (tools) that are controlled by the developer.
- **Frappe permissions are automatically enforced.** All database calls run as the logged-in user. If a nurse does not have permission to view Sales Invoices, the tool call will fail with a permission error — Frappe handles this the same way it does for any other page.
- **Write actions require confirmation.** The system prompt instructs the AI to always summarize what it intends to do and ask the user to confirm before calling any create or update tool.
- **API key is a server secret.** The Anthropic API key is stored in `site_config.json` on the server, never in code or git.
