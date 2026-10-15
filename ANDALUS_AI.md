# Andalus AI

Andalus AI is being upgraded from an educational chatbot into an agent that can read system data and execute controlled tasks.

## Current architecture

- `andalus_ai/engine.py`: natural-language understanding and agent orchestration.
- `andalus_ai/tools.py`: controlled tool registry. The AI can only act through registered tools.
- `AIResult`: normalized intent result (`answer`, `tool_call`, `clarification`).
- Mutating/external tools require confirmation by default.

## First tool surface

Read tools:

- `search_students`
- `get_student`
- `get_student_attendance`
- `get_student_grades`
- `get_absent_students`
- `get_student_parent`
- `create_report`

Action tools:

- `create_task`
- `schedule_task`
- `send_whatsapp`

The default handlers intentionally return a not-connected response. The next integration step is to connect these tools to the production Andalus data layer (Supabase/system APIs) instead of allowing the model to fabricate data.

## Example target interactions

> هاتلي غياب أحمد محمد

→ `get_student_attendance`

> هاتلي رقم ولي أمر محمد أحمد

→ `get_student_parent`

> حدد الطلبة اللي غابوا يوم 12 أكتوبر

→ `get_absent_students`

> الساعة 2 ابعت لهم رسالة واتساب

→ `schedule_task` / `send_whatsapp`, with confirmation before external sending.
