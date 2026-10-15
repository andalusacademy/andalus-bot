import os
import unittest
from unittest.mock import AsyncMock
from andalus_ai.engine import AIResult, AndalusAI
from andalus_ai.tools import Tool, ToolRegistry
from andalus_ai.supabase_adapter import AcademyData

class EngineTests(unittest.IsolatedAsyncioTestCase):
    async def test_confirmation_blocks_mutation_by_default(self):
        registry=ToolRegistry()
        handler=AsyncMock(return_value={"ok":True})
        registry.register(Tool("schedule_task","test",handler,True))
        agent=object.__new__(AndalusAI)
        agent.registry=registry
        result=AIResult("schedule",type="tool_call",tool="schedule_task",arguments={"title":"test"},confirmation_required=True)
        blocked=await agent.execute(result)
        self.assertTrue(blocked["confirmation_required"])
        handler.assert_not_awaited()
        executed=await agent.execute(result,confirmed=True)
        self.assertEqual(executed,{"ok":True})
        handler.assert_awaited_once_with(title="test")

    async def test_unknown_tool_rejected(self):
        registry=ToolRegistry()
        with self.assertRaises(ValueError):
            await registry.execute("drop_database",{})

    async def test_missing_supabase_configuration_is_explicit(self):
        old_url=os.environ.pop("SUPABASE_URL",None)
        old_key=os.environ.pop("SUPABASE_SERVICE_ROLE_KEY",None)
        try:
            data=AcademyData()
            self.assertFalse(data._ready())
        finally:
            if old_url is not None: os.environ["SUPABASE_URL"]=old_url
            if old_key is not None: os.environ["SUPABASE_SERVICE_ROLE_KEY"]=old_key

if __name__=="__main__":
    unittest.main()
