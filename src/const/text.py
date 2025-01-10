# -*- coding: utf-8 -*-

from typing import Optional
from aiogram.utils.formatting import (
    Text,
    Bold,
    Italic,
    Code,
    as_list,
    as_numbered_section,
    as_key_value,
)

# User types
user_types: dict[str, str] = {
    "unregistered": "Незарегистрированный пользователь",
    "registered": "Зарегистрированный пользователь",
    "developer": "Разработчик Телеграм-бота",
    "invite_adm": "Создатель приглашений",
    "fst_otm": "Администратор сайта ФСТ-ОТМ",
    "youtube_adm": "Администратор YouTube канала",
}

# Commands
cmd: dict[str, str] = {
    # Common buttons
    "exit": "🚪 Выход",
    # Main menu buttons
    "register": "🗝 Регистрация",
    "diag": "🛠 Диагностика",
    "invites": "🔗 Приглашения",
    "tables": "🗂 Генератор таблиц",
    "pictures": "🖼 Генератор картинок",
    "abonements": "🧗 Абонементы",
    # Register menu buttons
    "agree": "✅ Согласен",
    "disagree": "🚫 Не согласен",
    "share_phone": "☎ Поделиться",
    # Invites menu buttons
    "new_invite": "✨ Создать приглашение",
    "invite_history": "📅 История использования",
    # Generators menu buttons
    "as_picture": "🖼 Как картинку",
    "as_document": "💾 Как документ",
    "all": "*️⃣ Все",
    # Abonements menu buttons
    "my_abonements": "👤 Мои абонементы",
    "new_abonement": "✨ Новый абонемент",
    "join_abonement": "👥 Подключиться",
    "minus_visit": "👣 Списать посещение",
    "plus_visit": "👣 Записать посещение",
    "visits_history": "📅 История",
    "share": "📩 Поделиться",
    "edit": "✏ Изменить",
    "unlink": "✂️ Отвязать",
    "delete": "🗑 Удалить",
    "back": "⬅️ Назад",
    "prev": "⏪",
    "next": "⏩",
    "yes": "✅ Да",
    "no": "🚫 Нет",
    "txt_yes": "да",
    "txt_no": "нет",
}

