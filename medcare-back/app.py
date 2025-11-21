from flask import Flask, jsonify, request
from flask_mysqldb import MySQL
from flask_cors import CORS
from config import config
import secrets

app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "http://localhost:4200"}})

conexion = MySQL(app)

# para retornar el registro
def query_one(sql):
    cursor = conexion.connection.cursor()
    cursor.execute(sql)
    return cursor.fetchone()

def query_all(sql):
    cursor = conexion.connection.cursor()
    cursor.execute(sql)
    return cursor.fetchall()


# registrar usuarios
@app.route('/usuarios', methods=['POST'])
def registrar_usuario():
    try:
        data = request.json

        sql = """INSERT INTO usuarios (nombre, email, password, rol)
                 VALUES ('{0}', '{1}', '{2}', '{3}')""".format(
                 data['nombre'], data['email'], data['password'], data['rol'])

        cursor = conexion.connection.cursor()
        cursor.execute(sql)
        conexion.connection.commit()

        return jsonify({"msg": "Usuario registrado", "exito": True})

    except Exception as ex:
        return jsonify({"msg": "Error registrando usuario", "error": str(ex)})

# registrar pacientes
@app.route('/pacientes', methods=['POST'])
def registrar_paciente():
    try:
        data = request.json

        sql = """INSERT INTO pacientes
                 (id_paciente, curp, fecha_nacimiento, genero, telefono, grupo_sanguineo, alergias)
                 VALUES ({0}, '{1}', '{2}', '{3}', '{4}', '{5}', '{6}')""".format(
                 data['id_paciente'], data['curp'], data['fecha_nacimiento'],
                 data['genero'], data['telefono'], data['grupo_sanguineo'], data['alergias'])

        cursor = conexion.connection.cursor()
        cursor.execute(sql)
        conexion.connection.commit()

        # creaa expediente en blanco automáticamente si no existe
        try:
            exp_check = query_one("SELECT id_expediente FROM expedientes WHERE id_paciente = {0}".format(data['id_paciente']))
            if not exp_check:
                cursor.execute("INSERT INTO expedientes (id_paciente, progreso) VALUES ({0}, 0)".format(data['id_paciente']))
                conexion.connection.commit()
        except:
            pass

        return jsonify({"msg": "Paciente registrado", "exito": True})

    except Exception as ex:
        return jsonify({"msg": "Error", "error": str(ex)})

# registrar clinica
@app.route('/clinicas', methods=['POST'])
def registrar_clinica():
    try:
        data = request.json

        sql = """INSERT INTO clinicas 
                (nombre_comercial, rfc, correo, tipo_establecimiento, calle, colonia, codigo_postal)
                VALUES ('{0}','{1}','{2}','{3}','{4}','{5}','{6}')""".format(
                data['nombre_comercial'], data['rfc'], data['correo'],
                data['tipo_establecimiento'], data['calle'], data['colonia'], data['codigo_postal'])

        cursor = conexion.connection.cursor()
        cursor.execute(sql)
        conexion.connection.commit()
        return jsonify({"msg": "Clínica registrada", "exito": True})

    except Exception as ex:
        return jsonify({"msg": "Error", "error": str(ex)})

# registrar medico
@app.route('/medicos', methods=['POST'])
def registrar_medico():
    try:
        data = request.json

        sql = """INSERT INTO medicos 
                (id_medico, cedula, especialidad, clinica_id, consultorio)
                VALUES ({0}, '{1}', '{2}', {3}, '{4}')""".format(
                data['id_medico'], data['cedula'], data['especialidad'],
                data['clinica_id'] if data.get('clinica_id') is not None else "NULL", data.get('consultorio', ''))
        cursor = conexion.connection.cursor()
        cursor.execute(sql)
        conexion.connection.commit()
        return jsonify({"msg": "Médico registrado", "exito": True})

    except Exception as ex:
        return jsonify({"msg": "Error", "error": str(ex)})

