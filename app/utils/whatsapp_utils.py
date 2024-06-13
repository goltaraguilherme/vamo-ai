import logging
from flask import current_app, jsonify, send_file
import json
import requests
import base64
import pandas as pd
import openai
import os
from dotenv import load_dotenv
from .pdf_utils import ( generate_itinerary )
from sqlalchemy.exc import SQLAlchemyError
from ..model import Chats, db
import requests

# from app.services.openai_service import generate_response
import re

(START,
ROTEIRO_PERSONALIZADO_CIDADES,
ROTEIRO_PERSONALIZADO_PREFERENCIAS,
ROTEIRO_PERSONALIZADO_COMPANHIA,
ROTEIRO_PERSONALIZADO_DURACAO,
ROTEIRO_PERSONALIZADO_FINALIZACAO) = range(6)

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")
client = openai.api_key=OPENAI_API_KEY

def req_chatgpt(questao):
    resposta = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "Você é um assistente de viagens."},
            {"role": "user", "content": questao}
        ],
        max_tokens=4000,
        temperature=0.7
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
                "text": "Estou animado para embarcar nessa jornada incrível com você! Aqui, você encontrará dois serviços excepcionais:\n\n1. Roteiro Personalizado: Permita-me criar uma experiência única para você! Com base em suas preferências e estilo de viagem, vou montar um roteiro sob medida, garantindo que cada momento seja memorável.\n\n2. Busca de Informações: Curioso sobre um local específico? Não se preocupe! Estou aqui para fornecer todas as informações que você precisa, desde a história local até as melhores atrações e dicas de viagem. (Desabilitado até o momento)\n\nPor favor, escolha uma das opções acima para começarmos nossa aventura juntos!"
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
                        }
                         #{
                        #"id": "02",
                        #"title": "Busca de Informações",
                        #"description": ""
                        #}
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
*Segunda parada*: O que faz seu coração bater mais forte? 🤔🤔

Locais históricos
Praias ensolaradas
Montanhas desafiadoras
Cachoeiras revigorantes 
Bares e restaurantes

Envie suas preferências para gerarmos o roteiro perfeito para você!
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
                "text": "Uau, adorei sua escolha!\n\nAgora, vamos continuar montando o roteiro! Faltam só mais 2 perguntinhas.\n\nQuem vai ser sua companhia nessa jornada?\n\nAmigos, família, parceiro(a) ou você vai brilhar solo? ✨"
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
            "text": {"preview_url": False, "body": "Muito bom! Quantos dias vocês desejam passar no local? 🗓️"},
        }
    )

def get_set_cities(recipient):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": False, "body": "Vamo personalizar sua jornada!🎉\n\nEntão, me diga: você tem alguma cidade em mente para incluir no roteiro? 🏙️ Ou prefere que eu escolha os destinos surpresa? ✈️🌍"},
        }
    )

def get_finish_itineray(recipient):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": False, "body": "Parabéns, explorador(a)! Você completou o processo de personalização do seu roteiro!\n\n 🎉 Agora, vou dar um 'check-in' nas suas preferências e em instantes enviarei um roteiro personalizado que vai te deixar nas nuvens!\n\n ✈️🌟 Prepare-se para uma viagem cheia de 'bagagens' de diversão e memórias inesquecíveis! 🧳😄"},
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
    elif(state == ROTEIRO_PERSONALIZADO_CIDADES):  
        data = get_set_cities(number)
        send_message(data)
    elif(state == ROTEIRO_PERSONALIZADO_PREFERENCIAS): 
        chat.cities = message_body
        db.session.commit()
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
    elif(state == ROTEIRO_PERSONALIZADO_FINALIZACAO): 
        chat.days = message_body
        db.session.commit()
        data = get_finish_itineray(number)
        send_message(data)
        prompt = f"""
Você é um assistente de viagem especializado em criar roteiros personalizados. Preciso de um roteiro de viagem detalhado para um cliente que deseja visitar o Espirito Santo por {chat.days} dias. Aqui estão os detalhes e preferências do cliente:

    Destino: {chat.cities} no Espirito Santo, Brasil
    Interesses: {chat.preferences}
    Orçamento: Moderado (não muito caro, mas disposto a gastar em algumas experiências especiais)
    Preferências: Prefere transporte público e caminhadas, gosta de explorar bairros locais e menos turísticos, interessado em eventos ou festivais locais

Por favor, forneça um roteiro diário que inclua sugestões de atividades, locais para visitar e dicas úteis para aproveitar ao máximo a viagem. Inclua também opções para manhã, tarde e noite, com uma breve descrição de cada atividade e 2 comentários sobre cada atividade principalmente quanto a história e cultura do local, caso seja um local histórico.

A resposta deve ser formatada em JSON, conforme o exemplo abaixo e atente-se para nao enviar mais do que 4000 tokens e nada alem do JSON e não é necessário a marcação para indicar o JSON:
"""+"""
{
  "destino": "Paris, France",
  "roteiro": {
    "dia_01": {
      "manha": { 
        "atividade": "Chegada ao hotel e check-in. Caminhada pelo bairro de Marais, visitando pequenas lojas e galerias de arte.",
        "localizacao": "Marais",
      },
      "tarde": {
        "atividade": "Visita ao Museu Picasso. Explore as ruas históricas de Marais.",
        "localizacao": "Museu Picasso",
        "comentarios": [],
      },
      "noite": {
        "atividade": "Jantar no restaurante típico francês 'Le Petit Marché'.",
        "localizacao": "Le Petit Marché",
        "comentarios": []
      }
    },
    "dia_02": {
      "manha": {
        "atividade": "Visita ao Museu do Louvre. Dê prioridade às obras mais famosas como a Mona Lisa e a Vênus de Milo.",
        "localizacao": "Museu do Louvre",
        "comentarios": []
      },
      "tarde": {
        "atividade": "Passeio pelos Jardins das Tulherias e visita à Place de la Concorde.",
        "localizacao": "Jardins das Tulherias",
        "comentarios": []
      },
      "noite": {
        "activity": "Jantar no café histórico 'Café de Flore'.",
        "location": "Café de Flore",
        "comentarios": []
      }
    }
    //Continue até o ultimo dia
  }
}
"""
        roteiro = req_chatgpt(prompt)
        print(roteiro)
        print(json.loads(roteiro))
        generate_itinerary(json.loads(roteiro), number)
        data2 = send_itineray(number)
        send_message(data2)
        data3 = get_text_message_input(number, "Processo finalizado! Para começar novamente basta digitar 'Vamo viajar'")
        send_message(data3)
        try:
            chat = Chats.query.filter_by(number=number).first()
            if chat:
                db.session.delete(chat)
                db.session.commit()
            return '', 204
        except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500
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
