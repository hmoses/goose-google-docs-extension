#!/usr/bin/env python3
"""Google Docs MCP Extension for Goose"""

import json
import os
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import CallToolResult, TextContent, Tool

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive",
]

CONFIG_DIR = Path.home() / ".config" / "goose" / "google-docs-extension"
TOKEN_FILE = CONFIG_DIR / "token.json"
CREDENTIALS_FILE = CONFIG_DIR / "credentials.json"


def ensure_config_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def get_credentials():
    ensure_config_dir()
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        if creds and creds.valid:
            return creds
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                _save_token(creds)
                return creds
            except Exception:
                pass
    return None


def _save_token(creds):
    ensure_config_dir()
    TOKEN_FILE.write_text(creds.to_json())


def run_oauth_flow():
    if not CREDENTIALS_FILE.exists():
        raise FileNotFoundError(
            f"credentials.json not found at {CREDENTIALS_FILE}.\n"
            "Please follow the setup instructions to create a Google Cloud project "
            "and download your OAuth credentials file to that path."
        )
    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
    creds = flow.run_local_server(port=0, open_browser=True)
    _save_token(creds)
    return creds


def get_or_refresh_credentials():
    creds = get_credentials()
    if creds is None:
        creds = run_oauth_flow()
    return creds


def docs_service():
    return build("docs", "v1", credentials=get_or_refresh_credentials())


def drive_service():
    return build("drive", "v3", credentials=get_or_refresh_credentials())


def extract_doc_id(url_or_id):
    if url_or_id.startswith("http"):
        parsed = urlparse(url_or_id)
        parts = parsed.path.split("/")
        try:
            idx = parts.index("d")
            return parts[idx + 1]
        except (ValueError, IndexError):
            pass
    return url_or_id.strip()


def doc_content_to_text(doc):
    lines = []
    body = doc.get("body", {})
    for element in body.get("content", []):
        paragraph = element.get("paragraph")
        if not paragraph:
            continue
        line_parts = []
        for pe in paragraph.get("elements", []):
            text_run = pe.get("textRun")
            if text_run:
                line_parts.append(text_run.get("content", ""))
        lines.append("".join(line_parts))
    return "".join(lines)


def _ok(text):
    return CallToolResult(content=[TextContent(type="text", text=text)])


def _err(text):
    return CallToolResult(
        content=[TextContent(type="text", text=f"❌ Error: {text}")],
        isError=True,
    )


def tool_auth_status():
    creds = get_credentials()
    if creds and creds.valid:
        return _ok("✅ Authenticated with Google. Credentials are valid.")
    if creds and creds.expired:
        return _ok("⚠️  Credentials expired. Will auto-refresh on next API call.")
    return _ok(
        "❌ Not authenticated.\n"
        "Run the `google_docs_authenticate` tool to start the OAuth flow."
    )


def tool_authenticate():
    try:
        creds = get_or_refresh_credentials()
        if creds and creds.valid:
            return _ok(
                "✅ Successfully authenticated with Google!\n"
                f"Token saved to: {TOKEN_FILE}"
            )
        return _err("Authentication completed but credentials appear invalid.")
    except FileNotFoundError as e:
        return _err(str(e))
    except Exception as e:
        return _err(f"OAuth flow failed: {e}")


def tool_read_document(doc_id_or_url):
    try:
        doc_id = extract_doc_id(doc_id_or_url)
        service = docs_service()
        doc = service.documents().get(documentId=doc_id).execute()
        title = doc.get("title", "Untitled")
        text = doc_content_to_text(doc)
        return _ok(f"📄 **{title}**\n\n{text}")
    except HttpError as e:
        return _err(f"Google API error: {e}")
    except Exception as e:
        return _err(str(e))


def tool_get_document_metadata(doc_id_or_url):
    try:
        doc_id = extract_doc_id(doc_id_or_url)
        service = docs_service()
        doc = service.documents().get(documentId=doc_id).execute()
        meta = {
            "title": doc.get("title"),
            "documentId": doc.get("documentId"),
            "revisionId": doc.get("revisionId"),
            "suggestionsViewMode": doc.get("suggestionsViewMode"),
        }
        return _ok(json.dumps(meta, indent=2))
    except HttpError as e:
        return _err(f"Google API error: {e}")
    except Exception as e:
        return _err(str(e))


