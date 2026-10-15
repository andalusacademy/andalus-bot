from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict


@dataclass
class Tool:
    name: str
    description: str
    handler: Callable[..., Awaitable[Any]]
    requires_confirmation: bool = False


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def definitions(self) -> list[dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "requires_confirmation": t.requires_confirmation,
            }
            for t in self._tools.values()
        ]

    async def execute(self, name: str, arguments: dict[str, Any]) -> Any:
        if name not in self._tools:
            raise ValueError(f"Unknown Andalus AI tool: {name}")
        return await self._tools[name].handler(**arguments)

    def requires_confirmation(self, name: str) -> bool:
        return self._tools[name].requires_confirmation


async def not_connected(**_: Any) -> dict[str, Any]:
    return {
        "ok": False,
        "error": "الأداة غير موصولة ببيانات النظام بعد.",
    }


def build_default_registry() -> ToolRegistry:
    """Create the first safe tool surface.

    The handlers intentionally return a clear not-connected response until the
    production Supabase/system adapter is attached. This keeps the AI from
    inventing data or pretending that an action was executed.
    """
    registry = ToolRegistry()
    registry.register(Tool("search_students", "البحث عن متدربين بالاسم أو رقم القيد", not_connected))
    registry.register(Tool("get_student", "جلب بيانات متدرب محدد", not_connected))
    registry.register(Tool("get_student_attendance", "جلب حضور وغياب متدرب", not_connected))
    registry.register(Tool("get_student_grades", "جلب درجات متدرب", not_connected))
    registry.register(Tool("get_absent_students", "استخراج الغائبين حسب المحاضرة أو التاريخ", not_connected))
    registry.register(Tool("get_student_parent", "جلب بيانات ولي أمر متدرب", not_connected))
    registry.register(Tool("create_task", "إنشاء مهمة داخل النظام", not_connected, True))
    registry.register(Tool("schedule_task", "جدولة مهمة لتعمل تلقائيا", not_connected, True))
    registry.register(Tool("send_whatsapp", "إرسال رسالة واتساب لمستهدفين محددين", not_connected, True))
    registry.register(Tool("create_report", "إنشاء تقرير من بيانات النظام", not_connected, False))
    return registry
