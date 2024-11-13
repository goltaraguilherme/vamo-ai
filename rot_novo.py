import os
import textwrap
import requests
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import math
import pandas as pd

def draw_text_right_aligned(draw, text, font, position, max_width, fill):
    # Dividir o texto em palavras
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        # Testar a linha atual com a nova palavra
        test_line = current_line + word + " "
        test_width = draw.textlength(test_line, font=font)

        # Se a linha for maior que o máximo permitido, adiciona a linha anterior e começa uma nova
        if test_width > max_width and current_line:
            lines.append(current_line.rstrip())
            current_line = word + " "
        else:
            current_line = test_line

    # Adiciona a última linha
    if current_line:
        lines.append(current_line.rstrip())

    # Desenhar as linhas alinhadas à direita
    y_offset = 0
    for line in lines:
        line_width = draw.textlength(line, font=font)
        x = position[0] - line_width
        draw.text((x, position[1] + y_offset), line, font=font, fill=fill)
        y_offset += 80  # Mover para a próxima linha

def draw_rounded_rectangle(draw, position, radius, fill):
    # Desenhar o retângulo com bordas arredondadas
    left, top, right, bottom = position
    draw.rounded_rectangle([left, top, right, bottom], radius=radius, fill=fill)

def draw_multiline_text(draw, text, font, position, line_height, max_width, fill):
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = current_line + word + " "
        test_width = draw.textlength(test_line, font=font)

        if test_width > max_width and current_line:
            lines.append(current_line.rstrip())
            current_line = word + " "
        else:
            current_line = test_line

    if current_line:
        lines.append(current_line.rstrip())

    y_offset = 0
    for line in lines:
        draw.text((position[0], position[1] + y_offset), line, font=font, fill=fill)
        y_offset += line_height


def capa_layout(cidade, dias):
    # Carregar a imagem de background
    bg_path = 'bg-roteiros/rj.png'
    background = Image.open(bg_path).resize((1280,720))

    # Carregar a imagem a ser sobreposta
    bg_overlay_path = 'bg-roteiros/capa.png'
    overlay = Image.open(bg_overlay_path).resize((1280,720))

    # Converta a imagem de sobreposição para RGBA, se não estiver nesse modo
    if overlay.mode != 'RGBA':
        overlay = overlay.convert('RGBA')

    # Posição onde a imagem será sobreposta (no caso, 0, 0)
    position = (0, 0)

    # Sobrepor a imagem usando a própria imagem como máscara
    background.paste(overlay, position, overlay)

    # Carregar a imagem logo.png a ser sobreposta
    logo_path = 'bg-roteiros/logoVamo.png'
    logo = Image.open(logo_path).resize((200,200))

    # Converta a imagem do logo para RGBA, se não estiver nesse modo
    if logo.mode != 'RGBA':
        logo = logo.convert('RGBA')

    # Posição onde a imagem logo.png será sobreposta
    logo_position = (1210-200, 0)

    # Sobrepor logo.png na posição (1320, 200)
    background.paste(logo, logo_position, logo)

    # Configurar a fonte e o desenho
    draw = ImageDraw.Draw(background)

    # nome da cidade
    font_path_1 = 'bg-roteiros/BebasNeue-Regular.ttf'
    font_1 = ImageFont.truetype(font_path_1, 100)
    # Desenhar o texto "RIO DE JANEIRO" alinhado à direita
    text_position_1 = (1210, 240)
    draw_text_right_aligned(draw, cidade, font_1, text_position_1, 400, (255, 255, 255))

    # Texto de dias com a cor #ee9c22
    font_path_2 = 'bg-roteiros/Breathing.ttf'
    font_2 = ImageFont.truetype(font_path_2, 90)
    text_color_2 = (238, 156, 34)  # Cor convertida de #ee9c22
    draw.text((1200 - draw.textlength(dias+" dias", font=font_2), 450), dias+" dias", font=font_2, fill=text_color_2)

    # Configurações do retângulo
    rect_position = (1100, 610, 1210, 660)  # (left, top, right, bottom)
    rect_color = (238, 156, 34)  # Cor do retângulo (convertido de #ee9c22)
    rect_radius = 20  # Raio para bordas arredondadas

    # Desenhar o retângulo com bordas arredondadas
    draw_rounded_rectangle(draw, rect_position, rect_radius, rect_color)

    # Adicionar o texto "conhecer"
    text = "Conhecer"
    font_path = 'bg-roteiros/BebasNeue-Regular.ttf'  # Caminho para a fonte
    font_size = 16
    font = ImageFont.truetype(font_path, font_size)

    # Medir o tamanho do texto para centralizá-lo no retângulo
    text_width = draw.textlength(text, font=font)
    text_x = (rect_position[0] + rect_position[2]) // 2 - text_width // 2
    text_y = (rect_position[1] + rect_position[3]) // 2 - 22 // 2
    text_color = (255, 255, 255)  # Cor do texto (branco)

    # Desenhar o texto
    draw.text((text_x, text_y), text, font=font, fill=text_color)


    # Salvar a imagem final
    final_image_path = 'bg-roteiros/capa_test.png'
    background.save(final_image_path)

    # Exibir a imagem final (opcional)
    background.show()

