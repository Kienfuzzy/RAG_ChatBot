from itertools import product
import mysql.connector
from mysql.connector import Error
import json
from typing import List, Dict, Optional, Any
from app.config import settings


class MySQLService:
    """Service for querying structured product data using MySQL"""
    
    def __init__(self):
        self.connection_config = {
            'host': getattr(settings, 'mysql_host', 'localhost'),
            'port': getattr(settings, 'mysql_port', 3306),
            'database': getattr(settings, 'mysql_database', 'products'),
            'user': getattr(settings, 'mysql_user', 'raguser'),
            'password': getattr(settings, 'mysql_password', 'ragpass123')
        }
        self._initialize_db()
    
    def _get_connection(self):
        """Create and return a database connection"""
        return mysql.connector.connect(**self.connection_config)
    
    def _initialize_db(self):
        """Create products table if it doesn't exist"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    category VARCHAR(100),
                    price DECIMAL(10, 2),
                    brand VARCHAR(100),
                    specs JSON,
                    rating DECIMAL(2, 1),
                    review_count INT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_category (category),
                    INDEX idx_price (price),
                    INDEX idx_rating (rating),
                    INDEX idx_brand (brand)
                )
            """)
            
            conn.commit()
            cursor.close()
            conn.close()
        except Error as e:
            print(f"Error initializing database: {e}")
    
    def query(
        self,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_rating: Optional[float] = None,
        brand: Optional[str] = None,
        spec_search: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Query products with filters
        
        Args:
            category: Filter by product category (e.g., 'headphones', 'laptops')
            min_price: Minimum price
            max_price: Maximum price
            min_rating: Minimum rating (0-5)
            brand: Filter by brand name
            spec_search: Search keyword in specs JSON (e.g., 'usb-c', 'wireless')
            limit: Maximum number of results
        
        Returns:
            List of products matching the criteria
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)
            
            query = "SELECT * FROM products WHERE 1=1"
            params = []
            
            if category:
                query += " AND LOWER(category) = LOWER(%s)"
                params.append(category)

            if min_price is not None:
                query += " AND price >= %s"
                params.append(min_price)
            
            if max_price is not None:
                query += " AND price <= %s"
                params.append(max_price)
            
            if min_rating is not None:
                query += " AND rating >= %s"
                params.append(min_rating)
            
            if brand:
                query += " AND LOWER(brand) = LOWER(%s)"
                params.append(brand)
            
            if spec_search:
                # Handle different spec search patterns
                # 1. Try direct string match (e.g., "wireless", "usb-c")
                # 2. Extract numeric value and search for key-value pattern (e.g., "16gb" -> "ram_gb": 16)
                search_term = spec_search.lower()
                
                # Extract numeric value if present (e.g., "16gb" -> "16")
                import re
                numeric_match = re.search(r'(\d+)', search_term)
                
                if numeric_match:
                    # Get the numeric value
                    numeric_value = numeric_match.group(1)
                    # Try to infer the key (e.g., "16gb" might be ram_gb, "512gb" might be storage_gb)
                    if 'gb' in search_term or 'ram' in search_term or 'memory' in search_term:
                        # Search for ram_gb pattern with numeric value
                        query += " AND (LOWER(specs) LIKE LOWER(%s) OR specs LIKE %s)"
                        params.append(f"%{search_term}%")
                        params.append(f'%"ram_gb": {numeric_value}%')
                    else:
                        # General search with both string and numeric patterns
                        query += " AND (LOWER(specs) LIKE LOWER(%s) OR specs LIKE %s)"
                        params.append(f"%{search_term}%")
                        params.append(f'%: {numeric_value}%')
                else:
                    # No numeric value, just search the term
                    query += " AND LOWER(specs) LIKE LOWER(%s)"
                    params.append(f"%{search_term}%")
            
            query += " ORDER BY rating DESC, review_count DESC LIMIT %s"
            params.append(limit)
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            # Parse JSON specs
            for product in results:
                if product.get('created_at'):
                    product['created_at'] = product['created_at'].isoformat()
                if product.get('specs'):
                    try:
                        product['specs'] = json.loads(product['specs'])
                    except (json.JSONDecodeError, TypeError):
                        pass
                # Convert Decimal to float for JSON serialization
                if product.get('price'):
                    product['price'] = float(product['price'])
                if product.get('rating'):
                    product['rating'] = float(product['rating'])
            
            cursor.close()
            conn.close()
            
            return results
            
        except Error as e:
            print(f"Error querying database: {e}")
            return []
    
    def add_product(
        self,
        name: str,
        category: str,
        price: float,
        brand: str,
        specs: Dict[str, Any],
        rating: float,
        review_count: int
    ) -> Optional[int]:
        """Add a new product to the database"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """
                INSERT INTO products (name, category, price, brand, specs, rating, review_count)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (name, category, price, brand, json.dumps(specs), rating, review_count)
            )
            
            conn.commit()
            product_id = cursor.lastrowid
            
            cursor.close()
            conn.close()
            
            return product_id
            
        except Error as e:
            print(f"Error adding product: {e}")
            return None
    
    def populate_sample_data(self):
        """Populate database with sample products"""
        sample_products = [
            # Headphones
            {
                "name": "Sony WH-1000XM5",
                "category": "headphones",
                "price": 399.99,
                "brand": "Sony",
                "specs": {"anc": True, "battery_hours": 30, "wireless": True, "weight_g": 250},
                "rating": 4.7,
                "review_count": 2847
            },
            {
                "name": "Bose QuietComfort 45",
                "category": "headphones",
                "price": 329.00,
                "brand": "Bose",
                "specs": {"anc": True, "battery_hours": 24, "wireless": True, "weight_g": 240},
                "rating": 4.5,
                "review_count": 1923
            },
            {
                "name": "Apple AirPods Pro",
                "category": "headphones",
                "price": 249.00,
                "brand": "Apple",
                "specs": {"anc": True, "battery_hours": 6, "wireless": True, "weight_g": 56},
                "rating": 4.6,
                "review_count": 5432
            },
            {
                "name": "Anker Soundcore Q30",
                "category": "headphones",
                "price": 79.99,
                "brand": "Anker",
                "specs": {"anc": True, "battery_hours": 40, "wireless": True, "weight_g": 260},
                "rating": 4.4,
                "review_count": 3201
            },
            {
                "name": "JBL Tune 510BT",
                "category": "headphones",
                "price": 49.95,
                "brand": "JBL",
                "specs": {"anc": False, "battery_hours": 40, "wireless": True, "weight_g": 160},
                "rating": 4.3,
                "review_count": 1567
            },
            # Laptops
            {
                "name": "MacBook Pro 14\" M3 Pro",
                "category": "laptops",
                "price": 1999.00,
                "brand": "Apple",
                "specs": {"ram_gb": 18, "storage_gb": 512, "screen_inches": 14, "processor": "M3 Pro"},
                "rating": 4.8,
                "review_count": 892
            },
            {
                "name": "Dell XPS 15",
                "category": "laptops",
                "price": 1599.00,
                "brand": "Dell",
                "specs": {"ram_gb": 16, "storage_gb": 512, "screen_inches": 15.6, "processor": "Intel i7-13700H"},
                "rating": 4.5,
                "review_count": 1234
            },
            {
                "name": "Lenovo ThinkPad X1 Carbon",
                "category": "laptops",
                "price": 1349.00,
                "brand": "Lenovo",
                "specs": {"ram_gb": 16, "storage_gb": 512, "screen_inches": 14, "processor": "Intel i7-1365U"},
                "rating": 4.6,
                "review_count": 876
            },
            {
                "name": "HP Pavilion 15",
                "category": "laptops",
                "price": 649.00,
                "brand": "HP",
                "specs": {"ram_gb": 8, "storage_gb": 256, "screen_inches": 15.6, "processor": "AMD Ryzen 5"},
                "rating": 4.2,
                "review_count": 2103
            },
            # Accessories
            {
                "name": "Anker PowerCore 20000mAh",
                "category": "accessories",
                "price": 59.99,
                "brand": "Anker",
                "specs": {"capacity_mah": 20000, "ports": 2, "fast_charge": True},
                "rating": 4.7,
                "review_count": 4521
            }
        ]
        
        for product in sample_products:
            self.add_product(**product)
