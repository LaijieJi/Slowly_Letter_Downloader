import logging
import os
from os.path import exists
from datetime import datetime

# Paths
dir_path = os.getcwd()
log_path = os.path.join(dir_path, "logs")
download_path = os.path.join(dir_path, "letters")
user_data_path = os.path.join(dir_path, "sessions")
interface_path = os.path.join(dir_path, "interface")
compiled_path = os.path.join(dir_path, "lib")
settings_button_image_path = os.path.join(interface_path, "settings_button.png")

# Logger setup
if not exists(log_path):
    os.mkdir(log_path)

now = datetime.now()
log_name_format = now.strftime("%Y.%m.%d_%H.%M.%S.log")
log_name = f"SLD_{log_name_format}"

log_file = os.path.join(log_path, log_name)

logger = logging.getLogger("SLD")
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')

file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)


def show_folder_layout():
    folder_layout = os.listdir(dir_path)
    logger.debug("Root path items:")
    for item in folder_layout:
        logger.debug(os.path.join(dir_path, item))
    logger.debug("Module path items:")
    try:
        module_layout = os.listdir(compiled_path)
        module_path = compiled_path
    except Exception:
        logger.critical("No module path could be found!!!")
        return
    for item in module_layout:
        logger.debug(os.path.join(module_path, item))


# URLs
website = 'https://web.slowly.app/'
home_url = 'https://web.slowly.app/home'

# Regex
current_url_regex = r'([\w]*:\/\/[\w.]*\/)([\w]*)'
friend_regex = r'([\w]*:\/\/[\w.]*\/)(friend)(\/[\w\d]*)'
signature_regex = r'>(.*)<\/h5><p>(.* \d\d\d\d) .*<br>'
dot_regex = r'<button>\d*<\/button>'
penpal_regex = r'<span.*mt-1">(\w*)<\/span>'
penpals_regex = r'">(.*)<\/h6>'
id_regex = r'object .*\.(.*)>'

# XPath selectors
letter_xpath = "//div[@class='col-6 col-xl-4 mb-3']"
signature_xpath = "//div[@class='media-body mx-3 mt-2']"
dot_xpath = "//ul[@class='slick-dots']"
next_button_xpath = "//button[@class='slick-arrow slick-next']"
back_button_xpath = "//a[@class='no-underline link py-2 px-2 ml-n2 col-pixel-width-50 flip active']"
penpal_xpath = "//div[@class='col-9 pt-2']"
penpals_xpath = "//h6[@class='col pl-0 pr-0 mt-1 mb-0 text-truncate ']"
popup_xpath = "//button[@class='Toastify__close-button Toastify__close-button--warning']"

# Colors
slowly_bg = ("#F7F7F7", "#1b1d24")
slowly_fg = ("#FFFFFF", "#2b2f39")
slowly_yellow = ("#F9C32B", "#f9c32b")


def mk_penpal_dir(penpal):
    penpal_dir = os.path.join(download_path, penpal)
    if exists(penpal_dir):
        logger.info("Penpal download directory already exists in 'letters' folder.")
    else:
        logger.info(f"Making download directory for {penpal}")
        os.mkdir(penpal_dir)
    return penpal_dir
