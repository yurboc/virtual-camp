# -*- coding: utf-8 -*-

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
    "share_phone": "☎ Отправить телефон",
    # Invites menu buttons
    "new_invite": "✨ Создать приглашение",
    "invite_history": "📅 История использования",
    # Generators menu buttons
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
    "notify_on": "✅ Уведомлять",
    "notify_off": "❎ Уведомлять",
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
    "main_menu_exit": "Вы вышли в главное меню",
    "err_start_token": "Обработка ключа в сообщении не поддерживается",
    "err_params": "Параметры распознать не удалось",
    "no_proc": "Нет активных процессов",
    "unknown": "Сообщение не распознано",
    "none": "отсутствует",
    "unavailable": "информация недоступна",
    "example": "Пример",
    "current": "Текущее",
    "name": "Название",
    "done": "✅ Выполнено",
    "not_done": "❎ Не выполнено",
    "date_format": "ДД.ММ.ГГГГ",
    "date_time_format": "ДД.ММ.ГГГГ ЧЧ:ММ",
    "uuid_format": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    # General help
    "start": "/start - начало работы",
    "help": "/help - показать справку",
    "skip": "/skip - оставить без изменений",
    "empty": "/empty - оставить пустым",
    "cancel": "/cancel - отменить",
    # Access control
    "no_access": "⛔️ Ошибка доступа. Возврат в главное меню",
    "access_list": "Список прав доступа",
    "m_yes": "✅ ",
    "m_no": "🚫 ",
    # Deep linking
    "linking_main": "Разбираем ссылку, ждите...",
    # Deep linking: Join abonement
    "ab_wrong_key": "Неверный ключ абонемента",
    "ab_wrong_owner": "Нельзя присоединиться к своему абонементу",
    "ab_err_joined": "Вы уже присоединены к этому абонементу",
    "ab_joined": "Вы успешно присоединились к абонементу",
    "ab_err_unknown": "Не получилось присоединиться к абонементу",
    # Deep linking: Invite user
    "invite_err_key": "Неверный ключ приглашения",
    "invite_err_joined": "Вы уже имеете эти права",
    "invite_err_unknown": "Не получилось использовали приглашение",
    "invite_ok": "Приглашение принято",
    # Abonement: top-level menu
    "abonement_main": "Работа с абонементами. Выберите действие",
    "abonement_done": "Завершение работы с абонементами. Вы в главном меню",
    # Abonement: control menu
    "ab_title": "Абонемент",
    "ab_list_empty": "✨ Абонементов нет. Создайте или присоединитесь к существующему",
    "ab_list_count": "Доступно абонементов",
    "ab_list_my": "Мои абонементы",
    "ab_list_other": "Абонементы друзей",
    "ab_visit_ask": "Проход по абонементу:",
    "ab_visit_confirm": "Подтвердить проход?",
    "ab_visit": "✅ Проход записан",
    "ab_no_visit": "❌ Проход не записан",
    "notify_on": "🔔 Уведомления включены",
    "notify_off": "🔕 Уведомления выключены",
    "ab_empty": "На абонементе не осталось проходов",
    "ab_left_visits": "Осталось проходов",
    "ab_total_visits": "Всего проходов",
    "ab_unlim": "без ограничений",
    "ab_key": "Ключ",
    "ab_link": "Ссылка для подключения:",
    "ab_sheets": "Ссылка на Google Sheets:",
    "ab_ctrl_done": "Завершение работы с выбранным абонементом",
    "ab_ctrl_cancel": "/cancel - завершить работу с абонементами",
    "ab_unknown": "Неизвестная команда работы с абонементами",
    # Abonement: creation, editing, deleting
    "ab_edit_begin": "Редактирование абонемента",
    "ab_name_label": "Название абонемента:",
    "ab_new_name": "Введите название абонемента",
    "ab_edit_name": "Введите новое название абонемента",
    "ab_new_name_format": "Рекомендуемый формат: <Куда> на <Владелец>",
    "ab_new_wrong_name": "Неверное название абонемента",
    "ab_visits_label": "Количество посещений:",
    "ab_new_visits": "Введите количество посещений",
    "ab_zero_visits": "Чтобы не отслеживать посещения введите 0 или /empty",
    "ab_wrong_visits": "Неверное количество посещений",
    "ab_expiry_date_label": "Срок действия:",
    "ab_new_expiry_date": "Введите срок действия абонемента в формате",
    "ab_new_no_expiry_date": "/empty - без ограничений по сроку",
    "ab_wrong_expiry_date": "Неверный срок действия абонемента",
    "ab_descr_label": "Описание:",
    "ab_new_descr": "Введите описание абонемента",
    "ab_new_empty_descr": "/empty - без описания",
    "ab_new_wrong_descr": "Описание абонемента не подходит",
    "ab_new_done": "Новый абонемент создан",
    "ab_edit_done": "Абонемент изменён",
    "ab_not_del": "Абонемент не удален",
    "ab_visit_edit": "📝 Изменение даты посещения",
    "ab_visit_delete": "⚠️ Удаление посещения",
    "ab_visit_select": "Нажмите на кнопку с выбранным посещением",
    "ab_visit_not_owner": "Вы не владелец абонемента и посещение не ваше",
    "ab_visit_date": "Текущая дата",
    "ab_visit_new_date": "Задайте новую дату в формате",
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
    # Abonement notifications
    "ab_notify_visit_new": "❇️ Посещение по абонементу",
    "ab_notify_visit_edit": "📝 Изменение даты посещения",
    "ab_notify_visit_delete": "⚠️ Удаление посещения",
    "ab_notify_date": "📅 Дата",
    "ab_notify_visitor": "🧗‍♂️ Посетитель",
    "ab_notify_actor": "👨‍💻 Автор",
    # Diag mode messages
    "diag_main": "Режим диагностики включен",
    "diag_sys_info": "Информация о системе",
    "diag_version": "Версия",
    "diag_state": "Режим",
    "diag_time": "Время",
    "diag_bot": "Бот",
    "diag_bot_info": "Информация о пользователе в aiogram",
    "diag_db_info": "Информация о пользователе в БД",
    "diag_rabbitmq_info": "Информация об очередях",
    "diag_any_msg": "Расшифровка",
    "diag_cancel": "Завершение диагностики. Вы в главном меню",
    # Registration mode messages
    "reg_main": "Регистрация нового пользователя",
    "reg_no_agree": "Нужно согласиться или отправить /cancel",
    "reg_no_phone": "Нужно по кнопке отправить контакт или /cancel",
    "reg_no_name": "Нужно отправить своё имя или /skip или /cancel",
    "reg_done": "Информация записана, спасибо!",
    "reg_unknown": "Неизвестная команда регистрации",
    # Table generation messages
    "table_main": "Генерация таблиц ФСТ-ОТМ. Выберите таблицу",
    "table_bad_task": "Задание неверное",
    "table_generating": "Генерация запущена, ждите...",
    "table_end": "Завершение генерации. Вы в главном меню",
    "table_unknown": "Неизвестная команда генерации",
    # Picture generation messages
    "pictures_main": "Генерация обложек YouTube. Выберите фоновую картинку",
    "pictures_bad_task": "Задание неверное",
    "pictures_output_type": "Формат результата",
    "pictures_as_image": "формат 🖼 картинка",
    "pictures_as_document": "формат 💾 документ",
    "pictures_output_mode": "Формат результата записан. Выберите фоновую картинку",
    "pictures_text": "Напишите текст надписи на картинке (1-2 строки)",
    "pictures_bad_text": "Нужен просто текст (1 или 2 строки) или /cancel",
    "pictures_generating": "Генерация картинки запущена, ждите...",
    "pictures_end": "Завершение генерации картинок. Вы в главном меню",
    "pictures_unknown": "Неизвестная команда генерации картинок",
    # Invites messages
    "invites_main": "Создание и просмотр приглашений. Выберите действие",
    "invites_end": "Завершение работы с приглашениями. Вы в главном меню",
    "invites_create": "Создание приглашений. Выберите целевую группу",
    "table_bad_group": "Группа неверная",
    "invites_new": "Создание приглашения для группы",
    "invites_history": "Просмотр истории приглашений",
    "invites_users": "Приглашённые пользователи",
    "invites_empty": "Приглашений нет",
    "invites_unknown": "Неизвестная команда приглашений",
}

