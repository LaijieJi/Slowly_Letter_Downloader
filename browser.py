import logging
import os
import re
from os.path import exists

from playwright.sync_api import sync_playwright
from pdfrw import PdfReader, PdfWriter

from utils import (
    website, home_url, user_data_path, download_path,
    letter_xpath, signature_xpath, dot_xpath, next_button_xpath,
    back_button_xpath, penpals_xpath, popup_xpath,
    signature_regex, dot_regex, penpals_regex,
    current_url_regex,
    mk_penpal_dir,
)

logger = logging.getLogger("SLD")


class BrowserManager:
    def __init__(self):
        self.playwright = None
        self.context = None
        self.page = None

    def start_login(self, on_login_detected):
        """Open a headed browser for QR code login.

        Polls page.url until the home URL is detected, then closes
        the browser and calls on_login_detected.
        """
        logger.info("Opening browser for login")
        self.playwright = sync_playwright().start()
        self.context = self.playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_path,
            headless=False,
            viewport={"width": 960, "height": 720},
        )
        self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
        self.page.goto(website)

        # Poll for login
        while self.page.url != home_url:
            self.page.wait_for_timeout(500)

        logger.info("Login detected, closing headed browser")
        self.context.close()
        self.playwright.stop()
        self.playwright = None
        self.context = None
        self.page = None

        on_login_detected()

    def start_scraping(self):
        """Reopen browser in headless mode with the persisted session."""
        logger.info("Starting headless scraping session")
        self.playwright = sync_playwright().start()
        self.context = self.playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_path,
            headless=True,
            viewport={"width": 1920, "height": 1080},
        )
        self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
        self.page.goto(website)

    def verify_login(self):
        """Wait for redirect to home_url. Returns True if logged in."""
        for attempt in range(10):
            if self.page.url == home_url:
                logger.info("Login verified via persistent session")
                return True
            logger.warning(f"Login check attempt {attempt} — not at home URL yet")
            self.page.wait_for_timeout(1000)
        logger.critical("Login could not be verified")
        return False

    def get_penpals(self):
        """Wait for penpal list to load and return penpal names."""
        logger.debug("Waiting for penpals to appear")
        self.page.wait_for_selector(f"xpath={penpals_xpath}", timeout=30000)
        elements = self.page.locator(f"xpath={penpals_xpath}").all()
        penpals_list = []
        for el in elements:
            outer_html = el.evaluate("e => e.outerHTML")
            match = re.search(penpals_regex, outer_html)
            if match:
                penpals_list.append(match.group(1))
        logger.info(f"Found {len(penpals_list)} penpals")
        self.dismiss_popups()
        return penpals_list

    def dismiss_popups(self):
        """Close any notification popups."""
        popups = self.page.locator(f"xpath={popup_xpath}").all()
        for popup in popups:
            try:
                popup.click()
                logger.info("Popup closed")
            except Exception as e:
                logger.error(f"Error closing popup: {e}")

    def scroll_down(self):
        """Scroll to bottom to lazy-load all content.

        After each scroll, waits for network idle (no requests for 500ms)
        rather than a fixed delay. This is faster on quick connections
        and more reliable on slow ones.
        """
        page_height = self.page.evaluate("document.body.scrollHeight")
        while True:
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            try:
                self.page.wait_for_load_state("networkidle", timeout=3000)
            except Exception:
                pass  # timeout is fine — means no new requests were made
            new_height = self.page.evaluate("document.body.scrollHeight")
            if new_height == page_height:
                break
            page_height = new_height

    def check_for_photos(self):
        """Return True if the current letter has a photo carousel."""
        return self.page.locator(f"xpath={dot_xpath}").count() > 0

    def photo_amount(self):
        """Return the number of photos in the carousel."""
        photos_html = self.page.locator(f"xpath={dot_xpath}").first.inner_html()
        return len(re.findall(dot_regex, photos_html))

    def image_load_check(self):
        """Wait until all images on the page have finished loading."""
        self.page.wait_for_load_state("load")
        # Check all images in a single JS call instead of one per image
        self.page.wait_for_function(
            "() => Array.from(document.images).every(img => img.complete)",
            timeout=15000,
        )

    def make_pdf(self, letter_count, penpal_dir, penpal):
        """Generate a PDF of the current letter and write metadata."""
        sig_element = self.page.locator(f"xpath={signature_xpath}").first
        innerhtml = sig_element.inner_html()
        username = re.search(signature_regex, innerhtml).group(1)
        date = re.search(signature_regex, innerhtml).group(2)
        pdf_name = f"letter{letter_count}_{username}_{date}.pdf"
        pdf_path = os.path.join(penpal_dir, pdf_name)

        logger.info(f"Printing letter {letter_count}")
        self.page.pdf(
            path=pdf_path,
            landscape=True,
            print_background=True,
            display_header_footer=False,
        )

        # Write metadata with pdfrw
        data = PdfReader(pdf_path)
        data.Info.Letter = letter_count
        data.Info.Penpal = penpal
        os.remove(pdf_path)
        PdfWriter(pdf_path, trailer=data).write()

        if exists(pdf_path):
            logger.info(f"Letter {letter_count} successfully printed!")
        else:
            logger.error(f"Letter {letter_count} failed to print.")

    def open_letter(self, letter_int, letter_count, penpal_dir, penpal):
        """Click a letter, handle photo carousel, and generate PDF."""
        letters = self.page.locator(f"xpath={letter_xpath}").all()
        logger.debug(f"Penpal: {penpal}, letter count: {len(letters)}, letter_int: {letter_int}")
        letter = letters[letter_int]
        try:
            letter.click()
        except Exception as e:
            logger.critical(e)
            return
        logger.debug(f"Letter clicked")
        # Wait for letter content to appear instead of fixed 1s delay
        self.page.wait_for_selector(f"xpath={signature_xpath}", timeout=10000)
        self.scroll_down()

        if self.check_for_photos():
            amount = self.photo_amount()
            next_button = self.page.locator(f"xpath={next_button_xpath}").first
            logger.info("Loading images...")
            for _ in range(amount - 1):
                try:
                    next_button.click()
                except Exception as e:
                    logger.error(e)
                self.page.wait_for_timeout(300)
            logger.info("Waiting for images to load")
            self.image_load_check()

        self.make_pdf(letter_count, penpal_dir, penpal)
        logger.info("Going back to letters...")

    def load_and_print(self, penpal, progress_callback):
        """Download all new letters for a given penpal."""
        logger.info("Waiting until current URL matches penpal URL")
        while re.search(current_url_regex, self.page.url).group(2) != "friend":
            self.page.wait_for_timeout(100)
        logger.info(f"Penpal {penpal} selected!")

        # Wait for letters and scroll to load all
        self.page.wait_for_selector(f"xpath={letter_xpath}", timeout=30000)
        logger.info("Loading letters")
        self.scroll_down()
        logger.info("Letters loaded!")

        # Create penpal directory
        penpal_dir = mk_penpal_dir(penpal)

        # Check for existing letters via PDF metadata
        logger.info("Checking for existing letters")
        existing_letters = []
        for penpal_file in os.listdir(penpal_dir):
            if penpal_file.endswith(".pdf"):
                penpal_file_path = os.path.join(penpal_dir, penpal_file)
                meta_check = PdfReader(penpal_file_path).Info
                for key, value in meta_check.items():
                    if key == "/Letter":
                        existing_letters.append(int(value))

        letters = self.page.locator(f"xpath={letter_xpath}").all()
        amount_letters = len(letters)
        current_letter_int = amount_letters
        logger.debug(f"Letter count: {amount_letters}")

        logger.info("Beginning letter download process")
        for index in range(amount_letters):
            progress_callback(amount_letters, index + 1, penpal)
            if current_letter_int in existing_letters:
                logger.info(f"Letter {current_letter_int} already exists! Skipping...")
                current_letter_int -= 1
            else:
                logger.info(f"Opening letter {current_letter_int}")
                self.open_letter(index, current_letter_int, penpal_dir, penpal)
                logger.info(f"Letter {current_letter_int} finished processing")
                current_letter_int -= 1
                try:
                    self.page.locator(f"xpath={back_button_xpath}").first.click()
                    # Wait for letter list to reappear instead of fixed 2s delay
                    self.page.wait_for_selector(f"xpath={letter_xpath}", timeout=10000)
                except Exception as e:
                    logger.critical(e)
        logger.info(f"{amount_letters} letters successfully processed!")

    def select_penpal(self, penpal_index, penpal_name, progress_callback):
        """Click a penpal and download their letters."""
        logger.info(f"Selecting penpal: {penpal_name}")
        # Wait for penpal list to load before accessing by index
        self.page.wait_for_selector(f"xpath={penpals_xpath}", timeout=30000)
        self.dismiss_popups()
        penpals_elements = self.page.locator(f"xpath={penpals_xpath}").all()
        if penpal_index >= len(penpals_elements):
            logger.critical(f"Penpal index {penpal_index} out of range (found {len(penpals_elements)} penpals)")
            return
        try:
            penpals_elements[penpal_index].click()
        except Exception as e:
            logger.critical(e)
            return
        logger.debug(f"Clicked {penpal_name}")
        self.load_and_print(penpal_name, progress_callback)

    def close(self):
        """Shut down browser and Playwright."""
        logger.info("Closing browser")
        if self.context:
            try:
                self.context.close()
            except Exception as e:
                logger.error(f"Error closing context: {e}")
        if self.playwright:
            try:
                self.playwright.stop()
            except Exception as e:
                logger.error(f"Error stopping Playwright: {e}")
        self.context = None
        self.page = None
        self.playwright = None
