import openai
from flask import Flask, render_template, request, redirect, send_file, url_for
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from dotenv import load_dotenv, find_dotenv
import requests as req
import base64
import os
import io
import json

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///images.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
load_dotenv(find_dotenv())
api_key = os.getenv("api_key")

def gerar_ficha_tecnica(obs, image_datas):
    headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": "gpt-4o",
        "messages": [
        {

            "role": "system", "content": "Você é um assistente encarregado de procurar informações e montar fichas tecnicas de maquinários baseando-se em no máximo 3 imagens e um arquivo json do motor. O arquivo auxiliar tem como nome asset_info com o nome,modelo e seu fabricante respectivamente em name, manufacturer e model. As imagens provêm uma melhor apresentação da maquina. Existe tambem uma foto de um sensor que será utilizada para criar um parametro do estado atual do equipamento.",

            "role": "user",
            "content": [
            {
                "type" : "text",
                "text": "preencha a ficha tecnica do modelo correspondente em formato json, traduzido em portugues, caso não seja possivel determinar preencher com desconhecido. A ficha consiste nas seguintes perguntas: Nome: modelo do motor; Fabricante: empresa que fabrica estes modelos; Tipo: Baseado em seu modelo de funcionamento, por exemplo TriFásico; Identificação: Número encontrado na imagem ou no json; Potência: Potência que o motor consome ;Frequência: frequencia de giro do motor apresentada nas imagens ou passada na pesquisa do usuario, o padrão brasileiro é 60Hz; Tensão:tensão, medida em volts, de funcionamento do motor por padrão nesse ramo no brasil são 330v/660v; Rotação: Estimativa da velocidade de giro em rpm do motor; Grau de proteção: especificado em alguma foto do maquinário, é apresentado como um codigo;Eficiência: apresentado em alguma foto do maquinario como um valor percentual; Estado Atual da Maquina: baseado nas imagens e no sensor avaliar o quão danificada se apresenta a maquina para possivelmente evitar acidentes."

            },
            
            {
                "type": "text",
                "text" : f"{obs}"
                
            },

            ]
        }
        ],
    }
    
    for img in image_datas:
        payload["messages"][0]["content"].append({
            "type": "image_url",
            "image_url": {
            "url": f"data:image/jpeg;base64,{base64.b64encode(img).decode("utf-8")}"
            }
        })

    response = req.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    ans = response.json()
    dados = ans['choices'][0]['message']['content']

    return dados

class ImageModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    model_type = db.Column(db.String(50), nullable=False)
    filename = db.Column(db.String(150), nullable=False)
    data = db.Column(db.LargeBinary, nullable=False)
    obs = db.Column(db.String(500), nullable=True)


def create_db():
    with app.app_context():
        db.create_all()

