import os
from functools import wraps
from datetime import datetime, date, timedelta

from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, text
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'Manolo1029')
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_NAME = os.environ.get('DB_NAME', 'fabrica_tejas')

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'cambia-esta-clave-antes-de-publicar')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
db = SQLAlchemy(app)

# ---------- MODELOS ----------

class Cliente(db.Model):
    __tablename__ = 'clientes'
    id_cliente = db.Column(db.Integer, primary_key=True)
    tipo_persona = db.Column(db.Enum('Natural', 'Juridica'), nullable=False)
    numero_identificacion = db.Column(db.String(20), unique=True, nullable=False)
    nombre_razon_social = db.Column(db.String(150), nullable=False)
    telefono = db.Column(db.String(20))
    correo = db.Column(db.String(100))


class Producto(db.Model):
    __tablename__ = 'productos'
    id_producto = db.Column(db.Integer, primary_key=True)
    tipo_estilo = db.Column(db.String(50), nullable=False)
    calibre = db.Column(db.String(10), nullable=False)
    desarrollo = db.Column(db.String(10))
    precio_por_metro = db.Column(db.Numeric(10, 2), nullable=False)


class Pedido(db.Model):
    __tablename__ = 'pedidos'
    id_pedido = db.Column(db.Integer, primary_key=True)
    id_cliente = db.Column(db.Integer, db.ForeignKey('clientes.id_cliente'), nullable=False)
    id_vendedor = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=True)
    fecha_pedido = db.Column(db.Date, nullable=False)
    estado = db.Column(db.Enum('Pendiente', 'Listo para entrega', 'Entregado'), nullable=False, default='Pendiente')
    total_pedido = db.Column(db.Numeric(10, 2), default=0)

    cliente = db.relationship('Cliente', backref='pedidos')
    vendedor = db.relationship('Usuario', foreign_keys=[id_vendedor], backref='pedidos_facturados')


class DetallePedido(db.Model):
    __tablename__ = 'detallepedido'
    id_detalle = db.Column(db.Integer, primary_key=True)
    id_pedido = db.Column(db.Integer, db.ForeignKey('pedidos.id_pedido'), nullable=False)
    id_producto = db.Column(db.Integer, db.ForeignKey('productos.id_producto'), nullable=False)
    medida_metros = db.Column(db.Numeric(5, 2), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)

    pedido = db.relationship('Pedido', backref='detalles')
    producto = db.relationship('Producto')


class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id_usuario = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    correo = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.Enum('Cliente', 'Administrador', 'Operario', 'Vendedor'), nullable=False, default='Cliente')


class SolicitudRecuperacion(db.Model):
    __tablename__ = 'solicitudes_recuperacion'
    id_solicitud = db.Column(db.Integer, primary_key=True)
    correo = db.Column(db.String(120), nullable=False)
    fecha_solicitud = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    estado = db.Column(db.Enum('Pendiente', 'Atendida'), nullable=False, default='Pendiente')


# ---------- SEGURIDAD Y ROLES ----------

