import os
import textwrap
import requests
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from io import BytesIO
from collections import Counter


GOOGLE_PLACE_API_KEY = "AIzaSyB3fFwNUxFRONrvSdFw_Cij08LvPYZ8X8g"

def get_place_id(api_key, place_name):
    try:
        place_name = f"{place_name}, Domingos Martins" if place_name.upper() == "PEDRA AZUL" else place_name
        place_name = f"{place_name}, Vitoria" if place_name.upper() == "PRAIA DE CAMBURI" else place_name
        place_search_url = f'https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={place_name}&inputtype=textquery&fields=place_id&key={api_key}'
        response = requests.get(place_search_url)
        place_id = response.json()['candidates'][0]['place_id']
        return place_id
    except:
        response.raise_for_status()


def get_place_photo(api_key, place_name, max_width=1024):
    try:
        place_id = get_place_id(api_key, place_name)
        place_details_url = f'https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=photos&key={api_key}'
        response = requests.get(place_details_url)
        photo_reference = response.json()['result']['photos'][0]['photo_reference']
        photo_url = f'https://maps.googleapis.com/maps/api/place/photo?maxwidth={max_width}&photoreference={photo_reference}&key={api_key}'
        photo_response = requests.get(photo_url)
        return Image.open(BytesIO(photo_response.content))
    except:
        response.raise_for_status()
        photo_response.raise_for_status()
    

def round_corners(image, radius):
    mask = Image.new("L", image.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), image.size], radius, fill=255)
    output = Image.new("RGBA", image.size)
    output.paste(image, (0, 0), mask)
    return output

# Função para quebrar o texto a cada n palavras
def wrap_text_by_words1(text, words_per_line):
    words = text.split()
    wrapped_text = ''
    for i in range(0, len(words), words_per_line):
        wrapped_text += ' '.join(words[i:i+words_per_line]) + '\n'
    return wrapped_text.strip()

