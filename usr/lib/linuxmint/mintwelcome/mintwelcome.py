#!/usr/bin/python3
import apt
import gettext
import gi
import os
import platform
import subprocess
import locale
gi.require_version("Gtk", "3.0")
gi.require_version("XApp", "1.0")
from gi.repository import Gtk, XApp

NORUN_FLAG = os.path.expanduser("~/.linuxmint/mintwelcome/norun.flag")

# i18n
gettext.install("mintwelcome", "/usr/share/linuxmint/locale")
from locale import gettext as _
locale.bindtextdomain("mintwelcome", "/usr/share/linuxmint/locale")
locale.textdomain("mintwelcome")

class MintWelcome():

    def __init__(self):
        builder = Gtk.Builder()
        builder.set_translation_domain("mintwelcome")
        builder.add_from_file('/usr/share/linuxmint/mintwelcome/mintwelcome.ui')

        window = builder.get_object("main_window")
        window.set_icon_name("mintwelcome")
        window.set_position(Gtk.WindowPosition.CENTER)
        window.connect("destroy", Gtk.main_quit)

        with open("/etc/linuxmint/info") as f:
            config = dict([line.strip().split("=") for line in f])
        codename = config['CODENAME'].capitalize()
        edition = config['EDITION'].replace('"', '')
        release = config['RELEASE']
        desktop = config['DESKTOP']
        release_notes = config['RELEASE_NOTES_URL']
        new_features = config['NEW_FEATURES_URL']
        architecture = "64-bit"
        if platform.machine() != "x86_64":
            architecture = "32-bit"

        # distro-specific
        dist_name = "Linux Mint"
        if os.path.exists("/usr/share/doc/debian-system-adjustments/copyright"):
            dist_name = "LMDE"

        # Setup the labels in the Mint badge
        builder.get_object("label_version").set_text("%s %s" % (dist_name, release))
        builder.get_object("label_edition").set_text("%s %s" % (edition, architecture))

        # Action buttons
        builder.get_object("button_forums").connect("clicked", self.visit, "https://forums.linuxmint.com")
        builder.get_object("button_documentation").connect("clicked", self.visit, "https://linuxmint.com/documentation.php")
        builder.get_object("button_contribute").connect("clicked", self.visit, "https://linuxmint.com/getinvolved.php")
        builder.get_object("button_irc").connect("clicked", self.visit, "irc://irc.spotchat.org/linuxmint-help")
        builder.get_object("button_codecs").connect("clicked", self.visit, "apt://mint-meta-codecs?refresh=yes")
        builder.get_object("button_new_features").connect("clicked", self.visit, new_features)
        builder.get_object("button_release_notes").connect("clicked", self.visit, release_notes)
        builder.get_object("button_mintupdate").connect("clicked", self.launch, "mintupdate")
        builder.get_object("button_mintinstall").connect("clicked", self.launch, "mintinstall")
        builder.get_object("button_timeshift").connect("clicked", self.pkexec, "timeshift-gtk")
        builder.get_object("button_mintdrivers").connect("clicked", self.pkexec, "driver-manager")

        # Settings button depends on DE
        if os.getenv("XDG_CURRENT_DESKTOP") in ["Cinnamon", "X-Cinnamon"]:
            builder.get_object("button_settings").connect("clicked", self.launch, "cinnamon-settings")
        elif os.getenv("XDG_CURRENT_DESKTOP") == "MATE":
            builder.get_object("button_settings").connect("clicked", self.launch, "mate-control-center")
        elif os.getenv("XDG_CURRENT_DESKTOP") == "XFCE":
            builder.get_object("button_settings").connect("clicked", self.launch, "xfce4-settings-manager")
        else:
            # Hide settings
            builder.get_object("box_first_steps").remove(builder.get_object("box_settings"))

        # Hide codecs box if they're already installed
        add_codecs = False
        cache = apt.Cache()
        if "mint-meta-codecs" in cache:
            pkg = cache["mint-meta-codecs"]
            if not pkg.is_installed:
                add_codecs = True
        if not add_codecs:
            builder.get_object("box_first_steps").remove(builder.get_object("box_codecs"))

        # Hide drivers if mintdrivers is absent (LMDE)
        if not os.path.exists("/usr/bin/mintdrivers"):
            builder.get_object("box_first_steps").remove(builder.get_object("box_drivers"))

        # Hide new features page for LMDE
        if dist_name == "LMDE":
            builder.get_object("box_documentation").remove(builder.get_object("box_new_features"))

        # Construct the bottom toolbar
        box = builder.get_object("toolbar_bottom")
        checkbox = Gtk.CheckButton()
        checkbox.set_label(_("Show this dialog at startup"))
        if not os.path.exists(NORUN_FLAG):
            checkbox.set_active(True)
        checkbox.connect("toggled", self.on_button_toggled)
        box.pack_end(checkbox)

        window.set_default_size(800, 500)
        window.show_all()

    def on_button_toggled(self, button):
        if button.get_active():
            if os.path.exists(NORUN_FLAG):
                os.system("rm -rf %s" % NORUN_FLAG)
        else:
            os.system("mkdir -p ~/.linuxmint/mintwelcome")
            os.system("touch %s" % NORUN_FLAG)

    def visit(self, button, url):
        subprocess.Popen(["xdg-open", url])

    def launch(self, button, command):
        subprocess.Popen([command])

    def pkexec(self, button, command):
        subprocess.Popen(["pkexec", command])

if __name__ == "__main__":
    MintWelcome()
    Gtk.main()
