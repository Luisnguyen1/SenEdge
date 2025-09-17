from bs4 import BeautifulSoup
import requests
def scrape_mediamart_menu():
    # URL gốc để nối các link tương đối
    base_url = "https://mediamart.vn"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    response = requests.get(base_url, headers=headers)
    if response.status_code != 200:
        print({"error": f"Failed to fetch the page: {response.status_code}"})
    soup = BeautifulSoup(response.text, 'html.parser')  


    # Tìm container chính của menu
    navbar_main = soup.find('div', id='navbarMain')

    # Danh sách để lưu kết quả
    menu_items = []



    if navbar_main:
        # --- Lấy các mục menu chính (Level 1 - Các thẻ a trong span.nav-link-text) ---
        top_level_lis = navbar_main.find('ul', class_='navbar-nav').find_all('li', class_='nav-item dropdown', recursive=False)
        for li_top in top_level_lis:
            nav_link_text_span = li_top.find('span', class_='nav-link-text')
            if nav_link_text_span:
                inner_span = nav_link_text_span.find('span')
                if inner_span:
                    links = inner_span.find_all('a')
                    for link in links:
                        name = link.get_text(strip=True)
                        url = link.get('href', '#')
                        # Tạo URL tuyệt đối nếu là link tương đối
                        if url.startswith('/'):
                            url = base_url + url
                        if name and url != '#':
                            menu_items.append({'name': name, 'url': url})

            # --- Lấy các mục menu con (Level 2 - class="nav-link-2") ---
            submenu_1 = li_top.find('ul', class_='dropdown-menu-1')
            if submenu_1:
                # Tìm tất cả các thẻ <a> có class="nav-link-2" trong menu con này
                sub_links = submenu_1.find_all('a', class_='nav-link-2')
                for link in sub_links:
                    # Lấy text, loại bỏ text của thẻ span ẩn bên trong nếu có
                    name = link.get_text(strip=True)
                    hidden_span = link.find('span', class_='menu-item-view')
                    if hidden_span:
                        name = name.replace(hidden_span.get_text(strip=True), '').strip()

                    url = link.get('href', '#')

                    # Đảm bảo URL là tuyệt đối
                    if url.startswith('/'):
                        url = base_url + url
                    elif not url.startswith('http') and url != '#':
                        # Có thể là link đầy đủ hoặc link javascript, chỉ lấy link http(s) hoặc tương đối
                        print(f"Skipping potentially invalid URL: {url} for item: {name}")
                        continue # Bỏ qua nếu không phải link web hợp lệ

                    # Chỉ thêm nếu có tên và URL hợp lệ (không phải # hoặc javascript:;)
                    if name and url != '#' and not url.startswith('javascript:'):
                        # Tránh trùng lặp nếu mục này đã được thêm ở cấp độ 1
                        is_duplicate = False
                        for item in menu_items:
                            if item['name'] == name and item['url'] == url:
                                is_duplicate = True
                                break
                        if not is_duplicate:
                            menu_items.append({'name': name, 'url': url})
        return menu_items

    else:
        print("Không tìm thấy thẻ div#navbarMain")

menu_items = scrape_mediamart_menu()
import json
with open('mediamart_menu.json', 'w', encoding='utf-8') as f:
    json.dump(menu_items, f, ensure_ascii=False, indent=4)
print("\nĐã lưu dữ liệu vào file mediamart_menu.json")