import logging
from flask import current_app, jsonify, send_file
import json
import requests
import base64
import pandas as pd
import openai
import os
from dotenv import load_dotenv
from .pdf_utils import ( generate_itineray )
from sqlalchemy.exc import SQLAlchemyError
from ..model import Chats, db
import requests

# from app.services.openai_service import generate_response
import re

(START,
ROTEIRO_PERSONALIZADO_PREFERENCIAS,
ROTEIRO_PERSONALIZADO_COMPANHIA,
ROTEIRO_PERSONALIZADO_DURACAO,
ROTEIRO_PERSONALIZADO_CIDADES,
ROTEIRO_PERSONALIZADO_FINALIZACAO) = range(6)

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")
client = openai.api_key=OPENAI_API_KEY

def test_gpt(prompt):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    body = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "Você é um assistente de viagens."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 1500,
        "temperature": 0.5
    }
    try:
        response = requests.post(url="https://api.openai.com/v1/chat/completions", headers=headers, json=body)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"].strip()
    except:
        return response.raise_for_status()

def req_chatgpt(questao):
    resposta = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Você é um assistente de viagens."},
            {"role": "user", "content": questao}
        ],
        max_tokens=1500,
        temperature=0.5
    )
    return resposta.choices[0].message['content'].strip()

def log_http_response(response):
    logging.info(f"Status: {response.status_code}")
    logging.info(f"Content-type: {response.headers.get('content-type')}")
    logging.info(f"Body: {response.text}")


def get_text_message_input(recipient, text):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }
    )

def get_welcome_message(recipient):
    #title = base64.b64encode("Estou animado para embarcar nessa jornada incrível com você! Aqui, você encontrará dois serviços excepcionais:\n\n1. Roteiro Personalizado: Permita-me criar uma experiência única para você! Com base em suas preferências e estilo de viagem, vou montar um roteiro sob medida, garantindo que cada momento seja memorável.\n\n2. Busca de Informações: Curioso sobre um local específico? Não se preocupe! Estou aqui para fornecer todas as informações que você precisa, desde a história local até as melhores atrações e dicas de viagem.\n\nPor favor, escolha uma das opções acima para começarmos nossa aventura juntos!".encode()).decode()
    #print(title)
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "header": {
                "type": "text",
                "text": "Olá! Seja bem-vindo ao Vamo AI - Seu companheiro de viagens!"
                },
                "body": {
                "text": "Estou animado para embarcar nessa jornada incrível com você! Aqui, você encontrará dois serviços excepcionais:\n\n1. Roteiro Personalizado: Permita-me criar uma experiência única para você! Com base em suas preferências e estilo de viagem, vou montar um roteiro sob medida, garantindo que cada momento seja memorável.\n\n2. Busca de Informações: Curioso sobre um local específico? Não se preocupe! Estou aqui para fornecer todas as informações que você precisa, desde a história local até as melhores atrações e dicas de viagem.\n\nPor favor, escolha uma das opções acima para começarmos nossa aventura juntos!"
                },
                "footer": {
                "text": ""
                },
                "action": {
                "sections": [
                    {
                    "title": "Opções",
                    "rows": [
                        {
                        "id": "01",
                        "title": "Roteiro Personalizado",
                        "description": ""
                        },
                         {
                        "id": "02",
                        "title": "Busca de Informações",
                        "description": ""
                        }
                    ]
                    }
                ],
                "button": "Opções",
                }
            }
        }
    )

def get_likes_user_itinerary(recipient):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": False, "body": """
                    
Vamo personalizar sua jornada!

*Primeira parada*: Qual destino faz seu coração bater mais forte? 🤔🤔

Locais históricos, praias ensolaradas, montanhas desafiadoras, cachoeiras revigorantes ou quem sabe um roteiro noturno por bares animados? 🙌

