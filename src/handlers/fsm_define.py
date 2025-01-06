from aiogram.fsm.state import State, StatesGroup


# FSM Main group
class MainGroup(StatesGroup):
    diag_mode = State()
    generator_mode = State()
    abonement_mode = State()


# FSM Register group
class RegisterGroup(StatesGroup):
    agreement = State()
    phone = State()
    name = State()
    finish = State()


# FSM Abonement group
class AbonementGroup(StatesGroup):
    abonement_name = State()
    abonement_total_passes = State()
    abonement_description = State()
    abonement_join = State()
    abonement_accept = State()
    abonement_open = State()
    abonement_delete = State()
