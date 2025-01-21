from aiogram.fsm.state import State, StatesGroup


# FSM Main group
class MainGroup(StatesGroup):
    diag_mode = State()
    generator_mode = State()
    pictures_mode = State()
    abonement_mode = State()


# FSM Invites group
class InvitesGroup(MainGroup):
    begin = State()
    create = State()
    history = State()
    done = State()


# FSM Pictures group
class PicturesGroup(MainGroup):
    background = State()
    text = State()


# FSM Register group
class RegisterGroup(MainGroup):
    agreement = State()
    phone = State()
    name = State()
    finish = State()


# FSM Abonement group
class AbonementGroup(MainGroup):
    name = State()
    total_visits = State()
    expiry_date = State()
    description = State()
    join = State()
    accept = State()
    open = State()
    visit = State()
    visit_edit = State()
    visit_delete = State()
    visit_edit_confirm = State()
    visit_delete_confirm = State()
    delete = State()
