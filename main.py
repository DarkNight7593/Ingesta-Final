# script_poblar_directo.py
import boto3
import hashlib
import json
import random
import uuid

# Configuración
TABLE_USER = 'dev-t_usuario'
TABLE_CURSO = 'dev-t_curso'
TABLE_HORARIO = 'dev-t_horario'
PASSWORD = '12345'

TENANTS = ["udemy", "cursarplus", "edutec"]

# Inicializar recursos DynamoDB
dynamodb = boto3.resource('dynamodb')
t_user = dynamodb.Table(TABLE_USER)
t_curso = dynamodb.Table(TABLE_CURSO)
t_horario = dynamodb.Table(TABLE_HORARIO)

# Función para hashear contraseñas
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Cargar cursos desde archivo
def cargar_cursos(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

cursos_por_tenant = {
    "udemy": cargar_cursos("cursos_udemy.txt"),
    "cursarplus": cargar_cursos("cursos_cursarplus.txt"),
    "edutec": cargar_cursos("cursos_edutec.txt")
}

# Crear instructores y poblar cursos + horarios
def crear_instructores_y_poblar():
    for tenant_id in TENANTS:
        print(f"🏢 Procesando tenant: {tenant_id}")

        instructores = []
        for i in range(6):
            dni = f"{tenant_id[:3]}000{i+1}"
            full_name = f"Instructor {i+1} ({tenant_id})"
            item = {
                "tenant_id_rol": f"{tenant_id}#instructor",
                "dni": dni,
                "full_name": full_name,
                "rol": "instructor",
                "password": hash_password(PASSWORD)
            }
            t_user.put_item(Item=item)
            instructores.append(item)
            print(f"✅ Instructor creado: {dni} - {full_name}")

        cursos = cursos_por_tenant[tenant_id]
        cursos_por_instructor = [[] for _ in range(6)]
        for idx, curso in enumerate(cursos[:30]):
            cursos_por_instructor[idx % 6].append(curso)

        for i, instructor in enumerate(instructores):
            for curso in cursos_por_instructor[i]:
                curso_id = str(uuid.uuid4())
                item = {
                    "tenant_id": tenant_id,
                    "curso_id": curso_id,
                    "nombre": curso["nombre"],
                    "descripcion": curso["descripcion"],
                    "inicio": curso["inicio"],
                    "fin": curso["fin"],
                    "precio": curso["precio"],
                    "informacion": curso["informacion"],
                    "instructor_dni": instructor["dni"],
                    "instructor_nombre": instructor["full_name"],
                    "tenant_instructor": f"{tenant_id}#{instructor['dni']}"
                }
                t_curso.put_item(Item=item)
                print(f"  📘 Curso creado: {curso['nombre']} - ID: {curso_id}")

                tenant_curso_id = f"{tenant_id}#{curso_id}"

                for _ in range(3):
                    dias = random.sample(["Lun", "Mar", "Mie", "Jue", "Vie", "Sab"], k=random.randint(1, 3))
                    hora_inicio = f"0{random.randint(7, 9)}:{random.choice(['00', '30'])}"
                    hora_fin = f"{int(hora_inicio[:2]) + 1}:{hora_inicio[3:]}"
                    horario_id = str(uuid.uuid4())

                    horario_item = {
                        "tenant_id": tenant_id,
                        "tenant_id_curso_id": tenant_curso_id,
                        "horario_id": horario_id,
                        "dias": dias,
                        "inicio_hora": hora_inicio,
                        "fin_hora": hora_fin
                    }
                    t_horario.put_item(Item=horario_item)
                    print(f"    🕒 Horario creado: {dias} {hora_inicio}-{hora_fin}")

if __name__ == '__main__':
    crear_instructores_y_poblar()
    print("✅ Poblamiento de DynamoDB completo.")
