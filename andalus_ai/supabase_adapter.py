from __future__ import annotations
import os
from datetime import datetime, timezone
from typing import Any
import httpx

class AcademyData:
    """Allow-listed Supabase REST adapter. Credentials stay server-side."""
    def __init__(self) -> None:
        self.url = os.getenv("SUPABASE_URL", "").rstrip("/")
        self.key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        self.timeout = float(os.getenv("SUPABASE_TIMEOUT_SECONDS", "8"))
    def _ready(self) -> bool:
        return bool(self.url and self.key)
    async def _get(self, table: str, params: dict[str, str]) -> list[dict[str, Any]]:
        if not self._ready():
            return [{"ok": False, "error": "Supabase connection is not configured. Set server environment variables."}]
        headers = {"apikey": self.key, "Authorization": f"Bearer {self.key}", "Accept": "application/json"}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.url}/rest/v1/{table}", params=params, headers=headers)
            response.raise_for_status()
            payload = response.json()
            return payload if isinstance(payload, list) else []
    async def _students(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        q = query.strip()
        if not q: return []
        params = {"select":"id,name,enrollment_number,phone,guardian_name,guardian_phone,parent_name,parent_phone,branch,program,system_name,student_status",
                  "deleted_at":"is.null","or":f"(name.ilike.*{q}*,enrollment_number.eq.{q})",
                  "limit":str(max(1,min(int(limit),25)))}
        return await self._get("students", params)
    async def search_students(self, query: str, limit: int = 10) -> dict[str, Any]:
        rows=await self._students(query,limit)
        if len(rows)==1 and rows[0].get("ok") is False: return rows[0]
        return {"ok":True,"count":len(rows),"students":rows}
    async def get_student(self, query: str) -> dict[str, Any]:
        rows=await self._students(query,5)
        if len(rows)==1 and rows[0].get("ok") is False: return rows[0]
        return {"ok":True,"count":len(rows),"students":rows}
    async def _one_student(self, query: str) -> dict[str, Any] | None:
        rows=await self._students(query,5)
        if len(rows)==1 and rows[0].get("ok") is False: return rows[0]
        if not rows: return None
        exact=[r for r in rows if str(r.get("enrollment_number") or "").strip()==query.strip()]
        if len(exact)==1: return exact[0]
        exact=[r for r in rows if str(r.get("name") or "").strip().casefold()==query.strip().casefold()]
        return exact[0] if len(exact)==1 else {"_ambiguous":True,"matches":rows}
    def _ambiguous(self, student: dict[str, Any] | None) -> bool:
        return student is None or student.get("_ambiguous") or student.get("ok") is False
    async def get_student_attendance(self, query: str) -> dict[str, Any]:
        s=await self._one_student(query)
        if self._ambiguous(s): return {"ok":False,"message":"لم أتمكن من تحديد طالب واحد. استخدم الاسم الكامل أو رقم القيد.","matches":s.get("matches",[]) if s else []}
        rows=await self._get("attendance",{"select":"date,status,program,session_id,created_at","student_id":f"eq.{s['id']}","order":"date.desc","limit":"300"})
        if len(rows)==1 and rows[0].get("ok") is False: return {"ok":False,"error":rows[0]["error"]}
        absences=[r for r in rows if any(x in str(r.get("status","")).casefold() for x in ("غائب","غياب","absent","absence"))]
        return {"ok":True,"student":s.get("name"),"total_records":len(rows),"absence_count":len(absences),"absences":absences,"attendance":rows}
    async def get_student_grades(self, query: str) -> dict[str, Any]:
        s=await self._one_student(query)
        if self._ambiguous(s): return {"ok":False,"message":"لم أتمكن من تحديد طالب واحد. استخدم الاسم الكامل أو رقم القيد.","matches":s.get("matches",[]) if s else []}
        rows=await self._get("grades",{"select":"grade_1,grade_2,grade_1_note,grade_2_note,subjects(name,max_grade_1,max_grade_2,min_pass)","student_id":f"eq.{s['id']}","limit":"200"})
        if len(rows)==1 and rows[0].get("ok") is False: return {"ok":False,"error":rows[0]["error"]}
        return {"ok":True,"student":s.get("name"),"grades":rows}
    async def get_student_parent(self, query: str) -> dict[str, Any]:
        s=await self._one_student(query)
        if self._ambiguous(s): return {"ok":False,"message":"لم أتمكن من تحديد طالب واحد. استخدم الاسم الكامل أو رقم القيد.","matches":s.get("matches",[]) if s else []}
        return {"ok":True,"student":s.get("name"),"guardian_name":s.get("guardian_name") or s.get("parent_name"),"guardian_phone":s.get("guardian_phone") or s.get("parent_phone")}
    async def get_absent_students(self, date: str, program: str | None = None, limit: int = 100) -> dict[str, Any]:
        params={"select":"student_id,date,status,program,students(name,enrollment_number,phone,guardian_phone,parent_phone)","date":f"eq.{date}","status":"in.(غائب,غياب,absent,absence)","limit":str(max(1,min(int(limit),500)))}
        if program: params["program"]=f"eq.{program}"
        rows=await self._get("attendance",params)
        if len(rows)==1 and rows[0].get("ok") is False: return {"ok":False,"error":rows[0]["error"]}
        return {"ok":True,"date":date,"count":len(rows),"absentees":rows}
    async def create_task(self, title: str, details: str = "", run_at: str | None = None, task_type: str = "admin") -> dict[str, Any]:
        return await self._insert_task(title,details,run_at,task_type,"pending")
    async def schedule_task(self, title: str, details: str, run_at: str, task_type: str = "admin") -> dict[str, Any]:
        if not run_at: return {"ok":False,"error":"run_at is required in ISO-8601 format with timezone."}
        try:
            dt=datetime.fromisoformat(run_at.replace("Z","+00:00"))
            if dt.tzinfo is None: return {"ok":False,"error":"أرسل الموعد مع المنطقة الزمنية، مثل +03:00."}
            if dt<=datetime.now(timezone.utc): return {"ok":False,"error":"موعد المهمة يجب أن يكون في المستقبل."}
        except ValueError: return {"ok":False,"error":"صيغة الموعد غير صحيحة. استخدم ISO-8601."}
        return await self._insert_task(title,details,dt.isoformat(),task_type,"scheduled")
    async def _insert_task(self,title: str,details: str,run_at: str|None,task_type: str,status: str)->dict[str,Any]:
        if not self._ready(): return {"ok":False,"error":"Supabase connection is not configured."}
        body={"title":title[:180],"details":details[:5000],"task_type":task_type[:50],"status":status,"run_at":run_at}
        headers={"apikey":self.key,"Authorization":f"Bearer {self.key}","Content-Type":"application/json","Prefer":"return=representation"}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response=await client.post(f"{self.url}/rest/v1/andalus_ai_tasks",json=body,headers=headers)
            if response.is_error: return {"ok":False,"error":f"تعذر حفظ المهمة ({response.status_code}). تأكد من تطبيق migration الخاصة بـ Andalus AI."}
            return {"ok":True,"task":response.json()}
    async def send_whatsapp(self, recipients: list[dict[str,str]], message: str) -> dict[str,Any]:
        return {"ok":False,"error":"موفر WhatsApp غير موصل بعد. لم يتم إرسال أي رسالة.","recipient_count":len(recipients)}
    async def create_report(self,title: str,details: str="")->dict[str,Any]:
        return {"ok":True,"title":title[:180],"details":details[:5000],"created_at":datetime.now(timezone.utc).isoformat()}
