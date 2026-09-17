import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

import app
import auth_service


class CalendarSyncBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "planner.db"
        app.DB_PATH = self.db_path
        auth_service.DB_PATH = self.db_path
        app.DATA_DIR = Path(self.temp_dir.name)
        app.LOG_DIR = Path(self.temp_dir.name) / "logs"
        app.init_db()
        self.user_id = app.DEFAULT_LOCAL_USER_ID

    def tearDown(self):
        self.temp_dir.cleanup()

    def _calendar_mcp(self, mcp_url, tool_name, arguments=None):
        if tool_name == "list_calendars":
            return {
                "success": True,
                "result": [
                    {
                        "calendarId": "primary",
                        "summary": "我的日历",
                        "privilege": "owner",
                        "type": "primary",
                    }
                ],
            }
        if tool_name == "create_calendar_event":
            return {
                "success": True,
                "result": {
                    "eventId": "event-1",
                    "summary": arguments.get("summary", ""),
                    "startDateTime": arguments.get("startDateTime", ""),
                    "endDateTime": arguments.get("endDateTime", ""),
                },
            }
        if tool_name == "update_calendar_event":
            return {
                "success": True,
                "result": {
                    "eventId": arguments.get("eventId", ""),
                    "summary": arguments.get("summary", ""),
                    "startDateTime": arguments.get("startDateTime", ""),
                    "endDateTime": arguments.get("endDateTime", ""),
                },
            }
        if tool_name == "delete_calendar_event":
            return {"success": True, "result": {}}
        if tool_name == "list_calendar_events":
            return {"success": True, "result": []}
        raise AssertionError(f"unexpected MCP tool: {tool_name}")

    def _save_calendar_config(self, url, mode="push"):
        with patch.object(app, "call_dingtalk_mcp_tool", side_effect=self._calendar_mcp):
            return app.save_user_dingtalk_mcp_config(
                self.user_id,
                {
                    "calendar_mcp_url": url,
                    "calendar_id": "primary",
                    "calendar_sync_mode": mode,
                },
            )

    def _current_week_sync_slot(self):
        slot_keys = [
            "weekly_monday_am",
            "weekly_tuesday_am",
            "weekly_wednesday_am",
            "weekly_thursday_am",
            "weekly_friday_am",
            "weekly_saturday_am",
            "weekly_sunday_am",
        ]
        return slot_keys[date.today().weekday()]

    def test_existing_weekly_plan_is_not_backfilled_after_activation(self):
        week_start = app.get_week_start(date.today().isoformat())
        historical_settings = {
            "weekly_monday_am": "配置前已经存在的安排",
            "weekly_tuesday_pm": "配置前的未来安排",
        }
        app.save_weekly_plan_settings(week_start, historical_settings, user_id=self.user_id)

        with patch.object(app, "call_dingtalk_mcp_tool", side_effect=self._calendar_mcp):
            config = app.save_user_dingtalk_mcp_config(
                self.user_id,
                {
                    "calendar_mcp_url": "https://example.invalid/calendar-mcp?key=test",
                    "calendar_id": "primary",
                    "calendar_sync_mode": "two_way",
                },
            )

        self.assertEqual(config["calendar_sync_status"], "active")
        with app.get_connection() as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM schedule_items").fetchone()[0], 0)
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM dingtalk_calendar_sync_jobs").fetchone()[0], 0)

        unchanged = dict(historical_settings)
        app.save_weekly_plan_settings(week_start, unchanged, user_id=self.user_id)
        with app.get_connection() as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM schedule_items").fetchone()[0], 0)
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM dingtalk_calendar_sync_jobs").fetchone()[0], 0)

    def test_post_activation_change_creates_only_one_sync_item(self):
        week_start = app.get_week_start(date.today().isoformat())
        slot_key = self._current_week_sync_slot()
        app.save_weekly_plan_settings(
            week_start,
            {slot_key: "旧内容", "weekly_sunday_pm": "保留历史内容"},
            user_id=self.user_id,
        )
        with patch.object(app, "call_dingtalk_mcp_tool", side_effect=self._calendar_mcp):
            app.save_user_dingtalk_mcp_config(
                self.user_id,
                {
                    "calendar_mcp_url": "https://example.invalid/calendar-mcp?key=test",
                    "calendar_id": "primary",
                    "calendar_sync_mode": "push",
                },
            )

        changed = {
            slot_key: "配置后新增安排",
            "weekly_sunday_pm": "保留历史内容",
        }
        app.save_weekly_plan_settings(week_start, changed, user_id=self.user_id)

        with app.get_connection() as connection:
            items = connection.execute(
                "SELECT slot_key, title, status FROM schedule_items ORDER BY id"
            ).fetchall()
            jobs = connection.execute(
                "SELECT operation, status FROM dingtalk_calendar_sync_jobs ORDER BY id"
            ).fetchall()
        self.assertEqual([tuple(row) for row in items], [(slot_key, "配置后新增安排", "pending")])
        self.assertEqual([tuple(row) for row in jobs], [("upsert", "pending")])

    def test_sync_job_persists_remote_event_id(self):
        week_start = app.get_week_start(date.today().isoformat())
        slot_key = self._current_week_sync_slot()
        with patch.object(app, "call_dingtalk_mcp_tool", side_effect=self._calendar_mcp):
            app.save_user_dingtalk_mcp_config(
                self.user_id,
                {
                    "calendar_mcp_url": "https://example.invalid/calendar-mcp?key=test",
                    "calendar_id": "primary",
                    "calendar_sync_mode": "push",
                },
            )
            app.save_weekly_plan_settings(
                week_start,
                {slot_key: "需要同步的安排"},
                user_id=self.user_id,
            )
            job = app.list_due_dingtalk_calendar_sync_jobs()[0]
            app.process_dingtalk_calendar_sync_job(job)

        with app.get_connection() as connection:
            item = connection.execute(
                "SELECT dingtalk_event_id, status, last_local_hash FROM schedule_items"
            ).fetchone()
            job = connection.execute(
                "SELECT status, attempt_count FROM dingtalk_calendar_sync_jobs"
            ).fetchone()
        self.assertEqual(item["dingtalk_event_id"], "event-1")
        self.assertEqual(item["status"], "synced")
        self.assertTrue(item["last_local_hash"])
        self.assertEqual(job["status"], "sent")
        self.assertEqual(job["attempt_count"], 1)

    def test_switching_calendar_mcp_creates_new_event_without_touching_old_event(self):
        week_start = app.get_week_start(date.today().isoformat())
        slot_key = self._current_week_sync_slot()
        first_url = "https://example.invalid/calendar-mcp?key=first"
        second_url = "https://example.invalid/calendar-mcp?key=second"
        self._save_calendar_config(first_url)
        app.save_weekly_plan_settings(
            week_start,
            {slot_key: "旧 MCP 日程"},
            user_id=self.user_id,
        )

        calls = []

        def first_sync_mcp(mcp_url, tool_name, arguments=None):
            calls.append((mcp_url, tool_name, arguments or {}))
            if tool_name == "create_calendar_event":
                return {"success": True, "result": {"eventId": "old-event"}}
            return self._calendar_mcp(mcp_url, tool_name, arguments)

        with patch.object(app, "call_dingtalk_mcp_tool", side_effect=first_sync_mcp):
            app.process_dingtalk_calendar_sync_job(app.list_due_dingtalk_calendar_sync_jobs()[0])

        self._save_calendar_config(second_url)
        app.save_weekly_plan_settings(
            week_start,
            {slot_key: "新 MCP 日程"},
            user_id=self.user_id,
        )

        with app.get_connection() as connection:
            item = connection.execute(
                "SELECT sync_session_id, dingtalk_event_id, status FROM schedule_items"
            ).fetchone()
            sessions = connection.execute(
                "SELECT status FROM dingtalk_calendar_sync_sessions ORDER BY id"
            ).fetchall()
            jobs = connection.execute(
                "SELECT sync_session_id, operation, status FROM dingtalk_calendar_sync_jobs ORDER BY id"
            ).fetchall()
        self.assertEqual(item["dingtalk_event_id"], "")
        self.assertEqual(item["status"], "pending")
        self.assertEqual([row["status"] for row in sessions], ["frozen", "active"])
        self.assertEqual([row["operation"] for row in jobs], ["upsert", "upsert"])
        self.assertEqual(jobs[0]["status"], "sent")
        self.assertEqual(jobs[1]["status"], "pending")

        def second_sync_mcp(mcp_url, tool_name, arguments=None):
            calls.append((mcp_url, tool_name, arguments or {}))
            if tool_name == "create_calendar_event":
                return {"success": True, "result": {"eventId": "new-event"}}
            return self._calendar_mcp(mcp_url, tool_name, arguments)

        with patch.object(app, "call_dingtalk_mcp_tool", side_effect=second_sync_mcp):
            app.process_dingtalk_calendar_sync_job(app.list_due_dingtalk_calendar_sync_jobs()[0])

        self.assertIn((second_url, "create_calendar_event"), [(url, tool) for url, tool, _ in calls])
        self.assertNotIn((first_url, "update_calendar_event"), [(url, tool) for url, tool, _ in calls])
        self.assertNotIn((first_url, "delete_calendar_event"), [(url, tool) for url, tool, _ in calls])
        with app.get_connection() as connection:
            item = connection.execute(
                "SELECT dingtalk_event_id, status FROM schedule_items"
            ).fetchone()
        self.assertEqual(item["dingtalk_event_id"], "new-event")
        self.assertEqual(item["status"], "synced")

    def test_deleted_remote_event_removes_local_schedule_and_next_edit_recreates(self):
        week_start = app.get_week_start(date.today().isoformat())
        slot_key = self._current_week_sync_slot()
        calendar_url = "https://example.invalid/calendar-mcp?key=remote-delete"
        self._save_calendar_config(calendar_url, mode="two_way")
        app.save_weekly_plan_settings(
            week_start,
            {slot_key: "需要同步的安排"},
            user_id=self.user_id,
        )

        with patch.object(app, "call_dingtalk_mcp_tool", side_effect=self._calendar_mcp):
            app.process_dingtalk_calendar_sync_job(app.list_due_dingtalk_calendar_sync_jobs()[0])

        def missing_remote_event(_mcp_url, tool_name, _arguments=None):
            if tool_name == "list_calendar_events":
                return {"success": True, "result": []}
            if tool_name == "get_calendar_detail":
                raise RuntimeError("日程不存在或已被删除")
            raise AssertionError(f"unexpected MCP tool: {tool_name}")

        session = app.get_active_dingtalk_calendar_sync_session(self.user_id)
        with patch.object(app, "call_dingtalk_mcp_tool", side_effect=missing_remote_event):
            app.poll_dingtalk_calendar_sync_session(session)

        with app.get_connection() as connection:
            item = connection.execute(
                "SELECT dingtalk_event_id, last_remote_event_id, status FROM schedule_items"
            ).fetchone()
        self.assertEqual(item["dingtalk_event_id"], "")
        self.assertEqual(item["last_remote_event_id"], "event-1")
        self.assertEqual(item["status"], "remote_deleted")
        _, weekly_settings, _ = app.get_weekly_plan_settings(week_start, user_id=self.user_id)
        self.assertEqual(weekly_settings[slot_key], "")

        app.save_weekly_plan_settings(
            week_start,
            {slot_key: "远程删除后重新创建"},
            user_id=self.user_id,
        )
        job = app.list_due_dingtalk_calendar_sync_jobs()[0]
        calls = []

        def recreate_mcp(mcp_url, tool_name, arguments=None):
            calls.append((mcp_url, tool_name, arguments or {}))
            if tool_name == "create_calendar_event":
                return {"success": True, "result": {"eventId": "recreated-event"}}
            raise AssertionError(f"unexpected MCP tool: {tool_name}")

        with patch.object(app, "call_dingtalk_mcp_tool", side_effect=recreate_mcp):
            app.process_dingtalk_calendar_sync_job(job)

        self.assertIn("create_calendar_event", [tool for _, tool, _ in calls])
        self.assertNotIn("update_calendar_event", [tool for _, tool, _ in calls])
        with app.get_connection() as connection:
            item = connection.execute(
                "SELECT dingtalk_event_id, status FROM schedule_items"
            ).fetchone()
        self.assertEqual(item["dingtalk_event_id"], "recreated-event")
        self.assertEqual(item["status"], "synced")

    def test_cancelled_remote_event_removes_local_schedule_and_next_edit_recreates(self):
        week_start = app.get_week_start(date.today().isoformat())
        slot_key = self._current_week_sync_slot()
        calendar_url = "https://example.invalid/calendar-mcp?key=remote-cancel"
        self._save_calendar_config(calendar_url, mode="two_way")
        app.save_weekly_plan_settings(
            week_start,
            {slot_key: "需要同步的安排"},
            user_id=self.user_id,
        )

        with patch.object(app, "call_dingtalk_mcp_tool", side_effect=self._calendar_mcp):
            app.process_dingtalk_calendar_sync_job(app.list_due_dingtalk_calendar_sync_jobs()[0])

        def cancelled_remote_event(_mcp_url, tool_name, _arguments=None):
            if tool_name == "list_calendar_events":
                return {
                    "success": True,
                    "result": [
                        {
                            "eventId": "event-1",
                            "status": "cancelled",
                            "summary": "需要同步的安排",
                            "startDateTime": f"{date.today().isoformat()}T09:00:00+08:00",
                            "endDateTime": f"{date.today().isoformat()}T12:00:00+08:00",
                        }
                    ],
                }
            raise AssertionError(f"unexpected MCP tool: {tool_name}")

        session = app.get_active_dingtalk_calendar_sync_session(self.user_id)
        with patch.object(app, "call_dingtalk_mcp_tool", side_effect=cancelled_remote_event):
            app.poll_dingtalk_calendar_sync_session(session)

        with app.get_connection() as connection:
            item = connection.execute(
                "SELECT dingtalk_event_id, last_remote_event_id, status FROM schedule_items"
            ).fetchone()
        self.assertEqual(item["dingtalk_event_id"], "")
        self.assertEqual(item["last_remote_event_id"], "event-1")
        self.assertEqual(item["status"], "remote_cancelled")
        _, weekly_settings, _ = app.get_weekly_plan_settings(week_start, user_id=self.user_id)
        self.assertEqual(weekly_settings[slot_key], "")

        app.save_weekly_plan_settings(
            week_start,
            {slot_key: "取消后重新创建"},
            user_id=self.user_id,
        )
        calls = []

        def recreate_mcp(mcp_url, tool_name, arguments=None):
            calls.append((mcp_url, tool_name, arguments or {}))
            if tool_name == "create_calendar_event":
                return {"success": True, "result": {"eventId": "event-2"}}
            raise AssertionError(f"unexpected MCP tool: {tool_name}")

        with patch.object(app, "call_dingtalk_mcp_tool", side_effect=recreate_mcp):
            app.process_dingtalk_calendar_sync_job(app.list_due_dingtalk_calendar_sync_jobs()[0])

        self.assertIn("create_calendar_event", [tool for _, tool, _ in calls])
        self.assertNotIn("update_calendar_event", [tool for _, tool, _ in calls])
        with app.get_connection() as connection:
            item = connection.execute(
                "SELECT dingtalk_event_id, last_remote_event_id, status FROM schedule_items"
            ).fetchone()
        self.assertEqual(item["dingtalk_event_id"], "event-2")
        self.assertEqual(item["last_remote_event_id"], "event-2")
        self.assertEqual(item["status"], "synced")

    def test_local_delete_clears_remote_event_id_before_recreate(self):
        week_start = app.get_week_start(date.today().isoformat())
        slot_key = self._current_week_sync_slot()
        calendar_url = "https://example.invalid/calendar-mcp?key=local-delete"
        self._save_calendar_config(calendar_url)
        app.save_weekly_plan_settings(
            week_start,
            {slot_key: "先创建"},
            user_id=self.user_id,
        )
        with patch.object(app, "call_dingtalk_mcp_tool", side_effect=self._calendar_mcp):
            app.process_dingtalk_calendar_sync_job(app.list_due_dingtalk_calendar_sync_jobs()[0])

        app.save_weekly_plan_settings(
            week_start,
            {slot_key: ""},
            user_id=self.user_id,
        )
        with patch.object(app, "call_dingtalk_mcp_tool", side_effect=self._calendar_mcp):
            app.process_dingtalk_calendar_sync_job(app.list_due_dingtalk_calendar_sync_jobs()[0])

        with app.get_connection() as connection:
            item = connection.execute(
                "SELECT dingtalk_event_id, status FROM schedule_items"
            ).fetchone()
        self.assertEqual(item["dingtalk_event_id"], "")
        self.assertEqual(item["status"], "deleted")

        app.save_weekly_plan_settings(
            week_start,
            {slot_key: "重新创建"},
            user_id=self.user_id,
        )
        calls = []

        def recreate_mcp(mcp_url, tool_name, arguments=None):
            calls.append((mcp_url, tool_name, arguments or {}))
            if tool_name == "create_calendar_event":
                return {"success": True, "result": {"eventId": "recreated-event"}}
            raise AssertionError(f"unexpected MCP tool: {tool_name}")

        with patch.object(app, "call_dingtalk_mcp_tool", side_effect=recreate_mcp):
            app.process_dingtalk_calendar_sync_job(app.list_due_dingtalk_calendar_sync_jobs()[0])

        self.assertIn("create_calendar_event", [tool for _, tool, _ in calls])
        self.assertNotIn("update_calendar_event", [tool for _, tool, _ in calls])

    def test_new_timed_items_support_multiple_evening_events(self):
        week_start = app.get_week_start(date.today().isoformat())
        calendar_url = "https://example.invalid/calendar-mcp?key=timed-items"
        self._save_calendar_config(calendar_url)
        work_date = date.today().isoformat()
        settings = {
            "weekly_plan_items": [
                {
                    "id": "evening-meeting",
                    "work_date": work_date,
                    "start_time": "19:00",
                    "end_time": "21:00",
                    "title": "晚间会议",
                    "location": "线上会议室",
                },
                {
                    "id": "evening-follow-up",
                    "work_date": work_date,
                    "start_time": "21:15",
                    "end_time": "22:00",
                    "title": "会议纪要整理",
                },
            ],
        }
        app.save_weekly_plan_settings(week_start, settings, user_id=self.user_id)

        with app.get_connection() as connection:
            items = connection.execute(
                """
                SELECT slot_key, work_date, title, location, start_at, end_at, status
                FROM schedule_items
                ORDER BY slot_key
                """
            ).fetchall()
        self.assertEqual(len(items), 2)
        self.assertEqual(
            [
                (
                    row["slot_key"],
                    row["work_date"],
                    row["title"],
                    row["location"],
                    row["start_at"],
                    row["end_at"],
                    row["status"],
                )
                for row in items
            ],
            [
                (
                    "weekly_item:evening-follow-up",
                    work_date,
                    "会议纪要整理",
                    "",
                    f"{work_date}T21:15:00+08:00",
                    f"{work_date}T22:00:00+08:00",
                    "pending",
                ),
                (
                    "weekly_item:evening-meeting",
                    work_date,
                    "晚间会议",
                    "线上会议室",
                    f"{work_date}T19:00:00+08:00",
                    f"{work_date}T21:00:00+08:00",
                    "pending",
                ),
            ],
        )

        _, saved_settings, _ = app.get_weekly_plan_settings(week_start, user_id=self.user_id)
        client_settings = app.build_weekly_plan_client_settings(week_start, saved_settings)
        self.assertEqual(
            [
                (item["id"], item["start_time"], item["end_time"], item["title"])
                for item in client_settings["weekly_plan_items"]
            ],
            [
                ("evening-meeting", "19:00", "21:00", "晚间会议"),
                ("evening-follow-up", "21:15", "22:00", "会议纪要整理"),
            ],
        )

    def test_legacy_am_pm_items_keep_fixed_time_ranges_in_new_payload(self):
        week_start = app.get_week_start(date.today().isoformat())
        app.save_weekly_plan_settings(
            week_start,
            {
                "weekly_monday_am": "上午旧安排",
                "weekly_monday_pm": "下午旧安排",
            },
            user_id=self.user_id,
        )
        _, settings, _ = app.get_weekly_plan_settings(week_start, user_id=self.user_id)
        client_settings = app.build_weekly_plan_client_settings(week_start, settings)
        monday_items = [
            item
            for item in client_settings["weekly_plan_items"]
            if item["work_date"] == week_start
        ]
        self.assertEqual(
            [
                (item["legacy_slot_key"], item["start_time"], item["end_time"], item["title"])
                for item in monday_items
            ],
            [
                ("weekly_monday_am", "09:00", "12:00", "上午旧安排"),
                ("weekly_monday_pm", "13:30", "18:00", "下午旧安排"),
            ],
        )

    def test_timed_item_validation_rejects_invalid_range(self):
        week_start = app.get_week_start(date.today().isoformat())
        with self.assertRaises(ValueError):
            app.save_weekly_plan_settings(
                week_start,
                {
                    "weekly_plan_items": [
                        {
                            "id": "invalid",
                            "work_date": date.today().isoformat(),
                            "start_time": "22:00",
                            "end_time": "21:00",
                            "title": "结束时间错误",
                        }
                    ]
                },
                user_id=self.user_id,
            )

    def test_timed_item_validation_rejects_invalid_time_format(self):
        week_start = app.get_week_start(date.today().isoformat())
        with self.assertRaisesRegex(ValueError, "HH:MM"):
            app.save_weekly_plan_settings(
                week_start,
                {
                    "weekly_plan_items": [
                        {
                            "id": "invalid-format",
                            "work_date": date.today().isoformat(),
                            "start_time": "24:00",
                            "end_time": "10:00",
                            "title": "时间格式错误",
                        }
                    ]
                },
                user_id=self.user_id,
            )

    def test_timed_item_validation_normalizes_loose_time_input(self):
        week_start = app.get_week_start(date.today().isoformat())
        work_date = date.today().isoformat()
        app.save_weekly_plan_settings(
            week_start,
            {
                "weekly_plan_items": [
                    {
                        "id": "loose-time",
                        "work_date": work_date,
                        "start_time": "9",
                        "end_time": "１０；３０",
                        "title": "宽松时间输入",
                    }
                ]
            },
            user_id=self.user_id,
        )

        _, saved_settings, _ = app.get_weekly_plan_settings(week_start, user_id=self.user_id)
        client_settings = app.build_weekly_plan_client_settings(week_start, saved_settings)
        self.assertEqual(
            [
                (item["id"], item["start_time"], item["end_time"], item["title"])
                for item in client_settings["weekly_plan_items"]
            ],
            [("loose-time", "09:00", "10:30", "宽松时间输入")],
        )

    def test_client_settings_expose_missing_calendar_sync_state(self):
        week_start = app.get_week_start(date.today().isoformat())
        app.save_weekly_plan_settings(
            week_start,
            {
                "weekly_plan_items": [
                    {
                        "id": "missing-sync",
                        "work_date": date.today().isoformat(),
                        "start_time": "09:00",
                        "end_time": "10:00",
                        "title": "未配置同步的日程",
                    }
                ]
            },
            user_id=self.user_id,
        )

        _, settings, _ = app.get_weekly_plan_settings(week_start, user_id=self.user_id)
        client_settings = app.build_weekly_plan_client_settings(
            week_start,
            settings,
            user_id=self.user_id,
        )
        item = client_settings["weekly_plan_items"][0]
        self.assertEqual(item["calendar_sync"]["status"], "missing")
        self.assertEqual(client_settings["calendar_sync_summary"]["status"], "missing")
        self.assertFalse(client_settings["calendar_sync_summary"]["enabled"])

    def test_manual_calendar_sync_queues_existing_week_items_after_activation(self):
        week_start = app.get_week_start(date.today().isoformat())
        app.save_weekly_plan_settings(
            week_start,
            {
                "weekly_plan_items": [
                    {
                        "id": "manual-sync",
                        "work_date": date.today().isoformat(),
                        "start_time": "09:00",
                        "end_time": "10:00",
                        "title": "配置后手动同步",
                    }
                ]
            },
            user_id=self.user_id,
        )
        self._save_calendar_config(
            "https://example.invalid/calendar-mcp?key=manual-sync",
            mode="push",
        )
        with app.get_connection() as connection:
            self.assertEqual(
                connection.execute(
                    "SELECT COUNT(*) FROM dingtalk_calendar_sync_jobs"
                ).fetchone()[0],
                0,
            )

        queued = app.queue_weekly_plan_calendar_snapshot_for_user(
            self.user_id,
            week_start,
        )
        self.assertEqual(queued["status"], "queued")
        self.assertEqual(queued["item_count"], 1)
        with app.get_connection() as connection:
            self.assertEqual(
                connection.execute(
                    "SELECT COUNT(*) FROM dingtalk_calendar_sync_jobs"
                ).fetchone()[0],
                1,
            )

    def test_manual_two_way_sync_imports_remote_calendar_event(self):
        week_start = app.get_week_start(date.today().isoformat())
        work_date = date.today().isoformat()

        def import_mcp(mcp_url, tool_name, arguments=None):
            if tool_name == "list_calendar_events":
                return {
                    "success": True,
                    "result": [
                        {
                            "eventId": "remote-event-1",
                            "summary": "钉钉客户会议",
                            "description": "从钉钉拉取的日程",
                            "location": {"displayName": "A 会议室"},
                            "startDateTime": f"{work_date}T09:30:00+08:00",
                            "endDateTime": f"{work_date}T10:30:00+08:00",
                            "updatedAt": f"{work_date}T08:00:00+08:00",
                        }
                    ],
                }
            return self._calendar_mcp(mcp_url, tool_name, arguments)

        with patch.object(app, "call_dingtalk_mcp_tool", side_effect=import_mcp):
            app.save_user_dingtalk_mcp_config(
                self.user_id,
                {
                    "calendar_mcp_url": "https://example.invalid/calendar-mcp?key=import",
                    "calendar_id": "primary",
                    "calendar_sync_mode": "two_way",
                },
            )
            first_result = app.queue_weekly_plan_calendar_snapshot_for_user(
                self.user_id,
                week_start,
            )
            app.run_dingtalk_calendar_sync_now(self.user_id)
            second_result = app.queue_weekly_plan_calendar_snapshot_for_user(
                self.user_id,
                week_start,
            )

        self.assertEqual(first_result["status"], "imported")
        self.assertEqual(first_result["imported_count"], 1)
        self.assertEqual(first_result["queued_count"], 0)
        self.assertEqual(second_result["imported_count"], 0)
        with app.get_connection() as connection:
            rows = connection.execute(
                """
                SELECT slot_key, title, description, location, work_date,
                       start_at, end_at, dingtalk_event_id, status, source
                FROM schedule_items
                ORDER BY id
                """
            ).fetchall()
            job_count = connection.execute(
                "SELECT COUNT(*) FROM dingtalk_calendar_sync_jobs"
            ).fetchone()[0]
        self.assertEqual(job_count, 0)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertTrue(row["slot_key"].startswith("weekly_item:dingtalk_"))
        self.assertEqual(row["title"], "钉钉客户会议")
        self.assertEqual(row["description"], "从钉钉拉取的日程")
        self.assertEqual(row["location"], "A 会议室")
        self.assertEqual(row["work_date"], work_date)
        self.assertEqual(row["start_at"], f"{work_date}T09:30:00+08:00")
        self.assertEqual(row["end_at"], f"{work_date}T10:30:00+08:00")
        self.assertEqual(row["dingtalk_event_id"], "remote-event-1")
        self.assertEqual(row["status"], "synced")
        self.assertEqual(row["source"], app.DINGTALK_CALENDAR_IMPORTED_SOURCE)

        _, saved_settings, _ = app.get_weekly_plan_settings(week_start, user_id=self.user_id)
        client_settings = app.build_weekly_plan_client_settings(
            week_start,
            saved_settings,
            user_id=self.user_id,
        )
        self.assertEqual(len(client_settings["weekly_plan_items"]), 1)
        imported_item = client_settings["weekly_plan_items"][0]
        self.assertEqual(imported_item["title"], "钉钉客户会议")
        self.assertEqual(imported_item["start_time"], "09:30")
        self.assertEqual(imported_item["end_time"], "10:30")
        self.assertEqual(imported_item["location"], "A 会议室")
        self.assertEqual(imported_item["calendar_sync"]["status"], "synced")

    def test_imported_dingtalk_item_local_delete_keeps_remote_and_blocks_reimport(self):
        week_start = app.get_week_start(date.today().isoformat())
        work_date = date.today().isoformat()
        remote_event = {
            "eventId": "remote-event-delete-local",
            "summary": "本地删除的钉钉日程",
            "description": "保留钉钉端日程",
            "startDateTime": f"{work_date}T09:30:00+08:00",
            "endDateTime": f"{work_date}T10:30:00+08:00",
            "updatedAt": f"{work_date}T08:00:00+08:00",
        }
        calls = []

        def import_mcp(mcp_url, tool_name, arguments=None):
            calls.append((tool_name, arguments or {}))
            if tool_name == "list_calendar_events":
                return {"success": True, "result": [remote_event]}
            return self._calendar_mcp(mcp_url, tool_name, arguments)

        with patch.object(app, "call_dingtalk_mcp_tool", side_effect=import_mcp):
            self._save_calendar_config(
                "https://example.invalid/calendar-mcp?key=import-delete-local",
                mode="two_way",
            )
            first_result = app.queue_weekly_plan_calendar_snapshot_for_user(
                self.user_id,
                week_start,
            )

        self.assertEqual(first_result["imported_count"], 1)
        _, settings, _ = app.get_weekly_plan_settings(week_start, user_id=self.user_id)
        self.assertEqual(len(settings[app.WEEKLY_PLAN_ITEMS_KEY]), 1)

        app.save_weekly_plan_settings(
            week_start,
            {app.WEEKLY_PLAN_ITEMS_KEY: []},
            user_id=self.user_id,
        )

        with app.get_connection() as connection:
            row = connection.execute(
                """
                SELECT dingtalk_event_id, last_remote_event_id, status, source
                FROM schedule_items
                """
            ).fetchone()
            pending_jobs = connection.execute(
                """
                SELECT COUNT(*)
                FROM dingtalk_calendar_sync_jobs
                WHERE status IN ('pending', 'running')
                """
            ).fetchone()[0]
        self.assertEqual(row["dingtalk_event_id"], "")
        self.assertEqual(row["last_remote_event_id"], "remote-event-delete-local")
        self.assertEqual(row["status"], "deleted")
        self.assertEqual(row["source"], app.DINGTALK_CALENDAR_IMPORTED_SOURCE)
        self.assertEqual(pending_jobs, 0)

        with patch.object(app, "call_dingtalk_mcp_tool", side_effect=import_mcp):
            second_result = app.queue_weekly_plan_calendar_snapshot_for_user(
                self.user_id,
                week_start,
            )

        self.assertEqual(second_result["imported_count"], 0)
        self.assertEqual(second_result["skipped_count"], 1)
        self.assertNotIn("delete_calendar_event", [tool_name for tool_name, _ in calls])
        _, settings_after, _ = app.get_weekly_plan_settings(week_start, user_id=self.user_id)
        self.assertEqual(settings_after[app.WEEKLY_PLAN_ITEMS_KEY], [])

    def test_imported_dingtalk_item_remote_delete_keeps_local_item_with_status(self):
        week_start = app.get_week_start(date.today().isoformat())
        work_date = date.today().isoformat()
        remote_event = {
            "eventId": "remote-event-deleted-remotely",
            "summary": "钉钉删除后保留本地",
            "description": "远端删除测试",
            "startDateTime": f"{work_date}T11:00:00+08:00",
            "endDateTime": f"{work_date}T12:00:00+08:00",
            "updatedAt": f"{work_date}T08:00:00+08:00",
        }

        def import_mcp(mcp_url, tool_name, arguments=None):
            if tool_name == "list_calendar_events":
                return {"success": True, "result": [remote_event]}
            return self._calendar_mcp(mcp_url, tool_name, arguments)

        with patch.object(app, "call_dingtalk_mcp_tool", side_effect=import_mcp):
            self._save_calendar_config(
                "https://example.invalid/calendar-mcp?key=import-remote-delete",
                mode="two_way",
            )
            result = app.queue_weekly_plan_calendar_snapshot_for_user(
                self.user_id,
                week_start,
            )
        self.assertEqual(result["imported_count"], 1)

        def missing_remote_event(_mcp_url, tool_name, _arguments=None):
            if tool_name == "list_calendar_events":
                return {"success": True, "result": []}
            if tool_name == "get_calendar_detail":
                raise RuntimeError("日程不存在或已被删除")
            raise AssertionError(f"unexpected MCP tool: {tool_name}")

        session = app.get_active_dingtalk_calendar_sync_session(self.user_id)
        with patch.object(app, "call_dingtalk_mcp_tool", side_effect=missing_remote_event):
            app.poll_dingtalk_calendar_sync_session(session)

        with app.get_connection() as connection:
            row = connection.execute(
                "SELECT dingtalk_event_id, last_remote_event_id, status, source FROM schedule_items"
            ).fetchone()
        self.assertEqual(row["dingtalk_event_id"], "")
        self.assertEqual(row["last_remote_event_id"], "remote-event-deleted-remotely")
        self.assertEqual(row["status"], "remote_deleted")
        self.assertEqual(row["source"], app.DINGTALK_CALENDAR_IMPORTED_SOURCE)

        _, settings, _ = app.get_weekly_plan_settings(week_start, user_id=self.user_id)
        self.assertEqual(len(settings[app.WEEKLY_PLAN_ITEMS_KEY]), 1)
        client_settings = app.build_weekly_plan_client_settings(
            week_start,
            settings,
            user_id=self.user_id,
        )
        item = client_settings[app.WEEKLY_PLAN_ITEMS_KEY][0]
        self.assertEqual(item["calendar_sync"]["status"], "remote_deleted")
        self.assertEqual(item["calendar_sync"]["label"], "钉钉已删除")

    def test_calendar_sync_poll_interval_is_three_minutes(self):
        self.assertEqual(app.DINGTALK_CALENDAR_SYNC_POLL_SECONDS, 180)

    def test_cross_user_edit_cannot_delete_imported_dingtalk_item(self):
        work_date = date.today().isoformat()
        imported_item = {
            "id": "dingtalk_protected",
            "work_date": work_date,
            "start_time": "09:30",
            "end_time": "10:30",
            "title": "钉钉同步会议",
            "description": "",
            "location": "A 会议室",
            "sort_order": 1,
            "source": app.DINGTALK_CALENDAR_IMPORTED_SOURCE,
        }
        local_item = {
            "id": "local_item",
            "work_date": work_date,
            "start_time": "11:00",
            "end_time": "12:00",
            "title": "本地安排",
            "description": "",
            "location": "",
            "sort_order": 2,
            "source": "new",
        }
        current_settings = {app.WEEKLY_PLAN_ITEMS_KEY: [imported_item, local_item]}
        next_settings = {app.WEEKLY_PLAN_ITEMS_KEY: [local_item]}

        with self.assertRaisesRegex(PermissionError, "不能删除他人从钉钉同步的日程"):
            app.validate_cross_user_dingtalk_imported_plan_items(
                current_user={"user_id": "editor"},
                target_user={"user_id": "target"},
                current_settings=current_settings,
                next_settings=next_settings,
            )

        app.validate_cross_user_dingtalk_imported_plan_items(
            current_user={"user_id": "target"},
            target_user={"user_id": "target"},
            current_settings=current_settings,
            next_settings=next_settings,
        )
        app.validate_cross_user_dingtalk_imported_plan_items(
            current_user={"user_id": "editor"},
            target_user={"user_id": "target"},
            current_settings={app.WEEKLY_PLAN_ITEMS_KEY: [local_item]},
            next_settings={app.WEEKLY_PLAN_ITEMS_KEY: []},
        )

    def test_cross_user_edit_cannot_modify_imported_dingtalk_item(self):
        work_date = date.today().isoformat()
        imported_item = {
            "id": "dingtalk_protected",
            "work_date": work_date,
            "start_time": "09:30",
            "end_time": "10:30",
            "title": "钉钉同步会议",
            "description": "",
            "location": "A 会议室",
            "sort_order": 1,
            "source": app.DINGTALK_CALENDAR_IMPORTED_SOURCE,
        }
        changed_item = dict(imported_item)
        changed_item["title"] = "被他人修改"

        with self.assertRaisesRegex(PermissionError, "不能修改他人从钉钉同步的日程"):
            app.validate_cross_user_dingtalk_imported_plan_items(
                current_user={"user_id": "editor"},
                target_user={"user_id": "target"},
                current_settings={app.WEEKLY_PLAN_ITEMS_KEY: [imported_item]},
                next_settings={app.WEEKLY_PLAN_ITEMS_KEY: [changed_item]},
            )

    def test_client_settings_expose_synced_calendar_state(self):
        week_start = app.get_week_start(date.today().isoformat())
        slot_key = self._current_week_sync_slot()
        calendar_url = "https://example.invalid/calendar-mcp?key=client-state"
        with patch.object(app, "call_dingtalk_mcp_tool", side_effect=self._calendar_mcp):
            self._save_calendar_config(calendar_url, mode="push")
            app.save_weekly_plan_settings(
                week_start,
                {slot_key: "已同步日程"},
                user_id=self.user_id,
            )
            app.process_dingtalk_calendar_sync_job(
                app.list_due_dingtalk_calendar_sync_jobs()[0]
            )

        _, settings, _ = app.get_weekly_plan_settings(week_start, user_id=self.user_id)
        client_settings = app.build_weekly_plan_client_settings(
            week_start,
            settings,
            user_id=self.user_id,
        )
        item = next(
            item for item in client_settings["weekly_plan_items"]
            if item["legacy_slot_key"] == slot_key
        )
        self.assertEqual(item["calendar_sync"]["status"], "synced")
        self.assertEqual(client_settings["calendar_sync_summary"]["status"], "synced")

    def test_deleting_unsent_timed_item_replaces_pending_upsert_job(self):
        week_start = app.get_week_start(date.today().isoformat())
        self._save_calendar_config("https://example.invalid/calendar-mcp?key=delete-before-send")
        item = {
            "id": "delete-before-send",
            "work_date": date.today().isoformat(),
            "start_time": "19:00",
            "end_time": "20:00",
            "title": "稍后删除",
        }
        app.save_weekly_plan_settings(
            week_start,
            {"weekly_plan_items": [item]},
            user_id=self.user_id,
        )
        app.save_weekly_plan_settings(
            week_start,
            {"weekly_plan_items": []},
            user_id=self.user_id,
        )
        with app.get_connection() as connection:
            job = connection.execute(
                "SELECT operation, status FROM dingtalk_calendar_sync_jobs ORDER BY id DESC LIMIT 1"
            ).fetchone()
        self.assertEqual(job["operation"], "delete")
        self.assertEqual(job["status"], "pending")


if __name__ == "__main__":
    unittest.main()