def tool_create_document(title, body_text=""):
    try:
        service = docs_service()
        doc = service.documents().create(body={"title": title}).execute()
        doc_id = doc["documentId"]
        if body_text:
            requests = [{"insertText": {"location": {"index": 1}, "text": body_text}}]
            service.documents().batchUpdate(
                documentId=doc_id, body={"requests": requests}
            ).execute()
        url = f"https://docs.google.com/document/d/{doc_id}/edit"
        return _ok(f"✅ Created document: **{title}**\n🆔 ID: `{doc_id}`\n🔗 URL: {url}")
    except HttpError as e:
        return _err(f"Google API error: {e}")
    except Exception as e:
        return _err(str(e))


def tool_append_text(doc_id_or_url, text):
    try:
        doc_id = extract_doc_id(doc_id_or_url)
        service = docs_service()
        doc = service.documents().get(documentId=doc_id).execute()
        body = doc.get("body", {})
        content = body.get("content", [])
        end_index = content[-1].get("endIndex", 1) - 1 if content else 1
        requests = [{"insertText": {"location": {"index": end_index}, "text": text}}]
        service.documents().batchUpdate(
            documentId=doc_id, body={"requests": requests}
        ).execute()
        return _ok(f"✅ Appended text to document `{doc_id}`.")
    except HttpError as e:
        return _err(f"Google API error: {e}")
    except Exception as e:
        return _err(str(e))


def tool_replace_text(doc_id_or_url, find, replace_with):
    try:
        doc_id = extract_doc_id(doc_id_or_url)
        service = docs_service()
        requests = [{
            "replaceAllText": {
                "containsText": {"text": find, "matchCase": True},
                "replaceText": replace_with,
            }
        }]
        result = service.documents().batchUpdate(
            documentId=doc_id, body={"requests": requests}
        ).execute()
        replies = result.get("replies", [{}])
        count = replies[0].get("replaceAllText", {}).get("occurrencesChanged", 0)
        return _ok(f"✅ Replaced {count} occurrence(s) of '{find}' with '{replace_with}'.")
    except HttpError as e:
        return _err(f"Google API error: {e}")
    except Exception as e:
        return _err(str(e))


def tool_insert_text_at_index(doc_id_or_url, text, index):
    try:
        doc_id = extract_doc_id(doc_id_or_url)
        service = docs_service()
        requests = [{"insertText": {"location": {"index": index}, "text": text}}]
        service.documents().batchUpdate(
            documentId=doc_id, body={"requests": requests}
        ).execute()
        return _ok(f"✅ Inserted text at index {index} in document `{doc_id}`.")
    except HttpError as e:
        return _err(f"Google API error: {e}")
    except Exception as e:
        return _err(str(e))


def tool_delete_text_range(doc_id_or_url, start_index, end_index):
    try:
        doc_id = extract_doc_id(doc_id_or_url)
        service = docs_service()
        requests = [{"deleteContentRange": {"range": {"startIndex": start_index, "endIndex": end_index}}}]
        service.documents().batchUpdate(
            documentId=doc_id, body={"requests": requests}
        ).execute()
        return _ok(f"✅ Deleted text from index {start_index} to {end_index} in `{doc_id}`.")
    except HttpError as e:
        return _err(f"Google API error: {e}")
    except Exception as e:
        return _err(str(e))


def tool_apply_bold(doc_id_or_url, start_index, end_index):
    try:
        doc_id = extract_doc_id(doc_id_or_url)
        service = docs_service()
        requests = [{
            "updateTextStyle": {
                "range": {"startIndex": start_index, "endIndex": end_index},
                "textStyle": {"bold": True},
                "fields": "bold",
            }
        }]
        service.documents().batchUpdate(
            documentId=doc_id, body={"requests": requests}
        ).execute()
        return _ok(f"✅ Applied bold to range [{start_index}, {end_index}].")
    except HttpError as e:
        return _err(f"Google API error: {e}")
    except Exception as e:
        return _err(str(e))


