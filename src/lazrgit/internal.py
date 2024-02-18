#!/usr/bin/env python

import configparser
import os


class Context:
    def __init__(self):
        config_file_path = os.path.expanduser("~/.config/lazrgit/config")
        self.config = configparser.ConfigParser()
        self.config.read(config_file_path)


context = Context()
