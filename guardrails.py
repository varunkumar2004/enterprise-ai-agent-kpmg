import re 
from fastapi import HTTPException

def redact_pii(text: str) -> str:
    """Masks common PII patterns before processing."""
    text = re.sub(r'[\w\.-]+@[\w\.-]+', '[REDACTED_EMAIL]', text) # Mask email addresses
    text = re.sub(r'\b\d{4}[ -]?\d{4}[ -]?\d{4}[ -]?\d{4}\b', '[REDACTED_ACCOUNT]', text) # Mask 16-digit numbers (Credit Cards / Account Numbers)
    text = re.sub(r'\b\d{3}[ -]?\d{2}[ -]?\d{4}\b', '[REDACTED_ID]', text) # Mask 9-digit numbers (SSN/Standard IDs)
    return text

def check_intent(text: str):
    """Blocks non-coding or malicious requests."""
    forbidden_topics = ["phishing", "stock advice", "crypto", "hack", "bypass", "malware"]
    text_lower = text.lower()
    for topic in forbidden_topics:
        if topic in text_lower:
            raise HTTPException(
                status_code=403, 
                detail=f"Security Policy Violation: Request contains blocked intent ({topic})."
            )
        
def scan_output_for_hazards(text: str):
    """Prevents the AI from returning dangerous code patterns."""
    dangerous_patterns = ["password = ", "API_KEY", "os.system", "eval(", "exec("]
    for pattern in dangerous_patterns:
        if pattern in text:
            """In production, this would trigger an audit log and an alert to security."""
            raise HTTPException(
                status_code=500,
                detail="Output Blocked: AI generated potentially unsafe code patterns."
            )