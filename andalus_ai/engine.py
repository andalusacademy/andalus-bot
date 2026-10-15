from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any

import google.generativeai as genai

from .tools import ToolRegistry, build_default_registry


SYSTEM_PROMPT = """
أنت Andalus AI، المدير الذكي لنظام مركز الأندلس للتدريب.

مهمتك ليست مجرد الدردشة. افهم السؤال أو الأمر، وحدد هل المطلوب:
1) معلومة من النظام، أو
2) تنفيذ عملية داخل النظام، أو
3) إنشاء/جدولة مهمة مستقبلية.

تحدث مع المستخدم بنفس لغته. افهم العربية المصرية والعربية الفصحى والإنجليزية.
لا تخترع أي بيانات. إذا كانت المعلومة تحتاج بيانات النظام، استخدم الأداة المناسبة.
إذا كان الأمر ينفذ تغييرا أو إرسالا خارجيا، يجب اعتبار الأداة ذات requires_confirmation=true
وتطلب تأكيد المستخدم قبل التنفيذ.

أعد JSON فقط بهذا الشكل:
{
  "type": "answer" | "tool_call" | "clarification",
  "message": "...",
  "tool": null | "tool_name",
  "arguments": {}
}
"""


@dataclass
class AIResult:
    message: str
    type: str = "answer"
    tool: str | None = None
    arguments: dict[str, Any] = field(default_factory=dict)
    confirmation_required: bool = False
    raw: dict[str, Any] | None = None


class AndalusAI:
    """Provider-backed agent with a controlled tool surface."""

    def __init__(self, registry: ToolRegistry | None = None, model_name: str | None = None):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name or os.getenv("ANDALUS_AI_MODEL", "gemini-flash-latest"))
        self.registry = registry or build_default_registry()

    def _prompt(self, user_message: str, history: list[dict[str, str]] | None = None) -> str:
        tools = json.dumps(self.registry.definitions(), ensure_ascii=False)
        context = json.dumps(history or [], ensure_ascii=False)
        return f"{SYSTEM_PROMPT}\n\nالأدوات المتاحة:\n{tools}\n\nالسياق:\n{context}\n\nرسالة المستخدم:\n{user_message}"

    async def understand(self, user_message: str, history: list[dict[str, str]] | None = None) -> AIResult:
        response = self.model.generate_content(
            self._prompt(user_message, history),
            generation_config={"temperature": 0.1, "response_mime_type": "application/json"},
        )
        data = json.loads(response.text)
        tool = data.get("tool")
        return AIResult(
            message=data.get("message", ""),
            type=data.get("type", "answer"),
            tool=tool,
            arguments=data.get("arguments") or {},
            confirmation_required=bool(tool and self.registry.requires_confirmation(tool)),
            raw=data,
        )

    async def execute(self, result: AIResult) -> Any:
        if result.type != "tool_call" or not result.tool:
            return result.message
        if result.confirmation_required:
            return {
                "ok": False,
                "confirmation_required": True,
                "tool": result.tool,
                "arguments": result.arguments,
                "message": "هذه العملية تحتاج تأكيد المستخدم قبل التنفيذ.",
            }
        return await self.registry.execute(result.tool, result.arguments)
