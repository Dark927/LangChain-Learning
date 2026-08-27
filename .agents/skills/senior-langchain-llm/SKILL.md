---
name: senior-langchain-llm
description: >-
  Expert patterns and architectural standards for LangChain, LangGraph, and modern LLM application development.
  Use when building AI agents, designing tool-calling workflows, structured outputs, multi-provider LLM integrations,
  and resilient agentic orchestration.
---

# Senior LangChain & LLM Professional Skill

Comprehensive engineering guide for architecting production-ready LLM agents, tool-calling pipelines, and multi-model systems using LangChain and LangGraph.

---

## 1. Unified Model Initialization & Multi-Provider Strategy

Always leverage modern LangChain unified model initializers with provider decoupling:

- **Unified Model Factory (`init_chat_model`)**:
  ```python
  from langchain.chat_models import init_chat_model
  from langchain_core.language_models.chat_models import BaseChatModel

  def build_chat_model(provider: str, model_name: str, **kwargs) -> BaseChatModel:
      # e.g., "groq:openai/gpt-oss-120b", "google_genai:gemini-3.5-flash-lite"
      model_identifier = f"{provider}:{model_name}" if ":" not in model_name else model_name
      return init_chat_model(model_identifier, **kwargs)
  ```
- **Fallback Models**: Use `.with_fallbacks()` to gracefully recover from provider rate limits (`429`) or outages:
  ```python
  primary_model = init_chat_model("groq:openai/gpt-oss-120b")
  backup_model = init_chat_model("google_genai:gemini-3.5-flash-lite")
  resilient_model = primary_model.with_fallbacks([backup_model])
  ```

---

## 2. Professional Tool Engineering

Tools are the core interface between the LLM and external systems. Every tool must be bulletproof:

- **Precise Docstrings**: The LLM relies on docstrings to understand *when* and *how* to invoke tools. Include concise purpose, argument descriptions, and output format.
- **Strict Input Validation**: Use explicit Python type hints (or Pydantic args schemas for complex inputs):
  ```python
  from langchain_core.tools import tool
  from pydantic import BaseModel, Field

  class VectorSearchInput(BaseModel):
      query: str = Field(description="Search query to match against knowledge base.")
      top_k: int = Field(default=5, ge=1, le=20, description="Number of results to retrieve.")

  @tool(args_schema=VectorSearchInput)
  def search_knowledge_base(query: str, top_k: int = 5) -> str:
      """Search indexed documentation for relevant snippets based on semantic similarity."""
      try:
          # Execution logic
          return "..."
      except Exception as exc:
          # NEVER raise unhandled exceptions to the agent loop; return clear error strings
          return f"Error executing search: {str(exc)}"
  ```
- **Error Trapping**: Always return error messages as strings from tools so the agent can self-correct in the next step.

---

## 3. Structured Outputs & Pydantic Validation

Avoid parsing raw text when structured data is required:

- **`with_structured_output`**:
  ```python
  from pydantic import BaseModel, Field

  class AgentDecision(BaseModel):
      action: str = Field(description="Action to take: 'continue', 'clarify', or 'finish'")
      reasoning: str = Field(description="Brief rationale for the chosen action")
      data: dict[str, str] = Field(default_factory=dict, description="Payload data")

  structured_llm = model.with_structured_output(AgentDecision)
  decision: AgentDecision = structured_llm.invoke("Assess task completion status.")
  ```

---

## 4. Agent Architecture & State Management

- **ReAct Agents**: Use `create_agent` or LangGraph `create_react_agent` with explicitly typed tool lists.
- **Message Normalization**: Normalize message outputs (supporting `AIMessage`, `HumanMessage`, `ToolMessage`, and multi-part content blocks) with dedicated parser functions like `extract_text()`.
- **State Graphs**: For complex, multi-agent workflows, prefer **LangGraph** StateGraph over monolithic chains:
  - Define an explicit `TypedDict` state schema.
  - Nodes are pure functions `(state: State) -> dict[str, Any]`.
  - Edges handle conditional routing cleanly.

---

## 5. Token & Rate Limit Optimization

1. **Context Trimming**: Prune chat history using `trim_messages` or summarize earlier conversation turns to avoid exceeding context limits.
2. **Streaming & Observability**: Support streaming callback handlers (`on_llm_new_token`) and structured logging of raw prompt/completion tokens.
3. **Queueing & Delays**: When running batch evaluations on free-tier providers (Groq/Google), introduce exponential backoff or throttling to respect rate limits.
