from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# アクセストークンとシークレットを設定
LINE_CHANNEL_ACCESS_TOKEN = 'vpQX3ZT9bYa423omRNdulSxr4JekFoH9F2tG2DCgOAwqfMpMDgg+qw86kymh/EyywUAwpnfhzTQ3nB+1jzBrLqERaDWkVb2PhVNlTR1mEWPbPz7AaDMwQR/iSQdxlOcPIMis8tWeVbKslLMVTcsrUgdB04t89/1O/w1cDnyilFU='
LINE_CHANNEL_SECRET = '7fb356eb813fe6bab58f9c6fed071e71'

app = Flask(__name__)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Webhook受信用のルート
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# メッセージ受信時の処理
from sheet_utils import register_player  # または関数を同じファイルに直接書く

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text.strip()
    user_id = event.source.user_id

    if msg.startswith("/add"):
        name = msg.replace("/add", "").strip()
        print(f"登録試行中：{name} / {user_id}")  # ← 追加
        register_player(name, user_id)
        reply = f"{name}さんを登録しました。"
    else:
        reply = f"あなたのメッセージ：{msg}"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
