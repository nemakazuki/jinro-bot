import os
import json
import gspread
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials

# Google Sheets クライアント接続
def connect_client():
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    creds_dict = json.loads(os.environ.get('GOOGLE_CREDENTIALS'))
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

# プレイヤー一覧シートへ接続（必要なら残してもOK）
def connect_sheet():
    client = connect_client()
    sheet = client.open("jinro_game").worksheet("プレイヤー一覧")
    return sheet

# 状態シートの夜モード取得
def get_night_mode():
    client = connect_client()
    sheet = client.open("jinro_game").worksheet("状態")
    return sheet.acell("A1").value or "OFF"

# 状態シートの夜モード設定
def set_night_mode(mode):
    client = connect_client()
    sheet = client.open("jinro_game").worksheet("状態")
    sheet.update_acell("A1", mode)

# プレイヤー登録処理（プレイヤー一覧シート）
def register_player(name, user_id):
    sheet = connect_sheet()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    sheet.append_row([name, user_id, now])

# 夜の行動を夜の行動シートに記録
def record_night_action(user_id, name, action):
    client = connect_client()
    night_sheet = client.open("jinro_game").worksheet("夜の行動")
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    night_sheet.append_row([now, user_id, name, action])

# user_id から名前を取得（プレイヤー一覧シート）
def get_name_by_user_id(user_id):
    client = connect_client()
    player_sheet = client.open("jinro_game").worksheet("プレイヤー一覧")
    user_ids = player_sheet.col_values(2)[1:]  # ヘッダー除く
    names = player_sheet.col_values(1)[1:]
    for uid, name in zip(user_ids, names):
        if uid == user_id:
            return name
    return None


import random

def assign_roles_and_notify(line_bot_api):
    client = connect_client()
    player_sheet = client.open("jinro_game").worksheet("プレイヤー一覧")
    role_sheet = client.open("jinro_game").worksheet("役職一覧")
    setting_sheet = client.open("jinro_game").worksheet("設定")

    # ①プレイヤー一覧を取得
    names = player_sheet.col_values(1)[1:]
    user_ids = player_sheet.col_values(2)[1:]
    player_count = len(names)

    # ②役職一覧を取得・分類
    role_numbers = role_sheet.col_values(1)[1:]

    roles = {
        'werewolf': [],
        'human': [],
        'third': []
    }

    for i in range(1, len(role_numbers)+1):
        role_id = int(role_sheet.cell(i+1, 1).value)
        role_name = role_sheet.cell(i+1, 2).value
        role_desc = role_sheet.cell(i+1, 3).value
        role_adv = role_sheet.cell(i+1, 4).value
        role_data = (role_id, role_name, role_desc, role_adv)
        if 100 <= role_id < 200:
            roles['werewolf'].append(role_data)
        elif 200 <= role_id < 300:
            roles['human'].append(role_data)
        elif 300 <= role_id < 400:
            roles['third'].append(role_data)

    # ③設定から人数取得
    num_werewolf = int(setting_sheet.acell("B1").value)
    num_third = int(setting_sheet.acell("B2").value)
    num_human = player_count - num_werewolf - num_third

    # ④役職割り当て
    import random
    random.shuffle(roles['werewolf'])
    random.shuffle(roles['human'])
    random.shuffle(roles['third'])

    assigned_roles = (
        roles['werewolf'][:num_werewolf] +
        roles['human'][:num_human] +
        roles['third'][:num_third]
    )

    random.shuffle(assigned_roles)

    for i, (user_id, name) in enumerate(zip(user_ids, names)):
        role_id, role_name, role_desc, role_adv = assigned_roles[i]
        # シートに書き込み
        player_sheet.update_cell(i+2, 4, role_id)
        player_sheet.update_cell(i+2, 5, role_name)
        player_sheet.update_cell(i+2, 6, role_desc)
        player_sheet.update_cell(i+2, 7, role_adv)
        # LINE通知
        message = (
            f"あなたの役職は「{role_name}」です。\n\n"
            f"説明：{role_desc}\n\n"
            f"アドバイス：{role_adv}"
        )
        line_bot_api.push_message(user_id, TextSendMessage(text=message))
