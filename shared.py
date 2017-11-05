# Shared Assets and Data
import utilities
from default import *
import pygame as pg


class Global:

    def __init__(self):
        self._global_ticker = None
        self._global_bus = None
        self._log_message = True
        self._logger = utilities.Logger()
        self._images = {}
        self.game = None

    @property
    def bus(self):
        if self._global_bus is None:
            self._global_bus = utilities.Publisher()
            if self._log_message:
                self._global_bus.register(self._logger, function_to_call=self._logger.handle_published_message)
        return self._global_bus

    @property
    def ticker(self):
        if self._global_ticker is None:
            self._global_ticker = utilities.Ticker()
            print("Ticker initialized")
        return self._global_ticker

    @property
    def logger(self):
        if self._log_message:
            return self._logger
        else:
            return utilities.EmptyLogger()

    def load_images(self):
        if self._images is None or self._images == {}:
            self._images = utilities.load_all_images()

    def clean_before_save(self):
        """
        Clean the dictionary
        This is mandatory before saving to a file
        :return:
        """
        self._images = None

    def img(self, image_key):
        if image_key not in self._images:
            self.logger.error("Key [" + image_key + "] not in image dictionary")
            surface = pg.Surface(TILESIZE_SCREEN)
            surface.fill(RED)
            return surface
        else:
            return self._images[image_key]


GLOBAL = Global()