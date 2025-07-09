import os
import json
import gspread
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from linebot.models import TextSendMessage

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
    workbook = client.open("jinro_game")
    player_sheet = workbook.worksheet("プレイヤー一覧")
    role_sheet = workbook.worksheet("役職一覧")
    setting_sheet = workbook.worksheet("設定")

    # ① プレイヤー一覧をまとめて取得
    player_data = player_sheet.get_all_values()[1:]  # ヘッダー除く
    names = [row[0] for row in player_data]
    user_ids = [row[1] for row in player_data]
    player_count = len(names)

    # ② 役職一覧を一括取得
    role_data_all = role_sheet.get_all_values()[1:]  # ヘッダー除く
    roles = {'werewolf': [], 'human': [], 'third': []}
    for row in role_data_all:
        role_id = int(row[0])
        role = (role_id, row[1], row[2], row[3])
        if 100 <= role_id < 200:
            roles['werewolf'].append(role)
        elif 200 <= role_id < 300:
            roles['human'].append(role)
        elif 300 <= role_id < 400:
            roles['third'].append(role)

    # ③設定から人数取得（get_all_valuesを使って安全に取得）
    def parse_int_or_zero(cell_value):
        try:
            if not cell_value or cell_value.strip() == '':
                return 0
            return int(cell_value)
        except (ValueError, TypeError):
            return 0

    print("B1 raw value:", setting_sheet.acell("B1").value)
    print("B2 raw value:", setting_sheet.acell("B2").value)
    num_werewolf = parse_int_or_zero(setting_sheet.acell("B1").value)
    num_third = parse_int_or_zero(setting_sheet.acell("B2").value)
    num_human = player_count - num_werewolf - num_third  # ← ★ これを追加！


    # ④ 役職をランダムに割り当て
    random.shuffle(roles['werewolf'])
    random.shuffle(roles['human'])
    random.shuffle(roles['third'])

    assigned_roles = (
        roles['werewolf'][:num_werewolf] +
        roles['human'][:num_human] +
        roles['third'][:num_third]
    )
    random.shuffle(assigned_roles)

    # ⑤ 一括で書き込み準備
    updates = []
    for i, (user_id, name) in enumerate(zip(user_ids, names)):
        role_id, role_name, role_desc, role_adv = assigned_roles[i]
        updates.append({
            "row": i + 2,
            "values": [role_id, role_name, role_desc, role_adv]
        })
        # LINE通知
        message = (
            f"あなたの役職は「{role_name}」です。\n\n"
            f"説明：{role_desc}\n\n"
            f"アドバイス：{role_adv}"
        )
        line_bot_api.push_message(user_id, TextSendMessage(text=message))

    # ⑥ 一括更新（D列〜G列）
    row_count = len(user_ids)
    cell_list = player_sheet.range(f'D2:G{row_count+1}')
    for i in range(row_count):
        role_values = updates[i]["values"]
        cell_list[i * 4 + 0].value = role_values[0]
        cell_list[i * 4 + 1].value = role_values[1]
        cell_list[i * 4 + 2].value = role_values[2]
        cell_list[i * 4 + 3].value = role_values[3]
    player_sheet.update_cells(cell_list)
