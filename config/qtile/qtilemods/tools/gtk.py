import configparser
import os


def set_gtk_settings(**kwargs):
    for gtk_ver in (3, 4):
        settings = configparser.ConfigParser()
        settings_path = os.path.expanduser(f'~/.config/gtk-{gtk_ver}.0/settings.ini')
        settings_dir = os.path.dirname(settings_path)

        if os.path.exists(settings_path):
            settings.read(settings_path)

        if 'Settings' not in settings:
            settings.add_section('Settings')

        for k, v in kwargs.items():
            settings['Settings'][k] = str(v)

        if not os.path.exists(settings_dir):
            os.makedirs(settings_dir)

        with open(settings_path, 'w') as f:
            settings.write(f)
