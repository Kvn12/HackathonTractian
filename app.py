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

            "role": "system", "content": "Você é um assistente desenvolvido para procurar fichas tecnicas de máquinarios e afins com apenas 3 imagens como input e  ocasionalmente uma breve descrição da marca e do motor como um arquivo json. O arquivo auxiliar tem como nome asset info com o nome, breve descrição do modelo e seu fabricante respectivamente em name, manufacturer e model seguido do caractere ':' e separados por virgula e espaço",

            "role": "user",
            "content": [
            {
                "type": "text",
                "text": "retorne a ficha tecnica do modelo correspondente em formato json ,traduzido em portugues especificando a potencia consumida, dimensoes e brevemente descreva as 3 imagens recebidas e o conteudo apresentado no arquivo json"
            },
            
            {
                "type": "text",
                "text" : "o arquivo esta no tipo json onde as opcoes name seguido de nome, manufacturer como fornecedor e modelo {obs}"
                
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

    return response['choices'][0]['message']['content'].strip()

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

        ficha_tecnica = {
            "NOME": title,
            "TIPO": model_type,
            "IMAGENS": images,
            "FABRICANTE": "Extraído do GPT",
            "MODELO": "Extraído do GPT",
            "IDENTIFICAÇÃO": "Extraído do GPT",
            "LOCALIZAÇÃO": "Extraído do GPT",
            "ESPECIFICACOES_TECNICAS": {
                "POTÊNCIA": "Extraído do GPT",
                "TENSÃO": "Extraído do GPT",
                "FREQUÊNCIA": "Extraído do GPT",
                "ROTAÇÃO": "Extraído do GPT",
                "GRAU_DE_PROTEÇÃO": "Extraído do GPT",
                "EFICIÊNCIA": "Extraído do GPT"
            }
        }

        return render_template('ficha_tecnica.html', ficha=ficha_tecnica)

    return render_template('index.html')


@app.route('/ficha_tecnica/<int:item_id>')
def ficha_tecnica(item_id):
    item = ImageModel.query.get_or_404(item_id)
    images = ImageModel.query.filter_by(title=item.title, model_type=item.model_type).all()
    ficha_tecnica = {
            "NOME": item.title,
            "TIPO": item.model_type,
            "IMAGENS": images,
            "FABRICANTE": "Extraído do GPT",
            "MODELO": "Extraído do GPT",
            "IDENTIFICAÇÃO": "Extraído do GPT",
            "LOCALIZAÇÃO": "Extraído do GPT",
            "ESPECIFICACOES_TECNICAS": {
                "POTÊNCIA": "Extraído do GPT",
                "TENSÃO": "Extraído do GPT",
                "FREQUÊNCIA": "Extraído do GPT",
                "ROTAÇÃO": "Extraído do GPT",
                "GRAU_DE_PROTEÇÃO": "Extraído do GPT",
                "EFICIÊNCIA": "Extraído do GPT"
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
    