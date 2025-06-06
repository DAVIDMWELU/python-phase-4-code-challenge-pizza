#!/usr/bin/env python3
import os
from flask import Flask, jsonify, request, abort
from flask_migrate import Migrate
from flask_restful import Api
from models import db, Restaurant, RestaurantPizza, Pizza

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)    
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

db.init_app(app)        
migrate = Migrate(app, db)
api = Api(app)

@app.route("/")
def index():
    return "<h1>Code challenge</h1>"

@app.route("/restaurants", methods=["GET"])
def get_restaurants():
    restaurants = Restaurant.query.all()
    result = [
        {
            "id": r.id,
            "name": r.name,
            "address": r.address,
            # Exclude restaurant_pizzas as test expects
        }
        for r in restaurants
    ]
    return jsonify(result), 200

@app.route("/restaurants/<int:id>", methods=["GET"])
def get_restaurant(id):
    restaurant = Restaurant.query.get(id)
    if not restaurant:
        return jsonify({"error": "Restaurant not found"}), 404
    return jsonify({
        "id": restaurant.id,
        "name": restaurant.name,
        "address": restaurant.address,
        "restaurant_pizzas": [
            {
                "id": rp.id,
                "price": rp.price,
                "pizza": {
                    "id": rp.pizza.id,
                    "name": rp.pizza.name,
                    "ingredients": rp.pizza.ingredients,
                }
            }
            for rp in restaurant.restaurant_pizzas
        ]
    }), 200

@app.route("/restaurants/<int:id>", methods=["DELETE"])
def delete_restaurant(id):
    restaurant = Restaurant.query.get(id)
    if not restaurant:
        return jsonify({"error": "Restaurant not found"}), 404
    db.session.delete(restaurant)
    db.session.commit()
    return "", 204

@app.route("/pizzas", methods=["GET"])
def get_pizzas():
    pizzas = Pizza.query.all()
    result = [
        {
            "id": p.id,
            "name": p.name,
            "ingredients": p.ingredients,
            # Exclude restaurant_pizzas as test expects
        }
        for p in pizzas
    ]
    return jsonify(result), 200

@app.route("/restaurant_pizzas", methods=["POST"])
def create_restaurant_pizza():
    data = request.get_json()

    price = data.get("price")
    pizza_id = data.get("pizza_id")
    restaurant_id = data.get("restaurant_id")

    # Validate required fields
    if price is None or pizza_id is None or restaurant_id is None:
        return jsonify({"errors": ["validation errors"]}), 400

    # Validate price range
    if not (1 <= price <= 30):
        return jsonify({"errors": ["validation errors"]}), 400

    # Check if pizza and restaurant exist
    pizza = Pizza.query.get(pizza_id)
    restaurant = Restaurant.query.get(restaurant_id)
    if not pizza or not restaurant:
        return jsonify({"errors": ["validation errors"]}), 400

    # Check if restaurant_pizza exists already
    existing = RestaurantPizza.query.filter_by(
        pizza_id=pizza_id, restaurant_id=restaurant_id).first()
    if existing:
        # For simplicity, update price
        existing.price = price
        rp = existing
    else:
        rp = RestaurantPizza(price=price, pizza_id=pizza_id, restaurant_id=restaurant_id)
        db.session.add(rp)

    db.session.commit()

    return jsonify({
        "id": rp.id,
        "price": rp.price,
        "pizza_id": rp.pizza_id,
        "restaurant_id": rp.restaurant_id,
        "pizza": {
            "id": pizza.id,
            "name": pizza.name,
            "ingredients": pizza.ingredients,
        },
        "restaurant": {
            "id": restaurant.id,
            "name": restaurant.name,
            "address": restaurant.address,
        }
    }), 201

if __name__ == "__main__":
    app.run(port=5555, debug=True)