def tool_set_heading(doc_id_or_url, start_index, end_index, heading_level):
    valid = {"HEADING_1", "HEADING_2", "HEADING_3", "HEADING_4", "HEADING_5", "HEADING_6", "NORMAL_TEXT"}
    if heading_level not in valid:
        return _err(f"Invalid heading_level '{heading_level}'. Must be one of: {valid}")
    try:
        doc_id = extract_doc_id(doc_id_or_url)
        service = docs_service()
        requests = [{
            "updateParagraphStyle": {
                "range": {"startIndex": start_index, "endIndex": end_index},
                "paragraphStyle": {"namedStyleType": heading_level},
                "fields": "namedStyleType",
            }
        }]
        service.documents().batchUpdate(
            documentId=doc_id, body={"requests": requests}
        ).execute()
        return _ok(f"✅ Set heading '{heading_level}' for range [{start_index}, {end_index}].")
    except HttpError as e:
        return _err(f"Google API error: {e}")
    except Exception as e:
        return _err(str(e))


def tool_batch_update(doc_id_or_url, requests_json):
    try:
        doc_id = extract_doc_id(doc_id_or_url)
        requests_list = json.loads(requests_json)
        service = docs_service()
        result = service.documents().batchUpdate(
            documentId=doc_id, body={"requests": requests_list}
        ).execute()
        return _ok(f"✅ batchUpdate applied.\n\n{json.dumps(result, indent=2)}")
    except json.JSONDecodeError as e:
        return _err(f"Invalid JSON in requests_json: {e}")
    except HttpError as e:
        return _err(f"Google API error: {e}")
    except Exception as e:
        return _err(str(e))


def tool_list_documents(query="", max_results=20):
    try:
        service = drive_service()
        q = "mimeType='application/vnd.google-apps.document'"
        if query:
            q += f" and name contains '{query}'"
        results = service.files().list(
            q=q,
            pageSize=min(max_results, 100),
            fields="files(id, name, modifiedTime, webViewLink)",
            orderBy="modifiedTime desc",
        ).execute()
        files = results.get("files", [])
        if not files:
            return _ok("No documents found.")
        lines = ["📁 **Google Docs**\n"]
        for f in files:
            lines.append(
                f"- **{f['name']}**\n"
                f"  🆔 `{f['id']}`\n"
                f"  🕒 Modified: {f.get('modifiedTime', 'unknown')}\n"
                f"  🔗 {f.get('webViewLink', '')}\n"
            )
        return _ok("\n".join(lines))
    except HttpError as e:
        return _err(f"Google API error: {e}")
    except Exception as e:
        return _err(str(e))


def tool_copy_document(doc_id_or_url, new_title):
    try:
        doc_id = extract_doc_id(doc_id_or_url)
        service = drive_service()
        result = service.files().copy(fileId=doc_id, body={"name": new_title}).execute()
        new_id = result["id"]
        url = f"https://docs.google.com/document/d/{new_id}/edit"
        return _ok(f"✅ Copied document to: **{new_title}**\n🆔 `{new_id}`\n🔗 {url}")
    except HttpError as e:
        return _err(f"Google API error: {e}")
    except Exception as e:
        return _err(str(e))


def tool_delete_document(doc_id_or_url):
    try:
        doc_id = extract_doc_id(doc_id_or_url)
        service = drive_service()
        service.files().update(fileId=doc_id, body={"trashed": True}).execute()
        return _ok(f"🗑️ Document `{doc_id}` moved to trash.")
    except HttpError as e:
        return _err(f"Google API error: {e}")
    except Exception as e:
        return _err(str(e))


def tool_rename_document(doc_id_or_url, new_title):
    try:
        doc_id = extract_doc_id(doc_id_or_url)
        service = drive_service()
        service.files().update(fileId=doc_id, body={"name": new_title}).execute()
        return _ok(f"✅ Renamed document `{doc_id}` to **{new_title}**.")
    except HttpError as e:
        return _err(f"Google API error: {e}")
    except Exception as e:
        return _err(str(e))


def tool_share_document(doc_id_or_url, email, role="writer"):
    valid_roles = {"reader", "commenter", "writer"}
    if role not in valid_roles:
        return _err(f"Invalid role '{role}'. Must be one of: {valid_roles}")
    try:
        doc_id = extract_doc_id(doc_id_or_url)
        service = drive_service()
        permission = {"type": "user", "role": role, "emailAddress": email}
        service.permissions().create(
            fileId=doc_id, body=permission, sendNotificationEmail=True
        ).execute()
        return _ok(f"✅ Shared document `{doc_id}` with {email} as **{role}**.")
    except HttpError as e:
        return _err(f"Google API error: {e}")
    except Exception as e:
        return _err(str(e))


