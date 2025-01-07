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
    name = State()
    total_visits = State()
    description = State()
    join = State()
    accept = State()
    open = State()
    delete = State()
