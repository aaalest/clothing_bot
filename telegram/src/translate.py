from typing import Literal, Union


languages = Literal['en', 'ua']


class Descriptor:
    def __init__(self, translations):
        self.translations = translations

    def __get__(self, instance, owner):
        def translate(language: Union[languages, dict], *args):
            if isinstance(language, dict):
                language = language["language"]

            if language in self.translations:
                return self.translations[language].format(*args)
            else:
                raise ValueError(f"Translation for language '{language}' not found.")
        return translate


class Translate:
    start_massage = Descriptor({
        "en": "Hello, {}, this is a bot that can change clothes in photos. To get started, send a photo.",
        "ua": "Привіт, {}, це бот, який може змінювати одяг на фотографіях. Щоб почати, надішліть фото."
    })

    photo_not_found_upload_again = Descriptor({
        "en": "The photo was not found. Upload the photo again.",
        "ua": "Фотографія не знайдена. Завантажте фото ще раз."
    })

    message_not_found_try_again = Descriptor({
        "en": "The message was not found. Please try again.",
        "ua": "Повідомлення не знайдено. Будь ласка, спробуйте ще раз."
    })

    no_available_hosts = Descriptor({
        "en": "No available hosts to process the image. Please try again later.",
        "ua": "Немає доступних хостів для обробки зображення. Будь ласка, спробуйте пізніше."
    })

    choose_what_clothes_to_change_into = Descriptor({
        "en": "Choose what clothes to change into.",
        "ua": "Виберіть, на який одяг змінити."
    })

    clothing_was_not_found_please_try_a_different_photo = Descriptor({
        "en": "Clothing was not found. Please try a different photo.",
        "ua": "Одяг не знайдено. Будь ласка, спробуйте інше фото."
    })

    an_error_occurred_during_image_processing = Descriptor({
        "en": "An error occurred during image processing. Please try again later.",
        "ua": "Під час обробки зображення сталася помилка. Будь ласка, спробуйте пізніше."
    })

    language_changed = Descriptor({
        "en": "Language changed",
        "ua": "Мова змінена"
    })

    back = Descriptor({
        "en": "Back",
        "ua": "Назад"
    })

    language = Descriptor({
        "en": "Language",
        "ua": "Мова"
    })

    choose_language = Descriptor({
        "en": "Choose language",
        "ua": "Оберіть мову"
    })

    choose_upper_clothing = Descriptor({
        "en": "Choose upper part of clothing",
        "ua": "Оберіть верхню частину одягу"
    })

    choose_upper_color = Descriptor({
        "en": "Choose the color of the upper part of the clothing",
        "ua": "Оберіть колір верхньої частини одягу"
    })

    choose_lower_clothing = Descriptor({
        "en": "Choose lower part of clothing",
        "ua": "Оберіть нижню частину одягу"
    })

    choose_lower_color = Descriptor({
        "en": "Choose the color of the lower part of the clothing",
        "ua": "Оберіть колір нижньої частини одягу"
    })

    choose_style = Descriptor({
        "en": "Choose the style of clothing",
        "ua": "Оберіть стиль одягу"
    })

    generate = Descriptor({
        "en": "Generate",
        "ua": "Генерувати"
    })

    cancel = Descriptor({
        "en": "Cancel",
        "ua": "Скасувати"
    })

    regenerate = Descriptor({
        "en": "Regenerate",
        "ua": "Перегенерувати"
    })

    modify_generation = Descriptor({
        "en": "Modify generation",
        "ua": "Змінити генерацію"
    })

    generating = Descriptor({
        "en": "Generating",
        "ua": "Генерація"
    })

    upper = Descriptor({
        "en": "Upper",
        "ua": "Верх"
    })

    lower = Descriptor({
        "en": "Lower",
        "ua": "Низ"
    })

    color = Descriptor({
        "en": "Color",
        "ua": "Колір"
    })

    style = Descriptor({
        "en": "Style",
        "ua": "Стиль"
    })

    jacket = Descriptor({
        "en": "Jacket",
        "ua": "Куртка"
    })

    tshirt = Descriptor({
        "en": "T-shirt",
        "ua": "Футболка"
    })

    shirt = Descriptor({
        "en": "Shirt",
        "ua": "Сорочка"
    })

    sweater = Descriptor({
        "en": "Sweater",
        "ua": "Светр"
    })

    hoodie = Descriptor({
        "en": "Hoodie",
        "ua": "Худі"
    })

    coat = Descriptor({
        "en": "Coat",
        "ua": "Пальто"
    })

    dress = Descriptor({
        "en": "Dress",
        "ua": "Сукня"
    })

    auto = Descriptor({
        "en": "Auto",
        "ua": "Автоматично"
    })

    black = Descriptor({
        "en": "Black",
        "ua": "Чорний"
    })

    white = Descriptor({
        "en": "White",
        "ua": "Білий"
    })

    red = Descriptor({
        "en": "Red",
        "ua": "Червоний"
    })

    green = Descriptor({
        "en": "Green",
        "ua": "Зелений"
    })

    blue = Descriptor({
        "en": "Blue",
        "ua": "Синій"
    })

    yellow = Descriptor({
        "en": "Yellow",
        "ua": "Жовтий"
    })

    purple = Descriptor({
        "en": "Purple",
        "ua": "Фіолетовий"
    })

    orange = Descriptor({
        "en": "Orange",
        "ua": "Помаранчевий"
    })

    pink = Descriptor({
        "en": "Pink",
        "ua": "Рожевий"
    })

    brown = Descriptor({
        "en": "Brown",
        "ua": "Коричневий"
    })

    gray = Descriptor({
        "en": "Gray",
        "ua": "Сірий"
    })

    jeans = Descriptor({
        "en": "Jeans",
        "ua": "Джинси"
    })

    trousers = Descriptor({
        "en": "Trousers",
        "ua": "Штани"
    })

    shorts = Descriptor({
        "en": "Shorts",
        "ua": "Шорти"
    })

    skirts = Descriptor({
        "en": "Skirts",
        "ua": "Спідниці"
    })

    casual = Descriptor({
        "en": "Casual",
        "ua": "Кежуал"
    })

    sport = Descriptor({
        "en": "Sport",
        "ua": "Спорт"
    })

    formal = Descriptor({
        "en": "Formal",
        "ua": "Офіційний"
    })

    party = Descriptor({
        "en": "Party",
        "ua": "Вечірка"
    })


tr = Translate()
