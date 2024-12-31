from aiogram.fsm.state import State, StatesGroup


class MainGroup(StatesGroup):
    diag_mode = State()
    generator_mode = State()
