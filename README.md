# AI Employee - Bronze Tier Gmail Watcher

Autonomous AI employee that monitors Gmail, processes emails using Claude Code, and organizes everything in Obsidian.

## 🎯 What This Does

- **Watches** Gmail for important/urgent emails (24/7)
- **Detects** new emails and creates structured action items
- **Processes** emails using Claude Code with custom Agent Skills
- **Organizes** everything in an Obsidian vault for easy review

## 🏆 Hackathon Submission

- **Tier**: Bronze
- **Demo Video**: https://youtu.be/JnddztQi1mU
- **Participant**: ABU BAKAR RAMZAN 
- **Completion Date**: 23rd January 2026

## 📁 Project Structure
HACKATHON-0/
├── watchers/
│   ├── base_watcher.py          # Base class for all watchers
│   └── gmail_watcher.py         # Gmail monitoring implementation
├── agent_skills/
│   └── email_processing_skill.md # Claude's email processing instructions
├── orchestrator.py               # Coordinates watcher + Claude Code
├── test_setup.py                 # Setup verification script
└── .env.example                  # Configuration template

## 🚀 Setup Instructions

### Prerequisites

- Python 3.13+
- UV package manager ([Install guide](https://github.com/astral-sh/uv))
- Claude Code ([Download](https://github.com/anthropics/claude-code))
- Obsidian ([Download](https://obsidian.md/))
- Google Cloud account (for Gmail API)

### Installation

1. **Clone the repository**
```bash
   git clone 'repository_link'
   cd HACKATHON-0
```

2. **Install dependencies**
```bash
   uv sync
```

3. **Set up Gmail API credentials**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create project and enable Gmail API
   - Create OAuth 2.0 credentials (Desktop app)
   - Download and save as `credentials.json` in project root

4. **Configure environment**
```bash
   cp .env.example .env
   # Edit .env with your actual paths
```

5. **Set up Obsidian vault**
   - Create vault named `AI_Employee_Vault`
   - Create folders: `/Needs_Action`, `/Done`, `/Logs`, `/agent_skills`
   - Copy `agent_skills/email_processing_skill.md` to vault's `/agent_skills/`
   - Create `Dashboard.md` and `Company_Handbook.md`

6. **Test setup**
```bash
   uv run python test_setup.py
```

## 🏃 Running the AI Employee

### Start Both Components

**Terminal 1 - Gmail Watcher:**
```bash
uv run python watchers/gmail_watcher.py
```

**Terminal 2 - Orchestrator:**
```bash
uv run python orchestrator.py
```
## 🔄 Workflow

![Workflow Diagram](workflow_diagrams/Bronze_teir_workflow_diagram.mermaid)
```


---

## 🎨 The Workflow Shows:
```
📧 Email Arrives → 🔍 Watcher Detects → 📝 Needs_Action 
→ ⚙️ Orchestrator Triggers → 🤖 Claude Processes → ✅ Done


### Test It Works

1. Send yourself an email with "urgent" in the subject
2. Wait 2-3 minutes
3. Check your vault's `/Done` folder for the processed email
4. Check `Dashboard.md` for updated stats

## 🔧 Configuration

### Customize Gmail Search

Edit `gmail_watcher.py`, line 30:
```python
# Default: unread + important
search_query = 'is:unread is:important'

# Only from specific sender
search_query = 'is:unread from:boss@company.com'

# Only recent emails
search_query = 'is:unread is:important newer_than:1d'
```

### Adjust Check Frequency

In `.env`:
```bash
# Check every 2 minutes (default)
CHECK_INTERVAL=120

# Check every 5 minutes
CHECK_INTERVAL=300
```

### Customize Processing Behavior

Edit `agent_skills/email_processing_skill.md` to change:
- Priority keywords
- Response templates
- Approval thresholds

## 📊 Monitoring

### Logs Location

All activity logs are in your Obsidian vault:
AI_Employee_Vault/Logs/
├── 2026-01-22.log              # Watcher logs
├── 2026-01-22_orchestrator.log # Orchestrator logs
└── 2026-01-22_*_claude_output.md # Claude's responses

### Dashboard

Open `Dashboard.md` in Obsidian to see:
- System status
- Pending action count
- Completed task count
- Last check time

## 🔒 Security

### Credential Handling

- ✅ All secrets stored in `.env` (never committed)
- ✅ Gmail credentials in `credentials.json` (gitignored)
- ✅ OAuth tokens in `token.json` (gitignored)
- ✅ `.gitignore` prevents accidental secret commits

### What's Safe to Share

- ✅ All `.py` code files
- ✅ Agent skill files
- ✅ `.env.example` (template only)
- ✅ Documentation

### What's NEVER Shared

- ❌ `.env` (real values)
- ❌ `credentials.json`
- ❌ `token.json`
- ❌ Any files with API keys or passwords

## 🐛 Troubleshooting

### Gmail Authentication Fails
- Delete `token.json` and re-authenticate
- Verify Gmail API is enabled in Google Cloud Console
- Check OAuth consent screen is configured

### Watcher Not Detecting Emails
- Check Gmail search query in `gmail_watcher.py`
- Verify email matches criteria (unread + important)
- Check logs in vault's `/Logs` folder

### Claude Not Processing
- Verify Claude Code is installed: `claude --version`
- Check skill file path in orchestrator
- Review Claude's output in `/Logs/*_claude_output.md`

### Files Not Moving to /Done
- Check vault path in `.env` is correct
- Verify folder permissions
- Look for errors in orchestrator logs

## 📚 Resources

- [Hackathon Documentation](https://docs.google.com/document/d/[doc-id])
- [Gmail API Documentation](https://developers.google.com/gmail/api)
- [Claude Code Documentation](https://github.com/anthropics/claude-code)
- [Agent Skills Guide](https://platform.claude.com/docs/agents-and-tools/agent-skills)

## 🎓 What I Learned

Building this Bronze tier system taught me several things:

*Technical learnings:*
- How to integrate Gmail API with Python
- Working with Claude Code's automation capabilities
- Building reusable watcher patterns with proper error handling
- The importance of Agent Skills for consistent AI behavior

*Challenges I faced:*
- Getting Claude Code to run non-interactively was tricky - I had to use the 'yes' pipe trick to auto-approve file operations
- Managing permissions between the watcher, orchestrator, and Claude
- Preventing the watcher from processing old emails - I added a time filter

*What I'd do differently:*
- Add more robust error handling for network failures
- Implement better logging with log rotation
- Create a simple web dashboard instead of just Obsidian"

## 🚀 Future Improvements (Silver/Gold Tier)

- [ ] Add WhatsApp watcher
- [ ] Implement MCP servers for sending emails
- [ ] Add human-in-the-loop approval workflow
- [ ] Deploy to cloud for 24/7 operation
- [ ] Add more watchers (LinkedIn, Twitter)

## 📝 License

MIT License - feel free to use and modify!

## 🙏 Acknowledgments

- Anthropic for Claude Code
- Panaversity for the hackathon
- The Obsidian team

---

**Built for Personal AI Employee Hackathon 0 - Bronze Tier**