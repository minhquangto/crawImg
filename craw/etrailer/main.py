from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver
from tkinter import filedialog
from PIL import Image
from io import BytesIO
import requests
import os
import time
import re
import tkinter as tk


current_directory = os.path.dirname(os.path.abspath(__file__))
edge_driver_path = os.path.join(current_directory, "msedgedriver.exe")
edge_options = Options()
edge_options.use_chromium = True

def select_file():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Chọn tệp văn bản chứa URL",
        filetypes=[("Text files", "*.txt")]
    )
    return file_path

def select_folder():
    root = tk.Tk()
    root.withdraw()
    folder_path = filedialog.askdirectory(
        title="Chọn thư mục lưu ảnh"
    )
    return folder_path

def get_urls_from_file(file_path):
    urls = []
    with open(file_path, 'r') as file:
        for line in file:
            url = line.strip()
            if url:
                urls.append(url)
    return urls

def download_etrailer_images(driver, folder_path, name):
    images = driver.find_elements(By.XPATH, "//img[@itemprop='contentUrl']")
    for idx, image in enumerate(images):
        image_url = image.get_attribute("src")
        if image_url:
            response = requests.get(image_url)
            if response.status_code == 200:
                image_data = BytesIO(response.content)
                img = Image.open(image_data)
                width, height = img.size
                new_size = max(width, height)
                new_img = Image.new("RGB", (new_size, new_size), (255, 255, 255))
                left = (new_size - width) // 2
                top = (new_size - height) // 2
                new_img.paste(img, (left, top))
                image_name = f"{name} {len(os.listdir(folder_path)) + 1}.jpg"
                image_path = os.path.join(folder_path, image_name)
                new_img.save(image_path)
                # print(f"Đã lưu: {image_path}")

def process_etrailer_url(driver, url, folder_path):
    """
    Xử lý từng URL: tải hình ảnh và xử lý nút 'Show All' và 'Next'.

    :param driver: Đối tượng Selenium WebDriver.
    :param url: URL trang web để tải hình ảnh.
    :param folder_path: Đường dẫn đến thư mục lưu ảnh.
    """
    driver.get(url)

    time.sleep(5)

    try:
        prod_info_div = driver.find_element(By.CSS_SELECTOR, "div.prod-info-panel#prodInfo")
        h1_element = prod_info_div.find_element(By.TAG_NAME, "h1")
        h1_text = h1_element.text.strip()
        # print(f"Đoạn văn bản từ thẻ H1: {h1_text}")

        h1_text = re.sub(r'[^a-zA-Z\s]', '', h1_text)

        words = h1_text.split()
        h1_text = '-'.join(words)

        h1_text = re.sub(r'-{2,}', '-', h1_text)
        # print(f"Chuỗi sau khi thay đổi: {h1_text}")
    except NoSuchElementException:
        # print("Không tìm thấy thẻ H1 trong thẻ div.prod-info-panel#prodInfo.")
        h1_text = "default_name"

    download_etrailer_images(driver, folder_path, h1_text)
    try:
        show_all_element = driver.find_element(By.XPATH,
                                               "//div[contains(@class, 'image-expansion-link')]//p[contains(text(), 'Show All')]")
        show_all_text = show_all_element.text
        match = re.search(r'\((\d+)\)', show_all_text)
        if match:
            num_of_clicks = int(match.group(1)) - 1
            if num_of_clicks > 15:
                num_of_clicks = 15
            # print(f"Số lần nhấn nút 'Next': {num_of_clicks}")
        else:
            num_of_clicks = 8
            # print("Không tìm thấy số lượng hình ảnh trong 'Show All'.")

        for _ in range(num_of_clicks):
            try:
                next_button = driver.find_element(By.CLASS_NAME, "viewer-iterator-next")
                next_button.click()
                time.sleep(2)  # Đợi trang tải lại nội dung
                download_etrailer_images(driver, folder_path, h1_text)
            except NoSuchElementException:
                # print("Không tìm thấy nút 'Next'.")
                break

    except NoSuchElementException:
        print("Không tìm thấy nút 'Show All'.")

def main():
    # Chọn tệp văn bản chứa URL
    file_path = select_file()
    if not file_path:
        # print("Không chọn tệp. Kết thúc.")
        return

    # Chọn thư mục lưu ảnh
    folder_path = select_folder()
    if not folder_path:
        # print("Không chọn thư mục. Kết thúc.")
        return

    # Đọc tất cả các URL từ tệp văn bản
    urls = get_urls_from_file(file_path)
    if not urls:
        # print("Không tìm thấy URL trong tệp. Kết thúc.")
        return

    # Khởi tạo trình duyệt Edge với EdgeDriver (mở một lần duy nhất)
    service = Service(executable_path=edge_driver_path)
    driver = webdriver.Edge(service=service, options=edge_options)

    # Xử lý từng URL

    for url in urls:
        # print(f"Đang xử lý URL: {url}")
        process_etrailer_url(driver, url, folder_path)
    driver.quit()

if __name__ == "__main__":
    main()
