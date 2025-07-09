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
    setting_sheet = client.open("jinro_game").worksheet("設定")
    role_sheet = client.open("jinro_game").worksheet("役職一覧")
    player_sheet = client.open("jinro_game").worksheet("プレイヤー一覧")

    # ①設定値取得
    num_werewolves = int(setting_sheet.acell("B1").value)
    num_third_party = int(setting_sheet.acell("B2").value)
    player_names = player_sheet.col_values(1)[1:]
    user_ids = player_sheet.col_values(2)[1:]
    total_players = len(player_names)
    num_humans = total_players - num_werewolves - num_third_party

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

    # ③役職をシャッフルして選出
    random.shuffle(roles['werewolf'])
    random.shuffle(roles['human'])
    random.shuffle(roles['third'])
    selected_roles = (
        roles['werewolf'][:num_werewolves] +
        roles['third'][:num_third_party] +
        roles['human'][:num_humans]
    )
    if len(selected_roles) != total_players:
        raise ValueError("役職の人数とプレイヤー人数が一致しません。")

    # ④割り当て
    random.shuffle(selected_roles)
    for idx, (name, uid) in enumerate(zip(player_names, user_ids)):
        role_id, role_name, role_desc, role_adv = selected_roles[idx]
        row = idx + 2  # 2行目から始まる
        player_sheet.update_cell(row, 4, role_id)
        player_sheet.update_cell(row, 5, role_name)
        player_sheet.update_cell(row, 6, role_desc)
        player_sheet.update_cell(row, 7, role_adv)

        # ⑤通知
        message = f"あなたの役職は「{role_name}」です。\n\n説明：{role_desc}\n\nアドバイス：{role_adv}"
        line_bot_api.push_message(uid, TextSendMessage(text=message))
