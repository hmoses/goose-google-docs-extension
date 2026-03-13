# 📄 Google Docs MCP Extension for Goose

> **Give [Goose](https://github.com/block/goose) full read and write access to your Google Docs and Google Drive — just by asking.**

Built by [Harold Moses (@hmoses)](https://github.com/hmoses).

---

## What This Extension Does

This extension connects Goose directly to your **Google Docs** and **Google Drive** using the official Google APIs. Once installed and authenticated, you can ask Goose to read, write, create, edit, format, share, and manage your Google Docs using plain natural language — no copy-pasting, no manual editing.

**Before this extension**, if you wanted Goose to help with a Google Doc, you had to:
1. Open the doc manually
2. Copy all the text
3. Paste it into Goose
4. Get edits back
5. Manually apply them yourself

**With this extension**, just say:
> *"Read my resume at this URL and update the summary section to highlight my Kubernetes experience"*

Goose reads the doc, makes the edits, and writes them back — all without you leaving the conversation.

---

## ✨ What You Can Do

### 📖 Read & Inspect
- Read the full text content of any Google Doc by URL or ID
- Get document metadata (title, revision ID, doc ID)
- Export a doc as plain text or HTML
- List all your Google Docs, sorted by most recently modified
- Search your Drive for docs by name

### ✏️ Write & Edit
- Create brand new Google Docs with optional body text
- Append text to the end of any document
- Find and replace text across an entire document
- Insert text at any specific character position
- Delete any range of text by index
- Send raw Docs API `batchUpdate` requests for advanced edits

### 🎨 Format
- Apply **bold** formatting to any text range
- Set paragraph heading styles (Heading 1–6 or Normal Text)

### 📁 Manage
- Copy a document with a new title
- Rename a document
- Move a document to trash (soft delete)
- Share a document with any email address as reader, commenter, or writer

### 🔐 Authenticate
- Check your current Google auth status
- Trigger the OAuth 2.0 login flow with one command (browser-based, one-time setup)
- Credentials auto-refresh — you stay logged in

---

## 🛠 Tools Reference

| Tool | What It Does |
|------|-------------|
| `google_docs_auth_status` | Check if you're authenticated with Google |
| `google_docs_authenticate` | Start the OAuth 2.0 browser login flow |
| `google_docs_read` | Read the full text of a Google Doc |
| `google_docs_get_metadata` | Get title, doc ID, and revision info |
| `google_docs_create` | Create a new Google Doc |
| `google_docs_append_text` | Append text to the end of a doc |
| `google_docs_replace_text` | Find and replace text across a doc |
| `google_docs_insert_text` | Insert text at a specific character index |
| `google_docs_delete_range` | Delete a character range by index |
| `google_docs_apply_bold` | Bold a character range |
| `google_docs_set_heading` | Set heading level for a paragraph |
| `google_docs_batch_update` | Send a raw Docs API batchUpdate request |
| `google_docs_list` | List Google Docs in Drive (with optional search) |
| `google_docs_copy` | Copy a doc with a new title |
| `google_docs_delete` | Move a doc to trash |
| `google_docs_rename` | Rename a doc |
| `google_docs_share` | Share a doc with an email address |
| `google_docs_export` | Export a doc as plain text or HTML |

---

## 🚀 Installation

### Prerequisites

| Requirement | Version | Install |
|-------------|---------|---------|
| Python | 3.10+ | [python.org](https://www.python.org/downloads/) |
| uv *(recommended)* | latest | [astral.sh/uv](https://docs.astral.sh/uv/) |
| Goose | latest | [github.com/block/goose](https://github.com/block/goose) |

### 1. Clone the repo

```bash
git clone https://github.com/hmoses/goose-google-docs-extension.git
cd goose-google-docs-extension
```

### 2. Run the installer

```bash
chmod +x install.sh
./install.sh
```

The installer will:
- ✅ Create a Python virtual environment in `.venv/`
- ✅ Install all dependencies (`mcp`, `google-auth`, `google-api-python-client`, etc.)
- ✅ Create the credentials directory at `~/.config/goose/google-docs-extension/`
- ✅ Register the extension in `~/.config/goose/config.yaml`
- ✅ Print step-by-step instructions for Google Cloud setup

---

## 🔑 Google Cloud Setup (One-Time, ~10 Minutes)

You need a free Google Cloud project to get API access credentials.

### Step 1 — Create a Google Cloud Project
→ [console.cloud.google.com/projectcreate](https://console.cloud.google.com/projectcreate)

### Step 2 — Enable Both APIs
- **Google Docs API** → [Enable](https://console.cloud.google.com/apis/library/docs.googleapis.com)
- **Google Drive API** → [Enable](https://console.cloud.google.com/apis/library/drive.googleapis.com)

### Step 3 — Create OAuth 2.0 Credentials
1. Go to [Credentials](https://console.cloud.google.com/apis/credentials)
2. Click **+ Create Credentials → OAuth client ID**
3. Configure the **OAuth consent screen** if prompted (External, add your email as a test user)
4. Application type: **Desktop app**
5. Click **Create** → **Download JSON**

### Step 4 — Place the Credentials File
```bash
mv ~/Downloads/client_secret_*.json ~/.config/goose/google-docs-extension/credentials.json
```

### Step 5 — Add Yourself as a Test User
→ [console.cloud.google.com/auth/audience](https://console.cloud.google.com/auth/audience)
- Scroll to **Test users** → **+ Add Users** → enter your Gmail → Save

### Step 6 — Restart Goose and Authenticate
Restart Goose, then ask it:
```
"check google docs auth status"
```
Then:
```
"authenticate with google docs"
```
A browser window opens → log in → grant permissions → done! ✅

---

## 💬 Example Prompts

```
"Read this Google Doc: https://docs.google.com/document/d/YOUR_DOC_ID/edit"

"Create a new doc called 'Q2 OKRs' with our team goals for next quarter"

"Find and replace every instance of 'Q1' with 'Q2' in my budget doc"

"List all my Google Docs from the last month"

"Append a conclusion paragraph to this document: https://docs.google.com/..."

"Copy my proposal template and name it 'Project Alpha Proposal'"

"Share my roadmap doc with alice@example.com as a writer"

"Export my meeting notes doc as plain text"

"Update my resume at [URL] to highlight my experience with Kubernetes"
```

---

## 🔐 Security & Privacy

- All credentials are stored **locally** on your machine at `~/.config/goose/google-docs-extension/`
- OAuth tokens are auto-saved and auto-refreshed — no manual token management
- Only two API scopes are requested:
  - `https://www.googleapis.com/auth/documents` — Read/write Google Docs
  - `https://www.googleapis.com/auth/drive` — List/manage files in Drive
- **No data is sent anywhere except Google's own APIs**
- Revoke access anytime at [myaccount.google.com/permissions](https://myaccount.google.com/permissions)

---

## 🗂 Project Structure

```
goose-google-docs-extension/
├── server.py          # MCP server — 18 tools, all logic
├── pyproject.toml     # Python package metadata and dependencies
├── install.sh         # One-click installer and Goose config registration
└── README.md          # This file
```

---

## 🛠 How It Works

This extension is a **stdio MCP server** — Goose spawns it as a subprocess and communicates over `stdin/stdout` using the [Model Context Protocol](https://modelcontextprotocol.io).

```
Goose  ←──── MCP (stdio) ────→  server.py  ←──── HTTPS ────→  Google APIs
```

**Authentication flow:**
1. `google_docs_authenticate` opens a local OAuth flow in your browser
2. You log in with Google and grant permissions
3. The extension receives and saves access + refresh tokens to `token.json`
4. On subsequent calls, tokens are loaded from disk and auto-refreshed when expired

**API architecture:**
- Document content operations → [Google Docs API v1](https://developers.google.com/docs/api/reference/rest)
- File management (list, copy, share, delete, rename) → [Google Drive API v3](https://developers.google.com/drive/api/reference/rest/v3)

---

## ❓ Troubleshooting

| Error | Fix |
|-------|-----|
| `credentials.json not found` | Place your OAuth JSON at `~/.config/goose/google-docs-extension/credentials.json` |
| `Access blocked: app not verified` | Add your Gmail as a test user at [console.cloud.google.com/auth/audience](https://console.cloud.google.com/auth/audience) |
| `Token expired / invalid_grant` | Delete `~/.config/goose/google-docs-extension/token.json` and re-authenticate |
| Extension not showing in Goose | Restart Goose; check `~/.config/goose/config.yaml` for a `google-docs:` block |
| `Permission denied` on install.sh | Run `chmod +x install.sh` first |

---

## 🔄 Updating Dependencies

```bash
./install.sh
```

Re-running the installer is safe — it updates dependencies without overwriting your credentials.

---

## 👤 Author

Built by **Harold Moses** ([@hmoses](https://github.com/hmoses))

Submitted to the [Goose Extensions Marketplace](https://block.github.io/goose/extensions) as a community contribution.

---

## 📄 License

MIT © 2025 — Built for [Goose](https://github.com/block/goose) by the community.