# obtener perfil del paciente
@app.route('/pacientes/<id>', methods=['GET'])
def obtener_paciente(id):
    try:
        sql = "SELECT * FROM pacientes WHERE id_paciente = {}".format(id)
        datos = query_one(sql)

        if datos:
            paciente = {
                "id_paciente": datos[0],
                "curp": datos[1],
                "fecha_nacimiento": str(datos[2]),
                "genero": datos[3],
                "telefono": datos[4],
                "grupo_sanguineo": datos[5],
                "alergias": datos[6],
            }
            return jsonify({"paciente": paciente, "exito": True})
        else:
            return jsonify({"msg": "Paciente no encontrado", "exito": False})

    except Exception as ex:
        return jsonify({"msg": "Error", "error": str(ex)})

# obtiene historial del paciente
@app.route('/historial/<id_paciente>', methods=['GET'])
def historial_medico(id_paciente):
    try:
        # expediente
        sql1 = "SELECT id_expediente FROM expedientes WHERE id_paciente = {}".format(id_paciente)
        expediente = query_one(sql1)

        if not expediente:
            return jsonify({"msg": "Sin expediente", "exito": False})

        id_expediente = expediente[0]

        # diagnosticos
        sql2 = """SELECT id_diagnostico, enfermedad, descripcion, fecha, adjunto_url 
                  FROM diagnosticos WHERE id_expediente = {}""".format(id_expediente)
        diag_rows = query_all(sql2)

        diagnosticos = []
        for d in diag_rows:
            diagnosticos.append({
                "id_diagnostico": d[0],
                "enfermedad": d[1],
                "descripcion": d[2],
                "fecha": str(d[3]) if d[3] is not None else None,
                "adjunto_url": d[4]
            })

        # documentos
        sql3 = """SELECT id_documento, archivo_url, fecha_subida 
                  FROM documentos_clinicos WHERE id_expediente = {}""".format(id_expediente)
        doc_rows = query_all(sql3)

        documentos = []
        for doc in doc_rows:
            documentos.append({
                "id_documento": doc[0],
                "archivo_url": doc[1],
                "fecha_subida": str(doc[2]) if doc[2] is not None else None
            })

        return jsonify({
            "expediente": id_expediente,
            "diagnosticos": diagnosticos,
            "documentos": documentos,
            "exito": True
        })

    except Exception as ex:
        return jsonify({"msg": "Error", "error": str(ex)})

# prueba para ver lista de usuarios
@app.route('/usuarios', methods=['GET'])
def listar_usuarios():
    try:
        cursor = conexion.connection.cursor()
        cursor.execute("SELECT id_usuario, nombre, email, rol FROM usuarios")
        datos = cursor.fetchall()

        lista = []
        for fila in datos:
            lista.append({
                "id_usuario": fila[0],
                "nombre": fila[1],
                "email": fila[2],
                "rol": fila[3]
            })

        return jsonify({"usuarios": lista})
    except Exception as ex:
        return jsonify({"mensaje": str(ex)})

# CRUD de expediente (crea, muestra, actualiza y elimina)
@app.route('/expedientes', methods=['POST'])
def crear_expediente():
    try:
        data = request.json
        sql = "INSERT INTO expedientes (id_paciente, progreso) VALUES ({0}, {1})".format(
            data['id_paciente'], data.get('progreso', 0))
        cursor = conexion.connection.cursor()
        cursor.execute(sql)
        conexion.connection.commit()
        return jsonify({"msg": "Expediente creado", "exito": True})
    except Exception as ex:
        return jsonify({"msg": "Error creando expediente", "error": str(ex)})

@app.route('/expedientes/<id_paciente>', methods=['GET'])
def obtener_expediente(id_paciente):
    try:
        sql = "SELECT id_expediente, id_paciente, progreso FROM expedientes WHERE id_paciente = {}".format(id_paciente)
        datos = query_one(sql)
        if datos:
            expediente = {
                "id_expediente": datos[0],
                "id_paciente": datos[1],
                "progreso": datos[2]
            }
            return jsonify({"expediente": expediente, "exito": True})
        else:
            return jsonify({"msg": "No existe expediente", "exito": False})
    except Exception as ex:
        return jsonify({"msg": "Error obteniendo expediente", "error": str(ex)})

