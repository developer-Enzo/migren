from aiogram.fsm.state import StatesGroup, State


class RequestDateState(StatesGroup):
    date = State()
    
    
class AddNoneState(StatesGroup):
    headache = State()
    medicine = State()
    medicine_name = State()
    helped = State()
    other_medicine = State()
