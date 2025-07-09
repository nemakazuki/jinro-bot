from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from sheet_utils import (
    register_player, connect_sheet, set_night_mode, get_night_mode,
    get_name_by_user_id, record_night_action
)

LINE_CHANNEL_ACCESS_TOKEN = 'vpQX3ZT9bYa423omRNdulSxr4JekFoH9F2tG2DCgOAwqfMpMDgg+qw86kymh/EyywUAwpnfhzTQ3nB+1jzBrLqERaDWkVb2PhVNlTR1mEWPbPz7AaDMwQR/iSQdxlOcPIMis8tWeVbKslLMVTcsrUgdB04t89/1O/w1cDnyilFU='
LINE_CHANNEL_SECRET = '7fb356eb813fe6bab58f9c6fed071e71'

app = Flask(__name__)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text.strip()
    user_id = event.source.user_id

    if msg.startswith("/参加"):
        name = msg.replace("/参加", "").strip()
        print(f"登録試行中：{name} / {user_id}")
        register_player(name, user_id)
        reply = f"{name}さんを登録しました。"

    elif msg == "夜":
        set_night_mode("ON")
        sheet = connect_sheet()
        players = sheet.col_values(1)[1:]
        user_ids = sheet.col_values(2)[1:]
        player_list_str = "\n".join(players)
        message_text = (
            "夜の行動です。能力の対象にする参加者を決めて下さい。\n"
            "能力を使わない場合は「なし」と入力してください。\n\n"
            "【参加者リスト】\n" + player_list_str
        )
        for uid in user_ids:
            line_bot_api.push_message(uid, TextSendMessage(text=message_text))
        reply = "夜の行動を各プレイヤーに送信しました。"

    elif msg == "/朝":
        set_night_mode("OFF")
        sheet = connect_sheet()
        user_ids = sheet.col_values(2)[1:]
        for uid in user_ids:
            line_bot_api.push_message(uid, TextSendMessage(text="夜が明けました。議論を始めてください。"))
        reply = "夜モードを終了しました。"

    else:
        if get_night_mode() == "ON":
            name = get_name_by_user_id(user_id)
            if name:
                record_night_action(user_id, name, msg)
                reply = f"「{msg}」を夜の行動として受け付けました。"
            else:
                reply = "参加者として登録されていません。"
        else:
            reply = "現在は夜の行動時間ではありません。"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))


import os
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
