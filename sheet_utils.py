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