def upload_file(file, title, model_type, obs):
    if file.filename == '':
        return False
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        image_data = file.read()
        new_image = ImageModel(title=title, model_type=model_type, filename=filename, data=image_data, obs=obs)
        db.session.add(new_image)
        db.session.commit()
        return image_data
    return False


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        title = request.form['title']
        model_type = request.form['model_type']
        obs = request.form['additional_info']
        image_datas = []
        for file in request.files.getlist('file'):
            image_datas.append(upload_file(file, title, model_type, obs))


        # Fetching the images related to the current title and model_type
        images = ImageModel.query.filter_by(title=title, model_type=model_type).all()


        ficha_tecnica = gerar_ficha_tecnica(obs, image_datas)
        ficha_tecnica = json.loads(ficha_tecnica[7:-3])
        ficha_tecnica = {
                "NOME": title,
                "TIPO": model_type,
                "IMAGENS": images,
                "FABRICANTE": "desconhecido (tente recarregar a página)",
                "IDENTIFICAÇÃO": "desconhecido (tente recarregar a página)",
                "ESPECIFICACOES_TECNICAS": {
                    "POTÊNCIA": "desconhecido (tente recarregar a página)",
                    "TENSÃO": "desconhecido (tente recarregar a página)",
                    "FREQUÊNCIA": "desconhecido (tente recarregar a página)",
                    "ROTAÇÃO": "desconhecido (tente recarregar a página)",
                    "GRAU_DE_PROTEÇÃO": "desconhecido (tente recarregar a página)",
                    "EFICIÊNCIA": "desconhecido (tente recarregar a página)",
                    "ESTADO ATUAL": "desconhecido (tente recarregar a página)"
                }
            }

        for _ in range(3):
            ficha_tecnica = gerar_ficha_tecnica(obs, image_datas)
            try:
                ficha_tecnica = json.loads(ficha_tecnica[7:-3])
                print(ficha_tecnica)
                

                ficha_tecnica = {
                    "NOME": title,
                    "TIPO": model_type,
                    "IMAGENS": images,
                    "FABRICANTE": ficha_tecnica["Fabricante"],
                    "IDENTIFICAÇÃO": ficha_tecnica["Identificação"],
                    "ESPECIFICACOES_TECNICAS": {
                        "POTÊNCIA": ficha_tecnica["Potência"],
                        "TENSÃO": ficha_tecnica["Tensão"],
                        "FREQUÊNCIA": ficha_tecnica["Frequência"],
                        "ROTAÇÃO": ficha_tecnica["Rotação"],
                        "GRAU_DE_PROTEÇÃO": ficha_tecnica["Grau de proteção"],
                        "EFICIÊNCIA": ficha_tecnica["Eficiência"],
                        "ESTADO ATUAL": ficha_tecnica["Estado Atual da Maquina"]
                    }
                }
                break
            except:
                ficha_tecnica = {
                    "NOME": title,
                    "TIPO": model_type,
                    "IMAGENS": images,
                    "FABRICANTE": "desconhecido (tente recarregar a página)",
                    "IDENTIFICAÇÃO": "desconhecido (tente recarregar a página)",
                    "ESPECIFICACOES_TECNICAS": {
                        "POTÊNCIA": "desconhecido (tente recarregar a página)",
                        "TENSÃO": "desconhecido (tente recarregar a página)",
                        "FREQUÊNCIA": "desconhecido (tente recarregar a página)",
                        "ROTAÇÃO": "desconhecido (tente recarregar a página)",
                        "GRAU_DE_PROTEÇÃO": "desconhecido (tente recarregar a página)",
                        "EFICIÊNCIA": "desconhecido (tente recarregar a página)",
                        "ESTADO ATUAL": "desconhecido (tente recarregar a página)"
                    }
                }
        return render_template('ficha_tecnica.html', ficha=ficha_tecnica)

    return render_template('index.html')


