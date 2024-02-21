import asyncio
import logging
import sys
import time

from os import getenv

from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from dotenv import load_dotenv

from database import Database
from states import RequestDateState, AddNoneState
from keyboard import MainBtn, YesNoBtn, defer_notification_keyboard, change_notification_date_keyboard, medicine_list_keyboard
from utils import get_notification_unix_date, get_medicine_info, is_today, get_user_medicine_list


load_dotenv()

TOKEN = getenv("BOT_TOKEN")
NOTIFICATION_SNOOZE_TIME = int(getenv("NOTIFICATION_SNOOZE_TIME"))

dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: Message, db: Database, state: FSMContext) -> None:
    await message.answer(f"Добро пожаловать, {message.from_user.first_name}!", reply_markup=MainBtn.build_keyboard())
    
    user = await db.get_user(message.from_user.id)
    
    if user is None:
        await db.insert_user(message.from_user.id)
        await state.set_state(RequestDateState.date)
        await message.answer("Введите время в которое вы хотите получать уведомления: \n\nСпойлер:\nФормат: ЧАС:МИНУТА")


@dp.message(RequestDateState.date, F.text.regexp(r"\d\d:\d\d") | F.text.regexp(r"\d:\d\d"))
async def handler(message: types.Message, db: Database, state: FSMContext) -> None:
    notification_time = message.text
    
    await db.update_notification_time(message.from_user.id, notification_time)
    await state.clear()
    
    date = get_notification_unix_date(notification_time)
    await db.insert_notification(message.from_user.id, date)
    
    await message.answer(f"Время уведомлений установлено - {notification_time}")


@dp.message(RequestDateState.date)
async def handler(message: types.Message, db: Database, state: FSMContext) -> None:
    await message.answer("Неверный формат времени, пожалуйста укажите время в формате hh:mm")


@dp.message(F.text == MainBtn.add_note.value)
async def handler(message: types.Message, db: Database, state: FSMContext) -> None:
    await state.set_state(AddNoneState.headache)
    await message.answer("у вас сегодня болела голова?", reply_markup=YesNoBtn.build_keyboard())


@dp.message(AddNoneState.headache)
async def handler(message: types.Message, db: Database, state: FSMContext) -> None:
    answer = message.text
    
    if answer == YesNoBtn.yes.value:
        await state.update_data(headache=True, medicine_list=[])
        await state.set_state(AddNoneState.medicine)
        
        await message.answer("принимали какие-либо лекарства?")
    elif answer == YesNoBtn.no.value:
        await state.clear()
        await db.insert_note(message.from_user.id, False, False, None)
        
        await message.answer("Запись успешно добавлена!", reply_markup=MainBtn.build_keyboard())
    else:
        await message.answer("Дайте ответ: Да/Нет")


@dp.message(AddNoneState.medicine)
async def handler(message: types.Message, db: Database, state: FSMContext) -> None:
    answer = message.text
    
    if answer == YesNoBtn.yes.value:
        await state.set_state(AddNoneState.medicine_name)
        medicine_list = await get_user_medicine_list(db, message.from_user.id)
        await message.answer("Введите название лекарства", reply_markup=medicine_list_keyboard(medicine_list))
    elif answer == YesNoBtn.no.value:
        data = await state.get_data()
        await state.clear()
    
        await db.insert_note(message.from_user.id, data["headache"], False, None)
        
        await message.answer("Запись успешно добавлена!", reply_markup=MainBtn.build_keyboard())
    else:
        await message.answer("Дайте ответ: Да/Нет")


@dp.message(AddNoneState.medicine_name)
async def handler(message: types.Message, db: Database, state: FSMContext) -> None:
    medicine_name = message.text
    
    await state.update_data(medicine_name=medicine_name)
    await state.set_state(AddNoneState.helped)
    
    await message.answer("Помогло?", reply_markup=YesNoBtn.build_keyboard())

    