# Messages
msg: dict[str, str] = {
    # General messages
    "hello_bot": "Вас приветствует бот Virtual Camp!",
    "main_menu": "Вы в главном меню",
    "help": "Отправьте /help для справки",
    "cancel": "Отправьте /cancel для выхода",
    "start": "Отправьте /start для начала работы",
    "no_proc": "Нет активных процессов",
    "unknown": "Сообщение не распознано",
    "failure": "Обнаружен сбой. Отправьте /start",
    "unavailable": "информация недоступна",
    "err_params": "Параметры распознать не удалось",
    "uuid_format": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    # Access control
    "no_access": "⛔️ Ошибка доступа. Возврат в главное меню",
    "access_list": "Список прав доступа",
    "m_yes": "✅ ",
    "m_no": "🚫 ",
    # Deep linking: Join abonement
    "ab_wrong_key": "Неверный ключ абонемента",
    "ab_wrong_owner": "Нельзя присоединиться к своему абонементу",
    "ab_err_joined": "Вы уже присоединены к этому абонементу",
    "ab_joined": "Вы успешно присоединились к абонементу",
    # Deep linking: Invite user
    "invite_err_key": "Неверный ключ приглашения",
    "invite_err_joined": "Вы уже имеете эти права",
    "invite_err_unknown": "Не получилось использовали приглашение",
    "invite_ok": "Вы успешно использовали приглашение",
    # Abonement: top-level menu
    "abonement_main": "Работа с абонементами. Выберите действие",
    "abonement_done": "Завершение работы с абонементами. Вы в главном меню",
    # Abonement: control menu
    "ab_title": "Абонемент",
    "ab_list_empty": "✨ Абонементов нет. Создайте или присоединитесь к существующему",
    "ab_list_count": "Доступно абонементов",
    "ab_list_my": "Мои абонементы",
    "ab_list_other": "Абонементы друзей",
    "ab_visit": "✅ Проход записан",
    "ab_no_visit": "❌ Проход не записан",
    "ab_empty": "На абонементе не осталось проходов",
    "ab_total_visits": "Всего посещений",
    "ab_unlim_visits": "без ограничений",
    "ab_key": "Ключ",
    "ab_link": "Ссылка для подключения:",
    "ab_ctrl_done": "Завершение работы с выбранным абонементом",
    "ab_ctrl_cancel": "/cancel - завершить работу с абонементами",
    "ab_unknown": "Неизвестная команда работы с абонементами, выход по /cancel",
    # Abonement: creation, editing, deleting
    "ab_edit_begin": "Редактирование абонемента",
    "ab_new_name": "Введите название абонемента",
    "ab_new_name_format": "Формат: <Куда> до <дата> на <Владелец>",
    "ab_new_wrong_name": "Неверное название абонемента",
    "ab_new_visits": "Введите количество посещений",
    "ab_zero_visits": "Если посещения не отслеживаются, введите 0",
    "ab_wrong_visits": "Неверное количество посещений",
    "ab_new_descr": "Введите описание абонемента",
    "ab_new_skip_descr": "/skip - не заполнять описание",
    "ab_new_wrong_descr": "Описание абонемента не подходит",
    "ab_new_done": "Новый абонемент создан",
    "ab_edit_done": "Абонемент изменён",
    "ab_not_del": "Абонемент не удален",
    # Abonement: join using menu
    "ab_join_begin": "Подключаем существующий абонемент",
    "ab_join_key": "Введите ключ абонемента",
    "ab_wrong_key_format": "Нужен ключ абонемента. Строка в формате:",
    "ab_join_not_exist": "Абонементов с таким ключом нет",
    "ab_join_own": "Вы не можете присоединиться к своему абонементу",
    "ab_join_already": "Вы уже присоединены к этому абонементу",
    "ab_join_deleted": "Этот абонемент был удалён",
    "ab_join_ask": "Вы хотите присоединиться к абонементу?",
    "ab_wrong_yes_no": "Неверный ответ. Только Да или Нет",
    "ab_join_ok": "Присоединились. Теперь абонемент в вашем списке",
    "ab_join_no": "Не присоединились к абонементу",
    "ab_failure_callback": "Неверный ключ абонемента. Введите /cancel для выхода",
    # Diag mode messages
    "diag_main": "Режим диагностики, выход по команде /cancel",
    "diag_info": "Информация о пользователе",
    "diag_any_msg": "Расшифровка, выход по команде /cancel",
    "diag_cancel": "Завершение диагностики. Вы в главном меню",
    # Registration mode messages
    "reg_main": "Регистрация нового пользователя",
    "reg_no_agree": "Нужно согласиться или отправить /cancel",
    "reg_no_phone": "Нужно по кнопке отправить контакт или /cancel",
    "reg_no_name": "Нужно отправить своё имя или /skip или /cancel",
    "reg_done": "Информация записана, спасибо!",
    "reg_unknown": "Неизвестная команда регистрации, выход по /cancel",
    # Table generation messages
    "table_main": "Генерация таблиц ФСТ-ОТМ. Выберите таблицу",
    "table_bad_task": "Задание неверное, выход по /cancel",
    "table_generating": "Генерация запущена, ждите...",
    "table_end": "Завершение генерации. Вы в главном меню",
    "table_unknown": "Неизвестная команда генерации, выход по /cancel",
    # Picture generation messages
    "pictures_main": "Генерация обложек YouTube. Выберите фоновую картинку",
    "pictures_bad_task": "Задание неверное, выход по /cancel",
    "pictures_output_mode": "Формат результата записан. Выберите фоновую картинку",
    "pictures_text": "Напишите текст надписи на картинке (1-2 строки)",
    "pictures_bad_text": "Нужен просто текст (1 или 2 строки) или /cancel",
    "pictures_generating": "Генерация картинки запущена, ждите...",
    "pictures_end": "Завершение генерации картинок. Вы в главном меню",
    "pictures_unknown": "Неизвестная команда генерации картинок, выход по /cancel",
    # Invites messages
    "invites_main": "Создание и просмотр приглашений. Выберите действие",
    "invites_end": "Завершение работы с приглашениями. Вы в главном меню",
    "invites_create": "Создание приглашений. Выберите целевую группу",
    "table_bad_group": "Группа неверная, выход по /cancel",
    "invites_new": "Создание приглашения для группы",
    "invites_history": "Просмотр истории приглашений",
    "invites_users": "Приглашённые пользователи",
    "invites_empty": "Приглашений нет",
    "invites_unknown": "Неизвестная команда приглашений, выход по /cancel",
}