def introd_layout(cidade):
    # Carregar a imagem de background
    bg_path = 'bg-roteiros/introd-bg.png'
    background = Image.open(bg_path).resize((1280,720))

    # Carregar a imagem a ser sobreposta
    bg_overlay_path = 'bg-roteiros/cristo.jpg'
    overlay = Image.open(bg_overlay_path).resize((450,600))

    # Converta a imagem de sobreposição para RGBA, se não estiver nesse modo
    if overlay.mode != 'RGBA':
        overlay = overlay.convert('RGBA')

    # Posição onde a imagem será sobreposta (no caso, 0, 0)
    position = (60, 60)

    # Sobrepor a imagem usando a própria imagem como máscara
    background.paste(overlay, position, overlay)

    # Configurar a fonte e o desenho
    draw = ImageDraw.Draw(background)

    # Texto de dias com a cor #ee9c22
    breathing_font_path = 'bg-roteiros/Breathing.ttf'
    breathing_font = ImageFont.truetype(breathing_font_path, 35)
    text_color_2 = (238, 156, 34)  # Cor convertida de #ee9c22
    draw.text((600, 150), "Welcome to", font=breathing_font, fill=text_color_2)

    # nome da cidade
    bebas_font_path = 'bg-roteiros/BebasNeue-Regular.ttf'
    bebas_font = ImageFont.truetype(bebas_font_path, 50)
    draw.text((600, 180), cidade, font=bebas_font, fill=(11, 141, 147))

    montserrat_font_bold_path = 'bg-roteiros/static/Montserrat-Bold.ttf'
    montserrat_font_regular_path = 'bg-roteiros/static/Montserrat-Regular.ttf'
    montserrat_font_regular = ImageFont.truetype(montserrat_font_regular_path, 15)
    montserrat_font_bold = ImageFont.truetype(montserrat_font_bold_path, 50)
    draw.text((80, 25), "x", font=montserrat_font_bold, fill=text_color_2)
    about = """
O Rio de Janeiro, conhecido como a "Cidade Maravilhosa", é um dos destinos mais icônicos do Brasil, combinando uma rica história e cultura vibrante com paisagens naturais deslumbrantes. Suas praias, como Copacabana e Ipanema, são mundialmente famosas, oferecendo cenários perfeitos para relaxar e apreciar a vida carioca. Além de suas belezas naturais, o Rio é um centro cultural, onde a música, o samba e a alegria de seu povo refletem uma tradição única e cativante. A cidade promete uma experiência inesquecível para todos os visitantes.
""" 
    draw_multiline_text(draw, about, font=montserrat_font_regular, position=(600,280), max_width=580, fill=(50,50,50))

    # Salvar a imagem final
    final_image_path = 'bg-roteiros/introd_test.png'
    background.save(final_image_path)

    # Exibir a imagem final (opcional)
    background.show()

