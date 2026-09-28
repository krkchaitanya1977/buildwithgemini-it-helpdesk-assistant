# NovaSmart IT Helpdesk Assistant

![NovaSmart IT Helpdesk Assistant Demo](demo.gif)

NovaSmart IT Helpdesk Assistant is an enterprise AI agent built with Google's **Agent Development Kit (ADK)** and deployed to **Vertex AI Agent Runtime**. It assists employees with IT status checks, ticket management, network diagnostics, interactive visual setup guides, and troubleshooting videos.

---

## 🚀 Wired Google Cloud Services & Core Features

Based on the implementation in [`app/agent.py`](app/agent.py) and [`agents-cli-manifest.yaml`](agents-cli-manifest.yaml), the agent integrates the following Google Cloud services and tools:

* **Vertex AI Memory Bank (`VertexAiMemoryBankService`)**: Managed long-term cross-session memory service that remembers employee work locations (building, floor, desk), dietary/environmental allergies, and personal IT preferences.
* **Google Cloud Firestore**: Direct Firestore database integration for managing corporate IT tickets (`list_tickets`, `get_ticket`, `create_ticket`, `update_ticket_status`).
* **Google Cloud Storage (GCS)**: Direct in-memory byte streaming and public hosting for generated IT setup diagrams, cabling visuals, and troubleshooting videos.
* **Vertex AI Image Generation (`gemini-3.1-flash-lite-image`)**: On-demand technical diagram and infographic generation (`generate_it_guide_image`).
* **Google Omni Model Video Generation (`gemini-omni-flash-preview`)**: Generates short IT hardware troubleshooting and tutorial video clips in the `global` region (`generate_it_troubleshooting_video`).
* **A2UI (Agent-to-User Interface)**: Native A2UI v0.8 catalog integration emitting structured cards, columns, text rows, and image components.
* **Agent Engine Sandbox Code Executor (`AgentEngineSandboxCodeExecutor`)**: Safe Python code execution sandbox for calculating SLA resolution deadlines and parsing diagnostic logs.
* **Live DNS Resolution (`lookup_dns_records`)**: Resolves live A, AAAA, MX, CNAME, and TXT records via Google Public DNS API for network troubleshooting.
* **System Operational Status (`check_system_status`)**: Real-time status reporting for corporate infrastructure (Okta SSO, Corporate VPN, Gmail, Figma, GitHub).

---

## 📁 Project Structure

```
it-helpdesk-assistant/
├── app/
│   ├── agent.py               # Root agent, tools, A2UI callbacks, and Memory Bank service
│   ├── a2ui_utils.py          # A2UI after_model_callback transformer
│   └── fast_api_app.py        # Local FastAPI agent backend
├── frontend/                  # Rebranded FastAPI A2A proxy & dialogue UI
│   ├── main.py                # FastAPI proxy server connecting browser to Agent Engine
│   ├── Dockerfile             # Container configuration for Cloud Run deployment
│   ├── requirements.txt       # Dependencies pinned for A2A proxy (a2a-sdk>=0.3.0,<0.4.0)
│   └── static/
│       └── index.html         # Dialogue UI with prompt chips, status badges, and A2UI renderer
├── scripts/
│   ├── seed_firestore.py      # Seeds initial IT tickets in Firestore
│   ├── record_demo.py         # Playwright script for automated demo recording
│   └── convert_webm_imageio.py# Converts recorded demo video to optimized demo.gif
├── tests/                     # Unit and integration tests
├── demo.gif                   # Looping demo recording
└── agents-cli-manifest.yaml   # Agent Engine deployment manifest
```

---

## 🛠️ Local Development & Running Instructions

### 1. Prerequisites
Ensure you have the required CLI tools installed:
- **uv**: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **agents-cli**: `uv tool install google-agents-cli`
- **Google Cloud SDK**: Signed in with active GCP project credentials (`gcloud auth application-default login`)

### 2. Running the Agent Playground
To test the agent locally with hot-reloading:

```bash
agents-cli playground
```

### 3. Running the Frontend Proxy Locally
To run the custom chat frontend locally against your deployed agent:

```bash
cd frontend
uv run uvicorn main:app --host 0.0.0.0 --port 8080
```

### 4. Running Unit Tests
To execute the unit test suite:

```bash
uv run pytest tests/unit
```

### 5. Deploying to Agent Platform
To deploy or update the agent on Vertex AI Agent Runtime:

```bash
agents-cli deploy --no-confirm-project
```
