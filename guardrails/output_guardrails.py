from fastapi import HTTPException

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