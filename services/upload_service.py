# services/upload_service.py

from flask import (
    request,
    session,
    redirect,
    url_for,
    flash
)

from werkzeug.utils import secure_filename
from PIL import Image

import shutil
import time
import unicodedata

import config

import os
import zipfile

from database import get_db
from utils.paths import get_user_base_folder
from utils.helpers import get_folder_size, generate_thumb
from utils.validators import allowed_file