def passeio_layout_1(texto_turno, atracao, descricao, rating, ratingCount):
    # Carregar a imagem de background
    bg_path = 'bg-roteiros/rj.png'
    background = Image.open(bg_path).resize((1280,720))

    # Carregar a imagem a ser sobreposta
    bg_overlay_path = 'bg-roteiros/dia1-bg.png'
    overlay = Image.open(bg_overlay_path).resize((1280,720))

    star_path = 'bg-roteiros/estrela.png'
    star_icon = Image.open(star_path).resize((20,20))
    pin_path = 'bg-roteiros/pin.png'
    pin_icon = Image.open(pin_path).resize((30,30))

    # Converta a imagem de sobreposição para RGBA, se não estiver nesse modo
    if overlay.mode != 'RGBA':
        overlay = overlay.convert('RGBA')

    if pin_icon.mode != 'RGBA':
        pin_icon = pin_icon.convert('RGBA')

    # Posição onde a imagem será sobreposta (no caso, 0, 0)
    position = (0, 0)

    # Sobrepor a imagem usando a própria imagem como máscara
    background.paste(overlay, position, overlay)

    # Configurar a fonte e o desenho
    draw = ImageDraw.Draw(background)

    bebas_regular_font_path = 'bg-roteiros/BebasNeue-Regular.ttf'
    breathing_regular_font_path = 'bg-roteiros/Breathing.ttf'
    montserrat_font_bold_path = 'bg-roteiros/static/Montserrat-Bold.ttf'
    montserrat_font_regular_path = 'bg-roteiros/static/Montserrat-Regular.ttf'
    montserrat_font_regular = ImageFont.truetype(montserrat_font_regular_path, 15)
    montserrat_font_regular_sm = ImageFont.truetype(montserrat_font_regular_path, 15)
    montserrat_font_bold = ImageFont.truetype(montserrat_font_bold_path, 50)
    montserrat_font_bold_sm = ImageFont.truetype(montserrat_font_bold_path, 15)
    bebas_regular = ImageFont.truetype(bebas_regular_font_path, 50)
    breathing_regular_font = ImageFont.truetype(breathing_regular_font_path, 40)

    text_yellow = (238, 156, 34)  # Cor convertida de #ee9c22

    draw.text((50,30), "x", font=montserrat_font_bold, fill=text_yellow)
    draw.text((140, 120), texto_turno, font=breathing_regular_font, fill=text_yellow)
    draw.text((140, 150), atracao, font=bebas_regular, fill=(255,255,255))

    draw_multiline_text(draw, descricao, font=montserrat_font_regular, line_height=30, position=(140,270), max_width=500, fill=(255,255,255))

    draw.text((140, 520), "No Google", font=ImageFont.truetype(montserrat_font_bold_path, 15), fill=(255,255,255))
    background.paste(star_icon, (140, 540), star_icon)
    draw.text((170, 540), rating, font=montserrat_font_bold_sm, fill=(255,255,255))
    draw.text((140, 565), ratingCount, font=montserrat_font_regular_sm, fill=(255,255,255))

    background.paste(pin_icon, (135, 610), pin_icon)
    draw_multiline_text(draw, "R. Ernestina Maria de Jesus Peixoto, 485 - Rosário, São Thomé das Letras", font=ImageFont.truetype(montserrat_font_regular_path, 12), position=(170,610), line_height=15, max_width=400, fill=(255,255,255))

    # Salvar a imagem final
    final_image_path = 'bg-roteiros/passeio-teste.png'
    background.save(final_image_path)

    # Exibir a imagem final (opcional)
    background.show()