@app.route('/expedientes/<id_expediente>', methods=['PUT'])
def actualizar_expediente(id_expediente):
    try:
        data = request.json
        sql = "UPDATE expedientes SET progreso = {0} WHERE id_expediente = {1}".format(data['progreso'], id_expediente)
        cursor = conexion.connection.cursor()
        cursor.execute(sql)
        conexion.connection.commit()
        return jsonify({"msg": "Expediente actualizado", "exito": True})
    except Exception as ex:
        return jsonify({"msg": "Error actualizando expediente", "error": str(ex)})

@app.route('/expedientes/<id_expediente>', methods=['DELETE'])
def eliminar_expediente(id_expediente):
    try:
        sql = "DELETE FROM expedientes WHERE id_expediente = {}".format(id_expediente)
        cursor = conexion.connection.cursor()
        cursor.execute(sql)
        conexion.connection.commit()
        return jsonify({"msg": "Expediente eliminado", "exito": True})
    except Exception as ex:
        return jsonify({"msg": "Error eliminando expediente", "error": str(ex)})


# CRUD de diagnosticoas (crea, muestra, actualiza y elimina)
@app.route('/diagnosticos', methods=['POST'])
def crear_diagnostico():
    try:
        data = request.json
        sql = """INSERT INTO diagnosticos
                (id_expediente, id_medico, enfermedad, descripcion, fecha, adjunto_url)
                VALUES ({0}, {1}, '{2}', '{3}', '{4}', '{5}')""".format(
                data['id_expediente'], data['id_medico'], data['enfermedad'].replace("'", "''"),
                data['descripcion'].replace("'", "''"), data['fecha'], data.get('adjunto_url', ''))
        cursor = conexion.connection.cursor()
        cursor.execute(sql)
        conexion.connection.commit()
        return jsonify({"msg": "Diagnóstico registrado", "exito": True})
    except Exception as ex:
        return jsonify({"msg": "Error creando diagnóstico", "error": str(ex)})

@app.route('/diagnosticos/expediente/<id_expediente>', methods=['GET'])
def obtener_diagnosticos(id_expediente):
    try:
        sql = """SELECT id_diagnostico, enfermedad, descripcion, fecha, adjunto_url
                 FROM diagnosticos WHERE id_expediente = {}""".format(id_expediente)
        datos = query_all(sql)
        lista = []
        for d in datos:
            lista.append({
                "id_diagnostico": d[0],
                "enfermedad": d[1],
                "descripcion": d[2],
                "fecha": str(d[3]) if d[3] is not None else None,
                "adjunto_url": d[4]
            })
        return jsonify({"diagnosticos": lista, "exito": True})
    except Exception as ex:
        return jsonify({"msg": "Error obteniendo diagnósticos", "error": str(ex)})

@app.route('/diagnosticos/<id_diagnostico>', methods=['PUT'])
def actualizar_diagnostico(id_diagnostico):
    try:
        data = request.json
        sql = """UPDATE diagnosticos SET enfermedad='{0}', descripcion='{1}', fecha='{2}', adjunto_url='{3}'
                 WHERE id_diagnostico = {4}""".format(
                 data['enfermedad'].replace("'", "''"), data['descripcion'].replace("'", "''"),
                 data['fecha'], data.get('adjunto_url', ''), id_diagnostico)
        cursor = conexion.connection.cursor()
        cursor.execute(sql)
        conexion.connection.commit()
        return jsonify({"msg": "Diagnóstico actualizado", "exito": True})
    except Exception as ex:
        return jsonify({"msg": "Error actualizando diagnóstico", "error": str(ex)})

