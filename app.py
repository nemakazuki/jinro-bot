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
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    received_text = event.message.text
    reply_text = f"あなたが送ったメッセージ：{received_text}"
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    app.run()
