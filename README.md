# 📄 Google Docs MCP Extension for Goose

> Built by [Harold Moses (@hmoses)](https://github.com/hmoses)

A powerful [Model Context Protocol (MCP)](https://modelcontextprotocol.io) extension that gives [Goose](https://github.com/block/goose) full read and write access to your Google Docs and Google Drive. Ask Goose to read, edit, create, format, share, and manage your Google Docs — all in natural language.

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-compatible-green.svg)](https://modelcontextprotocol.io)

---

## ✨ Features — 18 Tools

| Tool | Description |
|------|-------------|
| `google_docs_auth_status` | Check authentication status |
| `google_docs_authenticate` | Trigger OAuth 2.0 login flow |
| `google_docs_read` | Read full text content of any Google Doc |
| `google_docs_get_metadata` | Get title, ID, and revision info |
| `google_docs_create` | Create a new Google Doc with optional body text |
| `google_docs_append_text` | Append text to the end of a document |
| `google_docs_replace_text` | Find-and-replace text across a document |
| `google_docs_insert_text` | Insert text at a specific character index |
| `google_docs_delete_range` | Delete a character range |
| `google_docs_apply_bold` | Apply bold formatting to a range |
| `google_docs_set_heading` | Set paragraph heading level (H1–H6 or Normal) |
| `google_docs_batch_update` | Send raw Docs API batchUpdate (advanced) |
| `google_docs_list` | List all your Google Docs (with optional search) |
| `google_docs_copy` | Duplicate a document with a new title |
| `google_docs_delete` | Move a document to trash |
| `google_docs_rename` | Rename a document |
| `google_docs_share` | Share a document with an email (reader/writer/commenter) |
| `google_docs_export` | Export document as plain text or HTML |

---

## 🚀 Quick Start

```bash
git clone https://github.com/hmoses/goose-google-docs-extension
cd goose-google-docs-extension
chmod +x install.sh && ./install.sh
```

Then follow the [Google Cloud Setup](#-google-cloud-setup) steps below.

---

## 🔑 Google Cloud Setup (One-Time)

1. **Create a project** → https://console.cloud.google.com/projectcreate
2. **Enable APIs:**
   - [Google Docs API](https://console.cloud.google.com/apis/library/docs.googleapis.com)
   - [Google Drive API](https://console.cloud.google.com/apis/library/drive.googleapis.com)
3. **Create OAuth credentials** → https://console.cloud.google.com/apis/credentials
   - Type: **Desktop app**
   - Download JSON → rename to `credentials.json`
4. **Place credentials:**
   ```bash
   mv ~/Downloads/client_secret_*.json ~/.config/goose/google-docs-extension/credentials.json
   ```
5. **Add yourself as test user** → https://console.cloud.google.com/auth/audience
6. **Restart Goose** and ask: *"authenticate with google docs"*

---

## 💬 Example Usage

```
"Read this Google Doc: https://docs.google.com/document/d/ID/edit"
"Create a new doc called 'Meeting Notes' with today's agenda"
"Find and replace 'Q1' with 'Q2' in my strategy doc"
"List all my Google Docs"
"Share this doc with alice@example.com as a writer"
"Append a conclusion section to this document"
"Copy my template and name it 'Project Alpha'"
```

---

## 🔐 Security

- Credentials stored locally at `~/.config/goose/google-docs-extension/`
- Only requests `documents` and `drive` OAuth scopes
- No data sent anywhere except Google's APIs
- Revoke access anytime: https://myaccount.google.com/permissions

---

## 📄 License

MIT © 2025 Harold Moses ([@hmoses](https://github.com/hmoses))
