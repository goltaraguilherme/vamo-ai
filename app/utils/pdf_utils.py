import os
import textwrap
import requests
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from io import BytesIO
from collections import Counter
#from dotenv import load_dotenv

#load_dotenv()

GOOGLE_PLACE_API_KEY = "-"
def get_place_id(api_key, place_name):
    try:
        place_name = f"{place_name}, Domingos Martins" if place_name.upper() == "PEDRA AZUL" else place_name
        place_name = f"{place_name}, Vitoria" if place_name in ["Praia de Camburi", "Triângulo das Bermudas"] else place_name
        place_search_url = f'https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={place_name}&inputtype=textquery&fields=place_id&key={api_key}'
        response = requests.get(place_search_url)
        response.raise_for_status()  # Levanta uma exceção para códigos de status HTTP de erro
        place_id = response.json()['candidates'][0]['place_id']
        return place_id
    except Exception as e:
        print(f"Erro ao obter o ID do local para {place_name}: {e}")
        return None

def get_place_photo(api_key, place_name, max_width=1024):
    try:
        place_id = get_place_id(api_key, place_name)
        if not place_id:
            return None

        place_details_url = f'https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=photos&key={api_key}'
        response = requests.get(place_details_url)
        response.raise_for_status()  # Levanta uma exceção para códigos de status HTTP de erro
        photo_reference = response.json()['result']['photos'][0]['photo_reference']
        
        try:  
            photo_url = f'https://maps.googleapis.com/maps/api/place/photo?maxwidth={max_width}&photoreference={photo_reference}&key={api_key}'
            photo_response = requests.get(photo_url)
            photo_response.raise_for_status()  # Levanta uma exceção para códigos de status HTTP de erro
            return Image.open(BytesIO(photo_response.content))
        except Exception as e:
            print(f"Erro ao obter a foto do local para {place_name}: {e}")
            return None
    except Exception as e:
        print(f"Erro ao obter os detalhes do local para {place_name}: {e}")
        return None
    

def round_corners(image, radius):
    mask = Image.new("L", image.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), image.size], radius, fill=255)
    output = Image.new("RGBA", image.size)
    output.paste(image, (0, 0), mask)
    return output

# Função para quebrar o texto a cada n palavras
def wrap_text_by_words2(text, max_width, draw, font):
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


def draw_text(draw, text, position, font, max_width, fill, line_spacing=20):
    # Quebrar o texto em frases com base no ponto final, mantendo o ponto
    sentences = [sentence + '.' for sentence in text.split('.') if sentence]
    lines = []
    for sentence in sentences:
        words = sentence.split()
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
        lines.append(' '.join(line))  # Adiciona a última linha da frase
        lines.append('')  # Adiciona uma linha em branco

    y = position[1]
    for line in lines:
        if line:  # Desenha somente se a linha não estiver vazia
            draw.text((position[0], y), line, font=font, fill=fill)
        y += draw.textbbox((0, 0), line, font=font)[3] - draw.textbbox((0, 0), line, font=font)[1] + line_spacing
    return draw, len([line for line in lines if line])  # Conta apenas as linhas não vazias


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

def draw_text_with_subtitles2(draw, position, text, text_font, subtitle_font, text_color, max_width):
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


# Função para quebrar linha limitando o número de caracteres por linha
def draw_text2(draw, text, position, font, max_width, fill, line_spacing=20, max_chars_per_line=12):
    words = text.split()
    lines = []
    line = ""
    
    for word in words:
        if len(line + word) + 1 > max_chars_per_line:
            lines.append(line.strip())
            line = word + " "
        else:
            line += word + " "
    
    if line:
        lines.append(line.strip())
    
    y = position[1]
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_width = bbox[2] - bbox[0]
        x = position[0] + (max_width - line_width) // 2
        draw.text((x, y), line, font=font, fill=fill)
        y += bbox[3] - bbox[1] + line_spacing
        if line.endswith('.'):
            y += line_spacing  # Adiciona um espaçamento extra após a linha com ponto final

# Função para criar o layout dos posts do instagram da 2 capa do roteiro
def create_instagram_post(draw, image, profile_name, likes, font):
    comentario_icon = Image.open('./app/assets/comentario.png').resize((50, 50))
    salvar_icon = Image.open('./app/assets/salvar.png').resize((50, 50))
    like_press_icon = Image.open('./app/assets/like_press.png').convert("RGBA").resize((50, 50))

    post_width, post_height = image.size
    post_image = Image.new('RGB', (post_width + 40, post_height + 150), '#FFFFFF')
    post_image.paste(image, (20, 50))

    draw = ImageDraw.Draw(post_image)
    profile_font = font
    likes_font = font

    # Desenhar retângulo arredondado branco
    rounded_rectangle_coords = [(0, 0), (post_width + 40, post_height + 150)]
    draw.rounded_rectangle(rounded_rectangle_coords, radius=15, fill='#FFFFFF')

    post_image.paste(image, (20, 50))

    # Adicionar texto
    draw.text((40, post_height - 280), profile_name, font=profile_font, fill='#000000')
    # Adicionar ícones
    icon_y_position = post_height + 60  # Ajuste a posição vertical dos ícones conforme necessário
    post_image.paste(like_press_icon, (10, icon_y_position), like_press_icon)
    post_image.paste(comentario_icon, (50, icon_y_position), comentario_icon)
    post_image.paste(salvar_icon, (270, icon_y_position), salvar_icon)

    # Adicionar texto de curtidas
    draw.text((20, icon_y_position + 60), f"{likes} curtidas", font=likes_font, fill='#000000')

    post_mask = Image.new("L", post_image.size, 0)
    post_draw = ImageDraw.Draw(post_mask)
    post_draw.rounded_rectangle(rounded_rectangle_coords, radius=15, fill=255)

    return post_image, post_mask

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
    return (255, 255, 255) if luminance < 128 else (0, 50, 200)

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
    logo_path = './app/assets/logoVamo.png'
    # Caminhos para as fontes
    font_path = './app/assets/Brice-Regular-SemiExpanded.ttf'
    font_path2 = './app/assets/Brice-Bold-SemiExpanded.ttf'

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
    print(images)
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
    desc1_text = place_names[0].split(',')[0]
    desc2_text = place_names[1].split(',')[0]
    desc3_text = place_names[2].split(',')[0]

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

    os.makedirs(f"./app/dados/{number}", exist_ok=True)
    # Salvar a imagem final
    output_path = f"./app/dados/{number}/capaTeste.png"
    img.save(output_path)

    return output_path

    # Mostrar a imagem final
    #img.show()

