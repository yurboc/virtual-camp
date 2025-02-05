# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Optional
from aiogram.utils.formatting import Text, Bold, Italic, Code
from aiogram.utils.formatting import as_list, as_numbered_section, as_key_value
from const.text import cmd, msg
from const.formats import date_fmt


# Register new user: begin
def reg_main() -> Text:
    return as_list(
        Bold("Регистрация нового пользователя"),
        "",
        as_numbered_section(
            "Нужно будет:",
            "Поделиться контактом",
            "Подтвердить своё имя",
        ),
        "",
        "В любой момент их можно изменить.",
        "Продолжаем?",
    )


# Register new user: begin edit
def reg_main_edit() -> Text:
    return as_list(
        Bold("Обновление данных пользователя"),
        "",
        as_numbered_section(
            "Можно изменить:",
            "Номер телефона (он будет скрыт)",
            "Своё имя (будет видно пользователям)",
        ),
        "",
        msg["cancel"],
    )


# Register new user: ask phone
def reg_phone() -> Text:
    return as_list(
        Bold("Отправьте свой номер телефона"),
        "",
        "Пожалуйста, не отправляйте его текстом!",
        "Надо поделиться своим контактом.",
        "",
        Bold("Для этого нажмите кнопку ниже"),
    )


# Register new user: ask name
def reg_name(currentName: Optional[str]) -> Text:
    res = as_list(
        Bold("Введите имя"),
        "Это имя будет видно другим пользователям.",
        as_key_value("Текущее имя", currentName) if currentName else "",
        msg["skip"],
    )
    return res


# Register new user: end
def reg_end() -> Text:
    return as_list("Завершение регистрации.", "", "Вы в главном меню")


# Abonement: info
def ab_info(
    name: str,
    description: Optional[str],
    expiry_date: Optional[datetime],
    total_visits: int,
    visits_count: int,
    my_visits_count: int,
    notify: Optional[str],
) -> Text:
    days = expiry_date.date() - datetime.now().date() if expiry_date else None
    days_left = days.days + 1 if days is not None else None
    days_left_str = ""
    if days_left is not None:
        if days_left > 1:
            days_left_str = f"Дней осталось: {days_left}"
        elif days_left == 1:
            days_left_str = "Сегодня последний день"
        else:
            days_left_str = "Просроченный"
    res = as_list(
        "Выбран абонемент",
        Bold(name),
        *[Italic(description), ""] if description else [""],
        (
            f"До {expiry_date.strftime(date_fmt)}"
            if expiry_date
            else Text(msg["ab_expiry_date_label"], " ", msg["ab_unlim"])
        ),
        *([days_left_str, ""] if days_left_str else [""]),
        (
            f"На {total_visits} посещений"
            if total_visits != 0
            else Text(msg["ab_visits_label"], " ", msg["ab_unlim"])
        ),
        as_key_value("Совершено проходов", visits_count),
        as_key_value("Из них мои проходы", my_visits_count),
        *(
            [
                as_key_value(
                    msg["ab_left_visits"],
                    total_visits - visits_count,
                ),
                "",
            ]
            if total_visits != 0
            else [""]
        ),
        msg["notify_on"] if notify and notify == "all" else msg["notify_off"],
    )
    return res


# Abonement: page with visits
def ab_page(offset: int, total: int, visits: int) -> Text:
    res = (
        Text(
            "📈 Проходы с ",
            Bold(offset + 1),
            " по ",
            Bold(offset + visits),
            " из ",
            Bold(total),
        )
        if total > 0
        else Text("✨ Проходов пока не было.")
    )
    return res


# Abonement Visit: ask to delete or unlink
def ab_del_visit_ask() -> Text:
    res = as_list(
        Text("Отправьте ", Bold(cmd["txt_yes"]), " чтобы удалить посещение"),
        "",
        "/cancel - отменить удаление посещения",
    )
    return res


# Abonement: ask to delete or unlink
def ab_del_ask(user_is_owner: bool, name: str) -> Text:
    res = as_list(
        ("🗑 Удаление абонемента" if user_is_owner else "⚠️ Отключение абонемента"),
        as_key_value(msg["name"], name),
        "",
        Text(
            "Отправьте ",
            Bold(cmd["txt_yes"]),
            " в ответ, если хотите ",
            (Bold("удалить") if user_is_owner else Bold("отключить")),
            " его",
        ),
        "",
        "/cancel - отменить удаление абонемента",
    )
    return res


# Abonement: delete or unlink result
def ab_del(
    operation: Optional[str], result: bool, abonement_key: Optional[str]
) -> Text:
    res = as_list(
        Text(
            "Абонемент",
            Bold(" не") if not result else "",
            " удален" if operation and operation == "delete" else " отключен",
        ),
        "",
        as_key_value(
            "Ключ",
            Code(abonement_key) if abonement_key else Italic("неизвестен"),
        ),
    )
    return res
