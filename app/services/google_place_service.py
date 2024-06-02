import os
import textwrap
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO


def get_place_id(api_key, place_name):
    place_search_url = f'https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={place_name}&inputtype=textquery&fields=place_id&key={api_key}'
    response = requests.get(place_search_url)
    response.raise_for_status()
    place_id = response.json()['candidates'][0]['place_id']
    return place_id

def get_place_photo(api_key, place_name, max_width=1024):
    place_id = get_place_id(api_key, place_name)
    place_details_url = f'https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=photos&key={api_key}'
    response = requests.get(place_details_url)
    response.raise_for_status()
    photo_reference = response.json()['result']['photos'][0]['photo_reference']
    photo_url = f'https://maps.googleapis.com/maps/api/place/photo?maxwidth={max_width}&photoreference={photo_reference}&key={api_key}'
    photo_response = requests.get(photo_url)
    photo_response.raise_for_status()
    return Image.open(BytesIO(photo_response.content))