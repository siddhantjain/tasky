#!/usr/bin/env python3
"""Tasky HTTP server for iOS app integration."""
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path
from datetime import date

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import (
    add_task,
    list_tasks,
    get_task,
    complete_task,
    delete_task,
    update_task,
    daily_summary,
    search_tasks,
)


class TaskyHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())

    def _send_error(self, message, status=400):
        self._send_json({"error": message}, status)

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        try:
            if path == "/api/tasks" or path == "/api/list":
                # Get filter params
                filters = {}
                if "status" in params:
                    filters["status"] = params["status"][0]
                if "priority" in params:
                    filters["priority"] = params["priority"][0]
                if "tag" in params:
                    filters["tag"] = params["tag"][0]
                if "due_today" in params:
                    filters["due_today"] = params["due_today"][0].lower() == "true"
                if "overdue" in params:
                    filters["overdue"] = params["overdue"][0].lower() == "true"
                
                tasks = list_tasks(**filters) if filters else list_tasks()
                self._send_json({"tasks": tasks, "count": len(tasks)})

            elif path == "/api/summary":
                summary = daily_summary()
                self._send_json(summary)

            elif path.startswith("/api/task/"):
                task_id = path.split("/api/task/")[1]
                task = get_task(task_id)
                if task:
                    self._send_json(task)
                else:
                    self._send_error("Task not found", 404)

            elif path == "/api/search":
                query = params.get("q", [""])[0]
                if not query:
                    self._send_error("Missing search query 'q'")
                else:
                    results = search_tasks(query)
                    self._send_json({"tasks": results, "count": len(results)})

            elif path == "/api/health":
                self._send_json({"status": "ok", "service": "tasky"})

            elif path == "/":
                # Simple dashboard redirect or info
                self._send_json({
                    "service": "Tasky API",
                    "version": "0.1.0",
                    "endpoints": [
                        "GET /api/tasks",
                        "GET /api/summary",
                        "GET /api/task/<id>",
                        "GET /api/search?q=<query>",
                        "POST /api/task",
                        "POST /api/task/<id>/complete",
                        "PUT /api/task/<id>",
                        "DELETE /api/task/<id>",
                    ]
                })

            else:
                self._send_error("Unknown endpoint", 404)

        except Exception as e:
            self._send_error(str(e), 500)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = {}
            if content_length > 0:
                body = json.loads(self.rfile.read(content_length))

            if path == "/api/task":
                # Create new task
                title = body.get("title")
                if not title:
                    self._send_error("Missing 'title'")
                    return
                
                task = add_task(
                    title=title,
                    due=body.get("due"),
                    priority=body.get("priority"),
                    tags=body.get("tags"),
                    notes=body.get("notes"),
                )
                self._send_json(task, 201)

            elif path.endswith("/complete"):
                # Complete a task
                task_id = path.replace("/api/task/", "").replace("/complete", "")
                result = complete_task(task_id)
                if result:
                    self._send_json(result)
                else:
                    self._send_error("Task not found", 404)

            else:
                self._send_error("Unknown endpoint", 404)

        except json.JSONDecodeError:
            self._send_error("Invalid JSON")
        except Exception as e:
            self._send_error(str(e), 500)

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path

        try:
            if path.startswith("/api/task/"):
                task_id = path.split("/api/task/")[1]
                result = delete_task(task_id)
                if result:
                    self._send_json({"deleted": True, "id": task_id})
                else:
                    self._send_error("Task not found", 404)
            else:
                self._send_error("Unknown endpoint", 404)

        except Exception as e:
            self._send_error(str(e), 500)

    def do_PUT(self):
        parsed = urlparse(self.path)
        path = parsed.path

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = {}
            if content_length > 0:
                body = json.loads(self.rfile.read(content_length))

            if path.startswith("/api/task/"):
                task_id = path.split("/api/task/")[1]
                # Build update kwargs from body
                updates = {}
                if "title" in body:
                    updates["title"] = body["title"]
                if "due" in body:
                    updates["due"] = body["due"]
                if "priority" in body:
                    updates["priority"] = body["priority"]
                if "notes" in body:
                    updates["notes"] = body["notes"]
                if "tags" in body:
                    updates["tags"] = body["tags"]
                
                result = update_task(task_id, **updates)
                if result:
                    self._send_json(result)
                else:
                    self._send_error("Task not found", 404)
            else:
                self._send_error("Unknown endpoint", 404)

        except json.JSONDecodeError:
            self._send_error("Invalid JSON")
        except Exception as e:
            self._send_error(str(e), 500)

    def log_message(self, format, *args):
        # Quieter logging
        pass


def run(port=4005, host="0.0.0.0"):
    server = HTTPServer((host, port), TaskyHandler)
    print(f"🗂️  Tasky server running on http://{host}:{port}")
    print(f"   API: http://localhost:{port}/api/tasks")
    server.serve_forever()


if __name__ == "__main__":
    run()
