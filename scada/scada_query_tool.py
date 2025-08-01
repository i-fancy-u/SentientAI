import os
import requests
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Adjust path for LangGraph compatibility
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(base_dir, "data", "scada_data.db")

month_map = {
    "january": "01", "february": "02", "march": "03", "april": "04",
    "may": "05", "june": "06", "july": "07", "august": "08",
    "september": "09", "october": "10", "november": "11", "december": "12"
}

def extract_month(q: str) -> str | None:
    for month_name, month_num in month_map.items():
        if month_name in q:
            return month_num
    return None

def query_scada(nl_question: str) -> str:
    engine = create_engine(f"sqlite:///{DB_PATH}")
    q = nl_question.lower()
    month_filter = extract_month(q)
    query = None

    if any(word in q for word in ["pressure", "psi", "capper", "compressor", "bar", "leak"]):
        query = "SELECT * FROM scada_logs WHERE metric_name='pressure_psi'"
    elif any(word in q for word in ["temperature", "temp", "celsius", "overheat", "boiler", "furnace", "chiller"]):
        query = "SELECT * FROM scada_logs WHERE metric_name='temperature_celsius'"
    elif any(word in q for word in ["vibration", "shake", "hz", "unbalance", "resonance", "oscillation"]):
        query = "SELECT * FROM scada_logs WHERE metric_name='vibration_hz'"
    elif any(word in q for word in ["load", "power", "grid", "electric", "kw", "average load", "main supply"]):
        query = "SELECT AVG(value) as avg_kw FROM scada_logs WHERE metric_name='load_kw'"
    elif any(word in q for word in ["rpm", "rotation", "overspeed", "underspeed", "shaft speed"]):
        query = "SELECT * FROM scada_logs WHERE metric_name='rpm'"
    elif any(word in q for word in ["error", "anomaly", "fault", "issue", "warning", "alarm", "problem", "503", "504", "505"]):
        query = "SELECT * FROM scada_logs WHERE error_code IS NOT NULL"

    if query:
        if month_filter:
            query += f" AND strftime('%m', timestamp) = '{month_filter}'"
        if "AVG" not in query:
            query += " ORDER BY timestamp DESC LIMIT 10;"
        else:
            query += ";"
    else:
        return fallback_response(nl_question)

    try:
        df = pd.read_sql(query, engine)
    except Exception as e:
        return f"❌ SQL Query Error: {str(e)}"

    if df.empty:
        return "⚠️ No data matched your query."

    result_text = df.to_string(index=False)
    return explain_data_with_llm(result_text)

def fallback_response(nl_question: str) -> str:
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama3-8b-8192",
            "messages": [
                {"role": "system", "content": "You are a SCADA diagnostics assistant."},
                {"role": "user", "content": nl_question}
            ],
            "temperature": 0.4
        }
    )
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"❌ Groq fallback error: {response.text}"

def explain_data_with_llm(data_str: str) -> str:
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama3-8b-8192",
            "messages": [
                {"role": "system", "content": "You are a helpful diagnostics assistant. Analyze the SCADA data and explain it simply."},
                {"role": "user", "content": f"Explain this data:\n\n{data_str}"}
            ],
            "temperature": 0.3
        }
    )
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"❌ Groq API error: {response.text}"

# ✅ For manual testing only
if __name__ == "__main__":
    while True:
        question = input("🔍 Ask a SCADA question (or 'exit'): ").strip()
        if question.lower() == "exit":
            break
        print(query_scada(question))