def tool_export_document(doc_id_or_url, export_format="text/plain"):
    valid = {"text/plain", "text/html"}
    if export_format not in valid:
        return _err(f"Invalid format '{export_format}'. Choose from: {valid}")
    try:
        doc_id = extract_doc_id(doc_id_or_url)
        service = drive_service()
        content = service.files().export(fileId=doc_id, mimeType=export_format).execute()
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")
        return _ok(content)
    except HttpError as e:
        return _err(f"Google API error: {e}")
    except Exception as e:
        return _err(str(e))


TOOLS = [
    Tool(name="google_docs_auth_status", description="Check whether you are currently authenticated with Google.", inputSchema={"type": "object", "properties": {}, "required": []}),
    Tool(name="google_docs_authenticate", description="Authenticate with Google via OAuth 2.0. Opens a browser window for login.", inputSchema={"type": "object", "properties": {}, "required": []}),
    Tool(name="google_docs_read", description="Read the full text content of a Google Doc. Accepts a document URL or ID.", inputSchema={"type": "object", "properties": {"doc_id_or_url": {"type": "string", "description": "Google Doc URL or bare document ID."}}, "required": ["doc_id_or_url"]}),
    Tool(name="google_docs_get_metadata", description="Get metadata for a Google Doc (title, ID, revision).", inputSchema={"type": "object", "properties": {"doc_id_or_url": {"type": "string"}}, "required": ["doc_id_or_url"]}),
    Tool(name="google_docs_create", description="Create a new Google Doc with a given title and optional initial text.", inputSchema={"type": "object", "properties": {"title": {"type": "string"}, "body_text": {"type": "string", "default": ""}}, "required": ["title"]}),
    Tool(name="google_docs_append_text", description="Append text to the end of a Google Doc.", inputSchema={"type": "object", "properties": {"doc_id_or_url": {"type": "string"}, "text": {"type": "string"}}, "required": ["doc_id_or_url", "text"]}),
    Tool(name="google_docs_replace_text", description="Find and replace all occurrences of text in a Google Doc.", inputSchema={"type": "object", "properties": {"doc_id_or_url": {"type": "string"}, "find": {"type": "string"}, "replace_with": {"type": "string"}}, "required": ["doc_id_or_url", "find", "replace_with"]}),
    Tool(name="google_docs_insert_text", description="Insert text at a specific character index in a Google Doc.", inputSchema={"type": "object", "properties": {"doc_id_or_url": {"type": "string"}, "text": {"type": "string"}, "index": {"type": "integer"}}, "required": ["doc_id_or_url", "text", "index"]}),
    Tool(name="google_docs_delete_range", description="Delete a range of characters in a Google Doc by start/end index.", inputSchema={"type": "object", "properties": {"doc_id_or_url": {"type": "string"}, "start_index": {"type": "integer"}, "end_index": {"type": "integer"}}, "required": ["doc_id_or_url", "start_index", "end_index"]}),
    Tool(name="google_docs_apply_bold", description="Apply bold formatting to a character range in a Google Doc.", inputSchema={"type": "object", "properties": {"doc_id_or_url": {"type": "string"}, "start_index": {"type": "integer"}, "end_index": {"type": "integer"}}, "required": ["doc_id_or_url", "start_index", "end_index"]}),
    Tool(name="google_docs_set_heading", description="Set the paragraph style (heading level) for a range in a Google Doc.", inputSchema={"type": "object", "properties": {"doc_id_or_url": {"type": "string"}, "start_index": {"type": "integer"}, "end_index": {"type": "integer"}, "heading_level": {"type": "string", "enum": ["HEADING_1", "HEADING_2", "HEADING_3", "HEADING_4", "HEADING_5", "HEADING_6", "NORMAL_TEXT"]}}, "required": ["doc_id_or_url", "start_index", "end_index", "heading_level"]}),
    Tool(name="google_docs_batch_update", description="Send a raw Docs API batchUpdate request for advanced edits.", inputSchema={"type": "object", "properties": {"doc_id_or_url": {"type": "string"}, "requests_json": {"type": "string"}}, "required": ["doc_id_or_url", "requests_json"]}),
    Tool(name="google_docs_list", description="List Google Docs in Drive, most recently modified first.", inputSchema={"type": "object", "properties": {"query": {"type": "string", "default": ""}, "max_results": {"type": "integer", "default": 20}}, "required": []}),
    Tool(name="google_docs_copy", description="Create a copy of a Google Doc with a new title.", inputSchema={"type": "object", "properties": {"doc_id_or_url": {"type": "string"}, "new_title": {"type": "string"}}, "required": ["doc_id_or_url", "new_title"]}),
    Tool(name="google_docs_delete", description="Move a Google Doc to trash.", inputSchema={"type": "object", "properties": {"doc_id_or_url": {"type": "string"}}, "required": ["doc_id_or_url"]}),
    Tool(name="google_docs_rename", description="Rename a Google Doc.", inputSchema={"type": "object", "properties": {"doc_id_or_url": {"type": "string"}, "new_title": {"type": "string"}}, "required": ["doc_id_or_url", "new_title"]}),
    Tool(name="google_docs_share", description="Share a Google Doc with an email address.", inputSchema={"type": "object", "properties": {"doc_id_or_url": {"type": "string"}, "email": {"type": "string"}, "role": {"type": "string", "enum": ["reader", "commenter", "writer"], "default": "writer"}}, "required": ["doc_id_or_url", "email"]}),
    Tool(name="google_docs_export", description="Export a Google Doc as plain text or HTML.", inputSchema={"type": "object", "properties": {"doc_id_or_url": {"type": "string"}, "export_format": {"type": "string", "enum": ["text/plain", "text/html"], "default": "text/plain"}}, "required": ["doc_id_or_url"]}),
]