Mal posso esperar para planejar essa aventura com você!
            """},
        }
    )

def get_companionship_message(recipient):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "header": {
                "type": "text",
                "text": ""
                },
                "body": {
                "text": "Uau, adorei sua escolha! Praia, montanha, cachoeira... cada opção tem sua vibe única! 🏖️⛰️🌊 Agora, vamos continuar montando o roteiro! Faltam só mais 3 perguntinhas. Quem vai ser sua companhia nessa jornada? Amigos, família, parceiro(a) ou você vai brilhar solo? ✨"
                },
                "footer": {
                "text": ""
                },
                "action": {
                "sections": [
                    {
                    "title": "Opções",
                    "rows": [
                        {
                        "id": "01",
                        "title": "Grupo de amigos",
                        "description": ""
                        },
                        {
                        "id": "02",
                        "title": "Familiares",
                        "description": ""
                        },
                        {
                        "id": "03",
                        "title": "Parceiro(a)",
                        "description": ""
                        },
                        {
                        "id": "04",
                        "title": "Vou viajar solo",
                        "description": ""
                        }
                    ]
                    }
                ],
                "button": "Sua companhia",
                }
            }
        }
    )

def get_days_travel(recipient):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": False, "body": "Que legal, uma viagem com seu amor sempre vale a pena! 💑 Quantos dias vocês desejam passar no local? 🗓️"},
        }
    )

def get_set_cities(recipient):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": False, "body": "Estamos quase lá, prontos para a última parada? 🎉 Então, me diga: você tem alguma cidade em mente para incluir no roteiro? 🏙️ Ou prefere que eu escolha os destinos surpresa? Fico à disposição para tornar essa viagem ainda mais especial! ✈️🌍"},
        }
    )

def get_finish_itineray(recipient):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": False, "body": "Parabéns, explorador(a)! Você completou o processo de personalização do seu roteiro! 🎉 Agora, vou dar um 'check-in' nas suas preferências e em instantes estarei decolando para criar um roteiro personalizado que vai te deixar 'nas nuvens'! ✈️🌟 Prepare-se para uma viagem cheia de 'bagagens' de diversão e memórias inesquecíveis! 🧳😄"},
        }
    )

def send_itineray(recipient):
    return json.dumps(
        {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient,
        "type": "document",
        "document": {
            "link": f"https://hopeful-native-bluegill.ngrok-free.app/view_pdf/{recipient}",
            "filename": "roteiro.pdf"
        }
    })


def generate_response(response):
    # Return text in uppercase
    return """ 🌟 *Olá! Seja bem-vindo ao Vamo AI - Seu companheiro de viagens!* 🌟

Estou animado para embarcar nessa jornada incrível com você! Aqui, você encontrará dois serviços excepcionais:

1. *Roteiro Personalizado:* Permita-me criar uma experiência única para você! Com base em suas preferências e estilo de viagem, vou montar um roteiro sob medida, garantindo que cada momento seja memorável.

2. *Busca de Informações:* Curioso sobre um local específico? Não se preocupe! Estou aqui para fornecer todas as informações que você precisa, desde a história local até as melhores atrações e dicas de viagem.

