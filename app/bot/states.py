from aiogram.fsm.state import State, StatesGroup

class ScreeningStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_q1 = State()
    waiting_for_q2 = State()
    waiting_for_q3 = State()
    waiting_for_q4 = State()
    waiting_for_q5 = State()
    waiting_for_q6 = State()
    waiting_for_link = State()
