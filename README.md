# LÁMINAS Y TABLEROS MONTOYA

## Configuración

Copia `.env.example` como `.env` para desarrollo y define todas sus variables. La aplicación no inicia si falta una; en Render configúralas como variables de entorno.

## Migraciones

La aplicación usa Flask-Migrate. No ejecuta `db.create_all()` al arrancar, porque las migraciones son la fuente de verdad del esquema.

```powershell
$env:FLASK_APP = 'app.py'
flask db upgrade
```

Para un cambio nuevo: `flask db migrate -m "descripcion"` y luego `flask db upgrade`. En Render, ejecuta `flask db upgrade` antes de iniciar Gunicorn.

La migración incluida agrega `clientes.id_usuario` de forma nullable. Los clientes existentes quedan sin vínculo: asígnalos desde Editar cliente. No se relacionan por correo automáticamente para evitar asociaciones erróneas.

`RATELIMIT_STORAGE_URI=memory://` funciona con un proceso; para varias instancias de Render usa Redis compartido.
