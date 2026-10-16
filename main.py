
from flask import Flask

app = Flask(__name__)


@app.route("/")
def home():
    return """
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>TaigoAir</title>
    </head>
    <body>
        <h1>TaigoAir</h1>
        <h2>Интеллектуальная система мониторинга воздуха</h2>
        <p>Сервер успешно запущен!</p>
    </body>
    </html>
    """


if __name__ == "__main__":
    app.run(debug=True, port=5000)
