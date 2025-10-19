import pandas as pd
import os
from typing import List, Dict, Optional
from app.config import get_settings

settings = get_settings()

class CSVKnowledgeBase:
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.df = None
        if os.path.exists(csv_path):
            self.load_csv()
    
    def load_csv(self):
        """Load CSV into memory"""
        try:
            self.df = pd.read_csv(self.csv_path)
            
            # Convert all columns to string to avoid .str accessor errors
            for col in self.df.columns:
                self.df[col] = self.df[col].astype(str)
            
            return True
        except Exception as e:
            print(f"Error loading CSV: {e}")
            return False
    
    def search_products(self, query: str) -> List[Dict]:
        """Search products based on query - now searches in more fields"""
        if self.df is None or self.df.empty:
            return []
        
        try:
            query_lower = query.lower()
            results = []
            
            # Search in name, brand, description, and reviews (new!)
            mask = (
                self.df['name'].str.lower().str.contains(query_lower, na=False, regex=False) |
                self.df['brand'].str.lower().str.contains(query_lower, na=False, regex=False) |
                self.df['description'].str.lower().str.contains(query_lower, na=False, regex=False) |
                self.df.get('breadcrumbs', pd.Series(dtype=str)).str.lower().str.contains(query_lower, na=False, regex=False)
            )
            
            filtered_df = self.df[mask]
            
            for _, row in filtered_df.iterrows():
                results.append(row.to_dict())
            
            return results
            
        except Exception as e:
            print(f"Error searching products: {e}")
            # If search fails, return all products as fallback
            return self.get_all_products()
    
    def get_all_products(self) -> List[Dict]:
        """Get all products"""
        if self.df is None or self.df.empty:
            return []
        return self.df.to_dict('records')
    
    def get_product_count(self) -> int:
        """Get total product count"""
        return len(self.df) if self.df is not None else 0
    
    def get_product_summary(self) -> str:
        """Get a summary of available products"""
        if self.df is None or self.df.empty:
            return "No products available."
        
        count = len(self.df)
        
        # Get unique brands (filter out 'nan' strings)
        brands = self.df['brand'].unique()
        brands = [b for b in brands if b != 'nan' and b != 'None' and str(b).strip()]
        
        # Check if we have ratings
        has_ratings = 'rating' in self.df.columns and self.df['rating'].notna().any()
        has_reviews = 'reviews' in self.df.columns and self.df['reviews'].notna().any()
        
        summary = f"We have {count} products available"
        if len(brands) > 0:
            summary += f" from brands including: {', '.join(brands[:5])}"
            if len(brands) > 5:
                summary += f" and {len(brands) - 5} more"
        
        if has_ratings:
            summary += ". Products include ratings and reviews."
        
        return summary
    
    def get_products_by_price_range(self, min_price: float = 0, max_price: float = float('inf')) -> List[Dict]:
        """Get products within a price range"""
        if self.df is None or self.df.empty:
            return []
        
        try:
            # Extract numeric price from price column
            self.df['price_numeric'] = self.df['price'].str.extract(r'(\d+)').astype(float)
            
            mask = (self.df['price_numeric'] >= min_price) & (self.df['price_numeric'] <= max_price)
            filtered_df = self.df[mask].sort_values('price_numeric')
            
            return filtered_df.to_dict('records')
        except Exception as e:
            print(f"Error filtering by price: {e}")
            return []
    
    def get_best_value_products(self, top_n: int = 10) -> List[Dict]:
        """Get products sorted by price (ascending) - best value"""
        if self.df is None or self.df.empty:
            return []
        
        try:
            # Extract numeric price
            self.df['price_numeric'] = self.df['price'].str.extract(r'(\d+)').astype(float)
            
            # Sort by price and get top N cheapest
            sorted_df = self.df.dropna(subset=['price_numeric']).sort_values('price_numeric').head(top_n)
            
            return sorted_df.to_dict('records')
        except Exception as e:
            print(f"Error getting best value products: {e}")
            return []
    
    def get_top_rated_products(self, top_n: int = 10) -> List[Dict]:
        """Get products sorted by rating (descending) - NEW"""
        if self.df is None or self.df.empty:
            return []
        
        if 'rating' not in self.df.columns:
            return []
        
        try:
            # Extract numeric rating (format: "4.5/5")
            self.df['rating_numeric'] = self.df['rating'].str.extract(r'(\d+(?:\.\d+)?)').astype(float)
            
            # Sort by rating and get top N
            sorted_df = self.df.dropna(subset=['rating_numeric']).sort_values('rating_numeric', ascending=False).head(top_n)
            
            return sorted_df.to_dict('records')
        except Exception as e:
            print(f"Error getting top rated products: {e}")
            return []
    
    def get_products_with_reviews(self, min_reviews: int = 1) -> List[Dict]:
        """Get products that have reviews - NEW"""
        if self.df is None or self.df.empty:
            return []
        
        if 'reviews' not in self.df.columns:
            return []
        
        try:
            # Filter products that have non-empty reviews
            mask = (self.df['reviews'] != 'nan') & (self.df['reviews'] != '') & self.df['reviews'].notna()
            filtered_df = self.df[mask]
            
            return filtered_df.to_dict('records')
        except Exception as e:
            print(f"Error getting products with reviews: {e}")
            return []
