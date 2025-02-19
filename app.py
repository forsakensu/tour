from os import getenv

from flask import Flask, jsonify, request, render_template
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from sqlalchemy import create_engine, Column, Integer, String, TIMESTAMP, func
from sqlalchemy.orm import DeclarativeBase, Session
from sqlalchemy.ext.declarative import declarative_base

app = Flask(__name__)
bcrypt = Bcrypt(app)
jwt_manager = JWTManager(app)

app.config["JWT_SECRET_KEY"] = getenv("JWT_SECRET_KEY")


class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    password_hash = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    created_at = Column(TIMESTAMP, default=func.now())

# Пример данных
tours = [
    {"id": 1, "title": "Малайзия", "description": "Описание тура1", "price": 100000},
    {"id": 2, "title": "Египет", "description": "Описание тура2", "price": 120000},
    {"id": 3, "title": "Таиланд", "description": "Описание тура3", "price": 220000},
    {"id": 4, "title": "Шри-Ланка", "description": "Описание тура4", "price": 150000},
]

users = {"frodo": "asd", "sam": "dsa"}


@app.get("/")
def index():
    return render_template("index.j2", tours=tours)


@app.get("/admin")
def admin():
    return render_template("index.j2", tours=tours, admin=True)


@app.post("/login")
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if username in users and users[username] == password:
        roles = ["admin", "user"] if username == "frodo" else ["user"]
        # token = create_access_token(identity={"username": username, "roles": roles})
        token = create_access_token(identity=str(username), additional_claims={"roles": roles})  
        return make_response("success", "Токен создан", {"access_token": token})
    
    return make_response("error", "Неверный логин или пароль", status_code=401)


@app.get("/profile")
@jwt_required()
def profile():
    current_user = get_jwt_identity()
    return make_response("success", current_user)


@app.route("/admin-check", methods=["GET"])
@jwt_required()
def admin_check():
    current_user = get_jwt_identity()
    current_user_details = get_jwt()
    if "admin" not in current_user_details.get("roles"):
        return make_response("error", f"Вы не админ, {current_user}", status_code=403)
    return make_response("success", "Вы успешно вошли, админ!", {"current_user": current_user, "current_user_details": current_user_details})


# Структура унифицированного ответа
def make_response(status, message, data=None, status_code=200):
    response = jsonify({
        "status": status,
        "message": message,
        "data": data
    })
    response.status_code = status_code
    return response


@app.get("/api/tours/<int:tour_id>")
def get_tour(tour_id=None):
    """Маршрут для получения тура по ID."""

    if tour_id is None:
        return make_response("error", "Не передан ID тура", status_code=400)

    # Найти тур в списке, где id совпадает с переданным tour_id
    for tour in tours:
        # TODO: переписать на next()
        if tour["id"] == tour_id:  # Если id совпадает
            return make_response("success", "Тур найден", data=tour)  # Возвращаем найденный тур в формате JSON

    # Если тур не найден
    return make_response("error", "Тур не найден", status_code=404)


@app.get("/api/tours")
def get_tours():
    """Получить все туры."""
    # TODO: почистить поля тура
    return make_response("success", "Показаны все направления", tours)


# Редактирование тура
@app.route("/api/tours/<int:tour_id>", methods=["PUT"])
def update_tour(tour_id):
    if request.content_type != "application/json":
        return make_response("error", "Неверный тип контента. Ожидается application/json", status_code=400)

    data = request.get_json()

    for tour in tours:
        if tour["id"] == tour_id:  # Если id совпадает
            tour["name"] = data.get("name", tour["name"])  # Обновляем название
            tour["price"] = data.get("price", tour["price"])  # Обновляем цену
            return make_response("success", "Тур отредактирован", tour)  # Возвращаем обновленный тур

    # Если тур не найден
    return make_response("error", "Тур не найден", status_code=404)


# Создание нового тура
@app.route("/api/tours", methods=["POST"])
def create_tour():
    if request.content_type != "application/json":
        return make_response("error", "Неверный тип контента. Ожидается application/json", status_code=400)

    data = request.get_json()

    # Проверка входных данных
    if not data or not data.get("name") or not data.get("price"):
        return make_response("error", "Название и цена обязательны", status_code=404)

    # Создание нового тура
    new_tour = {
        "id": len(tours) + 1,  # Генерация нового ID
        "name": data["name"],
        "price": data["price"],
    }
    tours.append(new_tour)  # Добавление в список туров
    return make_response("success", "Тур создан", new_tour)


# Удаление тура
@app.route("/api/tours/<int:tour_id>", methods=["DELETE"])
def delete_tour(tour_id):
    global tours
    tour_to_delete = next((tour for tour in tours if tour["id"] == tour_id), None)

    tour_name = tour_to_delete["name"]
    tours = [tour for tour in tours if tour["id"] != tour_id] # Удаляем тур с переданным id
    return make_response("success", f"Тур '{tour_name}' удалён"), 202 # Возвращаем подтверждение с кодом 202


# Обработка ошибок
@app.errorhandler(500)
def handle_500_error(e):
    return make_response("error", "Что-то пошло не так на сервере", status_code=500)


@app.errorhandler(404)
def handle_404_error(e):
    return make_response("error", "Ресурс не найден", status_code=404)


if __name__ == "__main__":
    app.run(debug=True)
