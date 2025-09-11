import os
from pathlib import Path
import dj_database_url
import cloudinary

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Секретный ключ и режим отладки теперь берутся из окружения
SECRET_KEY = os.environ.get('SECRET_KEY')
DEBUG = os.environ.get('DEBUG') == 'True' # Проверяем на строку 'True'

# ... (остальные настройки, которые у вас уже есть) ...

# Database
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL')
    )
}

# ... (остальной код) ...












