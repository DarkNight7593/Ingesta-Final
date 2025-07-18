import boto3
import json
import hashlib
import uuid
import random
from decimal import Decimal

# Configurar DynamoDB con región explícita
REGION = 'us-east-1'
dynamodb = boto3.resource('dynamodb', region_name=REGION)

# Tablas
t_usuario = dynamodb.Table('dev-t_usuario')
t_curso = dynamodb.Table('dev-t_curso')
t_horario = dynamodb.Table('dev-t_horario')
t_compras = dynamodb.Table('dev-t_compras')

# Cargar cursos desde archivos
with open('cursos_udemy.txt') as f:
    cursos_udemy = json.load(f)
with open('cursos_cursarplus.txt') as f:
    cursos_cursarplus = json.load(f)
with open('cursos_edutec.txt') as f:
    cursos_edutec = json.load(f)

cursos_por_tenant = {
    'udemy': cursos_udemy,
    'cursarplus': cursos_cursarplus
}

tenants = [
    {"tenant_id": "udemy"},
    {"tenant_id": "cursarplus"}
]

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generar_dni(prefijo, nro):
    return f"{prefijo}{nro:04d}"

def generar_horarios():
    dias_posibles = [["Lunes", "Miercoles"], ["Martes", "Jueves"], ["Viernes"], ["Sabado"], ["Lunes", "Viernes"]]
    horas = [("08:00", "09:00"), ("09:00", "10:30"), ("18:00", "19:00"), ("19:00", "20:00"), ("13:00", "15:00")]
    horarios = []
    usados = set()
    while len(horarios) < 3:
        dias = random.choice(dias_posibles)
        inicio, fin = random.choice(horas)
        clave = tuple(dias) + (inicio, fin)
        if clave not in usados:
            usados.add(clave)
            horarios.append({
                "dias": dias,
                "inicio_hora": inicio,
                "fin_hora": fin
            })
    return horarios

def crear_instructores_y_poblar():
    for tenant in tenants:
        tenant_id = tenant["tenant_id"]
        print(f"\n🏢 Procesando tenant: {tenant_id}")

        cursos = cursos_por_tenant[tenant_id]
        random.shuffle(cursos)
        cursor = 0

        # Crear admin
        admin_dni = generar_dni(tenant_id[:3], 9999)
        admin_name = f"Admin ({tenant_id})"
        t_usuario.put_item(Item={
            "tenant_id_rol": f"{tenant_id}#admin",
            "dni": admin_dni,
            "full_name": admin_name,
            "rol": "admin",
            "password": hash_password("12345"),
            "detalles": {
                "telefono": "999999999",
                "descripcion": "admin",
                "correo": f"admin@{tenant_id}.com"
            }
        })
        print(f"✅ Admin creado: {admin_dni} - {admin_name}")

        # Crear alumnos
        alumnos = []
        for i in range(6):
            dni = generar_dni(tenant_id[:3] + 'a', i + 1)
            full_name = f"Alumno {i+1} ({tenant_id})"
            alumno = {
                "dni": dni,
                "full_name": full_name
            }
            alumnos.append(alumno)
            t_usuario.put_item(Item={
                "tenant_id_rol": f"{tenant_id}#alumno",
                "dni": dni,
                "full_name": full_name,
                "rol": "alumno",
                "password": hash_password("12345"),
                "detalles": {
                    "telefono": f"99900000{i+1}",
                    "descripcion": "alumno",
                    "correo": f"{dni}@{tenant_id}.com"
                }
            })
            print(f"✅ Alumno creado: {dni} - {full_name}")

        # Crear instructores y sus cursos
        for i in range(5):
            dni = generar_dni(tenant_id[:3], i + 1)
            full_name = f"Instructor {i+1} ({tenant_id})"
            password = hash_password("12345")
            rol = "instructor"
            tenant_id_rol = f"{tenant_id}#{rol}"

            t_usuario.put_item(Item={
                "tenant_id_rol": tenant_id_rol,
                "dni": dni,
                "full_name": full_name,
                "rol": rol,
                "password": password,
                "detalles": {
                    "telefono": f"98765432{i+1}",
                    "descripcion": "instructor",
                    "correo": f"{dni}@{tenant_id}.com"
                }
            })
            print(f"✅ Instructor creado: {dni} - {full_name}")

            for _ in range(5):
                if cursor >= len(cursos):
                    break
                curso = cursos[cursor]
                cursor += 1
                curso_id = str(uuid.uuid4())
                item = {
                    "tenant_id": tenant_id,
                    "curso_id": curso_id,
                    "nombre": curso["nombre"],
                    "descripcion": curso["descripcion"],
                    "informacion": curso["informacion"],
                    "inicio": curso["inicio"],
                    "fin": curso["fin"],
                    "precio": Decimal(str(curso["precio"])),
                    "instructor_dni": dni,
                    "instructor_nombre": full_name,
                    "tenant_instructor": f"{tenant_id}#{dni}"
                }
                t_curso.put_item(Item=item)
                print(f"  📘 Curso creado: {curso['nombre']} - ID: {curso_id}")

                horarios = generar_horarios()
                for h_index, horario in enumerate(horarios):
                    horario_id = str(uuid.uuid4())
                    t_horario.put_item(Item={
                        "tenant_id": tenant_id,
                        "tenant_id_curso_id": f"{tenant_id}#{curso_id}",
                        "horario_id": horario_id,
                        "dias": horario["dias"],
                        "inicio_hora": horario["inicio_hora"],
                        "fin_hora": horario["fin_hora"]
                    })
                    print(f"    🕒 Horario creado: {horario['dias']} {horario['inicio_hora']}-{horario['fin_hora']}")

                    for alumno in alumnos[h_index*2:h_index*2+2]:
                        estado = random.choice(["reservado", "inscrito"])
                        pk = f"{tenant_id}#{alumno['dni']}#{estado}"
                        t_compras.put_item(Item={
                            "tenant_id_dni_estado": pk,
                            "curso_id": curso_id,
                            "tenant_id_curso_id": f"{tenant_id}#{curso_id}",
                            "alumno_dni": alumno['dni'],
                            "alumno_nombre": alumno['full_name'],
                            "estado": estado,
                            "horario_id": horario_id,
                            "fecha_inicio": curso["inicio"],
                            "fecha_fin": curso["fin"],
                            "precio": Decimal(str(curso["precio"])),
                            "instructor_dni": item["instructor_dni"],
                            "instructor_nombre": item["instructor_nombre"],
                            "curso_nombre": item["nombre"],
                            "dias": horario["dias"],
                            "inicio_hora": horario["inicio_hora"],
                            "fin_hora": horario["fin_hora"]
                        })
                        print(f"      🧾 Compra creada: {alumno['dni']} -> {estado}")

if __name__ == "__main__":
    crear_instructores_y_poblar()
