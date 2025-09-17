import json
import os
import time
from collections import defaultdict

def clean_data(input_files, output_file):
    """
    Clean data by removing duplicate products from multiple JSON files
    
    Args:
        input_files (list): List of input JSON file paths
        output_file (str): Output JSON file path
    """
    print(f"Cleaning data from {len(input_files)} files...")
    
    # Dictionary to store unique products with URL as key
    unique_products = {}
    # Track duplicate count
    duplicate_count = 0
    total_count = 0
    
    # Process each input file
    for file_path in input_files:
        print(f"Processing file: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                products = json.load(f)
            
            print(f"  - Found {len(products)} products in this file")
            total_count += len(products)
            
            # Process each product
            for product in products:
                # Use URL as unique identifier
                if 'url' in product:
                    product_url = product['url']
                    
                    # If product with this URL hasn't been seen before, add it
                    if product_url not in unique_products:
                        unique_products[product_url] = product
                    else:
                        duplicate_count += 1
                        
                        # If the existing product has less information than the current one,
                        # replace it with the more complete version
                        existing_keys = set(unique_products[product_url].keys())
                        current_keys = set(product.keys())
                        
                        if len(current_keys) > len(existing_keys):
                            unique_products[product_url] = product
        
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
    
    # Convert dictionary values to list for saving
    unique_product_list = list(unique_products.values())
    
    # Save cleaned data
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(unique_product_list, f, ensure_ascii=False, indent=4)
        
        print(f"\nClean data summary:")
        print(f"  - Total products processed: {total_count}")
        print(f"  - Duplicate products removed: {duplicate_count}")
        print(f"  - Unique products saved: {len(unique_product_list)}")
        print(f"  - Cleaned data saved to: {output_file}")
        return True
    
    except Exception as e:
        print(f"Error saving cleaned data to {output_file}: {e}")
        return False

def analyze_cleaned_data(cleaned_file):
    """
    Analyze the cleaned data to show statistics
    
    Args:
        cleaned_file (str): Path to the cleaned JSON file
    """
    try:
        with open(cleaned_file, 'r', encoding='utf-8') as f:
            products = json.load(f)
        
        print("\nData Analysis:")
        print(f"  - Total unique products: {len(products)}")
        
        # Count products by brand
        brands = defaultdict(int)
        for product in products:
            if 'brand' in product and product['brand']:
                brands[product['brand']] += 1
        
        print("\nProducts by brand:")
        for brand, count in sorted(brands.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {brand}: {count}")
            
        # Check for any possible remaining duplicates based on name
        name_count = defaultdict(int)
        for product in products:
            if 'name' in product and product['name']:
                name_count[product['name']] += 1
        
        duplicate_names = {name: count for name, count in name_count.items() if count > 1}
        if duplicate_names:
            print("\nPossible remaining duplicates (same name but different URLs):")
            for name, count in sorted(duplicate_names.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  - {name}: {count} products")
    
    except Exception as e:
        print(f"Error analyzing cleaned data: {e}")

if __name__ == "__main__":
    # Create data directory if it doesn't exist
    data_dir = 'data'
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    # List all JSON files in the data directory
    json_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) 
                 if f.endswith('.json') and os.path.isfile(os.path.join(data_dir, f))]
    
    if not json_files:
        print("No JSON files found in the data directory!")
    else:
        # Create output filename with timestamp
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(data_dir, f"cleaned_products_{timestamp}.json")
        
        # Clean the data
        success = clean_data(json_files, output_file)
        
        # Analyze the cleaned data if successful
        if success:
            analyze_cleaned_data(output_file)