import os
import json
import time
import concurrent.futures
from tqdm import tqdm
import pandas as pd
from urllib.parse import urljoin

from category import scrape_mediamart_menu
from listproduct import crawl_cap_noi_products, save_products_to_json
from product import scrape_mediamart_product

BASE_URL = "https://mediamart.vn"
MAX_WORKERS_DEFAULT = 5  # Số luồng mặc định

def get_menu_categories():
    """
    Lấy danh sách các danh mục từ menu của trang web
    Nếu đã có file cache, sẽ đọc từ file
    """
    try:
        # Kiểm tra xem file menu đã tồn tại chưa
        if os.path.exists('mediamart_menu.json'):
            print("Đọc danh mục từ file mediamart_menu.json")
            with open('mediamart_menu.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # Nếu không, crawl mới
        print("Crawling danh mục menu từ trang chủ...")
        menu_items = scrape_mediamart_menu()
        
        # Lưu menu vào file để sử dụng lần sau
        with open('mediamart_menu.json', 'w', encoding='utf-8') as f:
            json.dump(menu_items, f, ensure_ascii=False, indent=4)
        
        return menu_items
    
    except Exception as e:
        print(f"Lỗi khi crawl menu: {e}")
        return []

def get_product_links(category_url, max_pages=None):
    """
    Lấy danh sách các liên kết sản phẩm từ trang danh mục
    Sử dụng hàm crawl_cap_noi_products từ module listproduct
    """
    return crawl_cap_noi_products(category_url, max_pages)

def save_products_to_csv(products, filename):
    """
    Lưu thông tin sản phẩm vào file CSV
    """
    try:
        # Chuyển đổi cấu trúc dữ liệu phức tạp sang chuỗi
        products_copy = []
        for product in products:
            product_copy = product.copy()
            
            # Chuyển danh sách tính năng thành chuỗi
            if 'key_features' in product_copy and isinstance(product_copy['key_features'], list):
                product_copy['key_features'] = '|'.join(product_copy['key_features'])
                
            # Chuyển thông số kỹ thuật thành chuỗi
            if 'specifications' in product_copy and isinstance(product_copy['specifications'], dict):
                product_copy['specifications'] = json.dumps(product_copy['specifications'], ensure_ascii=False)
                
            # Chuyển danh sách hình ảnh thành chuỗi
            if 'image_urls' in product_copy and isinstance(product_copy['image_urls'], list):
                product_copy['image_urls'] = '|'.join(product_copy['image_urls'])
                
            products_copy.append(product_copy)
        
        # Tạo DataFrame và lưu thành CSV
        df = pd.DataFrame(products_copy)
        df.to_csv(filename, index=False, encoding='utf-8-sig')  # utf-8-sig để tương thích với Excel
        print(f"Đã lưu {len(products)} sản phẩm vào {filename}")
        return True
    except Exception as e:
        print(f"Lỗi khi lưu file {filename}: {e}")
        return False

def crawl_category_products(category, max_pages=None, max_workers=MAX_WORKERS_DEFAULT, max_products=None):
    """
    Crawl tất cả sản phẩm từ một danh mục cụ thể với đa luồng
    
    Args:
        category (dict): Thông tin danh mục (name, url)
        max_pages (int, optional): Số trang tối đa cần crawl
        max_workers (int): Số luồng tối đa để crawl
        max_products (int, optional): Số sản phẩm tối đa cần crawl
        
    Returns:
        list: Danh sách các thông tin chi tiết sản phẩm
    """
    # Lấy danh sách sản phẩm từ các trang danh mục
    print(f"\nCrawling danh mục: {category['name']} ({category['url']})")
    product_links = get_product_links(category['url'], max_pages)
    
    # Giới hạn số lượng sản phẩm nếu cần
    if max_products and len(product_links) > max_products:
        product_links = product_links[:max_products]
        print(f"Giới hạn crawl {max_products} sản phẩm")
    
    print(f"Tìm thấy {len(product_links)} sản phẩm trong danh mục {category['name']}")
    
    if not product_links:
        return []
    
    # Crawl chi tiết sản phẩm với đa luồng
    detailed_products = []
    
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Tạo các future cho mỗi sản phẩm
            future_to_url = {
                executor.submit(scrape_mediamart_product, product['url']): product
                for product in product_links
            }
            
            # Hiển thị tiến trình với tqdm
            with tqdm(total=len(future_to_url), desc=f"Crawling {category['name']}") as pbar:
                for future in concurrent.futures.as_completed(future_to_url):
                    product = future_to_url[future]
                    try:
                        detail = future.result()
                        if 'error' not in detail:
                            # Thêm thông tin từ danh sách sản phẩm nếu cần
                            for key in product:
                                if key not in detail:
                                    detail[key] = product[key]
                            detailed_products.append(detail)
                        else:
                            print(f"Lỗi khi crawl sản phẩm {product['url']}: {detail['error']}")
                    except Exception as e:
                        print(f"Lỗi khi xử lý kết quả từ {product['url']}: {e}")
                    pbar.update(1)
    
    except Exception as e:
        print(f"Lỗi khi crawl sản phẩm: {e}")
    
    return detailed_products

def main(auto_mode=True, max_pages=None, max_products=None, max_workers=MAX_WORKERS_DEFAULT):
    """
    Hàm chính để chạy crawler
    
    Args:
        auto_mode (bool): Nếu True, sẽ tự động crawl tất cả sản phẩm mà không cần tương tác
        max_pages (int, optional): Số trang tối đa cần crawl cho mỗi danh mục
        max_products (int, optional): Số sản phẩm tối đa cần crawl
        max_workers (int): Số luồng tối đa để crawl đồng thời
    """
    # Tạo thư mục data nếu chưa tồn tại
    data_dir = 'data'
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    try:
        # Lấy danh sách danh mục từ menu
        categories = get_menu_categories()
        
        # Đảm bảo categories không phải là None
        if categories is None:
            categories = []
            
        print(f"Tìm thấy {len(categories)} danh mục")
        
        # Nếu ở chế độ tự động, crawl tất cả sản phẩm mà không cần tương tác
        if auto_mode:
            choice = '5'  # Mặc định chọn crawl tất cả sản phẩm
        else:
            # Hiển thị danh sách danh mục
            print("\nDanh sách danh mục:")
            for i, category in enumerate(categories):
                print(f"{i+1}. {category['name']} - {category['url']}")
            
            # Tùy chọn lựa chọn danh mục để crawl
            print("\nTùy chọn:")
            print("1. Crawl một danh mục cụ thể")
            print("2. Crawl một số danh mục")
            print("3. Crawl tất cả danh mục")
            print("4. Crawl một URL cụ thể")
            print("5. Crawl tất cả sản phẩm")
            
            choice = input("Chọn tùy chọn (1-5): ")
            
            max_pages_input = input("Số trang tối đa cần crawl cho mỗi danh mục (0 để crawl tất cả): ")
            max_pages = None if max_pages_input == "0" or not max_pages_input else int(max_pages_input)
            
            max_products_input = input("Số sản phẩm tối đa cần crawl cho mỗi danh mục (0 để crawl tất cả): ")
            max_products = None if max_products_input == "0" or not max_products_input else int(max_products_input)
            
            max_workers_input = input("Số luồng tối đa để crawl đồng thời (mặc định 5): ")
            max_workers = int(max_workers_input) if max_workers_input else MAX_WORKERS_DEFAULT
        
        all_products = []
        
        if choice == '1':
            category_index = int(input(f"Chọn danh mục để crawl (1-{len(categories)}): ")) - 1
            if 0 <= category_index < len(categories):
                selected_category = categories[category_index]
                products = crawl_category_products(selected_category, max_pages, max_workers, max_products)
                all_products.extend(products)
                
                if products:
                    # Lưu dữ liệu của danh mục này vào file riêng
                    category_name = selected_category['name']
                    safe_name = "".join([c if c.isalnum() else "_" for c in category_name])
                    
                    json_file = os.path.join(data_dir, f"{safe_name}_products.json")
                    csv_file = os.path.join(data_dir, f"{safe_name}_products.csv")
                    
                    save_products_to_json(products, json_file)
        
        elif choice == '2':
            indices = input(f"Nhập các số từ 1-{len(categories)} của danh mục cần crawl (cách nhau bởi dấu phẩy): ")
            indices = [int(x.strip()) - 1 for x in indices.split(',') if x.strip().isdigit()]
            
            for idx in indices:
                if 0 <= idx < len(categories):
                    selected_category = categories[idx]
                    products = crawl_category_products(selected_category, max_pages, max_workers, max_products)
                    all_products.extend(products)
                    
                    if products:
                        # Lưu dữ liệu của danh mục này vào file riêng
                        category_name = selected_category['name']
                        safe_name = "".join([c if c.isalnum() else "_" for c in category_name])
                        
                        json_file = os.path.join(data_dir, f"{safe_name}_products.json")
                        csv_file = os.path.join(data_dir, f"{safe_name}_products.csv")
                        
                        save_products_to_json(products, json_file)
        
        elif choice == '3':
            for category in categories:
                products = crawl_category_products(category, max_pages, max_workers, max_products)
                all_products.extend(products)
                
                if products:
                    # Lưu dữ liệu của danh mục này vào file riêng
                    category_name = category['name']
                    safe_name = "".join([c if c.isalnum() else "_" for c in category_name])
                    
                    json_file = os.path.join(data_dir, f"{safe_name}_products.json")
                    csv_file = os.path.join(data_dir, f"{safe_name}_products.csv")
                    save_products_to_json(products, json_file)
        
        elif choice == '4':
            url = input("Nhập URL cụ thể để crawl: ")
            if url.startswith("http"):
                category_name = input("Nhập tên danh mục: ")
                category = {'name': category_name, 'url': url}
                products = crawl_category_products(category, max_pages, max_workers, max_products)
                all_products.extend(products)
                
                if products:
                    # Lưu dữ liệu của danh mục này vào file riêng
                    safe_name = "".join([c if c.isalnum() else "_" for c in category_name])
                    
                    json_file = os.path.join(data_dir, f"{safe_name}_products.json")
                    csv_file = os.path.join(data_dir, f"{safe_name}_products.csv")
                    
                    save_products_to_json(products, json_file)

        
        elif choice == '5':
            print("\nCrawl tất cả sản phẩm từ tất cả danh mục...")
            # Tạo một danh mục tổng hợp tất cả URL sản phẩm
            all_product_links = []
            
            # Đầu tiên, thu thập tất cả link sản phẩm từ tất cả danh mục
            print("Thu thập danh sách sản phẩm từ tất cả danh mục...")
            for category in categories:
                print(f"Đang quét danh mục: {category['name']}")
                category_links = get_product_links(category['url'], max_pages)
                if category_links:
                    print(f"Tìm thấy {len(category_links)} sản phẩm trong danh mục {category['name']}")
                    all_product_links.extend(category_links)
                    
            # Giới hạn số lượng sản phẩm nếu cần
            if max_products and len(all_product_links) > max_products:
                print(f"Giới hạn tổng số sản phẩm cần crawl thành {max_products} (từ tổng số {len(all_product_links)})")
                all_product_links = all_product_links[:max_products]
            
            print(f"\nTổng cộng tìm thấy {len(all_product_links)} sản phẩm từ tất cả danh mục")
            
            if not all_product_links:
                print("Không tìm thấy sản phẩm nào để crawl!")
            else:
                # Crawl chi tiết từng sản phẩm với đa luồng
                print("Bắt đầu crawl chi tiết sản phẩm...")
                
                # Tạo một category giả để sử dụng với hàm crawl_category_products
                pseudo_category = {
                    'name': 'all_products',
                    'url': BASE_URL
                }
                
        # Crawl với đa luồng
                detailed_products = []
                try:
                    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                        # Tạo các future cho mỗi sản phẩm
                        future_to_url = {
                            executor.submit(scrape_mediamart_product, product['url']): product
                            for product in all_product_links
                        }
                        
                        # Hiển thị tiến trình với tqdm
                        with tqdm(total=len(future_to_url), desc="Crawling tất cả sản phẩm") as pbar:
                            for future in concurrent.futures.as_completed(future_to_url):
                                product = future_to_url[future]
                                try:
                                    detail = future.result()
                                    if detail and 'error' not in detail:
                                        # Thêm thông tin từ danh sách sản phẩm nếu cần
                                        for key in product:
                                            if key not in detail:
                                                detail[key] = product[key]
                                        detailed_products.append(detail)
                                    else:
                                        print(f"Lỗi khi crawl sản phẩm {product['url']}: {detail.get('error', 'Unknown error')}")
                                except Exception as e:
                                    print(f"Lỗi khi xử lý kết quả từ {product['url']}: {e}")
                                    # Vẫn tiếp tục với sản phẩm tiếp theo
                                finally:
                                    # Đảm bảo thanh tiến trình luôn được cập nhật, kể cả khi có lỗi
                                    pbar.update(1)
                
                except Exception as e:
                    print(f"Lỗi khi crawl sản phẩm: {e}")
                
                
                # Lưu tất cả sản phẩm vào file
                if detailed_products:
                    all_products.extend(detailed_products)
                    
                    # Tạo tên file với timestamp
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    all_json_file = os.path.join(data_dir, f"all_products_{timestamp}.json")
                    all_csv_file = os.path.join(data_dir, f"all_products_{timestamp}.csv")
                    
                    print(f"\nLưu {len(detailed_products)} sản phẩm vào file...")
                    save_products_to_json(detailed_products, all_json_file)
                    
                    print(f"\nĐã crawl và lưu thành công {len(detailed_products)} sản phẩm")
        
        # Lưu tất cả dữ liệu vào file tổng hợp
        if all_products:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            all_json_file = os.path.join(data_dir, f"all_products_{timestamp}.json")
            all_csv_file = os.path.join(data_dir, f"all_products_{timestamp}.csv")
            
            save_products_to_json(all_products, all_json_file)
            
            print(f"\nTổng cộng đã crawl {len(all_products)} sản phẩm")
    
    except Exception as e:
        print(f"Lỗi: {e}")

if __name__ == "__main__":
    start_time = time.time()
    # Mặc định chạy ở chế độ tự động với các tham số sau
    # - auto_mode=True: Tự động crawl tất cả sản phẩm mà không cần tương tác
    # - max_pages=None: Không giới hạn số trang
    # - max_products=None: Không giới hạn số sản phẩm
    # - max_workers=10: Sử dụng 10 luồng đồng thời để tăng tốc độ
    main(auto_mode=True, max_pages=None, max_products=None, max_workers=10)
    end_time = time.time()
    
    # Hiển thị tổng thời gian chạy
    total_time = end_time - start_time
    hours, remainder = divmod(total_time, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    print(f"\nHoàn thành crawl trong: {int(hours)} giờ, {int(minutes)} phút, {seconds:.2f} giây")
