import os
import json
import gspread
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials

def connect_sheet():
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    creds_dict = json.loads(os.environ.get('GOOGLE_CREDENTIALS'))
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open("jinro_game").worksheet("プレイヤー一覧")
    return sheet
    
def connect_client():
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    creds_dict = json.loads(os.environ.get('GOOGLE_CREDENTIALS'))
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

def get_night_mode():
    client = connect_client()
    sheet = client.open("jinro_game").worksheet("状態")
    return sheet.acell("A1").value or "OFF"

def set_night_mode(mode):
    client = connect_client()
    sheet = client.open("jinro_game").worksheet("状態")
    sheet.update_acell("A1", mode)
# 登録処理
def register_player(name, user_id):
    sheet = connect_sheet()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    sheet.append_row([name, user_id, now])

def record_night_action(user_id, name, action):
    sheet = connect_sheet()
    night_sheet = sheet.worksheet("夜の行動")  # シート名に合わせて変更
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    night_sheet.append_row([now, user_id, name, action])

def get_name_by_user_id(user_id):
    sheet = connect_sheet()
    player_sheet = sheet.worksheet("プレイヤー一覧")
    user_ids = player_sheet.col_values(2)[1:]
    names = player_sheet.col_values(1)[1:]
    for uid, name in zip(user_ids, names):
        if uid == user_id:
            return name
    return None
