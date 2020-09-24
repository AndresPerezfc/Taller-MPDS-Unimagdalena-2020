from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL
from textblob import TextBlob
import speech_recognition as sr

r = sr.Recognizer()

app = Flask(__name__)

# ------------CONECCION A MYSQL----------------
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'clasificador'

mysql = MySQL(app)

# ------------RUTAS----------------
app.secret_key = 'myscretkey'


@app.route('/', methods=['POST', 'GET'])
def Index():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM productos')
    data = cur.fetchall()
    return render_template('index.html', productos=data)


@app.route('/producto/<id>')
def getProducto(id):
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM productos WHERE id = %s', (id))
    data = cur.fetchall()

    op_cur = mysql.connection.cursor()
    op_cur.execute('SELECT * FROM opiniones WHERE producto_id = %s', (id))
    opiniones_data = op_cur.fetchall()

    polaridad = mysql.connection.cursor()
    polaridad.execute(
        'SELECT COUNT(polaridad) FROM opiniones WHERE polaridad > 0 AND producto_id = %s', (id))
    polaridad_data = polaridad.fetchall()

    negativa = mysql.connection.cursor()
    negativa.execute(
        'SELECT COUNT(polaridad) FROM opiniones WHERE polaridad < 0 AND producto_id = %s', (id))
    negativa_data = negativa.fetchall()

    total = mysql.connection.cursor()
    total.execute(
        'SELECT COUNT(*) FROM opiniones WHERE producto_id = %s', (id))
    total_data = total.fetchall()

    negativas = negativa_data[0][0]
    positivas = polaridad_data[0][0]
    total_calificaciones = total_data[0][0]

    if(total_calificaciones != 0):
        ponderacionPositiva = (positivas)*(100) / (total_calificaciones)
        ponderacionNegativa = (negativas)*(100) / (total_calificaciones)
    else:
        ponderacionPositiva = 0.0
        ponderacionNegativa = 0.0

    return render_template('producto.html', producto=data[0], opiniones=opiniones_data, positividad=ponderacionPositiva, negatividad=ponderacionNegativa)


@app.route('/calificar/<id>', methods=['GET'])
def Calificar(id):
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM productos WHERE id = %s', (id))
    data = cur.fetchall()

    if request.method == 'GET':
        with sr.Microphone() as source:
            print("Di tu opinión...")
            audio = r.listen(source)
            try:
                text = r.recognize_google(audio, language="es-ES")
                textoanalizado = TextBlob(text)
                textotraducido = textoanalizado.translate(to="en")
                print("Tu opinión: {}".format(text))

                cur.execute('INSERT INTO opiniones (texto, subjetividad, polaridad, producto_id) VALUES (%s, %s, %s, %s)',
                            (text, textotraducido.subjectivity, textotraducido.polarity, id))
                mysql.connection.commit()
                flash("Producto calficiado con exito", category="exito")

                return redirect(url_for('getProducto', id=id))
            except:
                print("Tenemos un problema")
                flash("No se capturo la opinión", category="error")
                return redirect(url_for('getProducto', id=id))


if __name__ == '__main__':
    app.run(port=3000, debug=True)
