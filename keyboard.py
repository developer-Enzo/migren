from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup

from enum import Enum


class MainBtn(Enum):
    add_note = "Добавить запись"
    stats = "Статистика"
    
    @staticmethod
    def build_keyboard() -> ReplyKeyboardMarkup:
        builder = ReplyKeyboardBuilder()
        
        for btn in MainBtn:
            builder.button(text=btn.value)
    
        return builder.adjust(2).as_markup(resize_keyboard=True)


class YesNoBtn(Enum):
    yes = "Да"
    no = "Нет"
    
    @staticmethod
    def build_keyboard() -> ReplyKeyboardMarkup:
        builder = ReplyKeyboardBuilder()
        
        for btn in YesNoBtn:
            builder.button(text=btn.value)
    
        return builder.adjust(2).as_markup(resize_keyboard=True)
    
    
def defer_notification_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Отложить", callback_data="defer_notification")
    return builder.as_markup()


def change_notification_date_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Изменить время уведомлений", callback_data="change_notification_date")
    return builder.as_markup()


def medicine_list_keyboard(medicine_list: list) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
        
    for name in medicine_list:
        builder.button(text=name)

    return builder.adjust(1).as_markup(resize_keyboard=True)