@app.route('/diagnosticos/<id_diagnostico>', methods=['DELETE'])
def eliminar_diagnostico(id_diagnostico):
    try:
        sql = "DELETE FROM diagnosticos WHERE id_diagnostico = {}".format(id_diagnostico)
        cursor = conexion.connection.cursor()
        cursor.execute(sql)
        conexion.connection.commit()
        return jsonify({"msg": "Diagnóstico eliminado", "exito": True})
    except Exception as ex:
        return jsonify({"msg": "Error eliminando diagnóstico", "error": str(ex)})


# CRUD de documentos (crea, muestra y elimina)
@app.route('/documentos', methods=['POST'])
def subir_documento():
    try:
        data = request.json
        sql = """INSERT INTO documentos_clinicos (id_expediente, archivo_url)
                 VALUES ({0}, '{1}')""".format(data['id_expediente'], data['archivo_url'])
        cursor = conexion.connection.cursor()
        cursor.execute(sql)
        conexion.connection.commit()
        return jsonify({"msg": "Documento guardado", "exito": True})
    except Exception as ex:
        return jsonify({"msg": "Error subiendo documento", "error": str(ex)})

@app.route('/documentos/expediente/<id_expediente>', methods=['GET'])
def obtener_documentos(id_expediente):
    try:
        sql = """SELECT id_documento, archivo_url, fecha_subida 
                 FROM documentos_clinicos WHERE id_expediente = {}""".format(id_expediente)
        datos = query_all(sql)
        lista = []
        for d in datos:
            lista.append({
                "id_documento": d[0],
                "archivo_url": d[1],
                "fecha_subida": str(d[2]) if d[2] is not None else None
            })
        return jsonify({"documentos": lista, "exito": True})
    except Exception as ex:
        return jsonify({"msg": "Error obteniendo documentos", "error": str(ex)})

@app.route('/documentos/<id_documento>', methods=['DELETE'])
def eliminar_documento(id_documento):
    try:
        sql = "DELETE FROM documentos_clinicos WHERE id_documento = {}".format(id_documento)
        cursor = conexion.connection.cursor()
        cursor.execute(sql)
        conexion.connection.commit()
        return jsonify({"msg": "Documento eliminado", "exito": True})
    except Exception as ex:
        return jsonify({"msg": "Error eliminando documento", "error": str(ex)})


# CRUD de permisos para medico (crea, muestra, actualiza y elimina)
@app.route('/permisos', methods=['POST'])
def crear_permiso():
    try:
        data = request.json
        sql = """INSERT INTO permisos_medicos 
                 (id_medico, id_paciente, nivel_acceso)
                 VALUES ({0}, {1}, '{2}')""".format(
                 data['id_medico'], data['id_paciente'], data.get('nivel_acceso', 'lectura'))
        cursor = conexion.connection.cursor()
        cursor.execute(sql)
        conexion.connection.commit()
        return jsonify({"msg": "Permiso registrado", "exito": True})
    except Exception as ex:
        return jsonify({"msg": "Error creando permiso", "error": str(ex)})

@app.route('/permisos/medico/<id_medico>', methods=['GET'])
def permisos_por_medico(id_medico):
    try:
        sql = """SELECT id_permiso, id_paciente, nivel_acceso, fecha_otorgado 
                 FROM permisos_medicos WHERE id_medico = {}""".format(id_medico)
        datos = query_all(sql)
        lista = []
        for p in datos:
            lista.append({
                "id_permiso": p[0],
                "id_paciente": p[1],
                "nivel_acceso": p[2],
                "fecha_otorgado": str(p[3]) if p[3] is not None else None
            })
        return jsonify({"permisos": lista, "exito": True})
    except Exception as ex:
        return jsonify({"msg": "Error obteniendo permisos", "error": str(ex)})