@dp.message(AddNoneState.helped)
async def handler(message: types.Message, db: Database, state: FSMContext) -> None:
    answer = message.text
    
    if answer == YesNoBtn.yes.value:
        helped = True
    elif answer == YesNoBtn.no.value:
        helped = False
    else:
        await message.answer("Дайте ответ: Да/Нет")
        return
    
    data = await state.get_data()
    medicine_list: list = data["medicine_list"]
    medicine_list.append({"name": data["medicine_name"], "helped": helped})
    
    await state.update_data(medicine_list=medicine_list)
    await state.set_state(AddNoneState.other_medicine)
    
    await message.answer("употребляли другие лекарства?")


@dp.message(AddNoneState.other_medicine)
async def handler(message: types.Message, db: Database, state: FSMContext) -> None:
    answer = message.text

    if answer == YesNoBtn.yes.value:
        await state.set_state(AddNoneState.medicine_name)
        medicine_list = await get_user_medicine_list(db, message.from_user.id)
        await message.answer("Введите название лекарства", reply_markup=medicine_list_keyboard(medicine_list))
    elif answer == YesNoBtn.no.value:
        data = await state.get_data()
        await state.clear()
        
        user_notification = await db.get_user_notification(message.from_user.id)
        user = await db.get_user(message.from_user.id)

        await db.insert_note(message.from_user.id, data["headache"], True, data["medicine_list"])
        
        if is_today(int(user_notification[1])) or user_notification is None:
            date = get_notification_unix_date(user[1]) + 86400
            await db.insert_notification(message.from_user.id, date)
        
        await message.answer("Запись успешно добавлена!", reply_markup=MainBtn.build_keyboard())
    else:
        await message.answer("Дайте ответ: Да/Нет")


@dp.message(F.text == MainBtn.stats.value)
async def handler(message: types.Message, db: Database, state: FSMContext) -> None:
    user_notes = await db.get_user_notes(message.from_user.id)
    user = await db.get_user(message.from_user.id)
    
    info = get_medicine_info(user_notes)
    
    text = f"""
Приветствую, {message.from_user.first_name}!

Время отправки уведомления: {user[1]}
Добавлена ли сегодня запись: {info["post_added_today"]}

Вот ваша статистика за

Неделю: 
Дней с головной болью: {info["week_number_headaches"]}
Список использованных лекарств: 
{info["week_med_list_text"]}

Месяц:
Дней с головной болью: {info["month_number_headaches"]}
Список использованных лекарств: 
{info["month_med_list_text"]}
    """
    await message.answer(text, reply_markup=change_notification_date_keyboard())


@dp.callback_query(F.data == "change_notification_date")
async def change_notification_date_handler(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(RequestDateState.date)
    await call.message.edit_text("Введите время(в формете час:минута) в которое вы хотите получать уведомления:\n\nнапример 19:00")


@dp.callback_query(F.data == "defer_notification")
async def defer_notification_handler(call: CallbackQuery, db: Database) -> None:
    await db.insert_notification(
        call.from_user.id, 
        time.time() + NOTIFICATION_SNOOZE_TIME
    )
    await call.message.edit_text(f"Мы уведомим вас через {NOTIFICATION_SNOOZE_TIME / 60} минут")


async def notification_handler(db: Database) -> None:
    print("Start notification handler")
    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
    
    while True:
        notifications = await db.get_notifications()
        current_time = time.time()
        
        for user_id, date in notifications:
            if int(date) > current_time:
                continue
            
            try:
                await bot.send_message(
                    chat_id=user_id, 
                    text="Пришло время добавить сегодняшнюю запись", 
                    reply_markup=defer_notification_keyboard()
                )
                user = await db.get_user(user_id)
                await db.insert_notification(
                    user_id, 
                    get_notification_unix_date(user[1])
                )
            except Exception as e:
                print(e)
                await db.delete_notification(user_id)
        
        
        await asyncio.sleep(60)

    
async def main() -> None:
    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
    
    db = Database("database.db")
    await db.connect()
    await db.create_tables()
    
    loop = asyncio.get_event_loop()
    loop.create_task(notification_handler(db))
    
    await dp.start_polling(bot, db=db)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
