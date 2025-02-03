from aiogram.utils.formatting import Text, Bold, as_list
from const.text import help


def top_level_help(user_type: list[str] = ["unknown"]) -> Text:
    tokens: list[Text] = []
    # Common commands
    tokens.append(Bold(help["all_group"]))
    tokens.append(Text(help["all_start"]))
    tokens.append(Text(help["all_help"]))
    tokens.append(Text(help["all_cancel"]))
    tokens.append(Bold(help["my_group"]))
    # Commands with limited access
    if "registered" in user_type:
        tokens.append(Text(help["my_register_edit"]))
    else:
        tokens.append(Text(help["my_register"]))
    if "developer" in user_type:
        tokens.append(Text(help["my_diag"]))
        tokens.append(Text(help["my_info"]))
    if "invite_adm" in user_type:
        tokens.append(Text(help["my_invite"]))
    if "fst_otm" in user_type:
        tokens.append(Text(help["my_tables"]))
    if "youtube_adm" in user_type:
        tokens.append(Text(help["my_pictures"]))
    # Commands without access limitation
    tokens.append(Text(help["my_abonement"]))
    # Bot owner information
    tokens.append(Bold(help["owner_group"]))
    tokens.append(Text(help["owner_info"]))
    tokens.append(Text(help["owner_github"]))
    tokens.append(Text(help["owner_link"]))
    # Combine help in one list
    res = as_list(*tokens)
    return res