# Função para quebrar o texto a cada n palavras
def wrap_text_by_words(text, max_width, draw, font):
    words = text.split()
    lines = []
    line = []
    for word in words:
        test_line = ' '.join(line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        width = bbox[2] - bbox[0]
        if width <= max_width:
            line.append(word)
        else:
            lines.append(' '.join(line))
            line = [word]
    lines.append(' '.join(line))
    return '\n'.join(lines)

# Função para desenhar texto com quebra automática e espaçamento de linha
def draw_text(draw, text, position, font, max_width, fill, line_spacing=20):
    words = text.split()
    lines = []
    line = []
    for word in words:
        test_line = ' '.join(line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        width = bbox[2] - bbox[0]
        if width <= max_width:
            line.append(word)
        else:
            lines.append(' '.join(line))
            line = [word]
    lines.append(' '.join(line))
    y = position[1]
    for line in lines:
        draw.text((position[0], y), line, font=font, fill=fill)
        y += draw.textbbox((0, 0), line, font=font)[3] - draw.textbbox((0, 0), line, font=font)[1] + line_spacing

# Função com quebra de linha por meio do espaçamento e subtitulo
def draw_text(draw, text, position, font, max_width, fill, line_spacing=20):
    words = text.split()
    lines = []
    line = []
    for word in words:
        test_line = ' '.join(line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        width = bbox[2] - bbox[0]
        if width <= max_width:
            line.append(word)
            if word.endswith('.'):
                lines.append(' '.join(line))
                line = []
        else:
            lines.append(' '.join(line))
            line = [word]
            if word.endswith('.'):
                lines.append(' '.join(line))
                line = []
    if line:
        lines.append(' '.join(line))

    y = position[1]
    for line in lines:
        draw.text((position[0], y), line, font=font, fill=fill)
        y += draw.textbbox((0, 0), line, font=font)[3] - draw.textbbox((0, 0), line, font=font)[1] + line_spacing
        if line.endswith('.'):
            y += line_spacing  # Adiciona um espaçamento extra após a linha com ponto final

# Função para desenhar textos com subtítulos
def draw_text_with_subtitles(draw, position, text, text_font, subtitle_font, text_color, max_width):
    lines = text.split('\n')
    y = position[1]
    for line in lines:
        if ':' in line:
            subtitle, rest = line.split(':', 1)
            wrapped_subtitle = wrap_text_by_words(subtitle + ':', max_width, draw, subtitle_font)
            for sub_line in wrapped_subtitle.split('\n'):
                draw.text((position[0], y), sub_line, font=subtitle_font, fill=text_color)
                y += draw.textbbox((0, 0), sub_line, font=subtitle_font)[3] - draw.textbbox((0, 0), sub_line, font=subtitle_font)[1] + 5
            wrapped_rest = wrap_text_by_words(rest.strip(), max_width, draw, text_font)
            for rest_line in wrapped_rest.split('\n'):
                draw.text((position[0], y), rest_line, font=text_font, fill=text_color)
                y += draw.textbbox((0, 0), rest_line, font=text_font)[3] - draw.textbbox((0, 0), rest_line, font=text_font)[1] + 5
            y += 15  # Espaço extra entre os blocos de texto
        else:
            wrapped_line = wrap_text_by_words(line, max_width, draw, text_font)
            for sub_line in wrapped_line.split('\n'):
                draw.text((position[0], y), sub_line, font=text_font, fill=text_color)
                y += draw.textbbox((0, 0), sub_line, font=text_font)[3] - draw.textbbox((0, 0), sub_line, font=text_font)[1] + 5

# Função para melhorar as imagem da API do Google Places
def enhance_image(image):
    # Aumentar a nitidez
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(2.0)  # Ajuste o valor conforme necessário

    # Aumentar o contraste
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.5)  # Ajuste o valor conforme necessário

    # Aumentar o brilho
    enhancer = ImageEnhance.Brightness(image)
    image = enhancer.enhance(1.2)  # Ajuste o valor conforme necessário

    return image
def get_top_colors(image, n=2):
    image = image.resize((100, 100))
    image = image.convert('RGB')
    pixels = [pixel for pixel in image.getdata() if pixel != (0, 0, 0) and pixel != (255, 255, 255)]
    counter = Counter(pixels)
    top_colors = [color for color, count in counter.most_common(n)]
    return top_colors
def rgb_to_hex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(*rgb)
def is_similar_color(color1, color2, threshold=50):
    return all(abs(a - b) < threshold for a, b in zip(color1, color2))
def get_text_color(bg_color):
    # Calcula a luminância da cor de fundo
    luminance = 0.299 * bg_color[0] + 0.587 * bg_color[1] + 0.114 * bg_color[2]
    # Retorna branco para fundos escuros e branco para fundos claros novamente
    return (255, 255, 255) if luminance < 128 else (255, 255, 255)

# Função para decidir qual cor usar como fundo e como texto
def choose_colors(top_colors):
    if len(top_colors) == 0:
        return (0, 0, 0), (255, 255, 255)
    principal_color = top_colors[0]
    if len(top_colors) > 1:
        second_principal_color = top_colors[1]
        if is_similar_color(principal_color, second_principal_color):
            text_color = get_text_color(principal_color)
        else:
            text_color = second_principal_color
    else:
        text_color = get_text_color(principal_color)
    return principal_color, text_color

# Função para criar um layout de capa
def capa_layout_1(place_names, number, api_key=GOOGLE_PLACE_API_KEY):
    # Caminho para a logo
    logo_path = '../assets/logoVamo.png'
    # Caminhos para as fontes
    font_path = '../assets/Brice-Regular-SemiExpanded.ttf'
    font_path2 = '../assets/Brice-Bold-SemiExpanded.ttf'

    # Verificar se os arquivos de fonte existem
    if not os.path.exists(font_path):
        raise FileNotFoundError("O arquivo de fonte não foi encontrado. Verifique o caminho.")
    if not os.path.exists(font_path2):
        raise FileNotFoundError("O arquivo de fonte 2 não foi encontrado. Verifique o caminho.")

    # Verificar se o arquivo da logo existe
    if not os.path.exists(logo_path):
        raise FileNotFoundError("O arquivo de logo não foi encontrado. Verifique o caminho.")
    
    # Obter as imagens usando os nomes dos lugares
    images = [get_place_photo(api_key, place_name) for place_name in place_names]

    # Carregar a imagem de fundo
    background = images[3].resize((1080, 1080))

    # Criar uma nova imagem com as mesmas dimensões da imagem de fundo, suportando transparência
    img = Image.new('RGBA', background.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    # Redimensionar as imagens a serem inseridas
    image1 = images[0].resize((510, 210))
    image2 = images[1].resize((510, 210))
    image3 = images[2].resize((510, 210))

    # Arredondar as bordas
    image1 = round_corners(image1, 27)
    image2 = round_corners(image2, 27)
    image3 = round_corners(image3, 27)

    # Posições das imagens
    image1_position = (500, 200)
    image2_position = (500, 420)
    image3_position = (500, 640)

    # Colar as imagens na nova imagem
    img.paste(background, (0, 0))
    img.paste(image1, image1_position, image1)
    img.paste(image2, image2_position, image2)
    img.paste(image3, image3_position, image3)

    # Posições e tamanhos dos textos
    title_position = (85, 340)
    subtitle_position = (85, 480)
    desc1_position = (525, 340)
    desc2_position = (525, 560)
    desc3_position = (525, 780)

    # Fontes
    title_font = ImageFont.truetype(font_path, 40)
    subtitle_font = ImageFont.truetype(font_path2, 20)
    desc_font = ImageFont.truetype(font_path, 20)

    # Textos
    title_text = "VOCÊ SONHA E NÓS REALIZAMOS!"
    subtitle_text = "A VIAGEM DOS SEUS SONHOS ESTÁ AQUI!"
    desc1_text = place_names[0]
    desc2_text = place_names[1]
    desc3_text = place_names[2]

    wrapped_title_text = wrap_text_by_words1(title_text, 2)
    wrapped_subtitle_text = textwrap.fill(subtitle_text, width=25)
    wrapped_desc1_text = textwrap.fill(desc1_text, width=15)
    wrapped_desc2_text = textwrap.fill(desc2_text, width=15)
    wrapped_desc3_text = textwrap.fill(desc3_text, width=15)

    # Carregar e redimensionar a logo
    logo_image = Image.open(logo_path).convert("RGBA")
    logo_image = logo_image.resize((180, 200))  # Ajuste o tamanho conforme necessário
    logo_x = 20
    logo_y = 950

    # Colar a logo na imagem
    img.paste(logo_image, (logo_x, logo_y), logo_image)

    # Desenhar os textos na imagem
    draw.text(title_position, wrapped_title_text, font=title_font, fill='white')
    draw.text(subtitle_position, wrapped_subtitle_text, font=subtitle_font, fill='white')
    draw.text(desc1_position, wrapped_desc1_text, font=desc_font, fill='white')
    draw.text(desc2_position, wrapped_desc2_text, font=desc_font, fill='white')
    draw.text(desc3_position, wrapped_desc3_text, font=desc_font, fill='white')

    os.makedirs(f"../dados/{number}", exist_ok=True)
    # Salvar a imagem final
    output_path = f"../dados/{number}/capaTeste.png"
    img.save(output_path)

    return output_path

    # Mostrar a imagem final
    #img.show()

def morning_layout_1(place_names, dicas, dia_text, day_index, api_key=GOOGLE_PLACE_API_KEY):
#Testar para ver se as cores ficaram certas
#talvez para o titulo usar uma 3 cor mais presente na imagem

    # Caminho das imagens
    images = [get_place_photo(api_key, place_name) for place_name in place_names]

    logo_path = '../assets/logoVamo.png'  # Caminho para a logo
    # Carregar a imagem que será incluída na parte inferior
    bottom_image = images[0].resize((1080, 600))  # Redimensionar a imagem se necessário

    # Configurações de fonte
    font_path = '../assets/Brice-Bold-SemiExpanded.ttf'
    font_path2 = '../assets/Brice-Regular-SemiExpanded.ttf'
    title_font = ImageFont.truetype(font_path, 35)
    subtitle_font = ImageFont.truetype(font_path, 30)
    body_font = ImageFont.truetype(font_path2, 25)

    # Tamanho da nova imagem
    image_width, image_height = 1080, 1080

    top_colors1 = get_top_colors(bottom_image)
    bg_color1, text_color1 = choose_colors(top_colors1)

    # Criar uma nova imagem com fundo bg_color1
    new_image = Image.new('RGB', (image_width, image_height), bg_color1)

    # Desenhar textos
    draw = ImageDraw.Draw(new_image)

    dia_text = generate_day_text(day_index)
    title_text = f"{dia_text} dia de viagem!"  
    subtitle_text = f"Manhã: {place_names[0]} "  
    body_text = dicas[0]

    # Centralizar o título
    title_width, title_height = draw.textbbox((0, 0), title_text, font=title_font)[2:4]
    title_position = ((image_width - title_width) // 2, 20)

    # Coordenadas para os textos da coluna da esquerda
    subtitle_position = (50, 120)
    body_position = (50, 200)

    # Desenhando os textos
    draw.text(title_position, title_text, font=title_font, fill=text_color1) 
    draw_text(draw, subtitle_text, subtitle_position, subtitle_font, image_width - 100, text_color1)
    draw_text(draw, body_text, body_position, body_font, image_width - 100, text_color1)

    # Colar a imagem na parte inferior
    new_image.paste(bottom_image, (0, 600))

    # Carregar e redimensionar a logo
    logo_image = Image.open(logo_path).convert("RGBA")
    logo_image = logo_image.resize((180, 200))  # Ajuste o tamanho conforme necessário
    logo_x = 20
    logo_y = 950

    # Colar a logo na imagem
    new_image.paste(logo_image, (logo_x, logo_y), logo_image)

    # Salvar a nova imagem
    new_image.save('../dados/{number}/morning_{day}.png')
    new_image.show()

def day_odd_layout_1(place_names, dicas, day, dia_text, number, api_key=GOOGLE_PLACE_API_KEY):
    # Obter as imagens usando os nomes dos lugares
    images = [get_place_photo(api_key, place_name) for place_name in place_names]

    # Caminhos para as imagens e fon
    logo_path = "../assets/logoVamo.png"  # Caminho para a logo
    font_path_title = '../assets/Brice-Bold-SemiExpanded.ttf'
    font_path_subtitle = '../assets/Brice-SemiBoldExpanded.ttf'
    font_path_text = '../assets/Brice-Regular-SemiExpanded.ttf'

    # Dimensões da nova imagem
    image_width, image_height = 1080, 1080

    # Criar uma nova imagem com fundo branco
    img = Image.new('RGB', (image_width, image_height), 'white')
    draw = ImageDraw.Draw(img)

    # Redimensionar as imagens a serem inseridas
    image1 = images[0].resize((540, 540))  # Ajuste o tamanho conforme necessário
    image2 = images[1].resize((540, 540))  # Ajuste o tamanho conforme necessário

    # Posições das imagens
    image1_position = (540, 0)    # Imagem no canto superior direito
    image2_position = (0, 540)    # Imagem no canto inferior esquerdo

    # Colar as imagens na nova imagem
    img.paste(image1, image1_position)
    img.paste(image2, image2_position)

    # Cores de fundo para cada seção de texto
    # Obtém as cores principais
    top_colors1 = get_top_colors(image1)

    bg_color1, text_color1 = choose_colors(top_colors1)

    # Posições e tamanhos dos textos e retângulos
    section1_rect = [(0, 0), (540, 540)]
    section2_rect = [(540, 540), (1080, 1080)]

    # Desenhar retângulos coloridos atrás dos textos
    draw.rectangle(section1_rect, fill=bg_color1)
    draw.rectangle(section2_rect, fill=text_color1)

    # Fontes
    title_font = ImageFont.truetype(font_path_title, 23)
    subtitle_font = ImageFont.truetype(font_path_subtitle, 20)
    text_font = ImageFont.truetype(font_path_text, 18)

    # Títulos e Textos
    title1 = f"Tarde: {place_names[0]}"
    title2 = f"Noite: {place_names[1]}"
    text1 = dicas[0]
    text2 = dicas[1]

    # Posições dos títulos e textos
    title1_position = (20, 20)
    text1_position = (20, 100)
    title2_position = (560, 560)
    text2_position = (560, 640)

    # Desenhar os títulos e textos na imagem
    max_text_width1 = 540 - 40  # 540px de largura total menos 20px de cada lado
    max_text_width2 = 540 - 40  # 540px de largura total menos 20px de cada lado

    draw_text(draw, title1, title1_position, title_font, max_text_width1, text_color1)
    draw_text(draw, text1, text1_position, text_font, max_text_width1, text_color1)
    draw_text(draw, title2, title2_position, title_font, max_text_width2, bg_color1)
    draw_text(draw, text2, text2_position, text_font, max_text_width2, bg_color1)

    # Adicionar caixa com "Dia X" no meio do layout
    day_box_width, day_box_height = 130, 50
    day_box_position = ((image_width - day_box_width) // 2, (image_height - day_box_height) // 2 - 20)
    day_box = [(day_box_position[0], day_box_position[1]), 
                (day_box_position[0] + day_box_width, day_box_position[1] + day_box_height)]

    draw.rectangle(day_box, fill=bg_color1, outline="white")
    day_font = ImageFont.truetype(font_path_title, 25)
    day_text_size = draw.textbbox((0, 0), dia_text, font=day_font)
    day_text_position = (
        day_box_position[0] + (day_box_width - (day_text_size[2] - day_text_size[0])) // 2,
        day_box_position[1] + (day_box_height - (day_text_size[3] - day_text_size[1])) // 2
    )
    draw.text(day_text_position, dia_text, font=day_font, fill="white")

    # Carregar e redimensionar a logo
    logo_image = Image.open(logo_path).convert("RGBA")
    logo_image = logo_image.resize((180, 200))  # Ajuste o tamanho conforme necessário
    logo_x = 20
    logo_y = 950  

    # Colar a logo na imagem
    img.paste(logo_image, (logo_x, logo_y), logo_image)

    # Salvar a imagem final
    output_path = f"../dados/{number}/day_odd_{day}.png"
    img.save(output_path)
    
    # Mostrar a imagem final
    #img.show()
    return output_path

def day_even_layout_1(place_names, dicas, day, dia_text, number, api_key=GOOGLE_PLACE_API_KEY):
    # Obter as imagens usando os nomes dos lugares
    images = [get_place_photo(api_key, place_name) for place_name in place_names]

    # Caminho para a logo
    logo_path = '../assets/logoVamo.png'
    # Caminhos para as fontes
    font_path_title = '../assets/Brice-Bold-SemiExpanded.ttf'
    font_path_subtitle = '../assets/Brice-SemiBoldExpanded.ttf'
    font_path_text = '../assets/Brice-Regular-SemiExpanded.ttf'

    # Verificar se os arquivos de fonte existem
    if not os.path.exists(font_path_title) or not os.path.exists(font_path_subtitle) or not os.path.exists(font_path_text):
        raise FileNotFoundError("O arquivo de fonte não foi encontrado. Verifique o caminho.")

    # Dimensões da nova imagem
    image_width, image_height = 1080, 1080

    # Criar uma nova imagem com fundo branco
    img = Image.new('RGB', (image_width, image_height), 'white')
    draw = ImageDraw.Draw(img)

    # Redimensionar as imagens a serem inseridas
    image1 = images[0].resize((540, 540))  # Ajuste o tamanho conforme necessário
    image2 = images[1].resize((540, 540))  # Ajuste o tamanho conforme necessário

    # Posições das imagens
    image1_position = (0, 0)    # Imagem no canto superior esquerdo
    image2_position = (540, 540)    # Imagem no canto inferior direito

    # Colar as imagens na nova imagem
    img.paste(image1, image1_position)
    img.paste(image2, image2_position)

    # Obtém as cores principais
    top_colors1 = get_top_colors(image1)
    bg_color1, text_color1 = choose_colors(top_colors1)

    # Posições e tamanhos dos textos e retângulos
    section1_rect = [(540, 0), (1080, 540)]
    section2_rect = [(0, 540), (540, 1080)]

    # Desenhar retângulos coloridos atrás dos textos
    draw.rectangle(section1_rect, fill=bg_color1)
    draw.rectangle(section2_rect, fill=text_color1)

    # Fontes
    title_font = ImageFont.truetype(font_path_title, 23)
    subtitle_font = ImageFont.truetype(font_path_subtitle, 20)
    text_font = ImageFont.truetype(font_path_text, 18)

    # Títulos e Textos
    title1 = f"Tarde: {place_names[0]}"
    title2 = f"Noite: {place_names[1]}"

    text1 = dicas[0]
    text2 = dicas[1]

    # Posições dos títulos e textos
    title1_position = (560, 20)
    text1_position = (560, 100)
    title2_position = (20, 560)
    text2_position = (20, 640)

    # Desenhar os títulos e textos na imagem
    max_text_width1 = 540 - 40  # 540px de largura total menos 20px de cada lado
    max_text_width2 = 540 - 40  # 540px de largura total menos 20px de cada lado

    draw_text(draw, title1, title1_position, title_font, max_text_width1, text_color1)
    draw_text(draw, text1, text1_position, text_font, max_text_width1, text_color1)
    draw_text(draw, title2, title2_position, title_font, max_text_width2, bg_color1)
    draw_text(draw, text2, text2_position, text_font, max_text_width2, bg_color1)

    # Adicionar caixa com "Dia X" no meio do layout
    day_box_width, day_box_height = 130, 50
    day_box_position = ((image_width - day_box_width) // 2, (image_height - day_box_height) // 2 - 20)
    day_box = [(day_box_position[0], day_box_position[1]), 
                (day_box_position[0] + day_box_width, day_box_position[1] + day_box_height)]

    draw.rectangle(day_box, fill=bg_color1, outline="white")
    day_font = ImageFont.truetype(font_path_title, 25)
    day_text_size = draw.textbbox((0, 0), dia_text, font=day_font)
    day_text_position = (
        day_box_position[0] + (day_box_width - (day_text_size[2] - day_text_size[0])) // 2,
        day_box_position[1] + (day_box_height - (day_text_size[3] - day_text_size[1])) // 2
    )
    draw.text(day_text_position, dia_text, font=day_font, fill="white")

    # Carregar e redimensionar a logo
    logo_image = Image.open(logo_path).convert("RGBA")
    logo_image = logo_image.resize((180, 200))  # Ajuste o tamanho conforme necessário
    logo_x = 850
    logo_y = 950  

    # Colar a logo na imagem
    img.paste(logo_image, (logo_x, logo_y), logo_image)

    # Salvar a imagem final
    output_path = f"../dados/{number}/day_even_{day}.png"
    img.save(output_path)

    # Mostrar a imagem final
    #img.show()
    return output_path

def close_layout_1(place_names, number, api_key=GOOGLE_PLACE_API_KEY):
    # Obter as imagens usando os nomes dos lugares
    images = [get_place_photo(api_key, place_name) for place_name in place_names]

    # Caminho para a logo
    logo_path = '../assets/logoVamo.png'

    # Caminhos para as fontes
    font_path_title = '../assets/Brice-SemiBoldExpanded.ttf'
    font_path_subtitle = '../assets/Brice-SemiBoldExpanded.ttf'

    # Verificar se os arquivos de fonte existem
    if not os.path.exists(font_path_title) or not os.path.exists(font_path_subtitle):
        raise FileNotFoundError("O arquivo de fonte não foi encontrado. Verifique o caminho.")

    # Dimensões da nova imagem
    image_width, image_height = 1080, 1350

    # Criar uma nova imagem com fundo branco
    img = Image.new('RGB', (image_width, image_height), 'white')
    draw = ImageDraw.Draw(img)

    # Redimensionar as imagens a serem inseridas
    image1 = images[0].resize((540, 675))  # Ajuste o tamanho conforme necessário
    image2 = images[1].resize((1080, 675))  # Ajuste o tamanho conforme necessário

    # Posições das imagens
    image1_position = (540, 0)    # Imagem no canto superior direito
    image2_position = (0, 675)    # Imagem na parte inferior

    # Colar as imagens na nova imagem
    img.paste(image1, image1_position)
    img.paste(image2, image2_position)

    # Obtém as cores principais
    top_colors1 = get_top_colors(image1)
    bg_color1, text_color1 = choose_colors(top_colors1)

    # Cores de fundo para cada seção de texto
    background_color1 = bg_color1 
    background_color2 = text_color1  

    # Posições e tamanhos dos textos e retângulos
    section1_rect = [(0, 0), (540, 675)]
    section2_rect = [(0, 540), (1080, 675)]

    # Desenhar retângulos coloridos atrás dos textos
    draw.rectangle(section1_rect, fill=background_color1)
    draw.rectangle(section2_rect, fill=background_color2)

    # Fontes
    title_font = ImageFont.truetype(font_path_title, 38)
    subtitle_font = ImageFont.truetype(font_path_subtitle, 35)

    # Títulos e Textos
    title1 = "Quer comprar o seu Roteiro Personalizado em apenas uma mensagem?"
    subtitle1 = "Digite 'Vamo ai' e viaje com a gente!"

    # Posições dos títulos e textos
    title1_position = (20, 120)
    subtitle1_position = (20, 600)

    # Largura máxima para o texto
    max_text_width = 540 - 40  # 540px de largura total menos 20px de cada lado

    # Desenhar os títulos e textos na imagem
    draw_text(draw, title1, title1_position, title_font, max_text_width, text_color1)
    draw_text(draw, subtitle1, subtitle1_position, subtitle_font, image_width - 40, bg_color1)

    # Carregar e redimensionar a logo
    logo_image = Image.open(logo_path).convert("RGBA")
    logo_image = logo_image.resize((200, 220))  # Ajuste o tamanho conforme necessário
    logo_x = 20
    logo_y = 1200  

    # Colar a logo na imagem
    img.paste(logo_image, (logo_x, logo_y), logo_image)

    # Salvar a imagem final
    output_path = f"../dados/{number}/close_layout1.png"
    img.save(output_path)

    # Mostrar a imagem final
    #img.show()
    return output_path

def generate_pdf(images, number):
    # Converter todas as imagens para o modo RGB
    layouts = [Image.open(image).convert('RGB') for image in images]

    # Salvar as imagens em um PDF
    pdf_path = f'../dados/{number}/{number}.pdf'
    layouts[0].save(pdf_path, save_all=True, append_images=layouts[1:])

def generate_itineray(roteiro, number):
    dias = roteiro.get('roteiro').keys()
    atracoes = []
    for index, dia in enumerate(dias):
        atracoes.append(roteiro.get('roteiro').get(dia).get('atracoes')[0])
    count = 1
    while len(atracoes) < 4:
        atracoes.append(roteiro.get('roteiro').get(dia).get('atracoes')[count])
        count += 1
    capa_path = capa_layout_1(atracoes, number)
    count_even_days = 0
    count_odd_days = 0

    days_even_paths = []
    days_odd_paths = []

    for index, dia in enumerate(dias):
        cidade = roteiro.get('roteiro').get(dia).get('Cidade')
        atracoes = roteiro.get('roteiro').get(dia).get('atracoes')
        dicas = roteiro.get('roteiro').get(dia).get('dicas')
        
        # Gerar o texto dinâmico para "Dia X"
        dia_text = f"Dia {index + 1}"

        if index % 2 != 0:
            count_odd_days +=1
            path = day_odd_layout_1(atracoes, dicas, count_odd_days, dia_text, number)
            days_even_paths.append(path)
        elif index % 2 == 0:
            count_even_days +=1
            path = day_even_layout_1(atracoes, dicas, count_even_days, dia_text, number)
            days_odd_paths.append(path)
            
    cidade = roteiro.get('roteiro').get('dia_02').get('Cidade')
    atracoes = roteiro.get('roteiro').get('dia_02').get('atracoes')
    atracoes.append(cidade[0])
    close_path = close_layout_1(atracoes, number)
    final_paths = []
    final_paths.append(capa_path)

    tamanho_max = max(len(days_odd_paths), len(days_even_paths))
    
    # Itera sobre o tamanho máximo dos vetores
    for i in range(tamanho_max):
        # Adiciona o elemento do primeiro vetor se existir
        if i < len(days_odd_paths):
            final_paths.append(days_odd_paths[i])
        # Adiciona o elemento do segundo vetor se existir
        if i < len(days_even_paths):
            final_paths.append(days_even_paths[i])
    final_paths.append(close_path)

    generate_pdf(final_paths, number)

def generate_day_text(index):
    # Dicionário para mapeamento de números para palavras
    day_words = {
        0: "Primeiro",
        1: "Segundo",
        2: "Terceiro",
        3: "Quarto",
        4: "Quinto",
        5: "Sexto",
        6: "Sétimo",
        7: "Oitavo"
    }
    
    # Obter a palavra correspondente ao índice
    return day_words.get(index, f"{index + 1}º")

"""
resp_gpt = {
  "roteiro": {
    "dia_01": {
      "Cidade": ["Vitória"],
      "atracoes": ["Praia de Camburi", "Parque Pedra da Cebola", "Centro Histórico de Vitória"],
      "descricoes": [
        "A Praia de Camburi é a principal praia de Vitória, com uma extensa faixa de areia e ótima infraestrutura.",
        "O Parque Pedra da Cebola é um espaço verde ideal para caminhadas, piqueniques e apreciar a vista da cidade.",
        "O Centro Histórico de Vitória possui importantes edificações e igrejas, como a Catedral Metropolitana."
      ],
      "descricoes_historicas": [
        "Vitória, a capital do Espírito Santo, foi fundada em 1551 e possui um rico patrimônio histórico.",
        "A Catedral Metropolitana de Vitória, construída em estilo neogótico, é um dos principais marcos históricos da cidade."
      ],
      "dicas": [
        "Leve protetor solar e água para se manter hidratado na praia.",
        "Use roupas confortáveis para explorar o parque e o centro histórico.",
        "Prove a moqueca capixaba em um dos restaurantes locais."
      ]
    },
    "dia_02": {
      "Cidade": ["Vila Velha"],
      "atracoes": ["Praia da Costa", "Convento da Penha", "Fábrica de Chocolates Garoto"],
      "descricoes": [
        "A Praia da Costa é uma das praias mais famosas do Espírito Santo, conhecida por sua beleza e estrutura.",
        "O Convento da Penha é um dos santuários religiosos mais antigos do Brasil, situado no alto de um morro com vista panorâmica.",
        "A Fábrica de Chocolates Garoto oferece visitas guiadas onde é possível conhecer o processo de produção e degustar chocolates."
      ],
      "descricoes_historicas": [
        "O Convento da Penha, fundado em 1558, é um dos locais de peregrinação mais importantes do Espírito Santo."
      ],
      "dicas": [
        "Use calçados confortáveis para subir até o Convento da Penha.",
        "Leve uma câmera fotográfica para capturar as vistas panorâmicas.",
        "Na fábrica da Garoto, compre chocolates a preços mais acessíveis na loja de fábrica."
      ]
    },
    "dia_03": {
      "Cidade": ["Guarapari"],
      "atracoes": ["Praia do Morro", "Praia da Areia Preta", "Praia de Meaípe"],
      "descricoes": [
        "A Praia do Morro é uma das mais movimentadas de Guarapari, com quiosques e opções de esportes aquáticos.",
        "A Praia da Areia Preta é conhecida pelas suas areias monazíticas, que dizem ter propriedades terapêuticas.",
        "A Praia de Meaípe é famosa por suas águas calmas e pelos restaurantes de frutos do mar."
      ],
      "descricoes_historicas": [
        "Guarapari é conhecida como a 'Cidade Saúde' devido às propriedades medicinais de suas areias monazíticas."
      ],
      "dicas": [
        "Chegue cedo para garantir um bom lugar nas praias mais populares.",
        "Experimente a culinária local, especialmente os pratos de frutos do mar.",
        "Aproveite para fazer caminhadas ao longo das praias e apreciar a natureza."
      ]
    },
    "dia_04": {
      "Cidade": ["Domingos Martins"],
      "atracoes": ["Pedra Azul", "Rota do Lagarto", "Centro de Domingos Martins"],
      "descricoes": [
        "A Pedra Azul é um dos cartões-postais do Espírito Santo, com trilhas e paisagens deslumbrantes.",
        "A Rota do Lagarto é uma estrada turística com belas vistas, pousadas e restaurantes.",
        "O Centro de Domingos Martins tem um charme europeu, com construções em estilo enxaimel e uma atmosfera acolhedora."
      ],
      "descricoes_historicas": [
        "Domingos Martins foi colonizada por imigrantes alemães e italianos, refletindo em sua arquitetura e cultura."
      ],
      "dicas": [
        "Use roupas e calçados apropriados para trilhas na Pedra Azul.",
        "Prove as delícias da culinária alemã e italiana nos restaurantes locais.",
        "Reserve um tempo para explorar as lojinhas e cafés no centro de Domingos Martins."
      ]
    }
  }
}

generate_itineray(resp_gpt, '1')
"""
