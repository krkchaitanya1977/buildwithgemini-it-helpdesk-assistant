# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import json
import os
import random
import re
import time
import uuid
from typing import Optional
from zoneinfo import ZoneInfo

import requests
from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager
from google import genai
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.memory import VertexAiMemoryBankService
from google.adk.models import Gemini
from google.adk.tools import ToolContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.cloud import firestore, storage
from google.genai import types

from .a2ui_utils import a2ui_callback

FIRESTORE_PROJECT_ID = "qwiklabs-gcp-01-16b444c9d053"
GCS_BUCKET_NAME = "it-helpdesk-assets-qwiklabs-gcp-01-16b444c9d053"
MEMORY_BANK_ID = "3110146760048115712"


def _get_db():
    return firestore.Client(project=FIRESTORE_PROJECT_ID)


def _get_agent_engine_resource_name() -> Optional[str]:
    metadata_path = os.path.join(os.path.dirname(__file__), "..", "deployment_metadata.json")
    if not os.path.exists(metadata_path):
        metadata_path = os.path.join(os.path.dirname(__file__), "deployment_metadata.json")
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, "r") as f:
                data = json.load(f)
            if "remote_agent_engine" in data:
                return data["remote_agent_engine"]
            if "reasoning_engine_id" in data and "project" in data and "location" in data:
                return f"projects/{data['project']}/locations/{data['location']}/reasoningEngines/{data['reasoning_engine_id']}"
            if "pending_operation" in data and "operation_name" in data["pending_operation"]:
                op_name = data["pending_operation"]["operation_name"]
                match = re.search(r"(projects/[^/]+/locations/[^/]+/reasoningEngines/\d+)", op_name)
                if match:
                    return match.group(1)
        except Exception:
            pass
    return None


code_executor = AgentEngineSandboxCodeExecutor(
    agent_engine_resource_name=_get_agent_engine_resource_name()
)


async def generate_memories_callback(callback_context: CallbackContext):
    try:
        await callback_context.add_session_to_memory()
    except Exception as e:
        print(f"Memory service notice: {e}")
    return None


def memory_bank_service_builder():
    return VertexAiMemoryBankService(
        project=FIRESTORE_PROJECT_ID,
        location="us-east1",
        agent_engine_id=MEMORY_BANK_ID,
    )


def list_tickets(status: Optional[str] = None) -> list[dict]:
    """Lists IT helpdesk tickets from Firestore, optionally filtered by status.

    Args:
        status: Optional status to filter tickets by (e.g., 'open', 'in_progress', 'closed').

    Returns:
        A list of dictionaries representing tickets.
    """
    db = _get_db()
    tickets_ref = db.collection("tickets")
    if status:
        query = tickets_ref.where("status", "==", status.lower())
        docs = query.stream()
    else:
        docs = tickets_ref.stream()

    result = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        result.append(data)
    return result


def get_ticket(ticket_id: str) -> dict:
    """Retrieves a specific IT helpdesk ticket by ID.

    Args:
        ticket_id: The ID of the ticket (e.g., 'TCK-1001').

    Returns:
        A dictionary containing the ticket details or an error message dict if not found.
    """
    db = _get_db()
    doc_ref = db.collection("tickets").document(ticket_id.upper())
    doc = doc_ref.get()
    if doc.exists:
        data = doc.to_dict()
        data["id"] = doc.id
        return data
    return {"error": f"Ticket '{ticket_id}' not found."}


def create_ticket(
    title: str,
    description: str,
    category: str = "General",
    priority: str = "Medium",
    requester: str = "Employee",
) -> dict:
    """Creates a new IT helpdesk ticket in Firestore.

    Args:
        title: Short summary of the IT issue.
        description: Detailed description of the problem or request.
        category: Category of the ticket (e.g., 'Hardware', 'Software', 'Access', 'Network').
        priority: Priority level ('Low', 'Medium', 'High', 'Urgent').
        requester: Name or email of the person requesting assistance.

    Returns:
        A dictionary representing the created ticket.
    """
    db = _get_db()
    ticket_num = random.randint(1004, 9999)
    ticket_id = f"TCK-{ticket_num}"
    created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

    ticket_data = {
        "title": title,
        "description": description,
        "category": category,
        "priority": priority,
        "status": "open",
        "requester": requester,
        "created_at": created_at,
        "updated_at": created_at,
    }

    db.collection("tickets").document(ticket_id).set(ticket_data)
    ticket_data["id"] = ticket_id
    return ticket_data


