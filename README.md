# 🚀 Winjay OS: Agent Reliability Infrastructure
> *"LLMs propose. Evidence decides."*

**Hackathon Track:** Fortified Enterprise Fleet (All Things Agentic Hackathon)

## 📌 The Vision
Most AI agents today operate on a primitive `User Request -> LLM -> Output` loop. They act as chatbots that blindly agree with the user. In an enterprise environment, an agent that hallucinates false confidence is dangerous. 

**Winjay** transforms "Agent Intelligence" into **Agent Reliability Infrastructure**. We replace the chatbot model with a strict **Epistemic Architecture**:
- **Falsification Contracts:** Instead of just guessing, the Researcher Agent must define exactly *what would disprove* its hypothesis.
- **Independent Evidence Scoring:** The Falsifier Agent attacks the hypothesis and produces structured, scored evidence (-3 to +3).
- **Deterministic Belief Engine:** We stripped the LLM of its authority to make final decisions. A deterministic policy engine calculates the final epistemic confidence based on the evidence ledger. 
- **Immutable Audit Trail:** Uses Google Firestore as a *Hypothesis Ledger* to track belief history securely without overwriting past states.
- **Failure-Awareness:** If an API fails, Winjay escalates. It *never* fabricates evidence.

---

## 🏗️ Architecture Diagram

```mermaid
flowchart TD
    %% Styling
    classDef gcp fill:#4285F4,stroke:#fff,stroke-width:2px,color:#fff;
    classDef gemini fill:#8E24AA,stroke:#fff,stroke-width:2px,color:#fff;
    classDef db fill:#F4B400,stroke:#fff,stroke-width:2px,color:#fff;
    classDef alert fill:#DB4437,stroke:#fff,stroke-width:2px,color:#fff;
    classDef engine fill:#0F9D58,stroke:#fff,stroke-width:2px,color:#fff;

    %% Nodes
    Trigger["⚙️ Environment Delta (e.g., Code Commit)"]
    API["🌐 Event Gateway & Idempotency<br/>(FastAPI)"]:::gcp

    subgraph Agentic Reasoning
        R["🕵️ Researcher Agent<br/>(Outputs Falsification Contract)"]:::gemini
        F["🛡️ Falsifier Agent<br/>(Outputs Scored Evidence)"]:::gemini
    end

    subgraph Core Infrastructure
        DB[("🗄️ Immutable Hypothesis Ledger<br/>(Google Firestore)")]:::db
        BE["⚙️ Deterministic Belief Engine<br/>(Policy Engine)"]:::engine
    end

    subgraph Human-on-the-loop
        Eval{"Confidence Score<br/>(0.0 - 1.0)"}
        ActionAuto["✅ Auto-Action<br/>(High Confidence)"]
        ActionEscalate["⚠️ Escalation Required<br/>(Uncertain / Ambiguous)"]:::alert
        Human(("👨‍💻 Human Review"))
    end

    %% Flow
    Trigger -->|Webhook Event| API
    API -->|1. Idempotency Check| DB
    API -->|2. Generate Hypothesis| R
    
    R -->|Log Hypothesis & Contract| DB
    R -->|Passes Contract| F
    
    F -->|3. Attacks Hypothesis| DB
    F -->|Passes Structured Evidence| BE
    
    BE -->|4. Calculates Deterministic Score| DB
    BE --> Eval
    
    Eval -->|> 0.8 or < 0.2| ActionAuto
    Eval -->|Between 0.2 - 0.8| ActionEscalate
    ActionEscalate --> Human
```

---

## 🛠️ Tech Stack
- **AI Model:** Gemini 3.5 Flash (via Google AI Studio)
- **Framework:** FastAPI (Python)
- **Database (Memory Bank):** Google Cloud Firestore (Immutable Audit Trail)
- **Governance:** Deterministic Belief Engine (Custom Python Policy)

---

## 🚀 Spin-up Instructions

### 1. Prerequisites
- Python 3.10+

### 2. Installation
Clone the repository and install dependencies:
```bash
git clone https://github.com/wijaywi/WinjayAgent.git
cd WinjayAgent/backend
pip install -r requirements.txt
```

### 3. Environment Variables
Set your Gemini API Key in your terminal:
**Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
```

### 4. Run the Backend
Start the Event-Driven infrastructure:
```bash
uvicorn main:app --host 127.0.0.1 --port 8080
```

### 5. Trigger an Environment Delta
In a separate terminal, simulate a webhook trigger (e.g., a code commit removing a JWT check):
```powershell
$body = @{
    repository = "org/core-auth"
    commit_id = "a1b2c3d4"
    changes = "Removed JWT expiry check from middleware."
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8080/webhook/environment-delta" -Method Post -Body $body -ContentType "application/json"
```

Observe the system reject LLM hallucination and deterministically calculate the epistemic score!
