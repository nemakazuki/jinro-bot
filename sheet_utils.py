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

# 登録処理
def register_player(name, user_id):
    sheet = connect_sheet()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    sheet.append_row([name, user_id, now])
