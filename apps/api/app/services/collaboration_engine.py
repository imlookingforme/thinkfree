from __future__ import annotations

import asyncio
from datetime import datetime
import random
import string
from typing import Any, Dict, List, Optional
from fastapi import WebSocket


class Participant:
    def __init__(self, client_id: str, user_id: str, user_name: str, role: str):
        self.client_id = client_id
        self.user_id = user_id
        self.user_name = user_name
        self.role = role  # "driver" or "navigator"
        self.cursor_line: int = 1
        self.cursor_ch: int = 1
        self.keystroke_count: int = 0
        self.connected_at: datetime = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "client_id": self.client_id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "role": self.role,
            "cursor_line": self.cursor_line,
            "cursor_ch": self.cursor_ch,
            "keystroke_count": self.keystroke_count,
        }


class Room:
    def __init__(self, room_code: str, problem_id: str, initial_code: str = "", language: str = "python"):
        self.room_code = room_code
        self.problem_id = problem_id
        self.code = initial_code or "def solve(nums, target):\n    # Collaborative Thinking\n    pass\n"
        self.language = language
        self.created_at = datetime.utcnow()
        self.participants: Dict[str, Participant] = {}
        self.connections: List[WebSocket] = []
        self.chat_messages: List[Dict[str, Any]] = []

    def get_divergence_metrics(self) -> Dict[str, Any]:
        total_keystrokes = sum(p.keystroke_count for p in self.participants.values())
        if total_keystrokes < 25:
            return {
                "asymmetry_ratio": 0.5,
                "is_divergent": False,
                "message": "Balanced pair interaction.",
                "total_keystrokes": total_keystrokes
            }

        driver_keys = max(
            (p.keystroke_count for p in self.participants.values() if p.role == "driver"),
            default=0
        )
        asymmetry_ratio = round(driver_keys / max(1, total_keystrokes), 2)
        is_divergent = asymmetry_ratio >= 0.85

        message = (
            "Pedagogical alert: High effort asymmetry! Navigator has low interaction. Swap roles or explain reasoning."
            if is_divergent else "Healthy collaborative engagement across driver and navigator."
        )

        return {
            "asymmetry_ratio": asymmetry_ratio,
            "is_divergent": is_divergent,
            "message": message,
            "total_keystrokes": total_keystrokes
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "room_code": self.room_code,
            "problem_id": self.problem_id,
            "code": self.code,
            "language": self.language,
            "participants": [p.to_dict() for p in self.participants.values()],
            "divergence": self.get_divergence_metrics(),
            "chat_messages": self.chat_messages[-30:]
        }


class CollaborationEngine:
    _rooms: Dict[str, Room] = {}
    _lock = asyncio.Lock()

    @classmethod
    def generate_room_code(cls) -> str:
        code_suffix = "".join(random.choices(string.digits, k=6))
        return f"TF-{code_suffix}"

    @classmethod
    async def get_or_create_room(
        cls,
        problem_id: str,
        room_code: Optional[str] = None,
        initial_code: str = "",
        language: str = "python"
    ) -> Room:
        async with cls._lock:
            if room_code and room_code in cls._rooms:
                return cls._rooms[room_code]

            new_code = room_code or cls.generate_room_code()
            room = Room(new_code, problem_id, initial_code, language)
            cls._rooms[new_code] = room
            return room

    @classmethod
    def get_room(cls, room_code: str) -> Optional[Room]:
        return cls._rooms.get(room_code)

    @classmethod
    async def join_room(
        cls,
        room_code: str,
        websocket: WebSocket,
        user_id: str,
        user_name: str
    ) -> Optional[Participant]:
        room = cls.get_room(room_code)
        if not room:
            return None

        # Assign role: First user is driver, second is navigator, subsequent are spectators
        existing_roles = [p.role for p in room.participants.values()]
        if "driver" not in existing_roles:
            role = "driver"
        elif "navigator" not in existing_roles:
            role = "navigator"
        else:
            role = "navigator"

        client_id = f"peer_{user_id[:6]}_{random.randint(100, 999)}"
        participant = Participant(client_id, user_id, user_name, role)
        room.participants[client_id] = participant
        room.connections.append(websocket)

        # Record system join message
        room.chat_messages.append({
            "sender_name": "ThinkFree System",
            "role": "system",
            "text": f"{user_name} joined the pair room as {role.upper()}.",
            "ts": datetime.utcnow().isoformat()
        })

        return participant

    @classmethod
    async def leave_room(cls, room_code: str, websocket: WebSocket, client_id: str):
        room = cls.get_room(room_code)
        if not room:
            return

        if websocket in room.connections:
            room.connections.remove(websocket)

        part = room.participants.pop(client_id, None)
        if part:
            room.chat_messages.append({
                "sender_name": "ThinkFree System",
                "role": "system",
                "text": f"{part.user_name} left the room.",
                "ts": datetime.utcnow().isoformat()
            })

        # If driver left, promote navigator to driver
        if part and part.role == "driver" and room.participants:
            next_part = next(iter(room.participants.values()))
            next_part.role = "driver"
            room.chat_messages.append({
                "sender_name": "ThinkFree System",
                "role": "system",
                "text": f"{next_part.user_name} has been designated as the new DRIVER.",
                "ts": datetime.utcnow().isoformat()
            })

    @classmethod
    def swap_roles(cls, room_code: str):
        room = cls.get_room(room_code)
        if not room:
            return

        drivers = [p for p in room.participants.values() if p.role == "driver"]
        navigators = [p for p in room.participants.values() if p.role == "navigator"]

        if drivers and navigators:
            drivers[0].role = "navigator"
            navigators[0].role = "driver"
            room.chat_messages.append({
                "sender_name": "ThinkFree System",
                "role": "system",
                "text": f"Roles swapped! {navigators[0].user_name} is now DRIVER, and {drivers[0].user_name} is NAVIGATOR.",
                "ts": datetime.utcnow().isoformat()
            })

    @classmethod
    async def broadcast_room_state(cls, room_code: str):
        room = cls.get_room(room_code)
        if not room:
            return

        state = {"type": "room_state", "data": room.to_dict()}
        stale_conns = []
        for ws in room.connections:
            try:
                await ws.send_json(state)
            except Exception:
                stale_conns.append(ws)

        for ws in stale_conns:
            if ws in room.connections:
                room.connections.remove(ws)
