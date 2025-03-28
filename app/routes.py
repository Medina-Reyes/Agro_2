import os
import csv
from flask import render_template, request, redirect, url_for, flash, session, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from .views.financial_info import financial_info_bp
from .views.climate_analysis import climate_analysis_bp
from .views.chat_ai import chat_ai_bp
from .views.user_management import user_management_bp
import pdfkit  # Asegúrate de instalar pdfkit y wkhtmltopdf
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def register_routes(app):
    """
    Registra todos los blueprints de los módulos en la aplicación Flask.
    """
    app.register_blueprint(financial_info_bp, url_prefix='/financial-info')
    app.register_blueprint(climate_analysis_bp, url_prefix='/climate-analysis')
    app.register_blueprint(chat_ai_bp, url_prefix='/chat-ai')
    app.register_blueprint(user_management_bp, url_prefix='/user-management')

    # Ruta para registrar usuarios
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            # Obtener los datos del formulario
            username = request.form['username']
            telefono = request.form['telefono']
            email = request.form['email']
            password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
            dia = request.form['dia']
            mes = request.form['mes']
            año = request.form['año']
            genero = request.form['genero']
            terminos = request.form.get('terminos')

            # Ruta del archivo y creación de la carpeta si no existe
            file_path = 'users.csv'
            file_exists = os.path.isfile(file_path)

            # Guardar los datos en un archivo CSV
            with open(file_path, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=['username', 'telefono', 'email', 'password', 'fecha_nacimiento', 'genero', 'terminos'])
                if not file_exists:
                    writer.writeheader()
                writer.writerow({
                    'username': username,
                    'telefono': telefono,
                    'email': email,
                    'password': password,
                    'fecha_nacimiento': f"{dia}/{mes}/{año}",
                    'genero': genero,
                    'terminos': 'Aceptado' if terminos else 'No aceptado'
                })

            # Crear carpeta asociada al correo electrónico del usuario
            user_folder = os.path.join('data', email)
            if not os.path.exists(user_folder):
                os.makedirs(user_folder)

            # Iniciar sesión automáticamente después del registro
            session['user_id'] = email

            flash('Registro exitoso. Por favor, completa tus datos generales.', 'success')
            return redirect(url_for('datos_generales'))  # Redirigir al formulario de datos generales
        return render_template('register.html')

    # Ruta para iniciar sesión
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']

            # Verificar usuario en el archivo CSV
            file_path = 'users.csv'
            if not os.path.isfile(file_path):
                flash('El archivo de usuarios no existe. Contacte al administrador.', 'danger')
                return render_template('login.html')  # Mostrar error en la misma página

            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row['email'] == email and check_password_hash(row['password'], password):
                        session['user_id'] = email  # Usar el correo como identificador único

                        # Leer la actividad principal desde datos_generales.csv
                        user_folder = os.path.join('data', email)
                        general_file = os.path.join(user_folder, 'datos_generales.csv')
                        if os.path.isfile(general_file):
                            with open(general_file, mode='r', encoding='utf-8') as general_data_file:
                                general_reader = csv.DictReader(general_data_file)
                                general_data = next(general_reader, {})
                                actividad_principal = general_data.get('actividad_principal', '').strip().lower()

                                # Redirigir al dashboard correspondiente
                                if actividad_principal == 'citricos':
                                    return redirect(url_for('dashboard_citricos'))
                                elif actividad_principal == 'cafe':
                                    return redirect(url_for('dashboard_cafe'))
                                elif actividad_principal == 'maiz':
                                    return redirect(url_for('dashboard_maiz'))
                                elif actividad_principal == 'ganado_bovino':
                                    return redirect(url_for('dashboard_ganado'))
                                elif actividad_principal == 'cerdos':
                                    return redirect(url_for('dashboard_cerdos'))
                                elif actividad_principal == 'huevo':
                                    return redirect(url_for('dashboard_huevos'))
                                else:
                                    flash('Actividad principal no válida. Contacte al administrador.', 'warning')
                                    return render_template('login.html')

                        flash('No se encontró información de actividad principal. Complete sus datos generales.', 'warning')
                        return render_template('login.html')

            flash('Credenciales inválidas. Por favor, intente nuevamente.', 'danger')
        return render_template('login.html')

    # Ruta para cerrar sesión
    @app.route('/logout')
    def logout():
        session.pop('user_id', None)
        flash('Has cerrado sesión.', 'success')
        return redirect(url_for('login'))

    # Ruta para procesar el formulario de datos generales
    @app.route('/datos_generales', methods=['GET', 'POST'])
    def datos_generales():
        user_id = session.get('user_id')  # Obtener el correo electrónico del usuario desde la sesión
        if not user_id:
            flash('Por favor, inicia sesión.', 'danger')
            return redirect(url_for('login'))

        if request.method == 'POST':
            # Datos enviados desde el formulario
            data = {
                'idioma': request.form['idioma'],
                'actividad_principal': request.form['actividad_principal'],
                'otras_actividades': ', '.join(request.form.getlist('otras_actividades')),  # Manejar múltiples selecciones
                'tamano_produccion': request.form['tamano_produccion'],
                'anos_actividad': request.form['anos_actividad'],
                'ubicacion': request.form['ubicacion'],
                'coordenadas': request.form['coordenadas'],
                'clima_preocupacion': request.form['clima_preocupacion'],
                'perdidas_clima': request.form['perdidas_clima'],
                'tipo_ayuda': request.form['tipo_ayuda'],
                'frecuencia_chat': request.form['frecuencia_chat'],
                'comodidad_tecnologia': request.form['comodidad_tecnologia'],
                'aceptar_mejoras': request.form['aceptar_mejoras'],
                'aceptar_terminos': request.form['aceptar_terminos'],
                'fecha_captura': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            }

            # Crear carpeta del usuario si no existe
            user_folder = os.path.join('data', user_id)
            if not os.path.exists(user_folder):
                os.makedirs(user_folder)

            # Guardar los datos en un archivo CSV dentro de la carpeta del usuario
            file_path = os.path.join(user_folder, 'datos_generales.csv')
            file_exists = os.path.isfile(file_path)
            with open(file_path, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=data.keys())
                if not file_exists:
                    writer.writeheader()
                writer.writerow(data)

            flash('Datos generales guardados exitosamente.', 'success')
            return redirect(url_for('dashboard_cafe'))  # Redirigir al dashboard o a otra página
        return render_template('datos_generales.html')

    @app.route('/coffee_form', methods=['GET'])
    def coffee_form():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder al formulario.', 'danger')
            return redirect(url_for('login'))

        return render_template('coffee_form.html')


    # Ruta para guardar datos de café
    @app.route('/submit_coffee_form', methods=['POST'])
    def submit_coffee_form():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión.', 'danger')
            return redirect(url_for('login'))

        try:
            # Función para limpiar y convertir valores numéricos
            def parse_float(value):
                return float(value.replace(',', '').strip()) if value else 0

            # Datos específicos del formulario de café
            data = {
                # Datos financieros
                'total_ingresos': parse_float(request.form.get('q1', '0')),
                'produccion_total': parse_float(request.form.get('q1_2', '0')),
                'hectareas': parse_float(request.form.get('q1_3', '0')),
                'gastos_insumos': parse_float(request.form.get('q2', '0')),
                'pago_jornales': parse_float(request.form.get('q3', '0')),
                'gastos_servicios': parse_float(request.form.get('q4', '0')),
                'valor_maquinaria': parse_float(request.form.get('q5', '0')),
                'dinero_disponible': parse_float(request.form.get('q6', '0')),
                'gastos_imprevistos': parse_float(request.form.get('q7', '0')),
                'total_deudas': parse_float(request.form.get('q8', '0')),
                # Datos operativos
                'dias_trabajo': parse_float(request.form.get('q9', '0')),
                'trabajadores': parse_float(request.form.get('q10', '0')),
                'horas_venta': parse_float(request.form.get('q11', '0')),
                'horas_supervision': parse_float(request.form.get('q12', '0')),
                'lugar_comercializacion': request.form.get('q13', ''),
                'comentarios': request.form.get('comments', ''),
                # Fecha de captura enviada desde el formulario
                'fecha_captura': request.form.get('fecha_captura', '')
            }

            # Validar datos obligatorios
            if not data['total_ingresos'] or not data['produccion_total'] or not data['hectareas']:
                flash('Por favor, completa todos los campos obligatorios.', 'danger')
                return redirect(url_for('coffee_form'))

            # Cálculos financieros
            costos_directos = data['gastos_insumos'] + data['pago_jornales'] + data['gastos_servicios'] + data['gastos_imprevistos']
            data['utilidad_bruta'] = data['total_ingresos'] - costos_directos
            data['utilidad_neta'] = data['utilidad_bruta'] - data['total_deudas']
            activos_totales = data['dinero_disponible'] + data['valor_maquinaria']
            data['activos_totales'] = activos_totales
            data['patrimonio_neto'] = activos_totales - data['total_deudas']
            data['costo_por_unidad'] = costos_directos / data['produccion_total'] if data['produccion_total'] else 0
            data['margen_ganancia'] = (data['utilidad_bruta'] / data['total_ingresos']) * 100 if data['total_ingresos'] else 0
            data['razon_endeudamiento'] = data['total_deudas'] / activos_totales if activos_totales else 0
            data['productividad_por_hectarea'] = data['produccion_total'] / data['hectareas'] if data['hectareas'] else 0
            data['gastos_totales'] = costos_directos
            # Crear carpeta del usuario si no existe
            user_folder = os.path.join('data', user_id)
            if not os.path.exists(user_folder):
                os.makedirs(user_folder)

            # Ruta del archivo CSV
            file_path = os.path.join(user_folder, 'datos_financieros_cafe.csv')

            # Verificar si el archivo existe
            file_exists = os.path.isfile(file_path)

            # Guardar los datos en el archivo CSV
            with open(file_path, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=data.keys())
                if not file_exists:
                    writer.writeheader()  # Escribir encabezado si el archivo no existe
                writer.writerow(data)  # Agregar los datos al archivo

            flash('Datos de café guardados exitosamente.', 'success')
            return redirect(url_for('dashboard_cafe'))

        except ValueError as e:
            flash(f'Error en los datos ingresados: {e}', 'danger')
            return redirect(url_for('coffee_form'))
        except Exception as e:
            flash(f'Ocurrió un error inesperado: {e}', 'danger')
            return redirect(url_for('coffee_form'))

    # Ruta para guardar datos de cerdos
    @app.route('/submit_pig_form', methods=['POST'])
    def submit_pig_form():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión.', 'danger')
            return redirect(url_for('login'))

        # Datos específicos del formulario de cerdos
        data = {
            'total_ingresos': request.form['q1'],
            'cantidad_animales': request.form['q1_1'],
            'gastos_alimento': request.form['q2'],
            'pago_mano_obra': request.form['q3'],
            'gastos_servicios': request.form['q4'],
            'meses_engorda': request.form['q5'],
            'perdidas_animales': request.form['q6'],
            'dinero_disponible': request.form['q7'],
            'gastos_imprevistos': request.form['q8'],
            'total_deudas': request.form['q9'],
            'fecha_captura': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        }

        # Guardar datos en un archivo CSV
        file_path = f'{user_id}_cerdos.csv'
        file_exists = os.path.isfile(file_path)
        with open(file_path, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames(data.keys()))
            if not file_exists:
                writer.writeheader()
            writer.writerow(data)

        flash('Datos de cerdos guardados exitosamente.', 'success')
        return redirect(url_for('dashboard_cerdos'))

    # Ruta para guardar datos de ganado bovino
    @app.route('/submit_bovine_form', methods=['POST'])
    def submit_bovine_form():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión.', 'danger')
            return redirect(url_for('login'))

        # Datos específicos del formulario de ganado bovino
        data = {
            'total_ingresos': request.form['q1'],
            'cantidad_animales': request.form['q1_1'],
            'meses_engorda': request.form['q2'],
            'gastos_alimento': request.form['q3'],
            'pago_mano_obra': request.form['q4'],
            'gastos_servicios': request.form['q5'],
            'perdidas_animales': request.form['q6'],
            'dinero_disponible': request.form['q7'],
            'gastos_imprevistos': request.form['q8'],
            'total_deudas': request.form['q9'],
            'fecha_captura': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        }

        # Guardar datos en un archivo CSV
        file_path = f'{user_id}_ganado.csv'
        file_exists = os.path.isfile(file_path)
        with open(file_path, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames(data.keys()))
            if not file_exists:
                writer.writeheader()
            writer.writerow(data)

        flash('Datos de ganado bovino guardados exitosamente.', 'success')
        return redirect(url_for('dashboard_ganado'))

    # Ruta para guardar datos de huevos
    @app.route('/submit_eggs_form', methods=['POST'])
    def submit_eggs_form():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión.', 'danger')
            return redirect(url_for('login'))

        # Datos específicos del formulario de huevos
        data = {
            'total_ingresos': request.form['q1'],
            'cantidad_aves': request.form['q1_2'],
            'porcentaje_produccion': request.form['q1_3'],
            'huevos_diarios': request.form['q1_4'],
            'gastos_alimento': request.form['q2'],
            'pago_mano_obra': request.form['q3'],
            'gastos_servicios': request.form['q4'],
            'dinero_disponible': request.form['q5'],
            'gastos_imprevistos': request.form['q6'],
            'total_deudas': request.form['q7'],
            'fecha_captura': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        }

        # Guardar datos en un archivo CSV
        file_path = f'{user_id}_huevos.csv'
        file_exists = os.path.isfile(file_path)
        with open(file_path, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames(data.keys()))
            if not file_exists:
                writer.writeheader()
            writer.writerow(data)

        flash('Datos de huevos guardados exitosamente.', 'success')
        return redirect(url_for('dashboard_huevos'))

    # Ruta para guardar datos de maíz
    @app.route('/submit_corn_form', methods=['POST'])
    def submit_corn_form():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión.', 'danger')
            return redirect(url_for('login'))

        # Datos específicos del formulario de maíz
        data = {
            'total_ingresos': request.form['q1'],
            'meses_cosecha': request.form['q1_1'],
            'variedad_maiz': request.form['q1_2'],
            'hectareas': request.form['q1_3'],
            'gastos_insumos': request.form['q2'],
            'pago_jornales': request.form['q3'],
            'gastos_servicios': request.form['q4'],
            'valor_maquinaria': request.form['q5'],
            'dinero_disponible': request.form['q6'],
            'gastos_imprevistos': request.form['q7'],
            'total_deudas': request.form['q8'],
            'fecha_captura': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        }

        # Guardar datos en un archivo CSV
        file_path = f'{user_id}_maiz.csv'
        file_exists = os.path.isfile(file_path)
        with open(file_path, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames(data.keys()))
            if not file_exists:
                writer.writeheader()
            writer.writerow(data)

        flash('Datos de maíz guardados exitosamente.', 'success')
        return redirect(url_for('dashboard_maiz'))

    # Ruta para guardar datos de cítricos
    @app.route('/submit_citrus_form', methods=['POST'])
    def submit_citrus_form():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión.', 'danger')
            return redirect(url_for('login'))

        # Datos específicos del formulario de cítricos
        data = {
            'total_ingresos': request.form['q1'],
            'toneladas_cosechadas': request.form['q1_2'],
            'tipos_citricos': request.form['q1_3'],
            'hectareas': request.form['q1_4'],
            'gastos_insumos': request.form['q2'],
            'pago_jornales': request.form['q3'],
            'gastos_servicios': request.form['q4'],
            'valor_maquinaria': request.form['q5'],
            'dinero_disponible': request.form['q6'],
            'gastos_imprevistos': request.form['q7'],
            'total_deudas': request.form['q8'],
            'fecha_captura': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        }

        # Guardar datos en un archivo CSV
        file_path = f'{user_id}_citricos.csv'
        file_exists = os.path.isfile(file_path)
        with open(file_path, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames(data.keys()))
            if not file_exists:
                writer.writeheader()
            writer.writerow(data)

        flash('Datos de cítricos guardados exitosamente.', 'success')
        return redirect(url_for('dashboard_citricos'))
     # Ruta para el dashboard de café
    @app.route('/dashboard_cafe')
    def dashboard_cafe():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder al dashboard.', 'danger')
            return redirect(url_for('login'))

        # Leer datos generales desde el archivo CSV
        file_path = f'{user_id}_general_cafe.csv'
        general_data = {}
        if os.path.isfile(file_path):
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                general_data = next(reader, {})

        return render_template('dashboard_cafe.html', data=general_data)

    # Ruta para el dashboard de cerdos
    @app.route('/dashboard_cerdos')
    def dashboard_cerdos():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder al dashboard.', 'danger')
            return redirect(url_for('login'))

        # Leer datos generales desde el archivo CSV
        user_folder = os.path.join('data', user_id)
        file_path = os.path.join(user_folder, 'datos_generales.csv')
        general_data = {}
        if os.path.isfile(file_path):
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                general_data = next(reader, {})

        return render_template('dashboard_cerdos.html', data=general_data)
    # Ruta para el dashboard de ganado
    @app.route('/dashboard_ganado')
    def dashboard_ganado():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder al dashboard.', 'danger')
            return redirect(url_for('login'))

        # Leer datos generales desde el archivo CSV
        user_folder = os.path.join('data', user_id)
        file_path = os.path.join(user_folder, 'datos_generales.csv')
        general_data = {}
        if os.path.isfile(file_path):
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                general_data = next(reader, {})

        return render_template('dashboard_ganado.html', data=general_data)

    # Ruta para el dashboard de huevos
    @app.route('/dashboard_huevos')
    def dashboard_huevos():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder al dashboard.', 'danger')
            return redirect(url_for('login'))

        # Leer datos generales desde el archivo CSV
        user_folder = os.path.join('data', user_id)
        file_path = os.path.join(user_folder, 'datos_generales.csv')
        general_data = {}
        if os.path.isfile(file_path):
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                general_data = next(reader, {})

        return render_template('dashboard_huevos.html', data=general_data)
   
    # Ruta para el dashboard de maíz
    @app.route('/dashboard_maiz')
    def dashboard_maiz():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder al dashboard.', 'danger')
            return redirect(url_for('login'))

        # Leer datos generales desde el archivo CSV
        user_folder = os.path.join('data', user_id)
        file_path = os.path.join(user_folder, 'datos_generales.csv')
        general_data = {}
        if os.path.isfile(file_path):
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                general_data = next(reader, {})

        return render_template('dashboard_maiz.html', data=general_data)
  
    # Ruta para el dashboard de cítricos
    @app.route('/dashboard_citricos')
    def dashboard_citricos():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder al dashboard.', 'danger')
            return redirect(url_for('login'))

        # Leer datos generales desde el archivo CSV
        user_folder = os.path.join('data', user_id)
        file_path = os.path.join(user_folder, 'datos_generales.csv')
        general_data = {}
        if os.path.isfile(file_path):
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                general_data = next(reader, {})

        return render_template('dashboard_citricos.html', data=general_data)

    # Ruta para acceder a los datos financieros de café
    @app.route('/database_access_cafe', methods=['GET'])
    def database_access_cafe():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder a la base de datos.', 'danger')
            return redirect(url_for('login'))

        # Ruta del archivo CSV
        user_folder = os.path.join('data', user_id)
        file_path = os.path.join(user_folder, 'datos_financieros_cafe.csv')

        data = []
        rubros = [
            {'key': 'total_ingresos', 'label': 'Total de Ingresos'},
            {'key': 'produccion_total', 'label': 'Producción Total'},
            {'key': 'hectareas', 'label': 'Hectáreas'},
            {'key': 'gastos_insumos', 'label': 'Gastos en Insumos'},
            {'key': 'pago_jornales', 'label': 'Pago de Jornales'},
            {'key': 'gastos_servicios', 'label': 'Gastos en Servicios'},
            {'key': 'valor_maquinaria', 'label': 'Valor de Maquinaria'},
            {'key': 'dinero_disponible', 'label': 'Dinero Disponible'},
            {'key': 'gastos_imprevistos', 'label': 'Gastos Imprevistos'},
            {'key': 'total_deudas', 'label': 'Total de Deudas'},
            {'key': 'dias_trabajo', 'label': 'Días de Trabajo'},
            {'key': 'trabajadores', 'label': 'Trabajadores'},
            {'key': 'horas_venta', 'label': 'Horas de Venta'},
            {'key': 'horas_supervision', 'label': 'Horas de Supervisión'},
            {'key': 'lugar_comercializacion', 'label': 'Lugar de Comercialización'},
            {'key': 'comentarios', 'label': 'Comentarios'}
        ]

        if os.path.isfile(file_path):
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                data = list(reader)

        # Ordenar las fechas de captura en orden descendente
        fechas = sorted({row['fecha_captura'] for row in data}, reverse=True)

        return render_template('database_access_cafe.html', data=data, rubros=rubros, fechas=fechas)

    # Ruta para acceder a los datos financieros de cerdos
    @app.route('/database_access_cerdos')
    def database_access_cerdos():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder a la base de datos.', 'danger')
            return redirect(url_for('login'))

        # Leer datos financieros desde el archivo CSV
        file_path = f'{user_id}_cerdos.csv'
        financial_data = []
        if os.path.isfile(file_path):
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                financial_data = list(reader)

        return render_template('database_access_cerdos.html', data=financial_data)

    # Ruta para acceder a los datos financieros de ganado
    @app.route('/database_access_ganado')
    def database_access_ganado():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder a la base de datos.', 'danger')
            return redirect(url_for('login'))

        # Leer datos financieros desde el archivo CSV
        file_path = f'{user_id}_ganado.csv'
        financial_data = []
        if os.path.isfile(file_path):
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                financial_data = list(reader)

        return render_template('database_access_ganado.html', data=financial_data)

    # Ruta para acceder a los datos financieros de huevos
    @app.route('/database_access_huevos')
    def database_access_huevos():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder a la base de datos.', 'danger')
            return redirect(url_for('login'))

        # Leer datos financieros desde el archivo CSV
        file_path = f'{user_id}_huevos.csv'
        financial_data = []
        if os.path.isfile(file_path):
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                financial_data = list(reader)

        return render_template('database_access_huevos.html', data=financial_data)

    # Ruta para acceder a los datos financieros de maíz
    @app.route('/database_access_maiz')
    def database_access_maiz():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder a la base de datos.', 'danger')
            return redirect(url_for('login'))

        # Leer datos financieros desde el archivo CSV
        file_path = f'{user_id}_maiz.csv'
        financial_data = []
        if os.path.isfile(file_path):
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                financial_data = list(reader)

        return render_template('database_access_maiz.html', data=financial_data)

    # Ruta para acceder a los datos financieros de cítricos
    @app.route('/database_access_citricos')
    def database_access_citricos():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder a la base de datos.', 'danger')
            return redirect(url_for('login'))

        # Leer datos financieros desde el archivo CSV
        file_path = f'{user_id}_citricos.csv'
        financial_data = []
        if os.path.isfile(file_path):
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                financial_data = list(reader)

        return render_template('database_access_citricos.html', data=financial_data)
        # Ruta para generar estados financieros de café
    @app.route('/financial_statements_cafe', methods=['GET', 'POST'])
    def financial_statements_cafe():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder a los estados financieros.', 'danger')
            return redirect(url_for('login'))

        # Ruta del archivo CSV
        user_folder = os.path.join('data', user_id)
        file_path = os.path.join(user_folder, 'datos_financieros_cafe.csv')

        financial_data = []
        selected_date = None

        if os.path.isfile(file_path):
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                financial_data = list(reader)

        # Ordenar las fechas de captura en orden descendente
        fechas_disponibles = sorted([row['fecha_captura'] for row in financial_data], reverse=True)

        # Si no se envía una fecha desde el formulario, usar la fecha más reciente
        if request.method == 'POST':
            selected_date = request.form.get('fecha_captura')
        elif fechas_disponibles:
            selected_date = fechas_disponibles[0]  # Fecha más reciente

        # Filtrar los datos por la fecha seleccionada
        filtered_data = [row for row in financial_data if row['fecha_captura'] == selected_date]

        # Calcular estados financieros y razones financieras
        if filtered_data:
            data = filtered_data[0]  # Tomar el primer registro filtrado
            costos_directos = float(data['gastos_insumos']) + float(data['pago_jornales']) + float(data['gastos_servicios']) + float(data['gastos_imprevistos'])
            utilidad_bruta = float(data['total_ingresos']) - costos_directos
            utilidad_neta = utilidad_bruta - float(data['total_deudas'])
            activos_totales = float(data['dinero_disponible']) + float(data['valor_maquinaria'])
            patrimonio_neto = activos_totales - float(data['total_deudas'])
            total_gastos = costos_directos
            margen_ganancia = (utilidad_bruta / float(data['total_ingresos'])) * 100 if float(data['total_ingresos']) else 0
            razon_endeudamiento = float(data['total_deudas']) / activos_totales if activos_totales else 0

            # Valores de referencia para razones financieras
            referencias = {
                'margen_ganancia': 'Mayor al 20% es favorable',
                'razon_endeudamiento': 'Menor al 50% es favorable'
            }

            # Preparar datos para el HTML
            financial_summary = {
                'activos': {
                    'maquinaria_equipo': float(data['valor_maquinaria']),
                    'dinero_disponible': float(data['dinero_disponible']),
                    'total_activos': activos_totales
                },
                'pasivos': {
                    'deudas': float(data['total_deudas']),
                    'total_pasivos': float(data['total_deudas'])
                },
                'patrimonio': patrimonio_neto,
                'ingresos': {
                    'venta_cafe': float(data['total_ingresos'])
                },
                'gastos': {
                    'insumos': float(data['gastos_insumos']),
                    'jornales': float(data['pago_jornales']),
                    'servicios': float(data['gastos_servicios']),
                    'imprevistos': float(data['gastos_imprevistos']),
                    'total_gastos': total_gastos
                },
                'utilidad_neta': utilidad_neta,
                'razones_financieras': {
                    'margen_ganancia': margen_ganancia,
                    'razon_endeudamiento': razon_endeudamiento
                },
                'referencias': referencias,
                'fecha_captura': selected_date
            }
        else:
            financial_summary = None

        return render_template('financial_statements_cafe.html', data=financial_summary, fechas=fechas_disponibles)

    # Ruta para generar estados financieros de cerdos
    @app.route('/financial_statements_cerdos')
    def financial_statements_cerdos():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder a los estados financieros.', 'danger')
            return redirect(url_for('login'))

        # Leer datos financieros desde el archivo CSV
        file_path = f'{user_id}_cerdos.csv'
        financial_data = []
        if os.path.isfile(file_path):
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                financial_data = list(reader)

        return render_template('financial_statements_cerdos.html', data=financial_data)

    # Ruta para generar estados financieros de ganado
    @app.route('/financial_statements_ganado')
    def financial_statements_ganado():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder a los estados financieros.', 'danger')
            return redirect(url_for('login'))

        # Leer datos financieros desde el archivo CSV
        file_path = f'{user_id}_ganado.csv'
        financial_data = []
        if os.path.isfile(file_path):
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                financial_data = list(reader)

        return render_template('financial_statements_ganado.html', data=financial_data)

    # Ruta para generar estados financieros de huevos
    @app.route('/financial_statements_huevos')
    def financial_statements_huevos():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder a los estados financieros.', 'danger')
            return redirect(url_for('login'))

        # Leer datos financieros desde el archivo CSV
        file_path = f'{user_id}_huevos.csv'
        financial_data = []
        if os.path.isfile(file_path):
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                financial_data = list(reader)

        return render_template('financial_statements_huevos.html', data=financial_data)

    # Ruta para generar estados financieros de maíz
    @app.route('/financial_statements_maiz')
    def financial_statements_maiz():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder a los estados financieros.', 'danger')
            return redirect(url_for('login'))

        # Leer datos financieros desde el archivo CSV
        file_path = f'{user_id}_maiz.csv'
        financial_data = []
        if os.path.isfile(file_path):
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                financial_data = list(reader)

        return render_template('financial_statements_maiz.html', data=financial_data)

    # Ruta para generar estados financieros de cítricos
    @app.route('/financial_statements_citricos')
    def financial_statements_citricos():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder a los estados financieros.', 'danger')
            return redirect(url_for('login'))

        # Leer datos financieros desde el archivo CSV
        file_path = f'{user_id}_citricos.csv'
        financial_data = []
        if os.path.isfile(file_path):
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                financial_data = list(reader)

        return render_template('financial_statements_citricos.html', data=financial_data)
    
    @app.route('/submit_registro_cliente', methods=['POST'])
    def submit_registro_cliente():
        nombre = request.form['nombre']
        telefono = request.form['telefono']
        verificacion = request.form['verificacion']
        email = request.form.get('email', '')  # Opcional
        password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        dia = request.form['dia']
        mes = request.form['mes']
        año = request.form['año']
        genero = request.form['genero']
        terminos = request.form.get('terminos')

        # Ruta del archivo y creación de la carpeta si no existe
        base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
        file_path = os.path.join(base_dir, 'users.csv')

        # Guardar los datos en un archivo CSV
        file_exists = os.path.isfile(file_path)
        with open(file_path, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=['nombre', 'telefono', 'verificacion', 'email', 'password', 'fecha_nacimiento', 'genero'])
            if not file_exists:
                writer.writeheader()
            writer.writerow({
                'nombre': nombre,
                'telefono': telefono,
                'verificacion': verificacion,
                'email': email,
                'password': password,
                'fecha_nacimiento': f"{dia}/{mes}/{año}",
                'genero': genero
            })

        flash('Registro exitoso.', 'success')
        return redirect(url_for('login'))

    @app.route('/request_modification', methods=['POST'])
    def request_modification():
        try:
            # Obtener datos del formulario
            user_email = request.form.get('email')
            user_name = request.form.get('name')
            modification_details = request.form.get('details')

            # Validar que los campos no estén vacíos
            if not user_email or not user_name or not modification_details:
                return {'status': 'error', 'message': 'Todos los campos son obligatorios.'}, 400

            # Configuración del correo
            sender_email = "cidatmex@gmail.com"
            sender_password = "TU_CONTRASEÑA"  # Reemplaza con la contraseña del correo
            recipient_email = "cidatmex@gmail.com"

            # Correo para el administrador
            admin_subject = f"Cambio de base de datos de {user_email}"
            admin_body = f"""
            Se ha solicitado un cambio en la base de datos:
            - Nombre: {user_name}
            - Correo: {user_email}
            - Detalles: {modification_details}
            """
            send_email(sender_email, sender_password, recipient_email, admin_subject, admin_body)

            # Correo de confirmación para el usuario
            user_subject = "Tu solicitud está siendo procesada"
            user_body = f"""
            Estimado/a {user_name},

            Hemos recibido tu solicitud para modificar la base de datos. Nuestro equipo de servicio al cliente se pondrá en contacto contigo pronto.

            Agradecemos tu preferencia.

            Atentamente,
            Ciencia de Datos México
            """
            send_email(sender_email, sender_password, user_email, user_subject, user_body)

            return {'status': 'success', 'message': 'Solicitud enviada correctamente.'}, 200

        except Exception as e:
            return {'status': 'error', 'message': str(e)}, 500


    def send_email(sender_email, sender_password, recipient_email, subject, body):
        """Función para enviar correos electrónicos."""
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)

    @app.route('/my_analysis_cafe', methods=['GET', 'POST'])
    def my_analysis_cafe():
        user_id = session.get('user_id')
        if not user_id:
            flash('Por favor, inicia sesión para acceder al análisis.', 'danger')
            return redirect(url_for('login'))

        # Ruta del archivo CSV
        file_path = f"data/{user_id}/datos_financieros_cafe.csv"
        try:
            data = pd.read_csv(file_path)

            # Ordenar las fechas y obtener la más reciente
            data['fecha_captura'] = pd.to_datetime(data['fecha_captura'])
            data = data.sort_values(by='fecha_captura', ascending=False)
            fechas_disponibles = data['fecha_captura'].dt.strftime('%Y-%m-%d').unique()
            fecha_seleccionada = request.form.get('fecha_captura', fechas_disponibles[0])

            # Filtrar los datos por la fecha seleccionada
            data_filtrada = data[data['fecha_captura'] == pd.to_datetime(fecha_seleccionada)]

            # Cálculos obligatorios
            if 'gastos_insumos' in data.columns and 'pago_jornales' in data.columns and \
               'gastos_servicios' in data.columns and 'gastos_imprevistos' in data.columns:
                data['gastos_totales'] = data['gastos_insumos'] + data['pago_jornales'] + data['gastos_servicios'] + data['gastos_imprevistos']
            else:
                flash('Faltan columnas necesarias para calcular gastos totales.', 'danger')
                return render_template('my_analysis_cafe.html')

            # Verifica que la columna 'gastos_totales' exista
            if 'gastos_totales' not in data.columns:
                flash('Error al calcular gastos totales. Verifica los datos.', 'danger')
                return render_template('my_analysis_cafe.html')

            # Gráficos para Rentabilidad
            fig_sunburst = px.sunburst(
                data_filtrada,
                path=['gastos_insumos', 'pago_jornales', 'gastos_servicios', 'gastos_imprevistos'],
                values='gastos_totales',
                title="Jerarquía de Gastos"
            )
            fig_line = px.line(
                data,
                x='fecha_captura',
                y=['total_ingresos', 'utilidad_neta'],
                title="Ingresos vs. Utilidad Neta"
            )
            fig_bar = px.bar(
                data,
                x='fecha_captura',
                y=['total_ingresos', 'gastos_totales'],
                title="Ingresos vs. Gastos Totales"
            )

            # Convertir gráficos a HTML
            sunburst_html = fig_sunburst.to_html(full_html=False)
            line_html = fig_line.to_html(full_html=False)
            bar_html = fig_bar.to_html(full_html=False)

            return render_template(
                'my_analysis_cafe.html',
                sunburst_html=sunburst_html,
                line_html=line_html,
                bar_html=bar_html,
                ultimos_valores=data_filtrada.iloc[0].to_dict(),
                fechas_disponibles=fechas_disponibles,
                fecha_seleccionada=fecha_seleccionada
            )
        except FileNotFoundError:
            flash('No se encontraron datos para generar el análisis.', 'danger')
            return render_template('my_analysis_cafe.html')
