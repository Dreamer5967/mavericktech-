"""AEGIS Security & Prompt Injection Firewall.
Enforces strict privilege boundaries, input sanitization, and adversarial prompt detection.
Smart Technologies PS3 Compliance.
"""
from dataclasses import dataclass, field
import re
import math
import io
from typing import Literal

Role = Literal["operator", "vqa_reader", "viewer"]

@dataclass(frozen=True)
class SecurityContext:
    role: Role
    token: str
    client_id: str = "default-client"
    
    @property
    def can_actuate(self) -> bool:
        """Only authenticated operators can trigger simulation state changes."""
        return self.role == "operator"

@dataclass
class InspectionResult:
    is_safe: bool
    detected_injection: bool
    attack_type: str | None
    sanitized_text: str
    reasons: list[str] = field(default_factory=list)

class SecurityFirewall:
    """Security firewall that screens queries, uploaded media, and enforces role boundaries."""
    
    # Common prompt injection, jailbreak, and override patterns
    INJECTION_PATTERNS = [
        (r"(?i)\b(?:system\s+override|admin\s+override|root\s+override)\b", "direct_override"),
        (r"(?i)\b(?:ignore\s+(?:all\s+)?(?:previous|prior)\s+instructions?)\b", "instruction_bypass"),
        (r"(?i)\b(?:you\s+are\s+now\s+in\s+(?:developer|debug|god|maintenance)\s+mode)\b", "jailbreak_persona"),
        (r"(?i)\b(?:set|turn|force|switch)\s+(?:all\s+)?(?:lights?|signals?|junctions?)\s+(?:to\s+)?(?:green|red|yellow)\b", "unauthorized_actuation"),
        (r"(?i)\b(?:actuate|call|trigger)\s+[\w/]*(?:api|endpoint|reset|incident|fault)\b", "api_probing"),
        (r"(?i)\b(?:sudo|chmod|eval|exec|import\s+os)\b", "command_injection"),
    ]
    
    def __init__(self, operator_secret: str = "local-demo-only"):
        self.operator_secret = operator_secret

    def authenticate(self, auth_header: str | None) -> SecurityContext:
        """Authenticate request and assign minimal viable privilege role."""
        if not auth_header:
            return SecurityContext(role="viewer", token="")
        
        token = auth_header.removeprefix("Bearer ").strip()
        if token == self.operator_secret:
            return SecurityContext(role="operator", token=token)
        elif token.startswith("vqa-"):
            return SecurityContext(role="vqa_reader", token=token)
        else:
            return SecurityContext(role="viewer", token=token)

    def inspect_text(self, text: str) -> InspectionResult:
        """Inspects incoming user questions and visual text for prompt injection."""
        if not text:
            return InspectionResult(is_safe=True, detected_injection=False, attack_type=None, sanitized_text="")
        
        detected = False
        attack_type = None
        reasons = []
        
        for pattern, a_type in self.INJECTION_PATTERNS:
            if re.search(pattern, text):
                detected = True
                attack_type = a_type
                reasons.append(f"Matched pattern: {a_type}")
                break
        
        # Strip dangerous shell/eval characters
        sanitized = re.sub(r"[;&|`$><]", "", text).strip()
        
        return InspectionResult(
            is_safe=not detected,
            detected_injection=detected,
            attack_type=attack_type,
            sanitized_text=sanitized,
            reasons=reasons
        )

    def authorize_actuation(self, context: SecurityContext, action_name: str) -> tuple[bool, str]:
        """Strict authorization gate: blocks any non-operator from executing actuation."""
        if not context.can_actuate:
            return False, f"PERMISSION_DENIED: Role '{context.role}' has zero actuation privileges."
        return True, "AUTHORIZED"

    def sanitize_image_bytes(self, raw_bytes: bytes, max_size_mb: float = 5.0) -> tuple[bool, bytes | None, str]:
        """Validates image size and basic header signatures (PNG/JPEG) without leaking metadata."""
        if len(raw_bytes) > max_size_mb * 1024 * 1024:
            return False, None, "PAYLOAD_TOO_LARGE: Exceeds 5MB cap"
        
        # Check basic image magic numbers
        is_png = raw_bytes.startswith(b"\x89PNG\r\n\x1a\n")
        is_jpeg = raw_bytes.startswith(b"\xff\xd8\xff")
        
        if not (is_png or is_jpeg):
            return False, None, "UNSUPPORTED_MEDIA: Only PNG and JPEG formats are permitted"
        
        return True, raw_bytes, "VALID_IMAGE"
