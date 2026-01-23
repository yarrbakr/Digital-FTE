---

---

---
name : email_processing
description : Read emails and analyze their priority and intent, based on the priority, decide the action, draft a response ( if high priority) and finally update the dashboard and move original email to done. Call when user wants to process an email.

---
# Email_Processing_Skill

This skill teaches Claude Code how to process incoming email notifications from the Gmail Watcher and take appropriate action.

## When to Use This Skill

Activate this skill when:

- Files appear in `/Needs_Action` with prefix `EMAIL_`
- Dashboard shows pending email actions
- User requests email processing

## Procedure 

### 1. Scan for Email Files

```
Look in /Needs_Action folder for files starting with EMAIL_
Example: EMAIL_abc123.md
```

### 2. Read and Parse Email Content

Each email file has this structure:

markdown

```markdown
---
type: email
from: sender@example.com
subject: Subject Line Here
received: 2026-01-07T10:30:00Z
priority: high/medium/low
status: pending
---

## Email Content
[Email body or snippet here]

## Suggested Actions
- [ ] Reply to sender
- [ ] Forward to relevant party
- [ ] Archive after processing
```

### 3. Analyze Priority and Intent

**High Priority Indicators:**

- Keywords: "urgent", "asap", "payment", "invoice", "deadline"
- From known clients (check Company_Handbook.md for client list)
- Subject contains: "RE:", "FW:", question marks

**Low Priority Indicators:**

- Marketing emails
- Newsletters
- Automated notifications

### 4. Determine Action

Based on priority, decide:

**For High Priority:**

1. Create a draft response
2. Create approval file in `/Needs_Action` with prefix `APPROVAL_`
3. Update Dashboard.md with pending action

**For Medium Priority:**

1. Log summary in Dashboard.md
2. Move to `/Done` with note

**For Low Priority:**

1. Move to `/Done` with brief note

### 5. Create Draft Response (If High Priority)

Template for draft responses:

markdown

```markdown
---
type: draft_response
original_email: EMAIL_abc123.md
to: sender@example.com
subject: Re: [Original Subject]
status: needs_approval
---

## Draft Email

[Professional greeting]

[Address their specific request/question]

[Next steps or call to action]

[Professional closing]

---
**APPROVAL REQUIRED**: Review this draft and move to /Approved to send
```

### 6. Update Dashboard

Add entry to Dashboard.md under "## Recent Activity":

markdown

```markdown
- [YYYY-MM-DD HH:MM] 📧 Email from [sender] - [brief summary] - [Action taken]
```

### 7. Move Original Email to Done

After processing:

1. Add processing note to the email file
2. Move from `/Needs_Action` to `/Done`
3. Log completion time

## Example Workflow

**Input File:** `/Needs_Action/EMAIL_abc123.md`

markdown

```markdown
---
type: email
from: client@business.com
subject: Need invoice for January
priority: high
---

## Email Content
Hi, can you send me the invoice for January services? Need it by EOD.
```

**Your Actions:**

1. ✅ Identify as high priority (keyword: "invoice", "need")
2. ✅ Check Company_Handbook.md - is this a known client?
3. ✅ Create draft response offering to send invoice
4. ✅ Create approval request (since it's a client action)
5. ✅ Update Dashboard with pending action
6. ✅ Move original email to `/Done`

## Quality Checks

Before considering task complete:

- [ ]  Email content fully read and understood
- [ ]  Priority correctly assessed
- [ ]  Response draft is professional and addresses request
- [ ]  Dashboard updated
- [ ]  Original email moved to /Done
- [ ]  If approval needed, approval file created

## Error Handling

If you encounter:

- **Malformed email file**: Move to `/Logs` with error note
- **Unknown sender with suspicious content**: Flag in Dashboard, don't auto-respond
- **Ambiguous request**: Create approval file asking human for guidance

## Success Criteria

- All emails in `/Needs_Action` processed within 5 minutes
- No emails left unprocessed
- Dashboard accurately reflects current state
- High-priority items have draft responses ready
- Tone matches Company_Handbook.md guidelines