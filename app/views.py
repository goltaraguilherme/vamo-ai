import logging
import json
import pandas as pd
import datetime

from flask import Blueprint, request, jsonify, current_app
from sqlalchemy.exc import SQLAlchemyError

from .decorators.security import signature_required
from .utils.whatsapp_utils import (
    process_whatsapp_message,
    is_valid_whatsapp_message,
)

from .model import Chats, Messages, db

webhook_blueprint = Blueprint("webhook", __name__)

(START,
ROTEIRO_PERSONALIZADO_PREFERENCIAS,
ROTEIRO_PERSONALIZADO_COMPANHIA,
ROTEIRO_PERSONALIZADO_DURACAO,
ROTEIRO_PERSONALIZADO_CIDADES,
ROTEIRO_PERSONALIZADO_FINALIZACAO) = range(6)

def handle_message():
    """
    Handle incoming webhook events from the WhatsApp API.

    This function processes incoming WhatsApp messages and other events,
    such as delivery statuses. If the event is a valid message, it gets
    processed. If the incoming payload is not a recognized WhatsApp event,
    an error is returned.

    Every message send will trigger 4 HTTP requests to your webhook: message, sent, delivered, read.

    Returns:
        response: A tuple containing a JSON response and an HTTP status code.
    """
    body = request.get_json()
    # logging.info(f"request body: {body}")
    print(body)
    # Check if it's a WhatsApp status update
    if (
        body.get("entry", [{}])[0]
        .get("changes", [{}])[0]
        .get("value", {})
        .get("statuses")
    ):
        logging.info("Received a WhatsApp status update.")
        return jsonify({"status": "ok"}), 200

    wpp_id = body["entry"][0]["changes"][0]["value"]["messages"][0]["id"]
    try:
        message = Messages.query.filter_by(wpp_id=wpp_id).first()
        if message:
            return jsonify({"status": "ok"}), 200
        else:
            new_message = Messages(
                wpp_id=wpp_id
            )
            db.session.add(new_message)
            db.session.commit()
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 500
    try:
        if is_valid_whatsapp_message(body):
            number = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
            name_user = body["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]
            state = 0
            try:
                chat = Chats.query.filter_by(number=number).first()
                if chat:
                    state = chat.state
                else:
                    new_chat = Chats(
                        state=0,
                        number=number
                    )
                    db.session.add(new_chat)
                    db.session.commit()
            except SQLAlchemyError as e:
                return jsonify({"error": str(e)}), 500
            message = body["entry"][0]["changes"][0]["value"]["messages"][0]
            #logging.info(f"teste: {message}")
            message_body = message["text"]["body"] if 'text' in message else message["interactive"]["list_reply"]["title"]
            if(state == START and message_body.upper() == "ROTEIRO PERSONALIZADO"):
                state = ROTEIRO_PERSONALIZADO_PREFERENCIAS
            elif(state == ROTEIRO_PERSONALIZADO_PREFERENCIAS):
                state = ROTEIRO_PERSONALIZADO_COMPANHIA
            elif(state == ROTEIRO_PERSONALIZADO_COMPANHIA):
                state = ROTEIRO_PERSONALIZADO_DURACAO
            elif(state == ROTEIRO_PERSONALIZADO_DURACAO):
                state = ROTEIRO_PERSONALIZADO_CIDADES
            elif(state == ROTEIRO_PERSONALIZADO_CIDADES):
                state = ROTEIRO_PERSONALIZADO_FINALIZACAO
            
            if chat:
                chat.state = state
                db.session.commit()
            process_whatsapp_message(body, state, number)
            return jsonify({"status": "ok"}), 200
        else:
            # if the request is not a WhatsApp API event, return an error
            return (
                jsonify({"status": "error", "message": "Not a WhatsApp API event"}),
                404,
            )
    except json.JSONDecodeError:
        logging.error("Failed to decode JSON")
        return jsonify({"status": "error", "message": "Invalid JSON provided"}), 400


# Required webhook verifictaion for WhatsApp
def verify():
    # Parse params from the webhook verification request
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    # Check if a token and mode were sent
    if mode and token:
        # Check the mode and token sent are correct
        if mode == "subscribe" and token == current_app.config["VERIFY_TOKEN"]:
            # Respond with 200 OK and challenge token from the request
            logging.info("WEBHOOK_VERIFIED")
            return challenge, 200
        else:
            # Responds with '403 Forbidden' if verify tokens do not match
            logging.info("VERIFICATION_FAILED")
            return jsonify({"status": "error", "message": "Verification failed"}), 403
    else:
        # Responds with '400 Bad Request' if verify tokens do not match
        logging.info("MISSING_PARAMETER")
        return jsonify({"status": "error", "message": "Missing parameters"}), 400


@webhook_blueprint.route("/webhook", methods=["GET"])
def webhook_get():
    return verify()

@webhook_blueprint.route("/webhook", methods=["POST"])
@signature_required
def webhook_post():
    return handle_message()




