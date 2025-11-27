"""
Configuration module for InsightChat application.
Centralizes default values and configuration constants.
"""

# Default system prompts
DEFAULT_SYSTEM_PROMPT = "You are a helpful assistant. Respond in markdown format."

# CSV Analysis specific instructions
CSV_ANALYSIS_INSTRUCTIONS = """

ADDITIONAL INSTRUCTIONS FOR DOCUMENT ANALYSIS:
- When analyzing CSV/tabular data, be systematic and precise
- For row counting: Count each line including header (total rows in file)
- For data record counting: Count data rows only, excluding header
- When given complete documents, use them as the authoritative source
- Double-check your counting by examining the structure carefully
"""

# Model configuration
DEFAULT_MODEL = "llama3.2:latest"
DEFAULT_TEMPERATURE = 0.7

# RAG configuration
DEFAULT_RAG_CHUNKS = 5

# Chat configuration
MAX_MESSAGE_HISTORY = 6  # Maximum number of messages to keep in session
