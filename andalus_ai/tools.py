from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Awaitable, Callable
from .supabase_adapter import AcademyData

@dataclass
class Tool:
    name: str
    description: str
    handler: Callable[..., Awaitable[Any]]
    requires_confirmation: bool = False

class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}
    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool
    def definitions(self) -> list[dict[str, Any]]:
        return [{"name": t.name, "description": t.description, "requires_confirmation": t.requires_confirmation} for t in self._tools.values()]
    def requires_confirmation(self, name: str) -> bool:
        return self._tools[name].requires_confirmation
    async def execute(self, name: str, arguments: dict[str, Any]) -> Any:
        if name not in self._tools:
            raise ValueError(f"Unknown Andalus AI tool: {name}")
        return await self._tools[name].handler(**arguments)

def build_default_registry() -> ToolRegistry:
    data = AcademyData()
    registry = ToolRegistry()
    registry.register(Tool("search_students", "البحث عن المتدربين بالاسم أو رقم القيد", data.search_students))
    registry.register(Tool("get_student", "جلب بيانات متدرب محدد بالاسم أو رقم القيد", data.get_student))
    registry.register(Tool("get_student_attendance", "جلب حضور وغياب متدرب بالاسم أو رقم القيد", data.get_student_attendance))
    registry.register(Tool("get_student_grades", "جلب درجات متدرب بالاسم أو رقم القيد", data.get_student_grades))
    registry.register(Tool("get_absent_students", "استخراج الغائبين حسب تاريخ المحاضرة أو التاريخ", data.get_absent_students))
    registry.register(Tool("get_student_parent", "جلب اسم ورقم ولي أمر متدرب", data.get_student_parent))
    registry.register(Tool("create_task", "حفظ مهمة إدارية في قائمة المهام", data.create_task, True))
    registry.register(Tool("schedule_task", "جدولة مهمة إدارية لتعمل تلقائيا", data.schedule_task, True))
    registry.register(Tool("send_whatsapp", "إرسال رسالة واتساب؛ يحتاج موفر إرسال مهيأ وتأكيد", data.send_whatsapp, True))
    registry.register(Tool("create_report", "إنشاء ملخص تقرير من بيانات الأكاديمية", data.create_report))
    return registry
