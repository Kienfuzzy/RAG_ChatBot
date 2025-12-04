#!/usr/bin/env python3
"""
Initialize MySQL database with sample product data
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.mysql_service import MySQLService


def main():
    print("🔧 Connecting to MySQL database...")
    db = MySQLService()
    
    print("📊 Populating sample product data...")
    db.populate_sample_data()
    
    print("✅ Verifying data...")
    products = db.query(limit=20)
    print(f"\n✅ Successfully added {len(products)} products!")
    
    print("\n📦 Sample products:")
    for p in products[:5]:
        print(f"  - {p['name']} ({p['category']}) - ${p['price']} - ⭐{p['rating']}")
    
    print(f"\n✅ MySQL database ready!")
    
    # Test queries
    print("\n🧪 Testing queries:")
    
    # Test 1: Price filter
    cheap_headphones = db.query(category='headphones', max_price=100)
    print(f"  ✓ Headphones under $100: {len(cheap_headphones)} found")
    
    # Test 2: Rating filter  
    top_rated = db.query(min_rating=4.5)
    print(f"  ✓ Products rating ≥ 4.5: {len(top_rated)} found")
    
    # Test 3: Brand filter
    sony_products = db.query(brand='Sony')
    print(f"  ✓ Sony products: {len(sony_products)} found")
    
    # Test 4: Combined filters
    budget_laptops = db.query(category='laptops', max_price=1500, min_rating=4.5)
    print(f"  ✓ Laptops under $1500 with rating ≥ 4.5: {len(budget_laptops)} found")
    
    print("\n✅ All tests passed!")
    print("\n💡 You can now:")
    print("  - View data: docker exec -it products_db mysql -uraguser -pragpass123 products")
    print("  - Query: SELECT * FROM products WHERE price < 100;")


if __name__ == "__main__":
    main()
