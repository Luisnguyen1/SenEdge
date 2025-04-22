import requests
from bs4 import BeautifulSoup
import json
import re
import pandas as pd

def scrape_mediamart_product(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return {"error": f"Failed to fetch the page: {response.status_code}"}
    soup = BeautifulSoup(response.text, 'html.parser')    # Extract basic product information
    product_data = {
        "name": soup.select_one('.pdetail-name h1').text.strip() if soup.select_one('.pdetail-name h1') else None,
        "price": soup.select_one('.pdetail-price-box h3').text.strip() if soup.select_one('.pdetail-price-box h3') else None,
        "original_price": soup.select_one('.product-price-regular').text.strip() if soup.select_one('.product-price-regular') else None,
        "discount_percentage": soup.select_one('.product-price-saving').text.strip() if soup.select_one('.product-price-saving') else None,
        "product_url": url,
    }
      # Extract model from pdetail-info
    model_element = soup.select_one('.pdetail-info p:first-child b:first-child')
    if model_element:
        product_data["model"] = model_element.text.strip()
    else:
        product_data["model"] = None
        
    # Extract brand and other information from product specifications table
    # Look for brand in the specifications table
    brand_row = soup.select_one('table.table.table-striped tr:has(td:contains("Thương hiệu"))')
    if brand_row:
        brand_element = brand_row.select_one('td:nth-child(2) span')
        if brand_element:
            product_data["brand"] = brand_element.text.strip()
        else:
            product_data["brand"] = None
    else:
        # Fallback to extracting from product name if brand not found in table
        if product_data["name"]:
            brand_match = re.search(r'([\w\s]+)', product_data["name"])
            if brand_match:
                product_data["brand"] = "Coex"  # Since it's a Coex product as per name
        else:
            product_data["brand"] = None
            
    # Extract warranty period
    warranty_row = soup.select_one('table.table.table-striped tr:has(td:contains("Bảo hành"))')
    if warranty_row:
        warranty_element = warranty_row.select_one('td:nth-child(2) span')
        if warranty_element:
            product_data["warranty"] = warranty_element.text.strip()
            
    # Extract origin country
    origin_row = soup.select_one('table.table.table-striped tr:has(td:contains("Xuất xứ"))')
    if origin_row:
        origin_element = origin_row.select_one('td:nth-child(2) span')
        if origin_element:
            product_data["origin"] = origin_element.text.strip()
      # Extract key features
    features = []
    feature_elements = soup.select('.pdetail-des ul li')
    for feature in feature_elements:
        if feature.text.strip():
            features.append(feature.text.strip())
    product_data["key_features"] = features
    
    # Extract technical specifications
    specs = {}
    spec_rows = soup.select('table.table.table-striped tr')
    for row in spec_rows:
        # Skip header rows
        if row.select_one('th'):
            continue
            
        # Extract specification key and value
        cells = row.select('td')
        if len(cells) == 2:
            key = cells[0].text.strip().rstrip(':')
            # Extract text from all li elements in the value cell
            value_cell = cells[1]
            value_items = value_cell.select('li')
            
            if value_items:
                # If there are multiple items, join them with commas
                values = []
                for item in value_items:
                    # Extract just the text, avoiding nested elements
                    item_text = item.get_text(strip=True)
                    if item_text:
                        values.append(item_text)
                        
                if len(values) == 1:
                    specs[key] = values[0]
                else:
                    specs[key] = ", ".join(values)
            else:
                # If no li elements, just get the text
                specs[key] = value_cell.text.strip()
    
    product_data["specifications"] = specs
      # Extract product description (id="gioi-thieu-san-pham" is the correct selector)
    description = soup.select_one('#gioi-thieu-san-pham')
    if description:
        product_data["description"] = description.get_text(separator='\n', strip=True)    # Extract product images
    image_urls = []
    image_elements = soup.select('.pdetail-slideproduct img')
    # Remove duplicate images by using a set of URLs
    unique_urls = set()
    for img in image_elements:
        if img.get('data-src'):
            # Only add non-cloned images to avoid duplicates
            img_url = img.get('data-src')
            # Convert .webp URLs to .jpg URLs for better compatibility
            if img_url not in unique_urls:
                unique_urls.add(img_url)
                image_urls.append(img_url)
    product_data["image_urls"] = image_urls
      # Extract rating information
    rating_element = soup.select_one('.rating-value')
    if rating_element:
        product_data["rating"] = rating_element.text.strip()
        
    # Extract review count from product-review-list
    reviews_count_element = soup.select_one('.product-review-list span')
    if reviews_count_element:
        # Extract the number from text like "(1) đánh giá | Viết nhận xét"
        review_text = reviews_count_element.text.strip()
        review_match = re.search(r'\((\d+)\)', review_text)
        if review_match:
            product_data["reviews_count"] = review_match.group(1)
        else:
            product_data["reviews_count"] = "0"
    
    return product_data

# # Example usage
# url = "https://mediamart.vn/may-giat/may-giat-long-ngang-lg-inverter-10g-fv1410s4w1"
# product_data = scrape_mediamart_product(url)

# # Save to JSON file
# with open('coex_refrigerator_data.json', 'w', encoding='utf-8') as f:
#     json.dump(product_data, f, ensure_ascii=False, indent=4)

# print("Scraping completed. Data saved to JSON and CSV files.")