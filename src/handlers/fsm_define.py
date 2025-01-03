from aiogram.fsm.state import State, StatesGroup


class MainGroup(StatesGroup):
    diag_mode = State()
    generator_mode = State()
    abonement_mode = State()


class AbonementGroup(StatesGroup):
    abonement_name = State()
    abonement_total_passes = State()
    abonement_description = State()
    abonement_join = State()
    abonement_accept = State()