# Help messages
help: dict[str, str] = {
    "all_cmd": "Общие команды",
    "all_start": "/start - запуск бота",
    "all_help": "/help - справка по текущему режиму",
    "all_cancel": "/cancel - выход из текущего режима",
    "my_cmd": "Вам доступны режимы",
    "my_diag": "/diag - диагностика бота",
    "my_register": "/register - регистрация пользователя",
    "my_invite": "/invite - создание и просмотр приглашений",
    "my_tables": "/tables - генерация таблиц ФСТ-ОТМ",
    "my_pictures": "/pictures - генерация обложек YouTube",
    "my_abonement": "/abonement - подсчет посещений абонементов",
    "diag_cmd": "Режим диагностики",
    "diag_info": "/info - информация о пользователе",
    "reg_cmd": "Режим регистрации",
    "reg_cancel": "/cancel - отменить регистрацию",
    "invites_cmd": "Режим работы с приглашениями",
    "invites_cancel": "/cancel - завершить работу с приглашениями",
    "table_cmd": "Режим генерации таблиц ФСТ-ОТМ",
    "pictures_cmd": "Режим генерации обложек для YouTube",
    "pictures_cancel": "/cancel - отменить генерацию обложек",
    "ab_cmd": "Режим работы с абонементами",
    "ab_cancel": "/cancel - завершить работу с абонементами",
    "ab_ctrl_cmd": "Режим управления абонементами",
    "ab_ctrl_cancel": "/cancel - завершить работу с выбранным абонементом",
}

# Regular expression for UUID
re_uuid: str = r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$"

# Date format for Abonements and Visits
ab_date_fmt: str = "%d.%m.%Y %H:%M"

# Register new user: begin
reg_main: Text = as_list(
    Bold("Регистрация нового пользователя"),
    "",
    as_numbered_section(
        "Нужно будет ввести:",
        "Ваш номер телефона, он публиковаться не будет",
        "Ваше имя, которое будет видно другим пользователям",
    ),
    "",
    "В любой момент можно отказаться, отправив команду /cancel",
    "",
    "Продолжая, Вы соглашаетесь на обработку предоставленных Вами персональных данных.",
)

# Register new user: ask phone
reg_phone: Text = as_list(
    Bold("Номер телефона"),
    "",
    "Пожалуйста, подтвердите свой номер телефона для завершения регистрации",
    "",
    Bold("Для этого нажмите кнопку ниже"),
)


# Register new user: ask name
def reg_name(currentName: Optional[str]) -> Text:
    res = as_list(
        Bold("Введите имя"),
        "Это имя будет видно другим пользователям.",
        as_key_value("Текущее имя", currentName) if currentName else "",
        "Чтобы оставить текущее имя без изменений, отправьте /skip",
    )
    return res


# Register new user: end
reg_end: Text = as_list("Завершение регистрации.", "", "Вы в главном меню")


# Abonement: info
def ab_info(
    name: str,
    description: Optional[str],
    total_visits: int,
    visits_count: int,
    my_visits_count: int,
) -> Text:
    res = as_list(
        "Выбран абонемент",
        Bold(name),
        *[Italic(description), ""] if description else [""],
        (
            f"На {total_visits} посещений"
            if total_visits != 0
            else "Без ограничения посещений"
        ),
        as_key_value("Совершено проходов", visits_count),
        as_key_value("Из них мои проходы", my_visits_count),
        *(
            [
                as_key_value(
                    "Осталось проходов",
                    total_visits - visits_count,
                ),
                "",
            ]
            if total_visits != 0
            else [""]
        ),
        "Выберите действие",
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


# Abonement: ask to delete or unlink
def ab_del_ask(user_is_owner: bool, name: str) -> Text:
    res = as_list(
        ("🗑 Удаление абонемента" if user_is_owner else "⚠️ Отключение абонемента"),
        as_key_value("Название", name),
        "",
        Text(
            "Отправьте ",
            Bold("да"),
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