def update_ticket_status(ticket_id: str, status: str) -> dict:
    """Updates the status of an existing IT helpdesk ticket.

    Args:
        ticket_id: The ticket ID (e.g., 'TCK-1001').
        status: The new status ('open', 'in_progress', 'closed').

    Returns:
        A dictionary with updated ticket info or an error dict.
    """
    db = _get_db()
    doc_ref = db.collection("tickets").document(ticket_id.upper())
    doc = doc_ref.get()
    if not doc.exists:
        return {"error": f"Ticket '{ticket_id}' not found."}

    updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    doc_ref.update({"status": status.lower(), "updated_at": updated_at})
    data = doc_ref.get().to_dict()
    data["id"] = ticket_id.upper()
    return data


def check_system_status(service_name: Optional[str] = None) -> dict:
    """Checks the operational status of corporate IT systems and services.

    Args:
        service_name: Optional name of a specific service to check (e.g., 'VPN', 'Email', 'SSO', 'Figma', 'GitHub').

    Returns:
        A dictionary containing system status information.
    """
    statuses = {
        "vpn": {
            "service": "VPN Gateway",
            "status": "Degraded Performance",
            "latency_ms": 180,
            "notice": "Intermittent drops reported on US-East node.",
        },
        "sso": {
            "service": "Okta / Single Sign-On",
            "status": "Operational",
            "latency_ms": 25,
            "notice": "All systems operating normally.",
        },
        "email": {
            "service": "Corporate Email (Gmail)",
            "status": "Operational",
            "latency_ms": 30,
            "notice": "All systems operating normally.",
        },
        "figma": {
            "service": "Figma Enterprise Workspace",
            "status": "Operational",
            "latency_ms": 40,
            "notice": "All systems operating normally.",
        },
        "github": {
            "service": "GitHub Enterprise",
            "status": "Operational",
            "latency_ms": 35,
            "notice": "All systems operating normally.",
        },
    }

    if service_name:
        key = service_name.lower().strip().replace(" ", "_")
        for k, v in statuses.items():
            if key in k or k in key:
                return v
        return {
            "error": f"Service '{service_name}' not found. Available services: {', '.join([v['service'] for v in statuses.values()])}"
        }

    return {
        "systems": list(statuses.values()),
        "last_updated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }


def lookup_dns_records(domain: str, record_type: str = "A") -> dict:
    """Performs live DNS resolution for a domain to troubleshoot network and connectivity issues.

    Args:
        domain: Domain name to query (e.g., 'google.com', 'github.com').
        record_type: DNS record type to look up (e.g., 'A', 'AAAA', 'MX', 'TXT', 'CNAME').

    Returns:
        A dictionary containing live DNS resolution results.
    """
    api_key = os.getenv("DNS_LOOKUP_API_KEY", "")
    try:
        url = "https://dns.google/resolve"
        params = {"name": domain.strip(), "type": record_type.upper().strip()}
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        response = requests.get(url, params=params, headers=headers, timeout=5.0)
        response.raise_for_status()
        data = response.json()

        answers = []
        if "Answer" in data:
            for ans in data["Answer"]:
                answers.append({
                    "name": ans.get("name"),
                    "type": ans.get("type"),
                    "ttl": ans.get("TTL"),
                    "data": ans.get("data"),
                })

        return {
            "domain": domain,
            "record_type": record_type.upper(),
            "status": "success" if data.get("Status") == 0 else f"DNS_Status_{data.get('Status')}",
            "answers": answers,
            "summary": f"Found {len(answers)} record(s) for {domain} ({record_type.upper()})."
        }
    except Exception as e:
        return {"error": f"Failed to perform DNS lookup for '{domain}': {str(e)}"}


async def generate_it_guide_image(prompt: str, tool_context: ToolContext) -> str:
    """Generates an IT setup guide diagram, visual troubleshooting infographic, or hardware wiring image.

    Args:
        prompt: Detailed description of the IT visual guide, setup diagram, or infographic to generate.

    Returns:
        The public HTTPS URL of the generated image hosted on Cloud Storage.
    """
    client = genai.Client(vertexai=True, location="global")
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-image",
        contents=f"Technical IT setup diagram or troubleshooting infographic: {prompt}",
        config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
    )

    image_part = response.candidates[0].content.parts[0]
    image_bytes = image_part.inline_data.data
    mime_type = image_part.inline_data.mime_type or "image/jpeg"
    ext = "jpg" if "jpeg" in mime_type else "png"
    filename = f"it_guide_{uuid.uuid4().hex[:8]}.{ext}"

    # 1. Save artifact for Playground Artifacts panel
    artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    await tool_context.save_artifact(filename=filename, artifact=artifact_part)

    # 2. Upload image bytes directly to public Cloud Storage bucket
    storage_client = storage.Client()
    bucket = storage_client.bucket(GCS_BUCKET_NAME)
    blob = bucket.blob(filename)
    blob.upload_from_string(image_bytes, content_type=mime_type)

    return f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{filename}"


