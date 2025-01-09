from aiogram.utils.formatting import Text, Bold, as_list
from const.text import help


def generate_top_level_help(user_type: list[str] = ["unknown"]) -> Text:
    tokens: list[Text] = []
    tokens.append(Bold(help["all_cmd"]))
    tokens.append(Text(help["all_start"]))
    tokens.append(Text(help["all_help"]))
    tokens.append(Text(help["all_cancel"]))
    tokens.append(Bold(help["my_cmd"]))
    tokens.append(Text(help["my_diag"]))
    tokens.append(Text(help["my_register"]))
    if "invite_adm" in user_type:
        tokens.append(Text(help["my_invite"]))
    if "fst_otm" in user_type:
        tokens.append(Text(help["my_tables"]))
    if "youtube_adm" in user_type:
        tokens.append(Text(help["my_pictures"]))
    tokens.append(Text(help["my_abonement"]))

    # Combine help in one list
    res = as_list(*tokens)
    return res