def passeio_layout_2(texto_turno, atracao, descricao, rating, ratingCount):
    # Carregar a imagem de background
    bg_path = 'bg-roteiros/dia2.png'
    background = Image.open(bg_path).resize((1280,720))

    # Carregar a imagem a ser sobreposta
    photo_path = 'bg-roteiros/museu.jpg'
    overlay = Image.open(photo_path).resize((500,550))

    star_path = 'bg-roteiros/estrela.png'
    star_icon = Image.open(star_path).resize((20,20))
    pin_path = 'bg-roteiros/pin.png'
    pin_icon = Image.open(pin_path).resize((30,30))

    # Converta a imagem de sobreposição para RGBA, se não estiver nesse modo
    if overlay.mode != 'RGBA':
        overlay = overlay.convert('RGBA')

    if pin_icon.mode != 'RGBA':
        pin_icon = pin_icon.convert('RGBA')

    # Posição onde a imagem será sobreposta (no caso, 0, 0)
    position = (100, 170)

    # Sobrepor a imagem usando a própria imagem como máscara
    background.paste(overlay, position, overlay)

    # Configurar a fonte e o desenho
    draw = ImageDraw.Draw(background)

    bebas_regular_font_path = 'bg-roteiros/BebasNeue-Regular.ttf'
    breathing_regular_font_path = 'bg-roteiros/Breathing.ttf'
    montserrat_font_bold_path = 'bg-roteiros/static/Montserrat-Bold.ttf'
    montserrat_font_regular_path = 'bg-roteiros/static/Montserrat-Regular.ttf'
    montserrat_font_regular = ImageFont.truetype(montserrat_font_regular_path, 15)
    montserrat_font_regular_sm = ImageFont.truetype(montserrat_font_regular_path, 15)
    montserrat_font_bold = ImageFont.truetype(montserrat_font_bold_path, 50)
    montserrat_font_bold_sm = ImageFont.truetype(montserrat_font_bold_path, 15)
    bebas_regular = ImageFont.truetype(bebas_regular_font_path, 50)
    breathing_regular_font = ImageFont.truetype(breathing_regular_font_path, 40)

    text_yellow = (238, 156, 34)  # Cor convertida de #ee9c22

    draw.text((85,340), "x", font=montserrat_font_bold, fill=text_yellow)
    draw.text((640, 160), texto_turno, font=breathing_regular_font, fill=text_yellow)
    draw.text((640, 190), atracao, font=bebas_regular, fill=(11, 141, 147))

    draw_multiline_text(draw, descricao, font=montserrat_font_regular, line_height=30, position=(640,280), max_width=550, fill=(50,50,50))

    draw.text((640, 530), "No Google", font=ImageFont.truetype(montserrat_font_bold_path, 15), fill=(11, 141, 147))
    background.paste(star_icon, (640, 550), star_icon)
    draw.text((670, 551), rating, font=montserrat_font_bold_sm, fill=(11, 141, 147))
    draw.text((640, 575), ratingCount, font=montserrat_font_regular_sm, fill=(11, 141, 147))

    background.paste(pin_icon, (635, 620), pin_icon)
    draw_multiline_text(draw, "R. Ernestina Maria de Jesus Peixoto, 485 - Rosário, São Thomé das Letras", font=ImageFont.truetype(montserrat_font_regular_path, 12), position=(670,620), line_height=15, max_width=400, fill=(50,50,50))

    # Salvar a imagem final
    final_image_path = 'bg-roteiros/passeio-teste-2.png'
    background.save(final_image_path)

    # Exibir a imagem final (opcional)
    background.show()