@app.route('/ficha_tecnica/<int:item_id>')
def ficha_tecnica(item_id):
    item = ImageModel.query.get_or_404(item_id)
    images = ImageModel.query.filter_by(title=item.title, model_type=item.model_type).all()
    image_datas = []
    for img in images:
        image_datas.append(img.data)

    ficha_tecnica = {
                "NOME": item.title,
                "TIPO": item.model_type,
                "IMAGENS": images,
                "FABRICANTE": "desconhecido (tente recarregar a página)",
                "IDENTIFICAÇÃO": "desconhecido (tente recarregar a página)",
                "ESPECIFICACOES_TECNICAS": {
                    "POTÊNCIA": "desconhecido (tente recarregar a página)",
                    "TENSÃO": "desconhecido (tente recarregar a página)",
                    "FREQUÊNCIA": "desconhecido (tente recarregar a página)",
                    "ROTAÇÃO": "desconhecido (tente recarregar a página)",
                    "GRAU_DE_PROTEÇÃO": "desconhecido (tente recarregar a página)",
                    "EFICIÊNCIA": "desconhecido (tente recarregar a página)",
                    "ESTADO ATUAL": "desconhecido (tente recarregar a página)"
                }
            }

    for _ in range(3):
        ficha_tecnica = gerar_ficha_tecnica(images[0].obs, image_datas)
        try:
            ficha_tecnica = json.loads(ficha_tecnica[7:-3])
            print(ficha_tecnica)
            

            ficha_tecnica = {
                "NOME": item.title,
                "TIPO": item.model_type,
                "IMAGENS": images,
                "FABRICANTE": ficha_tecnica["Fabricante"],
                "IDENTIFICAÇÃO": ficha_tecnica["Identificação"],
                "ESPECIFICACOES_TECNICAS": {
                    "POTÊNCIA": ficha_tecnica["Potência"],
                    "TENSÃO": ficha_tecnica["Tensão"],
                    "FREQUÊNCIA": ficha_tecnica["Frequência"],
                    "ROTAÇÃO": ficha_tecnica["Rotação"],
                    "GRAU_DE_PROTEÇÃO": ficha_tecnica["Grau de proteção"],
                    "EFICIÊNCIA": ficha_tecnica["Eficiência"],
                    "ESTADO ATUAL": ficha_tecnica["Estado Atual da Maquina"]
                }
            }
            break
        except:
            ficha_tecnica = {
                "NOME": item.title,
                "TIPO": item.model_type,
                "IMAGENS": images,
                "FABRICANTE": "desconhecido (tente recarregar a página)",
                "IDENTIFICAÇÃO": "desconhecido (tente recarregar a página)",
                "ESPECIFICACOES_TECNICAS": {
                    "POTÊNCIA": "desconhecido (tente recarregar a página)",
                    "TENSÃO": "desconhecido (tente recarregar a página)",
                    "FREQUÊNCIA": "desconhecido (tente recarregar a página)",
                    "ROTAÇÃO": "desconhecido (tente recarregar a página)",
                    "GRAU_DE_PROTEÇÃO": "desconhecido (tente recarregar a página)",
                    "EFICIÊNCIA": "desconhecido (tente recarregar a página)",
                    "ESTADO ATUAL": "desconhecido (tente recarregar a página)"
                }
            }

    return render_template('ficha_tecnica.html', ficha=ficha_tecnica)


@app.route('/image/<int:image_id>')
def image(image_id):
    image = ImageModel.query.get_or_404(image_id)
    return send_file(io.BytesIO(image.data), mimetype='image/jpeg', as_attachment=False, download_name=image.filename)

@app.route('/images', methods=['GET'])
def list_images():   
    images = ImageModel.query.all()
    image_list = [{'id': img.id, 'filename': img.filename, 'url': url_for('image', image_id=img.id)} for img in images]
    print(image_list)
    return jsonify({'images': image_list})

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

@app.route('/get_data', methods=['GET'])
def get_data():
    # Fetching all records from the ImageModel table
    images = ImageModel.query.all()
    data = [{"id": image.id, "nome": image.title, "model": image.model_type} for image in images]
    return jsonify(data)

@app.route('/get_search_data', methods=['GET'])
def get_search_data():
    query = request.args['query']
    images = ImageModel.query.all()
    data = []
    titles = []
    for image in images:
        if not image.title in titles:
            data.append(f"\"nome\": {image.title}, \"model\": {image.model_type}")
            titles.append(image.title)

    print(data)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": "gpt-4o",
        "messages": [
        {

            "role": "system", "content": "Você é um assistente desenvolvido para filtrar dados em uma lista",

            "role": "user",
            "content": [
            {
                "type": "text",
                "text" : f"faça uma lista dos nomes do elementos que: {query}\n\n{data}\n\nresponda somente com os nomes na ordem, separados por espaço, se não houver nenhum elemento, enviar um espaço em branco"
            },

            ]
        }
        ],
    }
    
    print("faça uma lista dos nomes do elementos que: {query}\n\n{data}\n\nresponda somente com os nomes na ordem, separados por espaço")

    response = req.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload).json()
    print(response)

    data = [{"id": image.id, "nome": image.title, "model": image.model_type} for image in images if image.title in response['choices'][0]['message']['content'].strip().split()]
    return jsonify(data)

if __name__ == '__main__':
    create_db()
    app.run(debug=True)
    