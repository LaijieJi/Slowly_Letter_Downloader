import os
import logging
import threading
from os.path import exists
from itertools import count, cycle

import customtkinter
import tkinter as tk
from PIL import ImageTk, Image
import pyglet

from utils import (
    dir_path, download_path, interface_path, settings_button_image_path,
    slowly_bg, slowly_fg, slowly_yellow, logger,
)
from browser import BrowserManager


class App(customtkinter.CTk):
    WIDTH = 960
    HEIGHT = 720

    customtkinter.set_appearance_mode("System")
    customtkinter.set_default_color_theme("blue")

    def __init__(self):
        super().__init__()

        # Load fonts after Tk init to avoid NSApplication conflict with pyglet
        font_path = os.path.join(dir_path, "interface", "fonts")
        if not exists(font_path):
            font_path = os.path.join(dir_path, "fonts")
        for font_file in ["potra.ttf", "stone.ttf", "Botterill Signature.ttf",
                           "EnchantedPrairieDog.ttf", "typewriter.ttf"]:
            try:
                pyglet.font.add_file(os.path.join(font_path, font_file))
            except Exception as e:
                logger.warning(f"Could not load font {font_file}: {e}")

        self.loading_circle_loaded = False
        self.penpals = []
        self.check_var_dict = {}
        self.browser_manager = BrowserManager()

        self.title("Slowly Letter Downloader")
        self.geometry(f"{App.WIDTH}x{App.HEIGHT}")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        try:
            self.iconbitmap(os.path.join(interface_path, "SLD_icon.ico"))
        except tk.TclError:
            pass  # .ico not supported on this platform

        self.typewriter_font = "Mom\u00b4sTypewriter"

        # ============ create frames ============
        self.frame_left_scrollbar_width = 20
        self.frame_left_width = App.WIDTH // 3
        self.frame_right_width = App.WIDTH - self.frame_left_width

        self.frame_top = customtkinter.CTkFrame(master=self, height=100)
        self.frame_top.pack(anchor="n", fill="x")

        self.frame_left = customtkinter.CTkFrame(master=self, width=self.frame_left_width)
        self.frame_left.pack(side="left", fill="both")

        self.frame_bottom = customtkinter.CTkFrame(
            master=self, width=self.frame_right_width, height=100,
            fg_color=slowly_bg, bg_color=slowly_bg,
        )
        self.frame_bottom.pack(side="bottom", fill="x")

        self.frame_right = customtkinter.CTkFrame(master=self, width=self.frame_right_width)
        self.frame_right.pack(anchor="e", expand=1, fill="both")

        # Penpals title frame
        self.frame_left_penpals_title = customtkinter.CTkFrame(master=self.frame_left)
        self.frame_left_penpals_title.pack(side="top", expand=0, anchor="n")

        # Login state frames
        self.frame_right_login = customtkinter.CTkFrame(
            master=self.frame_right, width=self.frame_right_width,
        )
        self.frame_right_login.pack(expand=1, fill="both")

        self.frame_bottom_login = customtkinter.CTkFrame(
            master=self.frame_bottom, fg_color=slowly_bg, bg_color=slowly_bg,
        )
        self.frame_bottom_login.pack(anchor="s", side="bottom")

        self.frame_left_login = customtkinter.CTkFrame(
            master=self.frame_left, width=self.frame_left_width,
            fg_color=slowly_fg, bg_color=slowly_fg,
        )
        self.frame_left_login.pack(side="left", fill="both")

        # Progress state frames
        self.frame_right_progress = customtkinter.CTkFrame(master=self.frame_right)

        self.frame_bottom_progress_l = customtkinter.CTkFrame(
            master=self.frame_bottom, fg_color=slowly_bg, bg_color=slowly_bg,
        )
        self.frame_bottom_progress_r = customtkinter.CTkFrame(
            master=self.frame_bottom, fg_color=slowly_bg, bg_color=slowly_bg,
        )
        self.frame_left_progress = customtkinter.CTkFrame(
            master=self.frame_left,
            width=self.frame_left_width - self.frame_left_scrollbar_width,
            fg_color=slowly_fg, bg_color=slowly_fg,
        )

        # Loading state frame
        self.frame_right_loading = customtkinter.CTkFrame(master=self.frame_right)

        # ============ frame_top ============
        self.app_title = customtkinter.CTkLabel(
            master=self.frame_top,
            text="Slowly Letter Downloader",
            font=(self.typewriter_font, 45),
        )
        self.app_title.pack(anchor="center", pady=25)

        # ============ frame_bottom ============
        # Login frame
        logger.debug(f"settings_button.png exists? {exists(settings_button_image_path)}")
        self.settings_button_image = customtkinter.CTkImage(
            Image.open(settings_button_image_path), size=(30, 30),
        )

        self.open_settings_button = customtkinter.CTkButton(
            master=self.frame_bottom_login,
            image=self.settings_button_image, text="",
            fg_color=("#F7F7F7", "#1b1d24"), height=30, width=30,
            command=self.settings_popup,
        )
        self.open_settings_button.grid(row=0, column=0, pady=20, padx=20, sticky="w")

        # Progress frame buttons
        self.run_button = customtkinter.CTkButton(
            master=self.frame_bottom_progress_r,
            text="Run", font=(self.typewriter_font, 20),
            text_color="#000000", fg_color=slowly_yellow,
            command=self.run_button_click,
        )
        self.run_button.grid(row=0, column=2, columnspan=3, pady=20, padx=20, sticky="se")

        self.select_all_button = customtkinter.CTkButton(
            master=self.frame_bottom_progress_r,
            text="Select All", font=(self.typewriter_font, 20),
            text_color="#000000", fg_color=slowly_yellow,
            command=self.select_all_button_event,
        )
        self.select_all_button.grid(row=0, column=1, columnspan=1, pady=20, padx=20, sticky="sw")

        self.open_settings = customtkinter.CTkButton(
            master=self.frame_bottom_progress_l,
            image=self.settings_button_image, text="",
            fg_color=("#F7F7F7", "#1b1d24"), height=30, width=30,
            command=self.settings_popup,
        )
        self.open_settings.grid(row=0, column=0, pady=18, padx=20, sticky="w")

        # ============ frame_left ============
        self.penpal_label = customtkinter.CTkLabel(
            master=self.frame_left_penpals_title,
            text="Penpals", font=(self.typewriter_font, 30),
            width=self.frame_left_width - 20,
        )
        self.penpal_label.grid(row=1, column=0, pady=12, padx=12)

        # Scrollable penpal list (canvas + scrollbar)
        self.canvas_left_progress = customtkinter.CTkCanvas(
            master=self.frame_left_progress,
            width=self.frame_left_width - self.frame_left_scrollbar_width,
        )
        self.canvas_left_progress.pack(side="left", fill="both")

        self.left_scrollbar_progress = customtkinter.CTkScrollbar(
            master=self.frame_left_progress,
            orientation="vertical",
            command=self.canvas_left_progress.yview,
            width=self.frame_left_scrollbar_width,
        )
        self.left_scrollbar_progress.pack(side="left", fill="y")

        self.canvas_left_progress.configure(yscrollcommand=self.left_scrollbar_progress.set)
        self.canvas_left_progress.bind(
            "<Configure>", lambda e: self.canvas_left_progress.configure(
                scrollregion=self.scroll_bbox()))

        self.frame_left_second_progress = customtkinter.CTkFrame(
            master=self.canvas_left_progress,
            width=self.frame_left_width - self.frame_left_scrollbar_width,
            fg_color=slowly_fg, bg_color=slowly_fg,
        )

        self.canvas_left_progress.create_window(
            (0, 0), window=self.frame_left_second_progress,
            anchor="nw", width=self.frame_left_width,
        )

        self.frame_left_second_progress.grid_rowconfigure(0, minsize=10)

        # ============ frame_right ============
        # Login screen with login button
        self.frame_right_login.grid_rowconfigure((0, 3), weight=1)
        self.frame_right_login.grid_columnconfigure(0, weight=1)

        self.login_instruction = customtkinter.CTkLabel(
            master=self.frame_right_login,
            text="Click 'Login' to open a browser\nand scan your QR code",
            font=(self.typewriter_font, 25),
        )
        self.login_instruction.grid(row=1, column=0, sticky="nsew")

        self.login_button = customtkinter.CTkButton(
            master=self.frame_right_login,
            text="Login", font=(self.typewriter_font, 25),
            text_color="#000000", fg_color=slowly_yellow,
            command=self.login_button_event,
        )
        self.login_button.grid(row=2, column=0, pady=20)

        # Progress idle label
        self.progress_bar_title = customtkinter.CTkLabel(
            master=self.frame_right_progress,
            text="Select penpal(s)",
            font=("Roboto Medium", 30),
        )
        self.progress_bar_title.place(x=(self.frame_right_width // 2), y=260, anchor="center")

        # Loading penpals screen
        self.loading_frame_init()

    # ============ GIF animation ============

    def load_gif(self, gif_frame):
        self.selected_gif_frame = gif_frame
        gif_path = os.path.join(interface_path, 'loading_circle.gif')
        if not exists(gif_path):
            gif_frame.configure(text="...")
            self.gif_frames = None
            self.loading_circle_loaded = True
            return
        gif = Image.open(gif_path)
        frames = []
        try:
            for i in count(1):
                frames.append(ImageTk.PhotoImage(gif.copy()))
                gif.seek(i)
        except EOFError:
            pass
        self.gif_frames = cycle(frames[1:])
        try:
            self.gif_delay = gif.info['duration']
        except Exception:
            self.gif_delay = 100
        self.loading_circle_loaded = True
        self.next_gif_frame()

    def next_gif_frame(self):
        if self.gif_frames:
            self.selected_gif_frame.configure(image=next(self.gif_frames))
            self.after(self.gif_delay, self.next_gif_frame)

    def unload_gif(self):
        self.loading_gif_label.configure(image="", text="")
        self.gif_frames = None
        self.loading_circle_loaded = False

    # ============ Loading frame ============

    def loading_frame_init(self):
        self.frame_right_loading.grid_rowconfigure((0, 3), weight=1)
        self.frame_right_loading.grid_columnconfigure(0, weight=1)

        self.loading_title = customtkinter.CTkLabel(
            master=self.frame_right_loading,
            text="Loading penpals\nPlease wait...",
            font=(self.typewriter_font, 30),
        )
        self.loading_title.grid(row=1, column=0, sticky='nsew')

        self.loading_gif_label = customtkinter.CTkLabel(
            master=self.frame_right_loading, text="",
        )
        self.loading_gif_label.grid(row=2, column=0, sticky='nsew')

    def loading_frame_load(self):
        self.frame_right_loading.pack(expand=1, fill="both")
        self.load_gif(self.loading_gif_label)

    def loading_frame_unload(self):
        self.unload_gif()
        self.frame_right_loading.forget()

    # ============ Settings ============

    def settings_popup(self):
        self.settings_window = customtkinter.CTkToplevel(self)
        self.settings_window.title("Settings")
        self.settings_window.geometry("400x200")

        self.settings_popup_label = customtkinter.CTkLabel(
            self.settings_window, text="SLD Settings",
            font=(self.typewriter_font, 25),
        )
        self.settings_popup_label.pack(anchor="center", side="top", pady=20)

        self.appearance_selector = customtkinter.CTkOptionMenu(
            master=self.settings_window,
            values=["System", "Light", "Dark"],
            command=self.change_appearance_mode,
            font=(self.typewriter_font, 20),
            text_color="#000000",
        )
        self.appearance_selector.pack(anchor="center", pady=20)

    def change_appearance_mode(self, new_appearance_mode):
        customtkinter.set_appearance_mode(new_appearance_mode)

    # ============ Scrollbar helper ============

    def scroll_bbox(self):
        bbox = self.canvas_left_progress.bbox("all")
        bbox_mod = list(bbox)
        bbox_mod[1] = 2
        bbox_mod[3] = bbox_mod[3] - 2
        return bbox_mod

    # ============ Login flow ============

    def login_button_event(self):
        """User clicks Login — opens a headed Playwright browser in a thread."""
        self.login_button.configure(state="disabled")
        self.login_instruction.configure(
            text="Scan your QR code in the\nbrowser window that just opened",
        )
        thread = threading.Thread(target=self._do_login, daemon=True)
        thread.start()

    def _do_login(self):
        """Background thread: run headed login, then start scraping."""
        self.browser_manager.start_login(
            on_login_detected=lambda: self.after(0, self._on_login_complete),
        )

    def _on_login_complete(self):
        """Called on main thread when login is detected."""
        self.frame_right_login.forget()
        self.loading_frame_load()
        self.frame_right.update()
        thread = threading.Thread(target=self._do_scraping_init, daemon=True)
        thread.start()

    def _do_scraping_init(self):
        """Background thread: start headless scraping, fetch penpals, then close."""
        self.browser_manager.start_scraping()
        if not self.browser_manager.verify_login():
            self.browser_manager.close()
            self.after(0, self._login_failed)
            return
        penpals = self.browser_manager.get_penpals()
        self.browser_manager.close()
        self.after(0, lambda: self.penpal_checkboxes(penpals))

    def _login_failed(self):
        """Return to login screen if session didn't persist."""
        logger.info("Login not detected in headless mode")
        self.loading_frame_unload()
        self.frame_right_login.pack(expand=1, fill="both")
        self.login_button.configure(state="normal")
        self.login_instruction.configure(
            text="Login failed. Click 'Login' to try again.",
        )

    # ============ Penpal checkboxes ============

    def penpal_checkboxes(self, penpals):
        self.penpals = penpals
        logger.info("Loading penpals to GUI...")
        for index, penpal in enumerate(penpals):
            self.check_var_dict[index] = customtkinter.IntVar()
            checkbox = customtkinter.CTkCheckBox(
                master=self.frame_left_second_progress,
                text=f"{penpal}",
                font=("Roboto Medium", 20),
                variable=self.check_var_dict[index],
            )
            checkbox.grid(row=(index + 2), column=0, pady=5, padx=20, sticky="nw")
        self.frame_left_second_progress.update()
        self.switch_to_progress()

    def select_all_button_event(self):
        self.select_all_button.destroy()
        self.deselect_all_button = customtkinter.CTkButton(
            master=self.frame_bottom_progress_r,
            text="Deselect All", font=(self.typewriter_font, 20),
            text_color="#000000", fg_color=slowly_yellow,
            command=self.deselect_all_button_event,
        )
        self.deselect_all_button.grid(row=0, column=1, columnspan=1, pady=20, padx=20, sticky="sw")
        for index in self.check_var_dict:
            self.check_var_dict[index].set(1)
        self.frame_left.update()
        self.frame_bottom_progress_r.update()
        self.frame_bottom.update()

    def deselect_all_button_event(self):
        self.deselect_all_button.destroy()
        self.select_all_button = customtkinter.CTkButton(
            master=self.frame_bottom_progress_r,
            text="Select All", font=(self.typewriter_font, 20),
            text_color="#000000", fg_color=slowly_yellow,
            command=self.select_all_button_event,
        )
        self.select_all_button.grid(row=0, column=1, columnspan=1, pady=20, padx=20, sticky="sw")
        for index in self.check_var_dict:
            self.check_var_dict[index].set(0)
        self.frame_left.update()
        self.frame_bottom_progress_r.update()
        self.frame_bottom.update()

    # ============ Button state management ============

    def deactivate_buttons(self):
        self.run_button.configure(state="disabled")
        try:
            self.select_all_button.configure(state="disabled")
        except Exception:
            self.deselect_all_button.configure(state="disabled")

    def reactivate_buttons(self):
        self.run_button.configure(state="normal")
        try:
            self.select_all_button.configure(state="normal")
        except Exception:
            self.deselect_all_button.configure(state="normal")

    # ============ Run / Download ============

    def run_button_click(self):
        logger.info("Run button pressed")
        self.deactivate_buttons()
        self.run_button_event()

    def run_button_event(self):
        if not exists(download_path):
            os.mkdir(download_path)

        try:
            self.frame_right_progress_soft_reset()
        except Exception as e:
            logger.error(f"Error in frame_right_progress_soft_reset: {e}")

        thread = threading.Thread(target=self._download_selected_penpals, daemon=True)
        thread.start()

    def _download_selected_penpals(self):
        """Background thread: open browser, download letters, then close."""
        self.browser_manager.start_scraping()
        if not self.browser_manager.verify_login():
            logger.critical("Session expired, cannot download")
            self.browser_manager.close()
            self.after(0, self.run_button_end)
            return
        for index in self.check_var_dict:
            if self.check_var_dict[index].get() == 1:
                logger.info(f"Loading {self.penpals[index]}")
                self.browser_manager.select_penpal(
                    index,
                    self.penpals[index],
                    progress_callback=lambda total, current, name:
                        self.after(0, lambda t=total, c=current, n=name:
                            self.set_progress_bar(t, c, n)),
                )
        self.browser_manager.close()
        self.after(0, self.run_button_end)

    def run_button_end(self):
        logger.debug("Finished downloading")
        try:
            self.frame_right_progress_reset()
        except Exception as e:
            logger.error(f"Error in frame_right_progress_reset: {e}")

        try:
            self.frame_right_progress_idle()
        except Exception as e:
            logger.error(f"Error in frame_right_progress_idle: {e}")

        self.reactivate_buttons()
        self.loading_circle_loaded = False

    # ============ Progress UI ============

    def set_progress_bar(self, letter_amount, current_letter, penpal):
        self.frame_right_progress.grid_rowconfigure((0, 4), weight=1)
        self.frame_right_progress.grid_columnconfigure(0, weight=1)

        self.progress_bar_title = customtkinter.CTkLabel(
            master=self.frame_right_progress,
            text=f"{penpal}",
            font=("Roboto Medium", 30),
        )
        self.progress_bar_title.grid(row=1, column=0, sticky='nsew')

        if not self.loading_circle_loaded:
            self.progress_circle = customtkinter.CTkLabel(
                master=self.frame_right_progress, text="",
            )
        self.progress_circle.grid(row=2, column=0, sticky='nsew')

        self.progress_bar_footer = customtkinter.CTkLabel(
            master=self.frame_right_progress,
            text=f"Letter {current_letter} out of {letter_amount}",
            font=("Roboto Medium", 25),
        )
        self.progress_bar_footer.grid(row=3, column=0, sticky='nsew')

        self.frame_right.update()
        if not self.loading_circle_loaded:
            self.load_gif(self.progress_circle)

    def frame_right_progress_soft_reset(self):
        try:
            self.frame_right_progress.destroy()
        except Exception as e:
            logger.error(e)
        self.frame_right_progress = customtkinter.CTkFrame(master=self.frame_right)
        self.frame_right_progress.pack(expand=1, fill="both")

    def frame_right_progress_reset(self):
        try:
            self.frame_right_progress.destroy()
        except Exception as e:
            logger.error(e)
        self.frame_right_progress = customtkinter.CTkFrame(master=self.frame_right)
        self.frame_right_progress.pack(expand=1, fill="both")
        for index in self.check_var_dict:
            if self.check_var_dict[index].get() == 1:
                self.check_var_dict[index].set(0)
        self.frame_left.update()

    def frame_right_progress_idle(self):
        self.progress_bar_title = customtkinter.CTkLabel(
            master=self.frame_right_progress,
            text="Select penpal(s)",
            font=("Roboto Medium", 30),
        )
        self.progress_bar_title.place(x=(self.frame_right_width // 2), y=260, anchor="center")

    # ============ State transitions ============

    def switch_to_progress(self):
        logger.info("Switching to progress view")
        self.frame_bottom_login.forget()
        self.loading_frame_unload()
        self.frame_left_login.forget()
        self.frame_bottom_progress_l.pack(anchor="se", side="left")
        self.frame_bottom_progress_r.pack(anchor="sw", side="right")
        self.frame_right_progress.pack(expand=1, fill="both")
        self.frame_left_progress.pack(side="left", fill="both")
        self.frame_bottom.update()
        self.frame_right.update()
        self.frame_left.update()

    # ============ Cleanup ============

    def on_closing(self, event=0):
        logger.info("Shutting down")
        self.browser_manager.close()
        self.destroy()
        os._exit(0)


def main():
    logger.info("Opening GUI")
    app = App()
    app.mainloop()


if __name__ == '__main__':
    main()
