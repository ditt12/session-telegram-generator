from flask import Flask, render_template, request, send_file
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
import asyncio
import threading
import tempfile
import os

app = Flask(__name__)

loop = asyncio.new_event_loop()

client = None
session_file = None
session_name = "telegram.session"


def run_async(coro):
    return asyncio.run_coroutine_threadsafe(
        coro,
        loop
    ).result()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/send_code", methods=["POST"])
def send_code():

    global client, session_file

    api_id = int(request.form["api_id"])
    api_hash = request.form["api_hash"]
    phone = request.form["phone"]

    temp = tempfile.NamedTemporaryFile(
        suffix=".session",
        delete=False
    )

    session_file = temp.name
    temp.close()

    client = TelegramClient(
        session_file,
        api_id,
        api_hash
    )

    run_async(client.connect())

    run_async(
        client.send_code_request(phone)
    )

    return render_template(
        "otp.html",
        phone=phone
    )


@app.route("/login", methods=["POST"])
def login():

    global client

    code = request.form["code"]

    try:

        run_async(
            client.sign_in(
                code=code
            )
        )

        return render_template(
            "success.html"
        )


    except SessionPasswordNeededError:

        return render_template(
            "password.html"
        )


    except Exception as e:

        return f"Error: {e}"



@app.route("/password", methods=["POST"])
def password():

    global client

    password = request.form["password"]

    try:

        run_async(
            client.sign_in(
                password=password
            )
        )

        return render_template(
            "success.html"
        )


    except Exception as e:

        return f"Error: {e}"



@app.route("/download")
def download():

    global session_file

    file_path = session_file

    response = send_file(
        file_path,
        as_attachment=True,
        download_name="telegram.session"
    )

    return response



@app.route("/cleanup")
def cleanup():

    global session_file

    try:

        if session_file and os.path.exists(session_file):
            os.remove(session_file)

        return "Session deleted"

    except Exception as e:

        return str(e)



def start_loop():

    asyncio.set_event_loop(loop)

    loop.run_forever()



if __name__ == "__main__":

    threading.Thread(
        target=start_loop,
        daemon=True
    ).start()


    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
