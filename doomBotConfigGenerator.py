from configparser import ConfigParser

config_object = ConfigParser()

config_object['BOT_SETTINGS'] = {
    "libraryPath": r"C:\Users\oaris\PycharmProjects\DoomBot\music",
    "recent_songs_cap": "5"
}

with open('config.ini', 'w') as conf:
    config_object.write(conf)