def rest_layout_1(texto_turno, atracao, descricao, rating, ratingCount, df_data):
    # Carregar a imagem de background
    bg_path = 'bg-roteiros/rj.png'
    background = Image.open(bg_path).resize((1280,720))

    # Carregar a imagem a ser sobreposta
    bg_overlay_path = 'bg-roteiros/dia1-bg.png'
    overlay = Image.open(bg_overlay_path).resize((1280,720))

    star_path = 'bg-roteiros/icons/estrela.png'
    star_icon = Image.open(star_path).resize((20,20))
    pin_path = 'bg-roteiros/icons/pin.png'
    pin_icon = Image.open(pin_path).resize((30,30))

    # Converta a imagem de sobreposição para RGBA, se não estiver nesse modo
    if overlay.mode != 'RGBA':
        overlay = overlay.convert('RGBA')

    if pin_icon.mode != 'RGBA':
        pin_icon = pin_icon.convert('RGBA')

    # Posição onde a imagem será sobreposta (no caso, 0, 0)
    position = (0, 0)

    # Sobrepor a imagem usando a própria imagem como máscara
    background.paste(overlay, position, overlay)

    # Configurar a fonte e o desenho
    draw = ImageDraw.Draw(background)

    bebas_regular_font_path = 'bg-roteiros/BebasNeue-Regular.ttf'
    breathing_regular_font_path = 'bg-roteiros/Breathing.ttf'
    montserrat_font_bold_path = 'bg-roteiros/static/Montserrat-Bold.ttf'
    montserrat_font_regular_path = 'bg-roteiros/static/Montserrat-Regular.ttf'
    montserrat_font_regular = ImageFont.truetype(montserrat_font_regular_path, 15)
    montserrat_font_regular_sm = ImageFont.truetype(montserrat_font_regular_path, 15)
    montserrat_font_bold = ImageFont.truetype(montserrat_font_bold_path, 50)
    montserrat_font_bold_sm = ImageFont.truetype(montserrat_font_bold_path, 15)
    bebas_regular = ImageFont.truetype(bebas_regular_font_path, 50)
    breathing_regular_font = ImageFont.truetype(breathing_regular_font_path, 40)

    text_yellow = (238, 156, 34)  # Cor convertida de #ee9c22

    draw.text((50,30), "x", font=montserrat_font_bold, fill=text_yellow)
    draw.text((140, 120), texto_turno, font=breathing_regular_font, fill=text_yellow)
    draw_multiline_text(draw, atracao, font=bebas_regular, line_height=30, position=(140,150), max_width=500, fill=(255,255,255))

    draw_multiline_text(draw, descricao, font=montserrat_font_regular, line_height=25, position=(140,235), max_width=500, fill=(255,255,255))

    desc_list = [
        {'column': 'outdoorSeating', 'path': 'bg-roteiros/icons/dinner-table.png', 'desc': "Mesa externa"},
        {'column':'liveMusic', 'path': 'bg-roteiros/icons/musical-note.png','desc': "Música ao vivo"},
        {'column':'servesWine', 'path': 'bg-roteiros/icons/taca-com-vinho.png','desc': "Serve vinho" },
        {'column':'servesVegetarianFood', 'path': 'bg-roteiros/icons/salada.png', 'desc': "Serve comida vegetariana"},
        {'column':'goodForChildren', 'path': 'bg-roteiros/icons/feliz.png', 'desc': "Bom para crianças"},
        {'column':'allowsDogs', 'path': 'bg-roteiros/icons/pata-de-cachorro.png', 'desc': "Permite cachorros"},
        {'column':'goodForGroups', 'path': 'bg-roteiros/icons/grupos.png', 'desc': "Boa para grupos"},
        {'column':'goodForWatchingSports', 'path': 'bg-roteiros/icons/smart-tv.png','desc': "Bom para ver esportes" },
        {'column':'accessibilityOptions', 'path': 'bg-roteiros/icons/cadeira-de-rodas.png', 'desc': "Acessibilidade"}
    ]

    cont_true_total = 0

    for item in desc_list:
        if df_data[item.get("column")][0]:
            cont_true_total = cont_true_total + 1
    
    if(cont_true_total in [4,5,6]):
        desc_pos_init = (140, 360)
    elif(cont_true_total in [1,2,3]):
        desc_pos_init = (140, 400)
    elif(cont_true_total in [7,8,9]):
        desc_pos_init = (140, 330)

    cont_true = 0
    cont_line = 0

    for item in desc_list:
        if df_data[item.get("column")][0]:
            icon = Image.open(item.get("path")).resize((35,35))
            pos_icon = (desc_pos_init[0] + cont_line * 190, desc_pos_init[1] + (math.floor(cont_true/3) *70))
            pos_desc = (desc_pos_init[0] + cont_line *190+40, desc_pos_init[1] + 10 + (math.floor(cont_true/3) *70))
            background.paste(icon, pos_icon, icon)
            draw.text(pos_desc, item.get("desc"), font=ImageFont.truetype(montserrat_font_regular_path, 11), fill=(255,255,255))

            cont_true = cont_true + 1
            cont_line = 0 if cont_line == 2 else cont_line + 1

    draw.text((140, 525), "No Google", font=ImageFont.truetype(montserrat_font_bold_path, 15), fill=(255,255,255))
    background.paste(star_icon, (140, 545), star_icon)
    draw.text((170, 545), rating, font=montserrat_font_bold_sm, fill=(255,255,255))
    draw.text((140, 570), ratingCount, font=montserrat_font_regular_sm, fill=(255,255,255))

    background.paste(pin_icon, (135, 615), pin_icon)
    draw_multiline_text(draw, "R. Ernestina Maria de Jesus Peixoto, 485 - Rosário, São Thomé das Letras", font=ImageFont.truetype(montserrat_font_regular_path, 12), position=(170,615), line_height=15, max_width=400, fill=(255,255,255))

    # Salvar a imagem final
    final_image_path = 'bg-roteiros/rest-teste1.png'
    background.save(final_image_path)

    # Exibir a imagem final (opcional)
    background.show()

