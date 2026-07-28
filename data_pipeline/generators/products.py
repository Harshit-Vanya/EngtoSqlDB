"""Product data generator — realistic product catalog."""

import random

import pandas as pd
from faker import Faker

from data_pipeline.generators.base import GenerationConfig


# Realistic product name components per category
PRODUCT_TEMPLATES = {
    1: ["Wireless Charger", "USB-C Hub", "Power Bank", "HDMI Cable", "Screen Protector"],
    2: ["Laptop Stand", "Mechanical Keyboard", "Gaming Mouse", "Monitor Arm", "Webcam"],
    3: ["Phone Case", "Tablet Stand", "Stylus Pen", "Car Mount", "Fast Charger"],
    4: ["Wireless Headphones", "Bluetooth Speaker", "Earbuds Pro", "Soundbar", "Microphone"],
    5: ["Smart Watch Pro", "Fitness Band", "Sleep Tracker", "Heart Monitor", "GPS Watch"],
    6: ["LED Strip Lights", "Smart Plug", "Air Purifier", "Humidifier", "Thermostat"],
    7: ["Standing Desk", "Office Chair", "Bookshelf", "Coffee Table", "Shoe Rack"],
    8: ["Blender Pro", "Coffee Maker", "Air Fryer", "Instant Pot", "Kitchen Scale"],
    9: ["Desk Lamp", "Floor Lamp", "String Lights", "Night Light", "Smart Bulb"],
    10: ["Basic Tee", "Polo Shirt", "Hoodie", "Jacket", "Scarf"],
    11: ["Dress Shirt", "Chinos", "Blazer", "Denim Jeans", "Sneakers"],
    12: ["Summer Dress", "Yoga Pants", "Cardigan", "Ankle Boots", "Handbag"],
    13: ["Yoga Mat", "Resistance Bands", "Jump Rope", "Foam Roller", "Water Bottle"],
    14: ["Dumbbell Set", "Kettlebell", "Pull-Up Bar", "Exercise Bike", "Treadmill"],
    15: ["Camping Tent", "Sleeping Bag", "Hiking Backpack", "Camping Stove", "Headlamp"],
    16: ["Bestseller Novel", "Tech Handbook", "Cookbook", "Travel Guide", "Planner"],
    17: ["Whiteboard", "Notebook Set", "Pen Collection", "Desk Organizer", "Label Maker"],
    18: ["Face Cream", "Shampoo", "Sunscreen", "Vitamin Pack", "Essential Oil"],
    19: ["Board Game", "Puzzle 1000pc", "Building Blocks", "Card Game", "RC Car"],
    20: ["Phone Mount", "Seat Cushion", "Car Vacuum", "Dash Cam", "Tire Inflator"],
}

BRANDS = [
    "TechPro", "NovaBrand", "EcoSmart", "PrimeChoice", "UrbanEdge",
    "Summit", "Zenith", "CoreFit", "NatureLux", "DigitalWave",
]

SUPPLIERS = [
    "GlobalTech Inc", "Pacific Supply Co", "Atlantic Distributors",
    "MegaSource Ltd", "Premier Imports", "SwiftLogistics",
    "DirectSource", "ValueChain Corp", "QualityFirst Supply",
    "TrustTrade Partners",
]


def generate_products(config: GenerationConfig | None = None) -> pd.DataFrame:
    """Generate product catalog with realistic pricing and categories.

    Products have:
    - Weighted category distribution (electronics has more products)
    - Price ranges that make sense per category
    - Stock quantities with some out-of-stock items
    - Intentional NULLs in supplier field (~2%)
    """
    if config is None:
        from data_pipeline.generators.base import DEFAULT_CONFIG
        config = DEFAULT_CONFIG

    fake = Faker()
    Faker.seed(config.random_seed)
    random.seed(config.random_seed)

    # Price ranges per category (min, max)
    price_ranges = {
        1: (10, 150), 2: (30, 800), 3: (15, 200), 4: (25, 500), 5: (50, 600),
        6: (20, 300), 7: (50, 1500), 8: (25, 400), 9: (15, 200), 10: (15, 120),
        11: (20, 300), 12: (20, 350), 13: (10, 100), 14: (20, 2000), 15: (30, 500),
        16: (8, 50), 17: (5, 80), 18: (10, 100), 19: (10, 150), 20: (15, 200),
    }

    # Category weights (electronics and home are larger)
    category_weights = [
        0.12, 0.10, 0.08, 0.07, 0.06,  # Electronics subcategories
        0.05, 0.06, 0.05, 0.04, 0.04,  # Home, Clothing
        0.04, 0.04, 0.04, 0.03, 0.03,  # Sports
        0.04, 0.04, 0.03, 0.03, 0.03,  # Books, Office, Health, Toys, Auto
    ]

    products = []
    for i in range(1, config.num_products + 1):
        category_id = random.choices(range(1, 21), weights=category_weights, k=1)[0]

        # Pick a product name template and add variation
        templates = PRODUCT_TEMPLATES.get(category_id, ["Product"])
        base_name = random.choice(templates)
        variant = random.choice(["", " V2", " Plus", " Lite", " Max", " Pro", " Mini"])
        product_name = f"{random.choice(BRANDS)} {base_name}{variant}"

        # Realistic pricing
        min_price, max_price = price_ranges[category_id]
        price = round(random.uniform(min_price, max_price), 2)

        # Stock — some items out of stock
        stock = random.choices(
            [0, random.randint(1, 20), random.randint(20, 200), random.randint(200, 1000)],
            weights=[0.05, 0.20, 0.50, 0.25],
            k=1,
        )[0]

        # Supplier — with intentional NULLs
        supplier = random.choice(SUPPLIERS) if random.random() > config.null_rate else None

        # Created date
        created_date = fake.date_between(start_date="-2y", end_date="-30d")

        product = {
            "product_id": i,
            "product_name": product_name,
            "category_id": category_id,
            "price": price,
            "stock_quantity": stock,
            "supplier": supplier,
            "created_date": created_date,
            "is_active": random.random() > 0.05,  # 5% inactive
        }
        products.append(product)

    return pd.DataFrame(products)
