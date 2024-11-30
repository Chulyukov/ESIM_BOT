import base64
import io
import os
import uuid
import qrcode

from link_for_marketplace.db_link import db_insert_esims


def generate_qr_code(data, save_path=None):
    """Генерация QR-кода в base64 и сохранение в файл (если указан путь)."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Сохранение QR-кода в файл, если указан путь
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)  # Создаем директории, если их нет
        img.save(save_path)
        print(f"QR-код сохранен в файл: {save_path}")

    # Сохранение QR-кода в base64
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return img_base64


def generate_links(esim_number, country, gb_amount):
    """Генерация ссылок с QR-кодами."""
    # Создаем список eSIM
    esim_list = [{"id": str(uuid.uuid4()), "country": country, "gb_amount": gb_amount} for _ in range(esim_number)]

    # Создаем папку для сохранения QR-кодов
    output_dir = "qr_codes"

    # Генерация QR-кодов и сохранение
    for esim in esim_list:
        qr_code_url = f"https://esimunity.ru/{esim['country']}/{gb_amount}/{esim['id']}"
        file_path = os.path.join(f"{output_dir}/{country}/{gb_amount}", f"{esim['country']}_{gb_amount}_{esim['id']}.png")  # Уникальное имя файла
        generate_qr_code(qr_code_url, save_path=file_path)  # Сохраняем QR-код в файл

    # Сохраняем eSIM в базе данных
    db_insert_esims(esim_list)


# Генерация одного eSIM для Турции с объемом 3 ГБ
generate_links(25, "turkey", 20)