def rest_layout_2(texto_turno, atracao, descricao, rating, ratingCount, df_data):
    # Carregar a imagem de background
    bg_path = 'bg-roteiros/dia2.png'
    background = Image.open(bg_path).resize((1280,720))

    # Carregar a imagem a ser sobreposta
    photo_path = 'bg-roteiros/museu.jpg'
    overlay = Image.open(photo_path).resize((500,550))

    star_path = 'bg-roteiros/icons/estrela.png'
    star_icon = Image.open(star_path).resize((20,20))
    pin_path = 'bg-roteiros/icons/pin.png'
    pin_icon = Image.open(pin_path).resize((30,30))

    # Converta a imagem de sobreposição para RGBA, se não estiver nesse modo
    if overlay.mode != 'RGBA':
        overlay = overlay.convert('RGBA')

    if pin_icon.mode != 'RGBA':
        pin_icon = pin_icon.convert('RGBA')

    # Posição onde a imagem será sobreposta (no caso, 0, 0)
    position = (100, 170)

    # Sobrepor a imagem usando a própria imagem como máscara
    background.paste(overlay, position, overlay)

    # Configurar a fonte e o desenho
    draw = ImageDraw.Draw(background)

    bebas_regular_font_path = 'bg-roteiros/BebasNeue-Regular.ttf'
    breathing_regular_font_path = 'bg-roteiros/Breathing.ttf'
    montserrat_font_bold_path = 'bg-roteiros/static/Montserrat-Bold.ttf'
    montserrat_font_regular_path = 'bg-roteiros/static/Montserrat-Regular.ttf'
    montserrat_font_regular = ImageFont.truetype(montserrat_font_regular_path, 15)
    montserrat_font_regular_sm = ImageFont.truetype(montserrat_font_regular_path, 15)
    montserrat_font_bold = ImageFont.truetype(montserrat_font_bold_path, 50)
    montserrat_font_bold_sm = ImageFont.truetype(montserrat_font_bold_path, 15)
    bebas_regular = ImageFont.truetype(bebas_regular_font_path, 50)
    breathing_regular_font = ImageFont.truetype(breathing_regular_font_path, 40)

    text_yellow = (238, 156, 34)  # Cor convertida de #ee9c22

    draw.text((85,340), "x", font=montserrat_font_bold, fill=text_yellow)
    draw.text((640, 160), texto_turno, font=breathing_regular_font, fill=text_yellow)
    draw.text((640, 190), atracao, font=bebas_regular, fill=(11, 141, 147))

    draw_multiline_text(draw, descricao, font=montserrat_font_regular, line_height=30, position=(640,280), max_width=550, fill=(50,50,50))

    desc_list = [
        {'column': 'outdoorSeating', 'path': 'bg-roteiros/icons/dinner-table.png', 'desc': "Mesa externa"},
        {'column':'liveMusic', 'path': 'bg-roteiros/icons/musical-note.png','desc': "Música ao vivo"},
        {'column':'servesWine', 'path': 'bg-roteiros/icons/taca-com-vinho.png','desc': "Serve vinho" },
        {'column':'servesVegetarianFood', 'path': 'bg-roteiros/icons/salada.png', 'desc': "Serve comida vegetariana"},
        {'column':'goodForChildren', 'path': 'bg-roteiros/icons/feliz.png', 'desc': "Bom para crianças"},
        {'column':'allowsDogs', 'path': 'bg-roteiros/icons/pata-de-cachorro.png', 'desc': "Permite cachorros"},
        {'column':'goodForGroups', 'path': 'bg-roteiros/icons/grupos.png', 'desc': "Boa para grupos"},
        {'column':'goodForWatchingSports', 'path': 'bg-roteiros/icons/smart-tv.png','desc': "Bom para ver esportes" },
        {'column':'accessibilityOptions', 'path': 'bg-roteiros/icons/cadeira-de-rodas.png', 'desc': "Acessibilidade"}
    ]

    cont_true_total = 0

    for item in desc_list:
        if df_data[item.get("column")][0]:
            cont_true_total = cont_true_total + 1
    
    if(cont_true_total in [4,5,6]):
        desc_pos_init = (640, 420)
    elif(cont_true_total in [1,2,3]):
        desc_pos_init = (640, 440)
    elif(cont_true_total in [7,8,9]):
        desc_pos_init = (640, 380)

    cont_true = 0
    cont_line = 0

    for item in desc_list:
        if df_data[item.get("column")][0]:
            icon = Image.open(item.get("path")).resize((35,35))
            pos_icon = (desc_pos_init[0] + cont_line * 190, desc_pos_init[1] + (math.floor(cont_true/3) *70))
            pos_desc = (desc_pos_init[0] + cont_line *190+40, desc_pos_init[1] + 10 + (math.floor(cont_true/3) *70))
            background.paste(icon, pos_icon, icon)
            draw.text(pos_desc, item.get("desc"), font=ImageFont.truetype(montserrat_font_regular_path, 11), fill=(11, 141, 147))

            cont_true = cont_true + 1
            cont_line = 0 if cont_line == 2 else cont_line + 1

    draw.text((640, 580), "No Google", font=ImageFont.truetype(montserrat_font_bold_path, 15), fill=(11, 141, 147))
    background.paste(star_icon, (640, 600), star_icon)
    draw.text((670, 601), rating, font=montserrat_font_bold_sm, fill=(11, 141, 147))
    draw.text((640, 625), ratingCount, font=montserrat_font_regular_sm, fill=(11, 141, 147))

    background.paste(pin_icon, (635, 670), pin_icon)
    draw_multiline_text(draw, "R. Ernestina Maria de Jesus Peixoto, 485 - Rosário, São Thomé das Letras", font=ImageFont.truetype(montserrat_font_regular_path, 12), position=(670,670), line_height=15, max_width=400, fill=(50,50,50))

    # Salvar a imagem final
    final_image_path = 'bg-roteiros/rest-teste-2.png'
    background.save(final_image_path)

    # Exibir a imagem final (opcional)
    background.show()