def login_requerido(vista):
    @wraps(vista)
    def vista_protegida(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Inicia sesión para acceder a esta sección.', 'warning')
            return redirect(url_for('iniciar_sesion'))
        return vista(*args, **kwargs)
    return vista_protegida


def roles_requeridos(*roles):
    def decorador(vista):
        @wraps(vista)
        def vista_protegida(*args, **kwargs):
            if 'usuario_id' not in session:
                flash('Inicia sesión para acceder a esta sección.', 'warning')
                return redirect(url_for('iniciar_sesion'))
            if session.get('usuario_rol') not in roles:
                flash('No tienes permiso para acceder a esta sección.', 'danger')
                return redirect(url_for('panel'))
            return vista(*args, **kwargs)
        return vista_protegida
    return decorador

# ---------- RUTAS: CLIENTES ----------

@app.route('/')
@app.route('/empresa')
def pagina_empresa():
    return render_template('empresa.html')


# ---------- ACCESO DE USUARIOS ----------

@app.route('/configurar-admin-inicial', methods=['GET', 'POST'])
def configurar_admin_inicial():
    if Usuario.query.filter_by(rol='Administrador').first():
        flash('El administrador inicial ya fue configurado. Inicia sesión o crea una cuenta de cliente.', 'info')
        return redirect(url_for('iniciar_sesion'))

    if request.method == 'POST':
        usuario = Usuario(
            nombre=request.form['nombre'].strip(),
            correo=request.form['correo'].strip().lower(),
            password_hash=generate_password_hash(request.form['password']),
            rol='Administrador'
        )
        db.session.add(usuario)
        db.session.commit()
        flash('Administrador creado. Ya puedes iniciar sesión.', 'success')
        return redirect(url_for('iniciar_sesion'))
    return render_template('acceso.html', modo='administrador')


@app.route('/crear-cuenta', methods=['GET', 'POST'])
def crear_cuenta():
    if request.method == 'POST':
        correo = request.form['correo'].strip().lower()
        if Usuario.query.filter_by(correo=correo).first():
            flash('Ya existe una cuenta con ese correo.', 'danger')
            return redirect(url_for('crear_cuenta'))
        if len(request.form['password']) < 8:
            flash('La contraseña debe tener al menos 8 caracteres.', 'danger')
            return redirect(url_for('crear_cuenta'))

        usuario = Usuario(
            nombre=request.form['nombre'].strip(), correo=correo,
            password_hash=generate_password_hash(request.form['password']), rol='Cliente'
        )
        db.session.add(usuario)
        db.session.commit()
        flash('Tu cuenta fue creada. Ya puedes iniciar sesión.', 'success')
        return redirect(url_for('iniciar_sesion'))
    return render_template('acceso.html', modo='registro')


@app.route('/iniciar-sesion', methods=['GET', 'POST'])
def iniciar_sesion():
    if request.method == 'POST':
        usuario = Usuario.query.filter_by(correo=request.form['correo'].strip().lower()).first()
        if usuario and check_password_hash(usuario.password_hash, request.form['password']):
            session.clear()
            session['usuario_id'] = usuario.id_usuario
            session['usuario_nombre'] = usuario.nombre
            session['usuario_rol'] = usuario.rol
            return redirect(url_for('panel'))
        flash('Correo o contraseña incorrectos.', 'danger')
    return render_template('acceso.html', modo='login')


@app.route('/recuperar-contrasena', methods=['GET', 'POST'])
def recuperar_contrasena():
    if request.method == 'POST':
        correo = request.form['correo'].strip().lower()
        if Usuario.query.filter_by(correo=correo).first():
            solicitud = SolicitudRecuperacion(correo=correo)
            db.session.add(solicitud)
            db.session.commit()
        # El mensaje no revela si un correo está registrado.
        flash('Si el correo está registrado, un administrador recibirá tu solicitud de recuperación.', 'success')
        return redirect(url_for('iniciar_sesion'))
    return render_template('acceso.html', modo='recuperar')


@app.route('/cerrar-sesion')
def cerrar_sesion():
    session.clear()
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('pagina_empresa'))


@app.route('/panel')
@login_requerido
def panel():
    rol = session['usuario_rol']
    datos = {}
    if rol == 'Administrador':
        datos = {'Clientes registrados': Cliente.query.count(), 'Productos activos': Producto.query.count(), 'Pedidos registrados': Pedido.query.count()}
    elif rol == 'Operario':
        datos = {'Pedidos pendientes': Pedido.query.filter_by(estado='Pendiente').count(), 'Listos para entrega': Pedido.query.filter_by(estado='Listo para entrega').count(), 'Pedidos entregados': Pedido.query.filter_by(estado='Entregado').count()}
    elif rol == 'Vendedor':
        pedidos_vendedor = Pedido.query.filter_by(id_vendedor=session['usuario_id'])
        datos = {'Pedidos registrados': pedidos_vendedor.count(), 'Pendientes': pedidos_vendedor.filter_by(estado='Pendiente').count(), 'Listos para entrega': pedidos_vendedor.filter_by(estado='Listo para entrega').count()}
    else:
        cliente = Cliente.query.filter_by(correo=Usuario.query.get(session['usuario_id']).correo).first()
        pedidos_cliente = Pedido.query.filter_by(id_cliente=cliente.id_cliente).count() if cliente else 0
        datos = {'Mis pedidos': pedidos_cliente, 'Estado de cuenta': 'Activo', 'Atención': 'Contáctanos para cotizar'}
    return render_template('panel.html', datos=datos, rol=rol)


@app.route('/mis-pedidos')
@roles_requeridos('Cliente')
def mis_pedidos():
    usuario = Usuario.query.get(session['usuario_id'])
    cliente = Cliente.query.filter_by(correo=usuario.correo).first()
    pedidos = Pedido.query.filter_by(id_cliente=cliente.id_cliente).order_by(Pedido.fecha_pedido.desc()).all() if cliente else []
    return render_template('mis_pedidos.html', pedidos=pedidos, cliente_registrado=cliente is not None)