# Help messages
help: dict[str, str] = {
    "all_group": "Общие команды",
    "all_start": "/start - запуск бота",
    "all_help": "/help - справка по текущему режиму",
    "all_cancel": "/cancel - выход из текущего режима",
    "my_group": "Вам доступны режимы",
    "my_diag": "/diag - диагностика бота",
    "my_info": "/info - текущее состояние",
    "my_register": "/register - регистрация пользователя",
    "my_register_edit": "/register - изменение данных пользователя",
    "my_invite": "/invite - создание и просмотр приглашений",
    "my_tables": "/tables - генерация таблиц ФСТ-ОТМ",
    "my_pictures": "/pictures - генерация обложек YouTube",
    "my_abonement": "/abonement - подсчет посещений абонементов",
    "owner_group": "Информация о боте",
    "owner_info": "Вопросы пишите @botsev_yury",
    "owner_github": "Код доступен на GitHub: ",
    "owner_project": "virtual-camp",
    "owner_link": "https://github.com/yurboc/virtual-camp",
    "diag_cmd": "Режим диагностики",
    "diag_info": "/info - информация о пользователе",
    "reg_cmd": "Режим регистрации",
    "reg_cancel": "/cancel - отменить регистрацию",
    "invites_cmd": "Режим работы с приглашениями",
    "invites_cancel": "/cancel - завершить работу с приглашениями",
    "table_cmd": "Режим генерации таблиц ФСТ-ОТМ",
    "pictures_cmd": "Режим генерации обложек для YouTube",
    "pictures_as_image": "/image - генерация в формате картинки",
    "pictures_as_document": "/document - генерация в формате документа",
    "pictures_cancel": "/cancel - отменить генерацию обложек",
    "ab_cmd": "Режим работы с абонементами",
    "ab_cancel": "/cancel - завершить работу с абонементами",
    "ab_ctrl_cmd": "Режим управления абонементами",
    "ab_ctrl_cancel": "/cancel - завершить работу с выбранным абонементом",
}
