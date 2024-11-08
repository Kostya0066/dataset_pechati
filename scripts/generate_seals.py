import os
import random
import math
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter


def generate_seal(image_size=(256, 256)):
    # Создаём пустое изображение
    background_color = 'white'
    image = Image.new('RGB', image_size, background_color)
    draw = ImageDraw.Draw(image)

    # Параметры кругов
    center = (image_size[0] // 2, image_size[1] // 2)
    max_radius = min(center) - 10  # Отступы от краёв
    radius = random.randint(max_radius - 35, max_radius - 20)
    circle_width = random.randint(2, 5)

    # Рисуем внутренний круг
    draw.ellipse(
        [
            (center[0] - radius, center[1] - radius),
            (center[0] + radius, center[1] + radius)
        ],
        outline='blue',
        width=circle_width
    )

    # Определяем внешний радиус
    outer_radius = radius + 15
    if outer_radius > max_radius:
        outer_radius = max_radius

    # Рисуем внешний круг
    draw.ellipse(
        [
            (center[0] - outer_radius, center[1] - outer_radius),
            (center[0] + outer_radius, center[1] + outer_radius)
        ],
        outline='blue',
        width=circle_width
    )

    # Генерируем случайное название компании
    company_name = '«' + ''.join(random.choices([chr(code) for code in range(ord('А'), ord('Я') + 1)], k=7)) + '»'

    # Генерируем ИНН
    inn_digits = ''.join(random.choices('0123456789', k=10))
    inn_number = inn_digits

    # Загружаем шрифт
    fonts_dir = os.path.join(os.path.dirname(__file__), '..', 'fonts')
    if not os.path.exists(fonts_dir):
        raise FileNotFoundError(f"Папка со шрифтами не найдена: {fonts_dir}")
    font_files = [os.path.join(fonts_dir, f)
                  for f in os.listdir(fonts_dir) if f.endswith(('.ttf', '.otf'))]
    if not font_files:
        raise FileNotFoundError(
            "Не найдено ни одного файла шрифта в папке fonts/")

    font_path = random.choice(font_files)
    font_size = random.randint(20, 25)
    font = ImageFont.truetype(font_path, font_size)

    # Рисуем название компании в центре
    draw.text(center, company_name, font=font,
              fill='blue', anchor='mm')

    # Рисуем ИНН по внутренней окружности (цифры)
    inn_radius = radius - 10  # Сдвигаем ближе к центру
    inn_font_size = 14  # Уменьшаем размер шрифта для цифр
    inn_font = ImageFont.truetype(font_path, inn_font_size)
    draw_text_on_circle(image, center, inn_radius,
                        inn_number, inn_font, start_angle_deg=90, flip=False)  # Цифры остаются как есть

    # Генерируем случайный текст для внешнего круга
    outer_text = ''.join(random.choices(
        [chr(code) for code in range(ord('А'), ord('Я') + 1)], k=50))

    # Шрифт для внешнего текста
    outer_font_size = 14
    outer_font = ImageFont.truetype(font_path, outer_font_size)

    # Радиус для внешнего текста (между двумя кругами)
    outer_text_radius = (radius + outer_radius) / 2 + 1  # Увеличен отступ для текста

    # Рисуем внешний текст по окружности с правильной ориентацией (верх букв к краю)
    draw_text_on_circle(image, center, outer_text_radius,
                        outer_text, outer_font, start_angle_deg=270, clockwise=True, flip=True)  # Буквы нормальные, но низ направлен к центру

    # Применяем случайные трансформации
    image = apply_random_transformations(image, background_color)

    # Собираем метаданные
    metadata = {
        'company_name': company_name,
        'inn': inn_number,
        'outer_text': outer_text,
        'font': os.path.basename(font_path),
        'rotation_angle': image.info.get('rotation_angle', 0),
        'noise_level': image.info.get('noise_level', 0),
        'blur_radius': image.info.get('blur_radius', 0)
    }

    return image, metadata


def draw_text_on_circle(image, center, radius, text, font, start_angle_deg=0, text_color='blue', clockwise=True, flip=False):
    draw = ImageDraw.Draw(image)

    # Преобразуем начальный угол в радианы
    start_angle = math.radians(start_angle_deg)

    # Длина окружности
    circumference = 2 * math.pi * radius

    # Список для хранения угловых ширин символов
    char_angles = []

    # Вычисляем угловую ширину каждого символа
    for char in text:
        bbox = font.getbbox(char)
        w = bbox[2] - bbox[0]
        # Угловая ширина символа в радианах
        char_angle = (w / circumference) * 2 * math.pi
        char_angles.append(char_angle)

    # Общий угол текста
    total_text_angle = sum(char_angles)

    # Начальный угол (центрируем текст по окружности)
    if clockwise:
        current_angle = start_angle - total_text_angle / 2
    else:
        current_angle = start_angle + total_text_angle / 2

    for i, char in enumerate(text):
        char_angle = char_angles[i]
        w = font.getbbox(char)[2] - font.getbbox(char)[0]
        h = font.getbbox(char)[3] - font.getbbox(char)[1]

        if clockwise:
            angle = current_angle + char_angle / 2
        else:
            angle = current_angle - char_angle / 2

        # Координаты символа
        x = center[0] + radius * math.cos(angle)
        y = center[1] + radius * math.sin(angle)

        # Создаём изображение для символа
        char_image = Image.new('RGBA', (int(w * 2), int(h * 2)), (255, 255, 255, 0))
        char_draw = ImageDraw.Draw(char_image)
        char_draw.text((w / 2, h / 2), char,
                       font=font, fill=text_color)

        # Поворачиваем символы так, чтобы их низ был направлен к центру (перевёрнуто)
        rotation = math.degrees(angle) + 90 if flip else math.degrees(angle) - 90
        rotated_char_image = char_image.rotate(
            -rotation, resample=Image.BICUBIC, expand=True)

        # Вставляем повернутый символ на изображение
        image.paste(rotated_char_image,
                    (int(x - rotated_char_image.width / 2),
                     int(y - rotated_char_image.height / 2)),
                    rotated_char_image)

        # Обновляем текущий угол
        if clockwise:
            current_angle += char_angle
        else:
            current_angle -= char_angle


def apply_random_transformations(image, background_color):
    # Поворот
    rotation_angle = random.uniform(-5, 5)
    image = image.rotate(rotation_angle, expand=True,
                         fillcolor=background_color)
    image.info['rotation_angle'] = rotation_angle

    # Добавление шума
    noise_level = random.uniform(0.1, 0.3)
    image = add_noise(image, noise_level)
    image.info['noise_level'] = noise_level

    # Размытие
    blur_radius = random.uniform(0, 0.5)
    image = image.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    image.info['blur_radius'] = blur_radius

    return image


def add_noise(img, noise_level):
    if noise_level <= 0:
        return img

    img_array = np.array(img)
    noise = np.random.normal(
        0, noise_level * 255, img_array.shape)
    img_array = img_array + noise
    img_array = np.clip(img_array, 0, 255)
    return Image.fromarray(img_array.astype(np.uint8))


def generate_dataset(num_images, output_dir):
    images_dir = os.path.join(output_dir, 'images')
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)

    labels = []

    for i in range(1, num_images + 1):
        image, metadata = generate_seal()
        image_filename = f'seal_{i}.png'
        image.save(os.path.join(images_dir, image_filename))

        # Добавляем информацию об изображении в метаданные
        metadata['filename'] = image_filename
        labels.append(metadata)

        print(f'Изображение {i}/{num_images} сгенерировано.')

    # Сохраняем метаданные в JSON-файл
    labels_filepath = os.path.join(output_dir, 'labels.json')
    with open(labels_filepath, 'w', encoding='utf-8') as f:
        json.dump(labels, f, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    num_images = 3  # Задайте количество изображений
    output_directory = os.path.join(
        os.path.dirname(__file__), '..', 'dataset')
    generate_dataset(num_images, output_directory)











