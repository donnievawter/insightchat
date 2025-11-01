"""
Document processing utilities for handling large documents that exceed context limits.
"""

import os
from typing import List, Dict, Optional
from .utils import prompt_model

def chunk_text(text: str, chunk_size: int = 50000, overlap: int = 5000) -> List[str]:
    """
    Split text into overlapping chunks.
    
    Args:
        text: The text to chunk
        chunk_size: Size of each chunk in characters
        overlap: Number of characters to overlap between chunks
        
    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = min(start + chunk_size, len(text))
        
        # Try to end at a sentence boundary if possible
        if end < len(text):
            # Look for sentence endings within the last 1000 characters
            search_start = max(end - 1000, start)
            last_sentence = max(
                text.rfind('.', search_start, end),
                text.rfind('!', search_start, end),
                text.rfind('?', search_start, end),
                text.rfind('\n\n', search_start, end)
            )
            if last_sentence > search_start:
                end = last_sentence + 1
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = end - overlap if end < len(text) else end
    
    return chunks

def summarize_large_document(document_path: str, document_content: str, 
                           question: str, model: str = "qwen2.5vl:latest") -> Dict:
    """
    Process a large document by chunking and summarizing relevant parts.
    
    Args:
        document_path: Path/name of the document
        document_content: Full content of the document  
        question: User's question about the document
        model: Model to use for processing
        
    Returns:
        Dict with summary, relevant_chunks, and metadata
    """
    
    # First, create an overview of the document
    doc_preview = document_content[:10000]  # First 10K chars for overview
    
    overview_prompt = f"""Please provide a brief overview of this document and identify its main sections/topics:

Document: {document_path}
Preview: {doc_preview}

Question from user: {question}

Provide:
1. Document type and purpose
2. Main sections/topics covered  
3. Which sections are most relevant to the user's question
4. Recommended approach for analyzing this document given the question

Keep response under 200 words."""

    try:
        overview_response, _ = prompt_model(
            model=model,
            prompt=overview_prompt,
            history=[]
        )
        
        # Now chunk the document and process relevant sections
        chunks = chunk_text(document_content, chunk_size=40000, overlap=3000)
        
        relevant_summaries = []
        chunk_relevance_scores = []
        
        # Analyze each chunk for relevance
        for i, chunk in enumerate(chunks):
            if len(chunks) > 10 and i > 0:  # Don't process too many chunks
                break
                
            relevance_prompt = f"""Rate the relevance of this document section to the user's question (1-10 scale) and provide a brief summary if relevant (score 6+):

Question: {question}

Document section {i+1}/{len(chunks)}:
{chunk}

Response format:
Relevance Score: X/10
Summary: (only if score 6+, max 100 words)"""

            try:
                relevance_response, _ = prompt_model(
                    model=model,
                    prompt=relevance_prompt,
                    history=[]
                )
                
                # Extract score (simple parsing)
                score = 0
                if "Relevance Score:" in relevance_response:
                    score_line = relevance_response.split("Relevance Score:")[1].split("\n")[0]
                    try:
                        score = int(score_line.split("/")[0].strip())
                    except:
                        score = 0
                
                chunk_relevance_scores.append((i, score))
                
                if score >= 6:
                    relevant_summaries.append({
                        "chunk_index": i,
                        "relevance_score": score,
                        "summary": relevance_response,
                        "content_preview": chunk[:500] + "..." if len(chunk) > 500 else chunk
                    })
                    
            except Exception as e:
                print(f"Error processing chunk {i}: {e}")
                continue
        
        # Create final summary based on most relevant chunks
        if relevant_summaries:
            # Create the sections analysis string outside f-string to avoid backslash issue
            sections_analysis = "\n".join([f"Section {s['chunk_index']+1} (Relevance: {s['relevance_score']}/10):\n{s['summary']}" for s in relevant_summaries[:5]])
            
            final_prompt = f"""Based on the document analysis below, provide a comprehensive answer to the user's question:

Document: {document_path}
Question: {question}

Document Overview:
{overview_response}

Relevant Sections Analysis:
{sections_analysis}

Please provide a thorough answer based on this analysis. If you need to see specific sections in detail, mention that."""

            final_response, _ = prompt_model(
                model=model,
                prompt=final_prompt,
                history=[]
            )
        else:
            final_response = f"I analyzed the document '{document_path}' but couldn't find sections directly relevant to your question: '{question}'. The document overview is:\n\n{overview_response}\n\nPlease try asking a more specific question about particular aspects of the document."
        
        return {
            "success": True,
            "response": final_response,
            "document_overview": overview_response,
            "relevant_chunks": relevant_summaries,
            "total_chunks": len(chunks),
            "chunks_analyzed": min(len(chunks), 10),
            "document_size": len(document_content)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error processing large document: {str(e)}",
            "document_size": len(document_content)
        }

def get_processing_recommendation(document_size: int, question: str) -> str:
    """
    Provide recommendations for processing documents based on size and question type.
    """
    if document_size < 100000:  # <100K chars
        return "✅ Document size is manageable for direct analysis."
    
    elif document_size < 300000:  # 100K-300K chars  
        return """⚠️ **Large Document Detected**
This document may take longer to process. Consider:
- Ask specific questions about particular sections
- Request a summary first, then drill into details
- Use targeted keywords in your questions"""

    else:  # >300K chars
        return f"""🚫 **Very Large Document ({document_size:,} characters)**

**Recommended approaches:**
1. **Summarize first**: "Give me an overview of this document"
2. **Section-specific**: "What does the methodology section say about..."
3. **Targeted search**: "Find information about [specific topic]"
4. **Progressive analysis**: Start broad, then ask follow-up questions

**Why this matters:**
- Large documents exceed model context limits
- Processing time increases exponentially  
- Targeted questions get better answers"""