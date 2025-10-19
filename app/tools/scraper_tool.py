import os
from langchain.tools import tool
from app.utils.csv_handler import CSVKnowledgeBase
from app.config import get_settings

settings = get_settings()

# Import your scraper
import sys
sys.path.append(os.path.dirname(__file__))
from scrape_general import scrape

@tool
def scrape_website_tool(url: str, output_filename: str) -> str:
    """
    Scrapes product data from an e-commerce website and saves to CSV.
    Enhanced version with reviews, ratings, and better extraction.
    
    Args:
        url: The URL of the website to scrape (listing page or single product)
        output_filename: The output CSV filename (just filename, not full path)
    
    Returns:
        A message indicating success or failure
    """
    try:
        # Ensure data directory exists
        os.makedirs(settings.data_dir, exist_ok=True)
        
        # Full path for CSV
        csv_path = os.path.join(settings.data_dir, output_filename)
        
        # Ensure output directory exists in the CSV path
        output_dir = os.path.dirname(csv_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        print(f"\n{'='*70}")
        print(f"🔍 SCRAPING STARTED")
        print(f"{'='*70}")
        print(f"📍 URL: {url}")
        print(f"💾 Output: {output_filename}")
        print(f"📂 Directory: {os.path.abspath(settings.data_dir)}")
        print(f"📄 Full path: {os.path.abspath(csv_path)}")
        print(f"{'='*70}\n")
        
        # Run the scraper with full path
        scrape(url, csv_path)
        
        # Verify CSV was created
        if os.path.exists(csv_path):
            kb = CSVKnowledgeBase(csv_path)
            product_count = kb.get_product_count()
            file_size = os.path.getsize(csv_path) / 1024  # KB
            
            success_msg = (
                f"\n{'='*70}\n"
                f"✅ SCRAPING COMPLETED SUCCESSFULLY\n"
                f"{'='*70}\n"
                f"📊 Products scraped: {product_count}\n"
                f"📁 File location: {os.path.abspath(csv_path)}\n"
                f"💾 File size: {file_size:.2f} KB\n"
                f"ℹ️  Data includes: name, brand, price, reviews, ratings, descriptions\n"
                f"{'='*70}\n"
            )
            print(success_msg)
            return success_msg
        else:
            error_msg = f"❌ ERROR: CSV file was not created at {csv_path}"
            print(error_msg)
            return error_msg
    
    except Exception as e:
        import traceback
        error_msg = (
            f"\n{'='*70}\n"
            f"❌ SCRAPING FAILED\n"
            f"{'='*70}\n"
            f"Error: {str(e)}\n\n"
            f"Traceback:\n{traceback.format_exc()}\n"
            f"{'='*70}\n"
        )
        print(error_msg)
        return error_msg
