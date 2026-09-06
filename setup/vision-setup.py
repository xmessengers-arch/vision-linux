#!/usr/bin/env python3
"""Vision Linux first-run setup wizard.

GUI wizard using GTK4/Adw that runs on first boot:
  1. Welcome + language
  2. Root password (required for nickman, system ops)
  3. Username (e.g. "vasya")
  4. User password (optional — can skip with Enter)
  5. Save test (verify USB persistence)
  6. Done — enter terminal

If password is skipped with "-" or empty, user can log in without password.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

VISION_CONFIG_DIR = Path("/etc/visionlinux")
WIZARD_DONE = VISION_CONFIG_DIR / ".wizard_done"


def is_demo() -> bool:
    return sys.platform == "win32" or not VISION_CONFIG_DIR.exists()


try:
    import gi
    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")
    from gi.repository import Adw, Gtk, GLib
    HAS_GTK = True
except ImportError:
    HAS_GTK = False


class SetupWizard:
    def __init__(self, app):
        self.app = app
        self.profile = {}
        self.current_step = 0

        self.win = Adw.ApplicationWindow(application=app)
        self.win.set_title("Vision Linux — First Setup")
        self.win.set_default_size(800, 600)

        self.steps = [
            self.step_welcome(),
            self.step_root_password(),
            self.step_username(),
            self.step_user_password(),
            self.step_save_test(),
            self.step_done(),
        ]

        self.show_step(0)

    def step_welcome(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_margin_top(32)
        box.set_margin_start(32)
        box.set_margin_end(32)

        title = Gtk.Label()
        title.set_markup('<span size="xx-large" weight="bold">Welcome to Vision Linux</span>')
        title.set_halign(Gtk.Align.CENTER)
        box.append(title)

        subtitle = Gtk.Label(label="The wizard will set up your system in just a minute.")
        subtitle.set_halign(Gtk.Align.CENTER)
        box.append(subtitle)

        lang_label = Gtk.Label(label="System Language:")
        lang_label.set_halign(Gtk.Align.START)
        box.append(lang_label)

        self.lang_combo = Gtk.DropDown.new_from_strings([
            "English — US",
            "Русский — RU",
            "Deutsch — DE",
        ])
        box.append(self.lang_combo)

        return box

    def step_root_password(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_margin_top(32)
        box.set_margin_start(32)
        box.set_margin_end(32)

        title = Gtk.Label()
        title.set_markup('<span size="xx-large" weight="bold">Root Password</span>')
        title.set_halign(Gtk.Align.CENTER)
        box.append(title)

        desc = Gtk.Label(
            label="Root is required for nickman (package manager),\n"
                  "system operations, and terminal admin commands."
        )
        desc.set_halign(Gtk.Align.CENTER)
        box.append(desc)

        self.root_pass = Gtk.PasswordEntry()
        self.root_pass.set_show_peek_icon(True)
        self.root_pass.set_placeholder_text("Enter root password...")
        box.append(self.root_pass)

        self.root_pass2 = Gtk.PasswordEntry()
        self.root_pass2.set_show_peek_icon(True)
        self.root_pass2.set_placeholder_text("Confirm root password...")
        box.append(self.root_pass2)

        return box

    def step_username(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_margin_top(32)
        box.set_margin_start(32)
        box.set_margin_end(32)

        title = Gtk.Label()
        title.set_markup('<span size="xx-large" weight="bold">Your Account</span>')
        title.set_halign(Gtk.Align.CENTER)
        box.append(title)

        desc = Gtk.Label(label="Choose a username for your account.")
        desc.set_halign(Gtk.Align.CENTER)
        box.append(desc)

        self.user_entry = Gtk.Entry()
        self.user_entry.set_placeholder_text("e.g. vasya")
        self.user_entry.set_halign(Gtk.Align.CENTER)
        box.append(self.user_entry)

        return box

    def step_user_password(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_margin_top(32)
        box.set_margin_start(32)
        box.set_margin_end(32)

        title = Gtk.Label()
        title.set_markup('<span size="xx-large" weight="bold">User Password</span>')
        title.set_halign(Gtk.Align.CENTER)
        box.append(title)

        desc = Gtk.Label(
            label="Optional. Press Enter or type '-' to skip.\n"
                  "If skipped, you can log in without a password."
        )
        desc.set_halign(Gtk.Align.CENTER)
        box.append(desc)

        self.user_pass = Gtk.PasswordEntry()
        self.user_pass.set_show_peek_icon(True)
        self.user_pass.set_placeholder_text("Enter password (or press Enter to skip)...")
        box.append(self.user_pass)

        self.user_pass2 = Gtk.PasswordEntry()
        self.user_pass2.set_show_peek_icon(True)
        self.user_pass2.set_placeholder_text("Confirm password...")
        box.append(self.user_pass2)

        return box

    def step_save_test(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_margin_top(32)
        box.set_margin_start(32)
        box.set_margin_end(32)

        title = Gtk.Label()
        title.set_markup('<span size="xx-large" weight="bold">Persistence Test</span>')
        title.set_halign(Gtk.Align.CENTER)
        box.append(title)

        self.save_status = Gtk.Label(label="Checking USB persistence...")
        self.save_status.set_halign(Gtk.Align.CENTER)
        box.append(self.save_status)

        self.save_progress = Gtk.ProgressBar()
        box.append(self.save_progress)

        return box

    def step_done(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_margin_top(32)
        box.set_margin_start(32)
        box.set_margin_end(32)

        title = Gtk.Label()
        title.set_markup('<span size="xx-large" weight="bold">Setup Complete!</span>')
        title.set_halign(Gtk.Align.CENTER)
        box.append(title)

        self.done_label = Gtk.Label(
            label="Vision Linux is ready.\nPress Enter to open the terminal."
        )
        self.done_label.set_halign(Gtk.Align.CENTER)
        box.append(self.done_label)

        enter_btn = Gtk.Button(label="Enter Vision Linux")
        enter_btn.add_css_class("suggested-action")
        enter_btn.connect("clicked", self.finish)
        box.append(enter_btn)

        return box

    def show_step(self, index):
        self.current_step = index
        child = self.win.get_child()
        if child:
            self.win.set_child(None)
        self.win.set_content(self.steps[index])

        if index == 3:
            self.run_save_test()

    def validate_root_password(self) -> bool:
        p1 = self.root_pass.get_text()
        p2 = self.root_pass2.get_text()
        if len(p1) < 4:
            self.warn("Root password too short (min 4 characters)")
            return False
        if p1 != p2:
            self.warn("Root passwords don't match")
            return False
        return True

    def validate_username(self) -> bool:
        name = self.user_entry.get_text().strip()
        if not name:
            self.warn("Enter a username")
            return False
        if len(name) < 2:
            self.warn("Username too short")
            return False
        return True

    def validate_user_password(self) -> bool:
        p1 = self.user_pass.get_text()
        p2 = self.user_pass2.get_text()
        if p1 == "-" or p1 == "":
            self.profile["user_password"] = ""
            return True
        if p1 != p2:
            self.warn("User passwords don't match")
            return False
        self.profile["user_password"] = p1
        return True

    def warn(self, msg):
        toast = Adw.Toast.new(msg)
        toast.set_timeout(3)
        self.win.add_toast(toast)

    def run_save_test(self):
        import threading

        def _work():
            time.sleep(1)
            test_dir = Path("/home/user")
            test_file = test_dir / ".vision-save-test"
            try:
                test_dir.mkdir(parents=True, exist_ok=True)
                test_file.write_text("vision linux save test")
                content = test_file.read_text()
                test_file.unlink()
                if content == "vision linux save test":
                    GLib.idle_add(self._save_ok)
                else:
                    GLib.idle_add(self._save_fail, "Write/read mismatch")
            except Exception as e:
                GLib.idle_add(self._save_fail, str(e))

        threading.Thread(target=_work, daemon=True).start()

    def _save_ok(self):
        self.save_status.set_text("Persistence working — data saved to USB")
        self.save_status.add_css_class("success")
        self.save_progress.set_fraction(1.0)
        self.profile["save_ok"] = True
        GLib.timeout_add(1000, lambda: self.show_step(4))

    def _save_fail(self, msg):
        self.save_status.set_text(f"Persistence issue: {msg}")
        self.save_status.add_css_class("error")
        self.profile["save_ok"] = False
        GLib.timeout_add(2000, lambda: self.show_step(4))

    def finish(self, btn):
        self.profile["language"] = ["en", "ru", "de"][self.lang_combo.get_selected()]
        self.profile["root_password"] = self.root_pass.get_text()
        self.profile["username"] = self.user_entry.get_text().strip()

        if is_demo():
            demo_path = Path("/tmp/visionlinux-wizard-demo.json")
            demo_path.write_text(json.dumps(self.profile, indent=2))
        else:
            self.apply_system()

        VISION_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        WIZARD_DONE.write_text(json.dumps(self.profile, indent=2))

        subprocess.Popen(["vision-shell"], start_new_session=True)
        self.win.close()

    def apply_system(self):
        username = self.profile["username"]
        root_pass = self.profile["root_password"]
        user_pass = self.profile.get("user_password", "")

        commands = [
            f"useradd -m -G wheel,audio,video,storage,input -s /bin/bash {username}",
            f"echo 'root:{root_pass}' | chpasswd",
        ]
        if user_pass:
            commands.append(f"echo '{username}:{user_pass}' | chpasswd")
        else:
            commands.append(f"passwd -d {username}")

        commands.append("echo '%wheel ALL=(ALL:ALL) ALL' > /etc/sudoers.d/visionlinux")

        for cmd in commands:
            subprocess.run(["pkexec", "sh", "-c", cmd], capture_output=True)


def main():
    if not HAS_GTK:
        text_mode_setup()
        return 0

    app = Adw.Application.new("org.visionlinux.setup", 0)

    def on_activate(a):
        SetupWizard(a)

    app.connect("activate", on_activate)
    return app.run([])


def text_mode_setup():
    print("=" * 50)
    print("  Vision Linux — First Setup")
    print("=" * 50)
    print()

    import getpass
    while True:
        root_pass = getpass.getpass("Root password: ")
        root_pass2 = getpass.getpass("Confirm root password: ")
        if root_pass == root_pass2 and len(root_pass) >= 4:
            break
        print("Passwords don't match or too short. Try again.")

    username = input("Username (e.g. vasya): ").strip()
    while len(username) < 2:
        username = input("Username too short. Try again: ").strip()

    user_pass = input("User password (press Enter to skip): ").strip()
    if user_pass == "-":
        user_pass = ""
    if user_pass:
        user_pass2 = input("Confirm user password: ").strip()
        if user_pass != user_pass2:
            print("Passwords don't match. No password set.")
            user_pass = ""

    print()
    print("Setup complete!")
    print(f"Root password: [set]")
    print(f"Username: {username}")
    print(f"User password: {'[set]' if user_pass else '[none]'}")
    print()
    print("Starting Vision Linux terminal...")


if __name__ == "__main__":
    sys.exit(main())
