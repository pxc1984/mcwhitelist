from aiogram.fsm.state import State, StatesGroup


class RequestState(StatesGroup):
    waiting_comment = State()