#place_data = [{'outdoorSeating': True, 'liveMusic': False, 'servesWine': True, 'servesVegetarianFood': False, 'goodForChildren': False, 'allowsDogs': False, 'goodForGroups': False, 'goodForWatchingSports': False, 'accessibilityOptions': True}]
#df_data = pd.DataFrame.from_dict(place_data)

#rest_layout_2("Quinta de manhã", "Restaurante terra brasilis", "Local com ambiente familiar que serve comida brasileira, pizza e música com vista para o Pão de Açúcar. O menor movimento da noite pode colaborar com sua experiência.", "4.8", "(8.751 avaliações)", df_data)

def generate_pdf(images):
    images.append('./bg-roteiros/feedback.jpg')
    images.append('./bg-roteiros/contracapa.jpg')

    page_width, page_height = 1280, 720

    pdf_path = './bg-roteiros/roteiro.pdf'

    # Cria o PDF
    c = canvas.Canvas(pdf_path, pagesize=(page_width, page_height))

    # Para cada imagem, adiciona uma página no PDF
    for image in images:
        img = Image.open(image)
        
        # Obtém o tamanho da imagem
        width, height = img.size
        aspect = width / height
        
        # Ajusta a imagem para caber na página 1280x720, mantendo a proporção
        new_width, new_height = page_width, page_width / aspect

        if new_height > page_height:
            new_height = page_height
            new_width = page_height * aspect

        # Desenha a imagem na posição correta
        c.drawImage(image, 0, page_height - new_height, width=new_width, height=new_height)
        
        # Finaliza a página
        c.showPage()

    # Salva o PDF
    c.save()

capa_layout("Rio de Janeiro", "4")

generate_pdf([
    './bg-roteiros/capa_test.png', 
    './bg-roteiros/introd_test.png', 
    './bg-roteiros/rest-teste1.png', 
    './bg-roteiros/rest-teste-2.png',
    './bg-roteiros/passeio-teste.png',
    './bg-roteiros/passeio-teste-2.png'])