@app.route('/usuarios')
@roles_requeridos('Administrador')
def usuarios():
    solicitudes = SolicitudRecuperacion.query.filter_by(estado='Pendiente').order_by(SolicitudRecuperacion.fecha_solicitud.desc()).all()
    return render_template('usuarios.html', usuarios=Usuario.query.order_by(Usuario.nombre).all(), solicitudes=solicitudes)


@app.route('/usuarios/<int:id>/rol', methods=['POST'])
@roles_requeridos('Administrador')
def actualizar_rol(id):
    usuario = Usuario.query.get_or_404(id)
    nuevo_rol = request.form['rol']
    if nuevo_rol not in ('Cliente', 'Administrador', 'Operario', 'Vendedor'):
        flash('Rol no válido.', 'danger')
    elif usuario.id_usuario == session['usuario_id'] and nuevo_rol != 'Administrador':
        flash('No puedes quitarte tu propio rol de administrador.', 'danger')
    else:
        usuario.rol = nuevo_rol
        db.session.commit()
        flash(f'El rol de {usuario.nombre} fue actualizado.', 'success')
    return redirect(url_for('usuarios'))


@app.route('/usuarios/<int:id>/eliminar', methods=['POST'])
@roles_requeridos('Administrador')
def eliminar_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    if usuario.id_usuario == session['usuario_id']:
        flash('No puedes eliminar tu propia cuenta mientras tienes la sesión activa.', 'danger')
    elif usuario.rol == 'Administrador' and Usuario.query.filter_by(rol='Administrador').count() <= 1:
        flash('No puedes eliminar al único administrador del sistema.', 'danger')
    elif Pedido.query.filter_by(id_vendedor=usuario.id_usuario).first():
        flash(f'No puedes eliminar a {usuario.nombre} porque tiene pedidos registrados. Conserva la trazabilidad o reasigna sus pedidos.', 'danger')
    else:
        db.session.delete(usuario)
        db.session.commit()
        flash(f'La cuenta de {usuario.nombre} fue eliminada.', 'success')
    return redirect(url_for('usuarios'))


@app.route('/solicitudes-recuperacion/<int:id>/atender', methods=['POST'])
@roles_requeridos('Administrador')
def atender_solicitud_recuperacion(id):
    solicitud = SolicitudRecuperacion.query.get_or_404(id)
    usuario = Usuario.query.filter_by(correo=solicitud.correo).first()
    nueva_password = request.form['nueva_password']
    if usuario and len(nueva_password) >= 8:
        usuario.password_hash = generate_password_hash(nueva_password)
        solicitud.estado = 'Atendida'
        db.session.commit()
        flash(f'Contraseña restablecida para {usuario.correo}.', 'success')
    else:
        flash('La contraseña debe tener al menos 8 caracteres.', 'danger')
    return redirect(url_for('usuarios'))

@app.route('/administracion')
@roles_requeridos('Administrador')
def inicio():
    clientes = Cliente.query.all()
    return render_template('clientes.html', clientes=clientes)


@app.route('/nuevo_cliente', methods=['GET'])
@roles_requeridos('Administrador')
def mostrar_formulario_cliente():
    return render_template('nuevo_cliente.html', cliente=None)


@app.route('/nuevo_cliente', methods=['POST'])
@roles_requeridos('Administrador')
def guardar_cliente():
    nuevo = Cliente(
        tipo_persona=request.form['tipo_persona'],
        numero_identificacion=request.form['numero_identificacion'],
        nombre_razon_social=request.form['nombre_razon_social'],
        telefono=request.form['telefono'],
        correo=request.form['correo']
    )
    db.session.add(nuevo)
    db.session.commit()
    return redirect('/administracion')


@app.route('/editar_cliente/<int:id>', methods=['GET'])
@roles_requeridos('Administrador')
def mostrar_formulario_editar_cliente(id):
    cliente = Cliente.query.get(id)
    return render_template('nuevo_cliente.html', cliente=cliente)


@app.route('/editar_cliente/<int:id>', methods=['POST'])
@roles_requeridos('Administrador')
def actualizar_cliente(id):
    cliente = Cliente.query.get(id)
    cliente.tipo_persona = request.form['tipo_persona']
    cliente.numero_identificacion = request.form['numero_identificacion']
    cliente.nombre_razon_social = request.form['nombre_razon_social']
    cliente.telefono = request.form['telefono']
    cliente.correo = request.form['correo']
    db.session.commit()
    return redirect('/administracion')


