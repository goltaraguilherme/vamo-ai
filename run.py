import logging

from app import create_app
from flask import send_file
from app.model import db
from dotenv import load_dotenv
import os

load_dotenv()
POSTGRES_PWD = os.getenv("POSTGRES_PWD")

app = create_app()

app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://postgres:valovojucro@localhost:5432/postgres'
db.init_app(app)
with app.app_context():
    db.create_all()

@app.route('/view_pdf/<number_user>')
def view_file(number_user):
    file_path = f'./dados/{number_user}/{number_user}.pdf'
    return send_file(file_path)

if __name__ == "__main__":
    logging.info("Flask app started")
    app.run(host="0.0.0.0", port=8000, debug=True)


