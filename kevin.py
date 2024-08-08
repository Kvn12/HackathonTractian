from dotenv import load_dotenv, find_dotenv
import os
import openai
import base64
import requests
import json

load_dotenv(find_dotenv())
api_key = os.getenv("api_key")

def carregar_arquivo_json(caminho):
    with open(caminho, 'r') as arquivo:
        dados = json.load(arquivo)
    return json.dumps(dados, indent=2)

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

image_path1 = "/home/ec2021-ceb/ra247218/Documents/HackathonTractian/0c66f66c-97ac-4b66-98ec-550994441fd1.jpg"
base64_image1 = encode_image(image_path1)

image_path2 = "/home/ec2021-ceb/ra247218/Documents/HackathonTractian/3a799dea-1943-4cd4-b307-3e51bcc1ea51.jpg"
base64_image2 = encode_image(image_path2)

image_path3 = "/home/ec2021-ceb/ra247218/Documents/HackathonTractian/7ba51969-3fd4-4864-8a57-565a5045eefa.jpg"
base64_image3 = encode_image(image_path3)


jfile = carregar_arquivo_json("/home/ec2021-ceb/ra247218/Documents/HackathonTractian/asset_info.json")

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}

payload = {
    "model": "gpt-4o",
    "messages": [
    {

        "role": "system", "content": "Você é um assistente desenvolvido para procurar fichas tecnicas de máquinarios e afins com apenas 3 imagens como input e  ocasionalmente uma breve descrição da marca e do motor como um arquivo json. O arquivo auxiliar tem como nome asset info com o nome, breve descrição do modelo e seu fabricante respectivamente em name, manufacturer e model seguido do caractere ':' e separados por virgula e espaço",

        "role": "user",
        "content": [
        {
            "type": "text",
            "text": "retorne a ficha tecnica do modelo correspondente em formato json ,traduzido em portugues especificando a potencia consumida, dimensoes e brevemente descreva as 3 imagens recebidas e o conteudo apresentado no arquivo json"
        },
        ]
    }
    ],
}


response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)


print(response.json())