@app.route('/eliminar_cliente/<int:id>')
@roles_requeridos('Administrador')
def eliminar_cliente(id):
    cliente = Cliente.query.get(id)
    db.session.delete(cliente)
    db.session.commit()
    return redirect('/administracion')

# ---------- RUTAS: PRODUCTOS ----------

@app.route('/productos')
@roles_requeridos('Administrador')
def ver_productos():
    productos = Producto.query.all()
    return render_template('productos.html', productos=productos)


@app.route('/nuevo_producto', methods=['GET'])
@roles_requeridos('Administrador')
def mostrar_formulario_producto():
    return render_template('nuevo_producto.html', producto=None)


@app.route('/nuevo_producto', methods=['POST'])
@roles_requeridos('Administrador')
def guardar_producto():
    desarrollo_valor = request.form['desarrollo']
    if desarrollo_valor == '':
        desarrollo_valor = None

    nuevo = Producto(
        tipo_estilo=request.form['tipo_estilo'],
        calibre=request.form['calibre'],
        desarrollo=desarrollo_valor,
        precio_por_metro=request.form['precio_por_metro']
    )
    db.session.add(nuevo)
    db.session.commit()
    return redirect('/productos')


@app.route('/editar_producto/<int:id>', methods=['GET'])
@roles_requeridos('Administrador')
def mostrar_formulario_editar_producto(id):
    producto = Producto.query.get(id)
    return render_template('nuevo_producto.html', producto=producto)


@app.route('/editar_producto/<int:id>', methods=['POST'])
@roles_requeridos('Administrador')
def actualizar_producto(id):
    producto = Producto.query.get(id)
    desarrollo_valor = request.form['desarrollo']
    if desarrollo_valor == '':
        desarrollo_valor = None

    producto.tipo_estilo = request.form['tipo_estilo']
    producto.calibre = request.form['calibre']
    producto.desarrollo = desarrollo_valor
    producto.precio_por_metro = request.form['precio_por_metro']
    db.session.commit()
    return redirect('/productos')


@app.route('/eliminar_producto/<int:id>')
@roles_requeridos('Administrador')
def eliminar_producto(id):
    producto = Producto.query.get(id)
    db.session.delete(producto)
    db.session.commit()
    return redirect('/productos')

# ---------- RUTAS: PEDIDOS ----------

@app.route('/pedidos')
@roles_requeridos('Administrador', 'Operario', 'Vendedor')
def ver_pedidos():
    rol = session['usuario_rol']
    consulta = Pedido.query.order_by(Pedido.fecha_pedido.desc(), Pedido.id_pedido.desc())
    if rol == 'Vendedor':
        consulta = consulta.filter_by(id_vendedor=session['usuario_id'])
    pedidos = consulta.all()

    resumen = None
    if rol == 'Vendedor':
        hoy = date.today()
        def ventas_desde(inicio):
            return db.session.query(func.count(Pedido.id_pedido), func.coalesce(func.sum(Pedido.total_pedido), 0)).filter(Pedido.id_vendedor == session['usuario_id'], Pedido.fecha_pedido >= inicio).one()
        semana = ventas_desde(hoy - timedelta(days=6))
        quincena = ventas_desde(hoy - timedelta(days=14))
        mes = ventas_desde(hoy.replace(day=1))
        resumen = {
            'Esta semana': {'pedidos': semana[0], 'total': semana[1]},
            'Últimos 15 días': {'pedidos': quincena[0], 'total': quincena[1]},
            'Este mes': {'pedidos': mes[0], 'total': mes[1]},
        }
    return render_template('pedidos.html', pedidos=pedidos, resumen=resumen)


@app.route('/ver_pedido/<int:id>')
@roles_requeridos('Administrador', 'Operario', 'Vendedor')
def ver_pedido(id):
    pedido = Pedido.query.get_or_404(id)
    if session['usuario_rol'] == 'Vendedor' and pedido.id_vendedor != session['usuario_id']:
        flash('Solo puedes consultar los pedidos que registraste.', 'danger')
        return redirect(url_for('ver_pedidos'))
    return render_template('remision.html', pedido=pedido)