@app.route('/permisos/<id_permiso>', methods=['PUT'])
def actualizar_permiso(id_permiso):
    try:
        data = request.json
        sql = """UPDATE permisos_medicos
                 SET nivel_acceso='{0}'
                 WHERE id_permiso = {1}""".format(data['nivel_acceso'], id_permiso)
        cursor = conexion.connection.cursor()
        cursor.execute(sql)
        conexion.connection.commit()
        return jsonify({"msg": "Permiso actualizado", "exito": True})
    except Exception as ex:
        return jsonify({"msg": "Error actualizando permiso", "error": str(ex)})

@app.route('/permisos/<id_permiso>', methods=['DELETE'])
def eliminar_permiso(id_permiso):
    try:
        sql = "DELETE FROM permisos_medicos WHERE id_permiso = {}".format(id_permiso)
        cursor = conexion.connection.cursor()
        cursor.execute(sql)
        conexion.connection.commit()
        return jsonify({"msg": "Permiso eliminado", "exito": True})
    except Exception as ex:
        return jsonify({"msg": "Error eliminando permiso", "error": str(ex)})


# qr del paciente (crea, muestra y actualiza (token para validacion unica))
@app.route('/qr/generar', methods=['POST'])
def generar_qr():
    try:
        data = request.json
        # generar token seguro para mostrar info en el front
        token = secrets.token_urlsafe(32)
        codigo_qr_url = data.get('codigo_qr_url', '') #ruta que se genera con el front
        id_paciente = data['id_paciente']

        # si ya existe, se actualizar token y fecha
        existing = query_one("SELECT id_qr FROM qr_paciente WHERE id_paciente = {}".format(id_paciente))
        if existing:
            sql = """UPDATE qr_paciente SET token = '{0}', codigo_qr_url = '{1}', fecha_generacion = NOW()
                     WHERE id_paciente = {2}""".format(token, codigo_qr_url, id_paciente)
        else:
            sql = """INSERT INTO qr_paciente (id_paciente, codigo_qr_url, token)
                     VALUES ({0}, '{1}', '{2}')""".format(id_paciente, codigo_qr_url, token)

        cursor = conexion.connection.cursor()
        cursor.execute(sql)
        conexion.connection.commit()

        return jsonify({"msg": "QR generado", "token": token, "exito": True})
    except Exception as ex:
        return jsonify({"msg": "Error generando QR", "error": str(ex)})

@app.route('/qr/paciente/<id_paciente>', methods=['GET'])
def obtener_qr(id_paciente):
    try:
        sql = "SELECT id_qr, codigo_qr_url, token, fecha_generacion FROM qr_paciente WHERE id_paciente = {}".format(id_paciente)
        datos = query_one(sql)
        if datos:
            qr = {
                "id_qr": datos[0],
                "codigo_qr_url": datos[1],
                "token": datos[2],
                "fecha_generacion": str(datos[3]) if datos[3] is not None else None
            }
            return jsonify({"qr": qr, "exito": True})
        else:
            return jsonify({"msg": "No existe QR para este paciente", "exito": False})
    except Exception as ex:
        return jsonify({"msg": "Error obteniendo QR", "error": str(ex)})

@app.route('/qr/<id_qr>', methods=['PUT'])
def actualizar_qr(id_qr):
    try:
        data = request.json
        token = data.get('token', secrets.token_urlsafe(32))
        codigo_qr_url = data.get('codigo_qr_url', '')
        sql = """UPDATE qr_paciente SET token = '{0}', codigo_qr_url = '{1}', fecha_generacion = NOW()
                 WHERE id_qr = {2}""".format(token, codigo_qr_url, id_qr)
        cursor = conexion.connection.cursor()
        cursor.execute(sql)
        conexion.connection.commit()
        return jsonify({"msg": "QR actualizado", "exito": True})
    except Exception as ex:
        return jsonify({"msg": "Error actualizando QR", "error": str(ex)})



def pagina_no_encontrada(error):
    return "<h1>La página no existe</h1>", 404

if __name__ == '__main__':
    app.config.from_object(config['development'])
    app.register_error_handler(404, pagina_no_encontrada)
    app.run(debug=True)
