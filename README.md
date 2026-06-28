# 🤖 AI Copilot for Caseworkers — POC

A **Multi-Agent AI System** that helps Child Maintenance Service caseworkers understand financial calculations, assess enforcement risk, and get actionable case recommendations.

## ✨ What It Does

The AI Copilot **explains** calculations performed by the Siebel CRM system — it **never recalculates**. It acts as an auditor and translator, providing plain-English breakdowns that caseworkers can trust.

### 🤖 Three Specialized Agents

| Agent | Purpose |
|-------|---------|
| 📋 **Case Summarizer** | Generates a concise case overview with key metrics |
| 🔢 **Calculation Explainer** | Explains OGM, arrears, and collection dates in plain English |
| ⚡ **Action Advisor** | Classifies enforcement risk and suggests next steps |

All three agents run **in parallel** and return results within seconds.

## 🚀 Quick Start

### 1. Set Up Virtual Environment

It is recommended to run this project inside a Python virtual environment.

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Application

```bash
streamlit run app.py
```

### 3. Configure

1. Open the sidebar (⚙️)
2. Select your **LLM Provider** (OpenAI / Gemini / Azure)
3. Enter your **API Key**
4. Choose your **Model**

### 4. Analyze a Case

1. Click **"Load Demo Data"** (or paste/upload your own JSON)
2. Click **"🧠 Analyze Case with AI Agents"**
3. Review the results in the **Summary**, **Calculations**, and **Actions** tabs

## 📁 Project Structure

```
AI_Copilot_CW/
├── app.py                    ← Streamlit main application
├── requirements.txt          ← Python dependencies
├── .streamlit/config.toml    ← Dark theme configuration
├── agents/
│   ├── orchestrator.py       ← Multi-agent parallel orchestrator
│   ├── calculation_explainer.py
│   ├── action_advisor.py
│   └── case_summarizer.py
├── llm/
│   └── gateway.py            ← Unified LLM API gateway
├── prompts/
│   └── system_prompts.py     ← Agent prompt templates
├── data/
│   └── demo_case.json        ← Demo dataset
└── docs/
    ├── HLD.md                ← High-Level Design
    └── LLD.md                ← Low-Level Design
```

## 🔑 Supported LLM Providers

| Provider | Model Examples | Endpoint |
|----------|---------------|----------|
| **OpenAI** | gpt-4o, gpt-4.1 | api.openai.com |
| **Google Gemini** | gemini-2.0-flash | generativelanguage.googleapis.com |
| **Azure OpenAI** | gpt-4o (deployed) | Your Azure endpoint |

All providers use the **OpenAI-compatible API format**, making switching seamless.

## 📚 Documentation

- [High-Level Design (HLD)](docs/HLD.md)
- [Low-Level Design (LLD)](docs/LLD.md)

## 🔒 Security

- API keys are stored **only in session state** (never persisted)
- Keys are sent **only to the LLM provider** (no intermediate storage)
- No PII is logged
- For production: use a secrets manager (Azure Key Vault / AWS Secrets Manager)