DISPATCH = {
    "google_docs_auth_status": lambda args: tool_auth_status(),
    "google_docs_authenticate": lambda args: tool_authenticate(),
    "google_docs_read": lambda args: tool_read_document(args["doc_id_or_url"]),
    "google_docs_get_metadata": lambda args: tool_get_document_metadata(args["doc_id_or_url"]),
    "google_docs_create": lambda args: tool_create_document(args["title"], args.get("body_text", "")),
    "google_docs_append_text": lambda args: tool_append_text(args["doc_id_or_url"], args["text"]),
    "google_docs_replace_text": lambda args: tool_replace_text(args["doc_id_or_url"], args["find"], args["replace_with"]),
    "google_docs_insert_text": lambda args: tool_insert_text_at_index(args["doc_id_or_url"], args["text"], args["index"]),
    "google_docs_delete_range": lambda args: tool_delete_text_range(args["doc_id_or_url"], args["start_index"], args["end_index"]),
    "google_docs_apply_bold": lambda args: tool_apply_bold(args["doc_id_or_url"], args["start_index"], args["end_index"]),
    "google_docs_set_heading": lambda args: tool_set_heading(args["doc_id_or_url"], args["start_index"], args["end_index"], args["heading_level"]),
    "google_docs_batch_update": lambda args: tool_batch_update(args["doc_id_or_url"], args["requests_json"]),
    "google_docs_list": lambda args: tool_list_documents(args.get("query", ""), args.get("max_results", 20)),
    "google_docs_copy": lambda args: tool_copy_document(args["doc_id_or_url"], args["new_title"]),
    "google_docs_delete": lambda args: tool_delete_document(args["doc_id_or_url"]),
    "google_docs_rename": lambda args: tool_rename_document(args["doc_id_or_url"], args["new_title"]),
    "google_docs_share": lambda args: tool_share_document(args["doc_id_or_url"], args["email"], args.get("role", "writer")),
    "google_docs_export": lambda args: tool_export_document(args["doc_id_or_url"], args.get("export_format", "text/plain")),
}

server = Server("google-docs-mcp")

@server.list_tools()
async def list_tools():
    return TOOLS

@server.call_tool()
async def call_tool(name, arguments):
    handler = DISPATCH.get(name)
    if handler is None:
        result = _err(f"Unknown tool: {name}")
    else:
        try:
            result = handler(arguments)
        except Exception as e:
            result = _err(f"Unexpected error in '{name}': {e}")
    return result.content

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