@app.route('/pedidos/<int:id>/estado', methods=['POST'])
@roles_requeridos('Operario')
def actualizar_estado_pedido(id):
    pedido = Pedido.query.get_or_404(id)
    nuevo_estado = request.form.get('estado')
    estados_validos = ('Pendiente', 'Listo para entrega', 'Entregado')

    if nuevo_estado not in estados_validos:
        flash('El estado seleccionado no es válido.', 'danger')
    else:
        pedido.estado = nuevo_estado
        db.session.commit()
        flash(f'El pedido #{pedido.id_pedido} ahora está: {nuevo_estado}.', 'success')
    return redirect(url_for('ver_pedidos'))

@app.route('/nuevo_pedido', methods=['GET'])
@roles_requeridos('Administrador', 'Vendedor')
def mostrar_formulario_pedido():
    clientes = Cliente.query.all()
    productos = Producto.query.all()
    vendedores = Usuario.query.filter_by(rol='Vendedor').order_by(Usuario.nombre).all()
    return render_template('nuevo_pedido.html', clientes=clientes, productos=productos, vendedores=vendedores, pedido=None)


@app.route('/nuevo_pedido', methods=['POST'])
@roles_requeridos('Administrador', 'Vendedor')
def guardar_pedido():
    id_vendedor = session['usuario_id'] if session['usuario_rol'] == 'Vendedor' else request.form.get('id_vendedor', type=int)
    if not id_vendedor or not Usuario.query.filter_by(id_usuario=id_vendedor, rol='Vendedor').first():
        flash('Debes asignar un vendedor válido al pedido.', 'danger')
        return redirect(url_for('mostrar_formulario_pedido'))
    # 1. Crear el pedido (la cabecera)
    nuevo_pedido = Pedido(
        id_cliente=request.form['id_cliente'],
        id_vendedor=id_vendedor,
        fecha_pedido=request.form['fecha_pedido'],
        estado='Pendiente'
    )
    db.session.add(nuevo_pedido)
    db.session.commit()  # Se guarda ya, para que MySQL le asigne un id_pedido

    # 2. Calcular el subtotal de la linea de producto
    id_producto = request.form['id_producto']
    medida = float(request.form['medida_metros'])
    cantidad = int(request.form['cantidad'])

    producto = Producto.query.get(id_producto)
    subtotal = medida * float(producto.precio_por_metro) * cantidad

    # 3. Crear la linea de detalle
    detalle = DetallePedido(
        id_pedido=nuevo_pedido.id_pedido,
        id_producto=id_producto,
        medida_metros=medida,
        cantidad=cantidad,
        subtotal=subtotal
    )
    db.session.add(detalle)

    # 4. Actualizar el total del pedido
    nuevo_pedido.total_pedido = subtotal
    db.session.commit()

    return redirect('/pedidos')


@app.route('/editar_pedido/<int:id>', methods=['GET', 'POST'])
@roles_requeridos('Administrador', 'Vendedor')
def editar_pedido(id):
    pedido = Pedido.query.get_or_404(id)
    if session['usuario_rol'] == 'Vendedor' and pedido.id_vendedor != session['usuario_id']:
        flash('Solo puedes modificar los pedidos que registraste.', 'danger')
        return redirect(url_for('ver_pedidos'))

    if request.method == 'POST':
        pedido.id_cliente = request.form['id_cliente']
        pedido.fecha_pedido = request.form['fecha_pedido']
        if session['usuario_rol'] == 'Administrador':
            id_vendedor = request.form.get('id_vendedor', type=int)
            if not id_vendedor or not Usuario.query.filter_by(id_usuario=id_vendedor, rol='Vendedor').first():
                flash('Selecciona un vendedor válido.', 'danger')
                return redirect(url_for('editar_pedido', id=id))
            pedido.id_vendedor = id_vendedor
        detalle = pedido.detalles[0]
        detalle.id_producto = request.form['id_producto']
        detalle.medida_metros = float(request.form['medida_metros'])
        detalle.cantidad = int(request.form['cantidad'])
        producto = Producto.query.get_or_404(detalle.id_producto)
        detalle.subtotal = detalle.medida_metros * float(producto.precio_por_metro) * detalle.cantidad
        pedido.total_pedido = detalle.subtotal
        db.session.commit()
        flash(f'Pedido #{pedido.id_pedido} actualizado correctamente.', 'success')
        return redirect(url_for('ver_pedidos'))

    clientes = Cliente.query.all()
    productos = Producto.query.all()
    vendedores = Usuario.query.filter_by(rol='Vendedor').order_by(Usuario.nombre).all()
    return render_template('nuevo_pedido.html', clientes=clientes, productos=productos, vendedores=vendedores, pedido=pedido)

if __name__ == '__main__':
    app.run(debug=True)