def capa_layout_2(place_names, header_text, number, api_key=GOOGLE_PLACE_API_KEY):
    try:
        print("Início da função capa_layout_2")
        
        if len(place_names) < 3:
            raise ValueError("É necessário pelo menos três locais para gerar a capa.")
        
        images = []
        for place_name in place_names[:3]:
            print(f"Obtendo foto para o local: {place_name}")
            image = get_place_photo(api_key, place_name)
            if image:
                print(f"Redimensionando imagem de {place_name}")
                images.append(image.resize((300, 300)))
            else:
                raise FileNotFoundError(f"Não foi possível obter a foto do local: {place_name}")
        
        wave_image_path_top = './app/assets/onda2.png'
        logo_path = './app/assets/logoVamo.png'

        font_path = './app/assets/Brice-SemiBoldExpanded.ttf'
        font_path2 = './app/assets/Brice-Regular-SemiExpanded.ttf'

        print("Verificando a existência das imagens e fontes")
        if not os.path.exists(wave_image_path_top):
            raise FileNotFoundError(f"A imagem não foi encontrada: {wave_image_path_top}")
        if not os.path.exists(logo_path):
            raise FileNotFoundError(f"A imagem não foi encontrada: {logo_path}")
        if not os.path.exists(font_path):
            raise FileNotFoundError(f"O arquivo de fonte não foi encontrado: {font_path}")
        if not os.path.exists(font_path2):
            raise FileNotFoundError(f"O arquivo de fonte não foi encontrado: {font_path2}")

        title_font = ImageFont.truetype(font_path, 30)
        body_font = ImageFont.truetype(font_path2, 15)

        image_width, image_height = 1080, 1080
        new_image = Image.new('RGB', (image_width, image_height), '#EBE3D2')

        print("Carregando e redimensionando a imagem da onda")
        wave_image_top = Image.open(wave_image_path_top).convert("RGBA")
        wave_image_top = wave_image_top.resize((1080, 800), Image.LANCZOS)
        new_image.paste(wave_image_top, (0, 0), wave_image_top)

        draw = ImageDraw.Draw(new_image)
        header_position = (-300, 100)
        max_width = image_width
        draw_text2(draw, header_text, header_position, title_font, max_width, fill='#3871C1')

        post_y = 300
        post_gap = 50  # Ajuste o espaço entre os posts laterais e o post do meio
        left_post_x = 60
        right_post_x = image_width - 400

        # Desenhar posts laterais primeiro
        for i, image in enumerate(images):
            print(f"Desenhando post {i+1}")
            if i == 0:  # Post lateral esquerdo
                post_image, post_mask = create_instagram_post(draw, image, "@vamoai", "123", body_font)
                new_image.paste(post_image, (left_post_x, post_y), post_mask)
            elif i == 2:  # Post lateral direito
                post_image, post_mask = create_instagram_post(draw, image, "@vamoai", "123", body_font)
                new_image.paste(post_image, (right_post_x, post_y), post_mask)
        
        # Desenhar post do meio por último para sobrepor os laterais
        print("Desenhando post do meio")
        post_image, post_mask = create_instagram_post(draw, images[1], "@vamoai", "123", body_font)
        center_post_x = (image_width - post_image.width) // 2
        new_image.paste(post_image, (center_post_x, post_y - 50), post_mask)

        print("Carregando e posicionando o logo")
        logo_image = Image.open(logo_path).convert("RGBA")
        logo_image = logo_image.resize((280, 300))
        logo_x = 400
        logo_y = 880
        new_image.paste(logo_image, (logo_x, logo_y), logo_image)

        os.makedirs(f"./app/dados/{number}", exist_ok=True)
        # Salvar a imagem final
        output_path = f"./app/dados/{number}/capa.png"
        new_image.save(output_path)

        print(f"Imagem salva em {output_path}")
        return output_path

    except Exception as e:
        print(f'Error: {e}')

def morning_layout_1(place_names, atividade, dicas, day_index, number, api_key=GOOGLE_PLACE_API_KEY):
    # Caminho das imagens
    images = [get_place_photo(api_key, place_name) for place_name in place_names]

    logo_path = './app/assets/logoVamo.png'  # Caminho para a logo
    # Carregar a imagem que será incluída na parte inferior
    bottom_image = images[0].resize((1080, 600))  # Redimensionar a imagem se necessário

    # Configurações de fonte
    font_path = './app/assets/Brice-Bold-SemiExpanded.ttf'
    font_path2 = './app/assets/Brice-Regular-SemiExpanded.ttf'
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
    title_text = f"{dia_text} dia!"  
    subtitle_text = f"Manhã: {atividade} "  
    body_text = dicas

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
    output_path = f'./app/dados/{number}/morning_{day_index}.png'
    new_image.save(output_path)
    
    return output_path

