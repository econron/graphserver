uv pip install fastapi uvicorn langgraph langchain-core
uv run uvicorn app:app --reload

curl -N -H "Content-Type: application/json" -X POST \
  -d '{"input":"tool: LangGraph streaming"}' \
  http://127.0.0.1:8000/chat