Por favor, escolha uma das opções acima para começarmos nossa aventura juntos! 🌍✨
"""

def send_pdf(data, number):
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {current_app.config['ACCESS_TOKEN']}",
    }

    url = f"https://graph.facebook.com/{current_app.config['VERSION']}/{current_app.config['PHONE_NUMBER_ID']}/media"

    try:
        response = requests.post(
            url, data=data, headers=headers, timeout=10, files=[('file',('Roteiro.pdf',open(f'./{number}/roteiro.pdf','rb'),'application/pdf'))]
        )  # 10 seconds timeout as an example
        response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
    except requests.Timeout:
        logging.error("Timeout occurred while sending message")
        return jsonify({"status": "error", "message": "Request timed out"}), 408
    except (
        requests.RequestException
    ) as e:  # This will catch any general request exception
        logging.error(f"Request failed due to: {e}")
        return jsonify({"status": "error", "message": "Failed to send message"}), 500
    else:
        # Process the response as normal
        log_http_response(response)
        return response

def send_message(data):
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {current_app.config['ACCESS_TOKEN']}",
    }

    url = f"https://graph.facebook.com/{current_app.config['VERSION']}/{current_app.config['PHONE_NUMBER_ID']}/messages"

    try:
        response = requests.post(
            url, data=data, headers=headers, timeout=10
        )  # 10 seconds timeout as an example
        response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
    except requests.Timeout:
        logging.error("Timeout occurred while sending message")
        return jsonify({"status": "error", "message": "Request timed out"}), 408
    except (
        requests.RequestException
    ) as e:  # This will catch any general request exception
        logging.error(f"Request failed due to: {e}")
        return jsonify({"status": "error", "message": "Failed to send message"}), 500
    else:
        # Process the response as normal
        log_http_response(response)
        return response


def process_text_for_whatsapp(text):
    # Remove brackets
    pattern = r"\【.*?\】"
    # Substitute the pattern with an empty string
    text = re.sub(pattern, "", text).strip()

    # Pattern to find double asterisks including the word(s) in between
    pattern = r"\*\*(.*?)\*\*"

    # Replacement pattern with single asterisks
    replacement = r"*\1*"

    # Substitute occurrences of the pattern with the replacement
    whatsapp_style_text = re.sub(pattern, replacement, text)

    return whatsapp_style_text


def process_whatsapp_message(body, state, number):
    wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
    name = body["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]

    message = body["entry"][0]["changes"][0]["value"]["messages"][0]
    #logging.info(f"teste: {message}")
    message_body = message["text"]["body"] if 'text' in message else message["interactive"]["list_reply"]["title"]
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
    # TODO: implement custom function here
    if(state == START and message_body.upper() == "VAMO VIAJAR"):   
        data = get_welcome_message(number)
        send_message(data)
    elif(state == ROTEIRO_PERSONALIZADO_PREFERENCIAS): 
        data = get_likes_user_itinerary(number)
        send_message(data)
    elif(state == ROTEIRO_PERSONALIZADO_COMPANHIA):    
        chat.preferences = message_body
        db.session.commit()
        data = get_companionship_message(number)
        send_message(data)
    elif(state == ROTEIRO_PERSONALIZADO_DURACAO):    
        chat.company = message_body
        db.session.commit()
        data = get_days_travel(number)
        send_message(data)
    elif(state == ROTEIRO_PERSONALIZADO_CIDADES):  
        chat.days = message_body
        db.session.commit()
        data = get_set_cities(number)
        send_message(data)
    elif(state == ROTEIRO_PERSONALIZADO_FINALIZACAO):    
        chat.cities = message_body
        db.session.commit()
        data = get_finish_itineray(number)
        send_message(data)
        prompt = f"""Preciso de um roteiro de viagens de {chat.days} dias no Espírito Santo, vou viajar com a {chat.company} e 
        gostaria de uma viagem com {chat.preferences} e passeios passando pelas cidades de {chat.cities}. 
        Me gere a resposta no formato de um json da seguinte forma: roteiro: '{'dia_01: "{"Cidade: [], atracoes: [], descricoes: [], descricoes_historicas: [], dicas:[]}..."}"'}'
        Ampliando este modelo para os demais dias, inclua pelo menos duas dicas e caso tenha alguma referencia historica ou cultural adicione esta informacao. E nao me envie nada alem do JSON
        """
        roteiro = req_chatgpt(prompt)
        print(json.loads(roteiro))
        generate_itineray(json.loads(roteiro), number)
        data2 = send_itineray(number)
        send_message(data2)
    else:
        response = "Para começar, responda 'Vamo viajar'"
        data = get_text_message_input(number, response)
        send_message(data)

    # OpenAI Integration
    # response = generate_response(message_body, wa_id, name)
    # response = process_text_for_whatsapp(response)



def is_valid_whatsapp_message(body):
    """
    Check if the incoming webhook event has a valid WhatsApp message structure.
    """
    return (
        body.get("object")
        and body.get("entry")
        and body["entry"][0].get("changes")
        and body["entry"][0]["changes"][0].get("value")
        and body["entry"][0]["changes"][0]["value"].get("messages")
        and body["entry"][0]["changes"][0]["value"]["messages"][0]
    )