def morning_layout_2(place_names, atividade, dicas, day_index, number, api_key=GOOGLE_PLACE_API_KEY):
    try:
        print("Início da função morning_layout_2")
        print(f"place_names: {place_names}, atividade: {atividade}, dicas: {dicas}, day_index: {day_index}, number: {number}")

        # Obter a foto do local
        images = [get_place_photo(api_key, place_name) for place_name in place_names]
        print(f"Imagens obtidas: {images}")
        if not images or images[0] is None:
            raise ValueError("A foto não foi obtida corretamente")
        
        bottom_image = images[0].resize((1080, 600))  # Redimensionar a imagem se necessário
        print(f"Foto do local obtida e redimensionada: {bottom_image.size}")

        # Carregando imagens
        logo_path = './app/assets/logoVamo.png'
        wave_image_path = './app/assets/Onda.png'

        print(f"Verificando a existência das imagens: {logo_path} e {wave_image_path}")
        if not os.path.exists(logo_path):
            raise FileNotFoundError(f"A imagem não foi encontrada: {logo_path}")
        if not os.path.exists(wave_image_path):
            raise FileNotFoundError(f"A imagem não foi encontrada: {wave_image_path}")

        # Configurações de fonte
        font_path = './app/assets/Brice-SemiBoldExpanded.ttf' 
        font_path2 = './app/assets/Brice-Regular-SemiExpanded.ttf'

        print(f"Verificando a existência das fontes: {font_path} e {font_path2}")
        if not os.path.exists(font_path):
            raise FileNotFoundError(f"O arquivo de fonte não foi encontrado: {font_path}")
        if not os.path.exists(font_path2):
            raise FileNotFoundError(f"O arquivo de fonte não foi encontrado: {font_path2}")

        title_font = ImageFont.truetype(font_path, 50)
        subtitle_font = ImageFont.truetype(font_path, 26)
        body_font = ImageFont.truetype(font_path2, 22)

        # Tamanho da nova imagem
        image_width, image_height = 1080, 1080
        print(f"Tamanho da nova imagem: {image_width}x{image_height}")

        # Criar uma nova imagem com fundo branco
        new_image = Image.new('RGB', (image_width, image_height), '#FFFFFF')
        print("Nova imagem criada")

        # Colar a imagem na parte superior
        print("Colando a imagem na parte superior")
        new_image.paste(bottom_image, (0, 0))
        print("Imagem colada na parte superior")

        # Carregar a imagem da onda
        print("Carregando a imagem da onda")
        wave_image = Image.open(wave_image_path).convert("RGBA")
        wave_image = wave_image.resize((1080, 1250), Image.LANCZOS)
        print(f"Imagem da onda carregada e redimensionada: {wave_image.size}")

        # Criar uma máscara para a onda para preservar a transparência
        wave_mask = wave_image.split()[3]
        wave_mask = wave_mask.point(lambda i: i * 1.5)
        print("Máscara da onda criada")

        # Colar a imagem da onda na parte inferior usando a máscara
        print("Colando a imagem da onda na parte inferior")
        new_image.paste(wave_image, (0, -155), wave_mask)
        print("Imagem da onda colada na parte inferior")

        # Desenhar textos
        draw = ImageDraw.Draw(new_image)

        dia_text = generate_day_text(day_index)
        print(f"Texto do dia gerado: {dia_text}")
        title_text = f"{dia_text} dia!"  
        subtitle_text = f"Manhã: {atividade}"  
        body_text = dicas

        # Centralizar o título
        print("Centralizando e desenhando o título")
        title_width, title_height = draw.textbbox((0, 0), title_text, font=title_font)[2:4]
        print(f"Tamanho do título: {title_width}x{title_height}")
        title_position = ((image_width - title_width) // 10, 580)
        print(f"Posição do título: {title_position}")

        # Coordenadas para os textos
        subtitle_position = (50, 670)

        # Desenhando os textos
        print("Desenhando o título")
        #draw.text(title_position, title_text, font=title_font, fill='#3176F4')
        draw.text(title_position, title_text, font=title_font, fill='#3871C1')

        print("Desenhando subtitulo...")
        draw, lines_subtitle = draw_text(draw, subtitle_text, subtitle_position, subtitle_font, image_width - 100, '#000000')
        print(f"lines_subtitulo: {lines_subtitle}")

        # Ajustar a posição do texto baseado no número de linhas dos títulos
        body_position = (50, subtitle_position[1] + lines_subtitle * 50 + 10)  # 10 pixels de espaço

        print(f"Posição de text1: {body_position}")

        # Desenhar os textos
        print("Desenhando text1...")
        draw, lines_body = draw_text(draw, body_text, body_position, body_font, image_width - 100, '#000000')

        print(f"lines_body: {lines_body}")

        # Carregar e redimensionar a logo
        print("Carregando e redimensionando a logo")
        logo_image = Image.open(logo_path).convert("RGBA")
        logo_image = logo_image.resize((180, 200))  # Ajuste o tamanho conforme necessário
        print(f"Logo carregada e redimensionada: {logo_image.size}")
        logo_x = 20
        logo_y = 950

        # Colar a logo na imagem
        print("Colando a logo na imagem")
        new_image.paste(logo_image, (logo_x, logo_y), logo_image)
        print("Logo colada na imagem")

        # Salvar a nova imagem
        output_path = f'./app/dados/{number}/morning_{day_index}.png'
        print(f"Salvando a imagem em: {output_path}")
        new_image.save(output_path)
        print("Imagem salva")
        
        return output_path
    except Exception as e:
        print(f'Error: {e}')

def day_odd_layout_1(place_names, atividades, dicas, day, dia_text, number, api_key=GOOGLE_PLACE_API_KEY):
    # Obter as imagens usando os nomes dos lugares
    images = [get_place_photo(api_key, place_name) for place_name in place_names]

    # Caminhos para as imagens e fon
    logo_path = "./app/assets/logoVamo.png"  # Caminho para a logo
    font_path_title = './app/assets/Brice-Bold-SemiExpanded.ttf'
    font_path_subtitle = './app/assets/Brice-SemiBoldExpanded.ttf'
    font_path_text = './app/assets/Brice-Regular-SemiExpanded.ttf'

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
    title1 = f"Tarde: {atividades[0]}"
    title2 = f"Noite: {atividades[1]}"
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

    draw.rectangle(day_box, fill=(55, 148, 226), outline="white")
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
    output_path = f"./app/dados/{number}/day_odd_{day}.png"
    img.save(output_path)
    
    # Mostrar a imagem final
    #img.show()
    return output_path

def day_odd_layout_2(place_names, atividades, dicas, day, dia_text, number, api_key=GOOGLE_PLACE_API_KEY):
    # Obter as imagens usando os nomes dos lugares
    images = [get_place_photo(api_key, place_name) for place_name in place_names]

    # Caminhos para as imagens e fon
    logo_path = "./app/assets/logoVamo.png"  # Caminho para a logo
    font_path_title = './app/assets/Brice-Bold-SemiExpanded.ttf'
    font_path_subtitle = './app/assets/Brice-SemiBoldExpanded.ttf'
    font_path_text = './app/assets/Brice-Regular-SemiExpanded.ttf'

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
    background_color1 = "#03487a"  # Azul escuro
    background_color2 = "#EBE3D2"    # Branco

    # Posições e tamanhos dos textos e retângulos
    section1_rect = [(0, 0), (540, 540)]
    section2_rect = [(540, 540), (1080, 1080)]

    # Desenhar retângulos coloridos atrás dos textos
    draw.rectangle(section1_rect, fill=background_color1)
    draw.rectangle(section2_rect, fill=background_color2)

    # Fontes
    title_font = ImageFont.truetype(font_path_title, 23)
    subtitle_font = ImageFont.truetype(font_path_subtitle, 22)
    text_font = ImageFont.truetype(font_path_text, 20)

    # Títulos e Textos
    title1 = f"Tarde: {atividades[0]}"
    title2 = f"Noite: {atividades[1]}"
    text1 = dicas[0]
    text2 = dicas[1]

    # Posições dos títulos e textos
    title1_position = (20, 20)
    title2_position = (560, 560)

    # Desenhar os títulos e textos na imagem
    max_text_width1 = 540 - 40  # 540px de largura total menos 20px de cada lado
    max_text_width2 = 540 - 40  # 540px de largura total menos 20px de cada lado

    print("Desenhando title1...")
    draw, lines_title1 = draw_text(draw, title1, title1_position, title_font, max_text_width1, 'white')
    print(f"lines_title1: {lines_title1}")

    print("Desenhando title2...")
    draw, lines_title2 = draw_text(draw, title2, title2_position, title_font, max_text_width2, '#03487a')
    print(f"lines_title2: {lines_title2}")

    # Ajustar a posição do texto baseado no número de linhas dos títulos
    text1_position = (20, title1_position[1] + lines_title1 * 45 + 10)  # 10 pixels de espaço
    text2_position = (560, title2_position[1] + lines_title2 * 45 + 10)  # 10 pixels de espaço

    print(f"Posição de text1: {text1_position}")
    print(f"Posição de text2: {text2_position}")

    # Desenhar os textos
    print("Desenhando text1...")
    draw, lines_text1 = draw_text(draw, text1, text1_position, text_font, max_text_width1, 'white')
    print(f"lines_text1: {lines_text1}")

    print("Desenhando text2...")
    draw, lines_text2 = draw_text(draw, text2, text2_position, text_font, max_text_width2, '#03487a')
    print(f"lines_text1: {lines_text2}")

    # Adicionar caixa com "Dia X" no meio do layout
    day_box_width, day_box_height = 130, 50
    day_box_position = ((image_width - day_box_width) // 2, (image_height - day_box_height) // 2 - 20)
    day_box = [(day_box_position[0], day_box_position[1]), 
                (day_box_position[0] + day_box_width, day_box_position[1] + day_box_height)]

    draw.rectangle(day_box, fill='#03487a', outline="white")
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
    output_path = f"./app/dados/{number}/day_odd_{day}.png"
    img.save(output_path)
    
    # Mostrar a imagem final
    #img.show()
    return output_path

def day_even_layout_1(place_names, atividades, dicas, day, dia_text, number, api_key=GOOGLE_PLACE_API_KEY):
    # Obter as imagens usando os nomes dos lugares
    images = [get_place_photo(api_key, place_name) for place_name in place_names]

    # Caminho para a logo
    logo_path = './app/assets/logoVamo.png'
    # Caminhos para as fontes
    font_path_title = './app/assets/Brice-Bold-SemiExpanded.ttf'
    font_path_subtitle = './app/assets/Brice-SemiBoldExpanded.ttf'
    font_path_text = './app/assets/Brice-Regular-SemiExpanded.ttf'

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
    title1 = f"Tarde: {atividades[0]}"
    title2 = f"Noite: {atividades[1]}"

    text1 = dicas[0]
    text2 = dicas[1]

    # Posições dos títulos e textos
    title1_position = (560, 20)
    title2_position = (20, 560)

    # Desenhar os títulos e textos na imagem
    max_text_width1 = 540 - 40  # 540px de largura total menos 20px de cada lado
    max_text_width2 = 540 - 40  # 540px de largura total menos 20px de cada lado


    print("Desenhando title1...")
    lines_title1 = draw_text3(draw, title1, title1_position, title_font, max_text_width1, 'white')
    print(f"lines_title1: {lines_title1}")

    print("Desenhando title2...")
    lines_title2 = draw_text3(draw, title2, title2_position, title_font, max_text_width2, '#03487a')
    print(f"lines_title2: {lines_title2}")

    # Ajustar a posição do texto baseado no número de linhas dos títulos
 # Ajustar a posição do texto baseado no número de linhas dos títulos
    text1_position = (560, title1_position[1] + lines_title1 * 50 + 10)  # 10 pixels de espaço
    text2_position = (20, title2_position[1] + lines_title2 * 50 + 10)  # 10 pixels de espaço


    print(f"Posição de text1: {text1_position}")
    print(f"Posição de text2: {text2_position}")

    # Desenhar os textos
    print("Desenhando text1...")
    draw_text3(draw, text1, text1_position, text_font, max_text_width1, 'white')
    print("Desenhando text2...")
    draw_text3(draw, text2, text2_position, text_font, max_text_width2, '#03487a')
    # Adicionar caixa com "Dia X" no meio do layout
    day_box_width, day_box_height = 130, 50
    day_box_position = ((image_width - day_box_width) // 2, (image_height - day_box_height) // 2 - 20)
    day_box = [(day_box_position[0], day_box_position[1]), 
                (day_box_position[0] + day_box_width, day_box_position[1] + day_box_height)]

    draw.rectangle(day_box, fill=(55, 148, 226), outline="white")
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
    output_path = f"./app/dados/{number}/day_even_{day}.png"
    img.save(output_path)

    # Mostrar a imagem final
    #img.show()
    return output_path

def day_even_layout_2(place_names, atividades, dicas, day, dia_text, number, api_key=GOOGLE_PLACE_API_KEY):
    # Obter as imagens usando os nomes dos lugares
    images = [get_place_photo(api_key, place_name) for place_name in place_names]

    # Caminho para a logo
    logo_path = './app/assets/logoVamo.png'
    # Caminhos para as fontes
    font_path_title = './app/assets/Brice-Bold-SemiExpanded.ttf'
    font_path_subtitle = './app/assets/Brice-SemiBoldExpanded.ttf'
    font_path_text = './app/assets/Brice-Regular-SemiExpanded.ttf'

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

    # Cores de fundo para cada seção de texto
    background_color1 = '#03487a'  # Azul escuro para o texto superior direito
    background_color2 = "#EBE3D2"  # Branco para o texto inferior esquerdo

    # Posições e tamanhos dos textos e retângulos
    section1_rect = [(540, 0), (1080, 540)]
    section2_rect = [(0, 540), (540, 1080)]

    # Desenhar retângulos coloridos atrás dos textos (opcional)
    draw.rectangle(section1_rect, fill=background_color1)
    draw.rectangle(section2_rect, fill=background_color2)

    # Fontes
    title_font = ImageFont.truetype(font_path_title, 23)
    subtitle_font = ImageFont.truetype(font_path_subtitle, 22)
    text_font = ImageFont.truetype(font_path_text, 20)

    # Títulos e Textos
    title1 = f"Tarde: {atividades[0]}"
    title2 = f"Noite: {atividades[1]}"

    text1 = dicas[0]
    text2 = dicas[1]

    # Posições dos títulos e textos
    title1_position = (560, 20)
    title2_position = (20, 560)

     # Desenhar os títulos e contar as linhas
    max_text_width1 = 540 - 40  # 540px de largura total menos 20px de cada lado
    max_text_width2 = 540 - 40  # 540px de largura total menos 20px de cada lado

    print("Desenhando title1...")
    draw, lines_title1 = draw_text(draw, title1, title1_position, title_font, max_text_width1, 'white')
    print(f"lines_title1: {lines_title1}")

    print("Desenhando title2...")
    draw, lines_title2 = draw_text(draw, title2, title2_position, title_font, max_text_width2, '#03487a')
    print(f"lines_title2: {lines_title2}")

    # Ajustar a posição do texto baseado no número de linhas dos títulos
    text1_position = (560, title1_position[1] + lines_title1 * 45 + 10)  # 10 pixels de espaço
    text2_position = (20, title2_position[1] + lines_title2 * 45 + 10)  # 10 pixels de espaço

    print(f"Posição de text1: {text1_position}")
    print(f"Posição de text2: {text2_position}")

    # Desenhar os textos
    print("Desenhando text1...")
    draw, lines_text1 = draw_text(draw, text1, text1_position, text_font, max_text_width1, 'white')
    print(f"lines_text1: {lines_text1}")

    print("Desenhando text2...")
    draw, lines_text2 = draw_text(draw, text2, text2_position, text_font, max_text_width2, '#03487a')
    print(f"lines_text1: {lines_text2}")


    # Adicionar caixa com "Dia X" no meio do layout
    day_box_width, day_box_height = 130, 50
    day_box_position = ((image_width - day_box_width) // 2, (image_height - day_box_height) // 2 - 20)
    day_box = [(day_box_position[0], day_box_position[1]), 
                (day_box_position[0] + day_box_width, day_box_position[1] + day_box_height)]

    draw.rectangle(day_box, fill='#03487a', outline="white")
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
    output_path = f"./app/dados/{number}/day_even_{day}.png"
    img.save(output_path)

    # Mostrar a imagem final
    #img.show()
    return output_path

def close_layout_1(place_names, number, api_key=GOOGLE_PLACE_API_KEY):
    # Obter as imagens usando os nomes dos lugares
    images = [get_place_photo(api_key, place_name) for place_name in place_names]

    # Caminho para a logo
    logo_path = './app/assets/logoVamo.png'

    # Caminhos para as fontes
    font_path_title = './app/assets/Brice-SemiBoldExpanded.ttf'
    font_path_subtitle = './app/assets/Brice-SemiBoldExpanded.ttf'

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

    background_color1 = "#03487a"  # Azul escuro
    background_color2 = "#EBE3D2"    # Branco

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
    draw_text(draw, title1, title1_position, title_font, max_text_width,  fill='white')
    draw_text(draw, subtitle1, subtitle1_position, subtitle_font, image_width - 40, fill='#03487a')

    # Carregar e redimensionar a logo
    logo_image = Image.open(logo_path).convert("RGBA")
    logo_image = logo_image.resize((200, 220))  # Ajuste o tamanho conforme necessário
    logo_x = 20
    logo_y = 1200  

    # Colar a logo na imagem
    img.paste(logo_image, (logo_x, logo_y), logo_image)

    # Salvar a imagem final
    output_path = f"./app/dados/{number}/close_layout1.png"
    img.save(output_path)

    # Mostrar a imagem final
    #img.show()
    return output_path

def generate_pdf(images, number):
    # Converter todas as imagens para o modo RGB
    layouts = [Image.open(image).convert('RGB') for image in images]

    # Salvar as imagens em um PDF
    pdf_path = f'./app/dados/{number}/{number}.pdf'
    layouts[0].save(pdf_path, save_all=True, append_images=layouts[1:])
"""
def generate_itinerary(roteiro, number):
    try:
      dias = roteiro.get('roteiro').keys()
      print(dias)
      atracoes = []
      for index, dia in enumerate(dias):
          print(index, dia)
          atracoes.append(roteiro.get('roteiro').get(dia).get("tarde").get("localizacao"))
      if(len(atracoes) < 4): atracoes.append(roteiro.get('roteiro').get("dia_01").get("noite").get("localizacao"))
      print(atracoes)
      capa_path = capa_layout_2(atracoes, number)
      count_even_days = 0
      count_odd_days = 0

      days_even_paths = []
      days_odd_paths = []
      morning_paths = []
      turnos = ["manha", "tarde", "noite"]
      
      for index, dia in enumerate(dias):
          atracoes = []
          atividades = []
          dicas = []
          #cidade = roteiro.get('roteiro').get(dia).get('Cidade')[0]

          for turno in turnos:
            atividade = roteiro.get('roteiro').get(dia).get(turno).get("atividade")
            local = roteiro.get('roteiro').get(dia).get(turno).get("localizacao")
            dica = "\n".join(roteiro.get('roteiro').get(dia).get(turno).get("comentarios"))
            if turno == "manha": 
              path = morning_layout_2([local], atividade, dica, index, number)
              morning_paths.append(path)
            else:
              dicas.append(dica)
              atracoes.append(local)
              atividades.append(atividade)

          # Gerar o texto dinâmico para "Dia X"
          dia_text = f"Dia {index + 1}"

          if index % 2 != 0:
              count_odd_days +=1
              path = day_odd_layout_2(atracoes, atividades, dicas, count_odd_days, dia_text, number)
              days_even_paths.append(path)
          elif index % 2 == 0:
              count_even_days +=1
              path = day_even_layout_2(atracoes, atividades, dicas, count_even_days, dia_text, number)
              days_odd_paths.append(path)
              
      atracoes = []
      cidade = roteiro.get('roteiro').get('dia_02').get('Cidade')[0]
      atracoes.append(list(roteiro.get('roteiro').get('dia_02').get('detalhes')[0].get("Tarde").keys())[0]+f", {cidade}")
      atracoes.append(cidade)
      close_path = close_layout_1(atracoes, number)
      
      final_paths = []
      final_paths.append(capa_path)
      
      tamanho_max = max(len(days_odd_paths), len(days_even_paths))
      
      count_mornings = 0
      # Itera sobre o tamanho máximo dos vetores
      for i in range(tamanho_max):
          # Adiciona o elemento do primeiro vetor se existir
          if i < len(days_odd_paths):
              final_paths.append(morning_paths[count_mornings])
              count_mornings += 1
              final_paths.append(days_odd_paths[i])
          # Adiciona o elemento do segundo vetor se existir
          if i < len(days_even_paths):
              final_paths.append(morning_paths[count_mornings])
              count_mornings += 1
              final_paths.append(days_even_paths[i])
      #final_paths.append(close_path)

      generate_pdf(final_paths, number)

      return 'success'
    except:
      print('error')
"""
def generate_itinerary(roteiro, number):
    try:
        print("Início da função generate_itinerary")
        
        dias = roteiro.get('roteiro').keys()
        print(f"Dias no roteiro: {dias}")
        
        atracoes = []
        for index, dia in enumerate(dias):
            print(f"Processando dia: {index}, {dia}")
            try:
                tarde_local = roteiro.get('roteiro').get(dia).get("tarde").get("localizacao")
                print(f"Localização da tarde: {tarde_local}")
                atracoes.append(tarde_local)
            except Exception as e:
                print(f"Erro ao obter localização da tarde: {e}")
        
        if len(atracoes) < 4:
            try:
                noite_local = roteiro.get('roteiro').get("dia_01").get("noite").get("localizacao")
                print(f"Localização da noite: {noite_local}")
                atracoes.append(noite_local)
            except Exception as e:
                print(f"Erro ao obter localização da noite: {e}")
        
        print(f"Atrações: {atracoes}")
        
        try:
            capa_path = capa_layout_2(atracoes, "Seu companheiro de viagem!", number)
            print(f"Caminho da capa: {capa_path}")
        except Exception as e:
            print(f"Erro ao gerar capa: {e}")

        count_even_days = 0
        count_odd_days = 0

        days_even_paths = []
        days_odd_paths = []
        morning_paths = []
        turnos = ["manha", "tarde", "noite"]
        
        for index, dia in enumerate(dias):
            print(f"Processando dia: {index}, {dia}")
            atracoes = []
            atividades = []
            dicas = []
            
            for turno in turnos:
                try:
                    atividade = roteiro.get('roteiro').get(dia).get(turno).get("atividade")
                    local = roteiro.get('roteiro').get(dia).get(turno).get("localizacao")
                    comentarios = roteiro.get('roteiro').get(dia).get(turno).get("comentarios")
                    dica = "\n".join(comentarios)
                    
                    print(f"Turno: {turno}, Atividade: {atividade}, Local: {local}, Dica: {dica}")
                    
                    if turno == "manha": 
                        path = morning_layout_2([local], atividade, dica, index, number)
                        print(f"Caminho da manhã: {path}")
                        morning_paths.append(path)
                    else:
                        dicas.append(dica)
                        atracoes.append(local)
                        atividades.append(atividade)
                except Exception as e:
                    print(f"Erro ao processar turno {turno}: {e}")

            dia_text = f"Dia {index + 1}"
            print(f"Texto do dia: {dia_text}")

            try:
                if index % 2 != 0:
                    count_odd_days += 1
                    path = day_odd_layout_2(atracoes, atividades, dicas, count_odd_days, dia_text, number)
                    print(f"Caminho do dia ímpar: {path}")
                    days_even_paths.append(path)
                else:
                    count_even_days += 1
                    path = day_even_layout_2(atracoes, atividades, dicas, count_even_days, dia_text, number)
                    print(f"Caminho do dia par: {path}")
                    days_odd_paths.append(path)
            except Exception as e:
                print(f"Erro ao gerar layout do dia: {e}")

        final_paths = []
        final_paths.append(capa_path)
        print(f"Caminhos finais até agora: {final_paths}")

        tamanho_max = max(len(days_odd_paths), len(days_even_paths))
        print(f"Tamanho máximo: {tamanho_max}")

        count_mornings = 0
        for i in range(tamanho_max):
            try:
                if i < len(days_odd_paths):
                    final_paths.append(morning_paths[count_mornings])
                    count_mornings += 1
                    final_paths.append(days_odd_paths[i])
                if i < len(days_even_paths):
                    final_paths.append(morning_paths[count_mornings])
                    count_mornings += 1
                    final_paths.append(days_even_paths[i])
            except Exception as e:
                print(f"Erro ao iterar sobre os caminhos finais: {e}")
        
        print(f"Caminhos finais: {final_paths}")

        try:
            generate_pdf(final_paths, number)
            print(f"PDF gerado com sucesso para o número: {number}")
        except Exception as e:
            print(f"Erro ao gerar PDF: {e}")

    except Exception as e:
        print(f"Erro geral: {e}")


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
    return day_words.get(index, f"{index}º")

resp_gpt = {
  "destino": "Espírito Santo, Brasil",
  "data": "15 a 21 de setembro de 2024",
  "roteiro": {
    "dia_01": {
      "manha": {
        "atividade": "Chegada ao hotel e check-in; Caminhada pela Praia da Costa em Vila Velha, visitando as barracas de praia e apreciando a vista.",
        "localizacao": "Praia da Costa, Vila Velha",
        "comentarios": [
          "Praia da Costa é uma das praias mais conhecidas do Espírito Santo e oferece uma bela vista do Atlântico.",
          "A região possui várias barracas que servem comidas e bebidas típicas."#,
          #"É um ótimo local para começar a explorar o clima de praia e relaxar após a viagem."
        ]
      },
      "tarde": {
        "atividade": "Visita ao Convento da Penha, um dos santuários mais antigos do Brasil, com uma vista panorâmica da região.",
        "localizacao": "Convento da Penha, Vila Velha",
        "comentarios": [
          "O Convento da Penha foi fundado em 1558 e é um importante marco histórico e religioso.",
          "A vista do alto do convento é espetacular, abrangendo a cidade e o mar."#,
          #"É um local de peregrinação e oferece uma experiência cultural e espiritual única."
        ]
      },
      "noite": {
        "atividade": "Jantar no restaurante 'Pirão', conhecido por suas comidas típicas capixabas, como a moqueca.",
        "localizacao": "Restaurante Pirão, Vila Velha",
        "comentarios": [
          "O restaurante Pirão é famoso por suas especialidades em frutos do mar.",
          "Provar a moqueca capixaba é uma experiência gastronômica imperdível."#,
          #"O ambiente é acolhedor e perfeito para uma noite tranquila."
        ]
      }
    },
    "dia_02": {
      "manha": {
        "atividade": "Passeio pela Praça do Papa e Parque da Fonte Grande, em Vitória.",
        "localizacao": "Praça do Papa, Vitória",
        "comentarios": [
          "A Praça do Papa oferece uma bela vista do mar e da cidade de Vitória.",
          "O Parque da Fonte Grande é uma ótima opção para caminhadas e trilhas."#,
          #"O local é perfeito para fotos e um início de dia relaxante."
        ]
      },
      "tarde": {
        "atividade": "Visita ao Palácio Anchieta, sede do governo do estado e um dos prédios históricos mais importantes.",
        "localizacao": "Palácio Anchieta, Vitória",
        "comentarios": [
          "O Palácio Anchieta é um dos mais antigos edifícios em funcionamento no Brasil.",
          "Foi construído no século XVI e possui uma rica história política e cultural."#,
          #"Oferece visitas guiadas que proporcionam um mergulho na história capixaba."
        ]
      },
      "noite": {
        "atividade": "Jantar no 'Caranguejo do Assis', restaurante famoso por seus pratos de frutos do mar.",
        "localizacao": "Restaurantee Caranguejo do Assis, Vitória",
        "comentarios": [
          "O Caranguejo do Assis é renomado pelos pratos com caranguejo e outros frutos do mar.",
          "É uma ótima oportunidade para degustar a culinária local em um ambiente descontraído."#,
          #"Os pratos são bem servidos e o atendimento é elogiado."
        ]
      }
    },
    "dia_03": {
      "manha": {
        "atividade": "Exploração do Parque Estadual da Pedra Azul, famoso por suas trilhas e formações rochosas.",
        "localizacao": "Parque Estadual da Pedra Azul, Domingos Martins",
        "comentarios": [
          "O parque é conhecido pela Pedra Azul, uma imponente formação rochosa que muda de cor conforme a luz do sol.",
          "As trilhas oferecem diferentes níveis de dificuldade, todas com paisagens deslumbrantes."#,
          #"É um local perfeito para amantes da natureza e fotografia."
        ]
      },
      "tarde": {
        "atividade": "Almoço em um dos restaurantes de Domingos Martins, conhecida pela influência da cultura alemã.",
        "localizacao": "Domingos Martins",
        "comentarios": [
          "Domingos Martins tem uma forte influência alemã, visível na arquitetura e culinária.",
          "Os restaurantes locais oferecem pratos típicos como salsichas e chucrute."#,
          #"É um ótimo lugar para experimentar algo diferente e apreciar a cultura local."
        ]
      },
      "noite": {
        "atividade": "Passeio noturno pelo centro de Domingos Martins, com suas lojas de artesanato e produtos locais.",
        "localizacao": "Centro de Domingos Martins",
        "comentarios": [
          "O centro da cidade é encantador, com lojas que vendem artesanato e produtos típicos da região.",
          "À noite, a cidade tem uma atmosfera tranquila e charmosa."#,
          #"É um ótimo momento para comprar lembranças e conhecer os moradores locais."
        ]
      }
    },
    "dia_04": {
      "manha": {
        "atividade": "Visita ao Projeto Tamar, em Vitória, para conhecer sobre a preservação das tartarugas marinhas.",
        "localizacao": "Projeto Tamar, Vitória",
        "comentarios": [
          "O Projeto Tamar é uma importante iniciativa de conservação das tartarugas marinhas no Brasil.",
          "Os visitantes podem aprender sobre as espécies de tartarugas e os esforços de preservação."#,
          #"É uma atividade educativa e inspiradora, especialmente para quem se interessa por vida marinha."
        ]
      },
      "tarde": {
        "atividade": "Passeio pela Praia de Camburi, com paradas em cafés e quiosques.",
        "localizacao": "Praia de Camburi, Vitória",
        "comentarios": [
          "A Praia de Camburi é a mais extensa da capital capixaba e muito frequentada por moradores e turistas.",
          "É um ótimo local para caminhadas e desfrutar de um dia de sol."#,
          #"Os cafés e quiosques ao longo da praia oferecem diversas opções de lanches e bebidas."
        ]
      },
      "noite": {
        "atividade": "Jantar no 'Argento Parrilla', especializado em carnes argentinas.",
        "localizacao": "Argento Parrilla, Vitória",
        "comentarios": [
          "O Argento Parrilla é conhecido pela qualidade de suas carnes e o estilo argentino de preparo.",
          "É uma excelente escolha para quem aprecia um bom churrasco."#,
          #"O ambiente é aconchegante e o serviço é altamente elogiado."
        ]
      }
    },
    "dia_05": {
      "manha": {
        "atividade": "Visita ao Parque Botânico Vale, com trilhas e um belo jardim botânico.",
        "localizacao": "Parque Botânico Vale, Vitória",
        "comentarios": [
          "O Parque Botânico Vale oferece diversas trilhas em meio à natureza e um jardim botânico bem cuidado.",
          "É uma excelente opção para um passeio relaxante em contato com a natureza."#,
          #"O parque também promove atividades de educação ambiental."
        ]
      },
      "tarde": {
        "atividade": "Almoço no restaurante 'Barroco', que serve pratos tradicionais capixabas.",
        "localizacao": "Restaurante Barroco, Vitória",
        "comentarios": [
          "O restaurante Barroco é famoso pela culinária capixaba autêntica.",
          "Oferece uma variedade de pratos típicos, com destaque para os frutos do mar."#,
          #"O ambiente é rústico e acolhedor, proporcionando uma experiência gastronômica única."
        ]
      },
      "noite": {
        "atividade": "Último passeio pelo centro de Vitória, aproveitando para fazer compras em lojas locais.",
        "localizacao": "Centro de Vitória",
        "comentarios": [
          "O centro de Vitória é um excelente lugar para compras, com muitas lojas que vendem produtos locais.",
          "É uma boa oportunidade para comprar lembranças e conhecer mais sobre a cultura local."#,
          #"A noite no centro é movimentada, com muitas opções de entretenimento e restaurantes."
        ]
      }
    }
  }
}

generate_itinerary(resp_gpt, '3')