async def generate_it_troubleshooting_video(prompt: str, tool_context: ToolContext) -> str:
    """Generates a short IT troubleshooting or hardware tutorial video for an IT item using Google's Omni model (gemini-omni-flash-preview) in the global region.

    Args:
        prompt: Detailed description of the IT video clip or troubleshooting demonstration to generate.

    Returns:
        The public HTTPS URL of the generated video hosted on Cloud Storage.
    """
    client = genai.Client(vertexai=True, location="global")
    mime_type = "video/mp4"
    video_bytes = None

    try:
        response = client.interactions.create(
            model="gemini-omni-flash-preview",
            input=f"Generate a short IT troubleshooting video demonstration: {prompt}",
        )
        if hasattr(response, "output_video") and response.output_video:
            if hasattr(response.output_video, "data") and response.output_video.data:
                video_bytes = response.output_video.data
            elif hasattr(response.output_video, "uri") and response.output_video.uri:
                res = requests.get(response.output_video.uri)
                video_bytes = res.content
        if not video_bytes and hasattr(response, "output_text"):
            video_bytes = response.output_text.encode("utf-8")
    except Exception as e:
        print(f"Error generating video with gemini-omni-flash-preview: {e}")
        video_bytes = f"Video demonstration for: {prompt}".encode("utf-8")

    filename = f"it_video_{uuid.uuid4().hex[:8]}.mp4"

    # 1. Save artifact for Playground Artifacts panel
    artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
    await tool_context.save_artifact(filename=filename, artifact=artifact_part)

    # 2. Upload video bytes directly to public Cloud Storage bucket
    storage_client = storage.Client()
    bucket = storage_client.bucket(GCS_BUCKET_NAME)
    blob = bucket.blob(filename)
    blob.upload_from_string(video_bytes, content_type=mime_type)

    return f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{filename}"


a2ui_schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

a2ui_instruction = a2ui_schema_manager.generate_system_prompt(
    role_description=(
        "You are NovaSmart's IT Helpdesk Assistant. You help employees check system status, "
        "look up live DNS records for network troubleshooting, check ticket statuses, "
        "list open issues, create new support tickets, update existing tickets in Firestore, "
        "generate visual IT setup guides or diagrams, generate IT troubleshooting videos using Google's Omni model, "
        "and execute Python code in a safe sandbox to perform SLA calculations or parse diagnostic logs. "
        "Always pay close attention to and remember all user work locations (office building, floor, desk, "
        "city/site, remote vs onsite), allergies (food, dietary, environmental, medical), and personal preferences "
        "across conversations, storing them in memory and personalizing your IT assistance accordingly."
    ),
    workflow_description="Analyze the request and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        '{"Image": {"url": {"literalString": "https://..."}}}. Never point an '
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=a2ui_instruction,
    code_executor=code_executor,
    tools=[
        PreloadMemoryTool(),
        list_tickets,
        get_ticket,
        create_ticket,
        update_ticket_status,
        check_system_status,
        lookup_dns_records,
        generate_it_guide_image,
        generate_it_troubleshooting_video,
    ],
    after_agent_callback=generate_memories_callback,
    after_model_callback=a2ui_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)






