"""Region data generator."""

import pandas as pd


def generate_regions() -> pd.DataFrame:
    """Generate geographic regions."""
    regions = [
        {"region_id": 1, "region_name": "North America", "country": "United States", "continent": "North America"},
        {"region_id": 2, "region_name": "Western Europe", "country": "United Kingdom", "continent": "Europe"},
        {"region_id": 3, "region_name": "Central Europe", "country": "Germany", "continent": "Europe"},
        {"region_id": 4, "region_name": "East Asia", "country": "Japan", "continent": "Asia"},
        {"region_id": 5, "region_name": "South Asia", "country": "India", "continent": "Asia"},
        {"region_id": 6, "region_name": "South America", "country": "Brazil", "continent": "South America"},
        {"region_id": 7, "region_name": "Southeast Asia", "country": "Singapore", "continent": "Asia"},
        {"region_id": 8, "region_name": "Oceania", "country": "Australia", "continent": "Oceania"},
        {"region_id": 9, "region_name": "Northern Europe", "country": "Sweden", "continent": "Europe"},
        {"region_id": 10, "region_name": "Middle East", "country": "UAE", "continent": "Asia"},
    ]
    return pd.DataFrame(regions)


def generate_categories() -> pd.DataFrame:
    """Generate product categories with a hierarchy."""
    categories = [
        {"category_id": 1, "category_name": "Electronics", "description": "Electronic devices and accessories", "parent_category_id": None},
        {"category_id": 2, "category_name": "Computers", "description": "Laptops, desktops, and peripherals", "parent_category_id": 1},
        {"category_id": 3, "category_name": "Phones & Tablets", "description": "Smartphones and tablets", "parent_category_id": 1},
        {"category_id": 4, "category_name": "Audio", "description": "Headphones, speakers, and audio equipment", "parent_category_id": 1},
        {"category_id": 5, "category_name": "Wearables", "description": "Smart watches and fitness trackers", "parent_category_id": 1},
        {"category_id": 6, "category_name": "Home & Garden", "description": "Home improvement and garden supplies", "parent_category_id": None},
        {"category_id": 7, "category_name": "Furniture", "description": "Indoor and outdoor furniture", "parent_category_id": 6},
        {"category_id": 8, "category_name": "Kitchen", "description": "Kitchen appliances and tools", "parent_category_id": 6},
        {"category_id": 9, "category_name": "Lighting", "description": "Lamps and lighting fixtures", "parent_category_id": 6},
        {"category_id": 10, "category_name": "Clothing", "description": "Apparel and fashion", "parent_category_id": None},
        {"category_id": 11, "category_name": "Men's Clothing", "description": "Men's apparel", "parent_category_id": 10},
        {"category_id": 12, "category_name": "Women's Clothing", "description": "Women's apparel", "parent_category_id": 10},
        {"category_id": 13, "category_name": "Sports & Outdoors", "description": "Sports equipment and outdoor gear", "parent_category_id": None},
        {"category_id": 14, "category_name": "Fitness", "description": "Gym and fitness equipment", "parent_category_id": 13},
        {"category_id": 15, "category_name": "Camping", "description": "Camping and hiking gear", "parent_category_id": 13},
        {"category_id": 16, "category_name": "Books & Media", "description": "Books, music, and digital media", "parent_category_id": None},
        {"category_id": 17, "category_name": "Office Supplies", "description": "Office and school supplies", "parent_category_id": None},
        {"category_id": 18, "category_name": "Health & Beauty", "description": "Personal care and wellness", "parent_category_id": None},
        {"category_id": 19, "category_name": "Toys & Games", "description": "Toys, games, and puzzles", "parent_category_id": None},
        {"category_id": 20, "category_name": "Automotive", "description": "Car accessories and parts", "parent_category_id": None},
    ]
    return pd.DataFrame(categories)
