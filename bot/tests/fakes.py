from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class FakeUser:
    id: int
    full_name: str = "Test User"
    username: Optional[str] = None


@dataclass
class FakeChat:
    id: int
    type: str = "private"


@dataclass
class FakeMessage:
    chat: FakeChat
    from_user: FakeUser
    text: Optional[str] = None
    reply_to_message: Optional["FakeMessage"] = None
    entities: Optional[List[Any]] = None
    message_id: int = 1
    replies: List[str] = field(default_factory=list)
    answers: List[str] = field(default_factory=list)
    edits: List[str] = field(default_factory=list)

    async def reply(self, text: str) -> None:
        self.replies.append(text)

    async def answer(self, text: str, reply_markup: Any = None) -> None:
        self.answers.append(text)

    async def edit_text(self, text: str, reply_markup: Any = None) -> None:
        self.edits.append(text)


@dataclass
class FakeCallbackQuery:
    data: str
    from_user: FakeUser
    message: Optional[FakeMessage] = None
    answers: List[Dict[str, Any]] = field(default_factory=list)

    async def answer(self, text: Optional[str] = None, show_alert: bool = False) -> None:
        self.answers.append({"text": text, "show_alert": show_alert})


class FakeFSMContext:
    def __init__(self) -> None:
        self.data: Dict[str, Any] = {}
        self.state: Optional[str] = None
        self.cleared = False

    async def update_data(self, **kwargs: Any) -> None:
        self.data.update(kwargs)

    async def set_state(self, state: Any) -> None:
        self.state = state

    async def get_data(self) -> Dict[str, Any]:
        return dict(self.data)

    async def clear(self) -> None:
        self.cleared = True
        self.data.clear()


class FakeConn:
    def __init__(self) -> None:
        self.fetchrow_result: Any = None
        self.fetch_result: List[Any] = []
        self.execute_calls: List[Any] = []
        self.last_query: Optional[str] = None
        self.last_params: Optional[tuple] = None

    async def fetchrow(self, query: str, *params: Any) -> Any:
        self.last_query = query
        self.last_params = params
        return self.fetchrow_result

    async def fetch(self, query: str, *params: Any) -> List[Any]:
        self.last_query = query
        self.last_params = params
        return list(self.fetch_result)

    async def execute(self, query: str, *params: Any) -> None:
        self.execute_calls.append((query, params))
        self.last_query = query
        self.last_params = params

    def transaction(self) -> "FakeConn":
        return self

    async def __aenter__(self) -> "FakeConn":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


class FakePool:
    def __init__(self, conn: FakeConn) -> None:
        self.conn = conn

    def acquire(self) -> FakeConn:
        return self.conn


class FakeBot:
    def __init__(self) -> None:
        self.sent: List[Dict[str, Any]] = []
        self.chats: Dict[str, Any] = {}
        self.reactions: List[Dict[str, Any]] = []

    async def send_message(self, chat_id: int, text: str, reply_markup: Any = None) -> None:
        self.sent.append({"chat_id": chat_id, "text": text, "reply_markup": reply_markup})

    async def get_chat(self, username: str) -> Any:
        return self.chats.get(username)

    async def set_message_reaction(
        self,
        chat_id: int,
        message_id: int,
        reaction: Optional[List[Any]] = None,
        is_big: Optional[bool] = None,
    ) -> None:
        self.reactions.append(
            {
                "chat_id": chat_id,
                "message_id": message_id,
                "reaction": reaction,
                "is_big": is_big,
            }
        )
