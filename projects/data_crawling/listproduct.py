# filepath: d:\IoTChallenge2025\listproduct.py
import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin

def crawl_cap_noi_products(url, max_pages=None):
    """
    Crawl product names and URLs from the cap-noi category page
    
    Args:
        url (str): The URL of the cap-noi category page
        max_pages (int, optional): Maximum number of pages to crawl
        
    Returns:
        list: List of dictionaries containing product names and URLs
    """
    base_url = "https://mediamart.vn"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    all_products = []
    current_page = 1
    
    while True:
        # Construct the URL for the current page
        if current_page == 1:
            page_url = url
        else:
            # Assuming pagination format is category-url?page=X
            if '?' in url:
                page_url = f"{url}&page={current_page}"
            else:
                page_url = f"{url}?page={current_page}"
        
        print(f"Crawling page {current_page}: {page_url}")
        
        try:
            response = requests.get(page_url, headers=headers)
            response.raise_for_status()  # Raise an exception for bad responses
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch page {current_page}: {e}")
            break
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all product elements on the page
        product_elements = soup.select('div.col-6.col-md-3.col-lg-3')
        
        if not product_elements:
            print(f"No products found on page {current_page}")
            break
            
        # Extract name and URL from each product element
        for product_element in product_elements:
            product_info = {}
            
            # Find the product link
            product_link = product_element.select_one('a.product-item')
            if product_link:
                # Get the relative URL and convert to absolute URL
                relative_url = product_link.get('href')
                product_info['url'] = urljoin(base_url, relative_url)
            
            # Extract product name
            product_name = product_element.select_one('.product-name')
            if product_name:
                product_info['name'] = product_name.text.strip()
            
            # Only add products that have both name and URL
            if 'name' in product_info and 'url' in product_info:
                all_products.append(product_info)
        
        print(f"Found {len(product_elements)} products on page {current_page}")
                
        # Check if there's a next page
        next_page = soup.select_one('a.page-link[rel="next"]')
        if not next_page:
            print("No more pages")
            break
            
        # Increment page counter
        current_page += 1
        
        # Stop if max_pages is reached
        if max_pages and current_page > max_pages:
            print(f"Reached maximum number of pages ({max_pages})")
            break
    
    return all_products

def save_products_to_json(products, filename):
    """
    Save product information to a JSON file
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=4)
    print(f"Saved {len(products)} products to {filename}")

# if __name__ == "__main__":
#     # Crawl products from the cap-noi category
#     cap_noi_url = "https://mediamart.vn/cap-noi"
#     products = crawl_cap_noi_products(cap_noi_url)
    
#     # Save the results to a JSON file
#     if products:
#         save_products_to_json(products, "cap_noi_products.json")
        
#     # Print the first few products as a sample
#     print("\nSample of extracted products:")
#     for i, product in enumerate(products[:5]):
#         print(f"{i+1}. {product['name']} - {product['url']}")
    
#     print(f"\nTotal number of products extracted: {len(products)}")
