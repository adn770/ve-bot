#!/usr/bin/env python3
#
# MIT License
#
# Copyright (c) 2020 Josep Torra
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

"""
vebot

Discord bot to assist in "Vella Escola JDR"

Usage:
    vebot [options]

Options:
    -h --help             Show this message
    --token=TOKEN         Bot security token
    --version             Show version
    --log-level=LEVEL     Level of logging to produce [default: INFO]
    --log-file=PATH       Specify a file to write the log
    -v --verbose          Verbose logging (equivalent to --log-level=DEBUG)

Log levels:  DEBUG INFO WARNING ERROR CRITICAL

"""

import json
import logging
import sys
from os import path, listdir
from discord import Activity, ActivityType
from discord.ext import commands
from discord.ext.commands.errors import BotMissingPermissions, \
    MissingPermissions, \
    NotOwner, \
    MissingRequiredArgument, \
    CommandNotFound

from docopt import docopt

from lib.books import load_json_from_disk, Library

CURDIR = path.dirname(path.abspath(__file__))
TOPDIR = path.dirname(CURDIR)


class Settings():  # pylint: disable=too-many-instance-attributes
    """Application settings"""
    SETTINGS_FILE: str = path.abspath('.vebot.json')
    USER_FACING_SETTINGS: list = ['language', 'opengame', 'system', 'mode',
                                  'attributes', 'score_threshold', 'monsters']
    __filename: str
    token: str
    language: str
    opengame: str
    system: str
    mode: str
    attributes: str
    score_threshold: int
    monsters: str

    def __init__(self):
        self.token = ""
        self.language = "en"
        self.opengame = "yes"
        self.system = "ve"  # vieja escuela
        self.mode = "default"
        self.attributes = "ve"
        self.score_threshold = 60
        self.books_path = path.join(TOPDIR, 'books')
        self.monsters = "mmbecmi"
        self.load()

    @property
    def library_paths(self) -> list:
        """Computes library paths"""
        result = [self.books_path]
        for key in ['system', 'mode']:
            sub_path = path.join(self.books_path, f'{self.__dict__[key]}_{self.language}')
            if path.isdir(sub_path):
                result += [sub_path]
        logging.info("Library paths:\n%s", "\n".join(result))
        return result

    def set(self, key: str, value: any, valid_values: list = None) -> bool:
        """Changes a setting value saving it on disk too"""
        if valid_values and value not in valid_values:
            return False
        self.__dict__[key] = value
        self.save()
        return True

    def get_valid_values(self, setting: str) -> list:
        """Provides setting constrains"""
        if setting not in self.USER_FACING_SETTINGS:
            return None

        valid_values = []
        if setting == 'opengame':
            valid_values = ['yes', 'no']
        elif setting == 'system':
            valid_values = ['ve', 'ose']
        elif setting == 'attributes':
            valid_values = ['inorder', 'inorder+', 've', 'heroic']
        return valid_values

    def load(self):
        """Loads settings from specified file"""
        if not path.isfile(self.SETTINGS_FILE):
            return
        data = load_json_from_disk(self.SETTINGS_FILE)
        for (key, value) in data.items():
            self.__dict__[key] = value

    def save(self):
        """Saves json to disk"""
        with open(self.SETTINGS_FILE, 'w') as handle:
            data = dict()
            for (key, value) in self.__dict__.items():
                if not key.startswith('__'):
                    data[key] = value
            json.dump(data, handle)

    def details(self) -> str:
        """Provides a string with the settings to show at !info"""
        return f"- **language**: [{self.language}]\n" \
               f"- **opengame**: [{self.opengame}]\n" \
               f"- **system**: [{self.system}]\n" \
               f"- **mode**: [{self.mode}]\n" \
               f"- **attributes**: [{self.attributes}]\n " \
               f"- **score_threshold**: [{self.score_threshold}]\n " \
               f"- **monsters**: [{self.monsters}]\n"


class Cogs():
    """Handles the list of Cogs"""
    __COG_PATH = path.join(CURDIR, 'cogs')
    __cogs: list

    def __init__(self):
        self.reload([])

    def __is_cog(self, file: str, cog_path: str = "") -> bool:
        if not cog_path:
            cog_path = self.__COG_PATH
        return path.isfile(path.join(cog_path, file))

    def reload(self, subdirs: list):
        """reloads the cog list with the selected mode"""
        self.__cogs = [f'cogs.{cog.replace(".py","")}'
                       for cog in listdir(self.__COG_PATH) if self.__is_cog(cog)]

        for sub in subdirs:
            if not sub:
                continue
            sub_path = path.join(self.__COG_PATH, sub)
            if path.isdir(sub_path):
                self.__cogs += [f'cogs.{sub_path}.{cog.replace(".py","")}'
                                for cog in listdir(sub_path) if self.__is_cog(cog)]

    def get(self) -> list:
        """returns the list of cogs to be loaded"""
        return self.__cogs


class App(commands.Bot):
    """The bot application"""
    AVATAR_PATH = path.join(TOPDIR, 'img', 'avatar.png')
    AVATAR_HASH = '0e2cba3d8bec4ff4db557700231b3c10'

    __settings: Settings
    __cogs: Cogs
    __activity: Activity
    library: Library
    version_number: str
    current_mode: str

    def __init__(self, settings: Settings, cogs: Cogs, version: str = '1.0', **options):
        super().__init__(**options)
        self.__settings = settings
        self.__cogs = cogs
        self.__activity = Activity(type=ActivityType.playing, name='vebot')
        self.version_number = version
        self.library = Library(settings)

        # Try to load cogs
        try:
            self.__load_cogs()
        except (commands.ExtensionNotLoaded,
                commands.ExtensionNotFound,
                commands.NoEntryPointError,
                commands.ExtensionFailed):
            logging.error('Error on loading cogs.')
            sys.exit(1)

        # Add mode command
        self.add_command(App.__set)

    @property
    def app_settings(self):
        """Returns __settings"""
        return self.__settings

    @property
    def app_cogs(self):
        """Returns __cogs"""
        return self.__cogs

    @property
    def app_avatar(self):
        """Reads app avatar from disk"""
        with open(self.AVATAR_PATH, 'rb') as handle:
            return handle.read()

    def reload_library(self):
        """Reload library"""
        self.library = Library(self.app_settings)

    def reload_cogs(self):
        """Reload cogs"""
        self.app_cogs.reload([self.app_settings.system, self.app_settings.mode])
        for cog in self.app_cogs.get():
            logging.info('loading %s', cog)
            self.reload_extension(cog)

    async def on_ready(self):
        """Handles the event triggered when bot is ready"""
        logging.info('Bot online as %s.', self.user)
        logging.info('avatar %s', self.user.avatar)
        if not self.user.avatar or self.user.avatar != self.AVATAR_HASH:
            logging.info('Changing avatar.')
            await self.user.edit(avatar=self.app_avatar)
        await self.change_presence(activity=self.__activity)

    async def on_message(self, message):
        """General message handler"""
        await self.process_commands(message)

    async def on_command_error(self, context, exception):
        """Handle command errors"""
        message = {
            BotMissingPermissions: lambda err: 'Missing Bot Permission: '
                                               f'{", ".join(err.missing_perms)}.',
            MissingPermissions: lambda err: 'Missing Permission: '
                                            f'{", ".join(err.missing_perms)}',
            NotOwner: lambda err: 'Missing Permission: You are not an owner.',
            MissingRequiredArgument: lambda err: 'Missing argument: '
                                                 'Check "!help".',
            CommandNotFound: lambda err: 'Command not found: Check "!help".',
        }

        exception_type = exception.__class__
        if exception_type in message:
            await context.send(message[exception_type](exception))
        else:
            logging.exception(exception, stack_info=True)

    def __load_cogs(self):
        """Load all cogs into bot."""
        for cog in self.__cogs.get():
            logging.info('loading %s', cog)
            self.load_extension(cog)

    @staticmethod
    @commands.command(name="set", aliases=['s'])
    @commands.is_owner()
    async def __set(ctx: commands.Context, setting: str, value: str):
        """Command to change a setting value."""
        settings = ctx.bot.app_settings
        valid_settings = settings.USER_FACING_SETTINGS
        found = [key for key in valid_settings if key.startswith(setting)]
        if len(found) == 1:
            setting = found[0]
        else:
            await ctx.send(f'Invalid setting "{setting}". Valid choices are:'
                           f' [{", ".join(valid_settings)}]')
            return

        valid_values = settings.get_valid_values(setting)
        if not settings.set(setting, value, valid_values):
            if valid_values:
                await ctx.send(f'invalid value, use [{", ".join(valid_values)}]')
            return

        # Reload library when needed
        if setting in ['language', 'system', 'mode']:
            ctx.bot.reload_library()

        # Reload cogs when needed
        if setting in ['system', 'mode']:
            try:
                logging.info('%s triggered a cogs reload.', ctx.author)
                await ctx.send(f'{ctx.message.author.mention} triggered a mode change.')
                ctx.bot.reload_cogs()
            except (commands.ExtensionNotLoaded,
                    commands.ExtensionNotFound,
                    commands.NoEntryPointError,
                    commands.ExtensionFailed):
                # Inform User that reload was not successful
                message_error = 'Error on reloading cogs.'
                logging.error(message_error)
                await ctx.send(message_error)
                return

        message_success = f'{setting} changed to "{value}".'
        logging.info(message_success)
        await ctx.send(message_success)
        return


def main():
    """main"""
    args = docopt(__doc__, version="0.1")

    if args.pop('--verbose'):
        loglevel = 'DEBUG'
    else:
        loglevel = args.pop('--log-level').upper()

    logging.basicConfig(filename=args.pop('--log-file'), filemode='w',
                        level=loglevel, format='%(levelname)s: %(message)s')

    # Check python version
    is_min_python_3_6 = sys.version_info[0] == 3 and sys.version_info[1] >= 6
    if not is_min_python_3_6:
        logging.error('The bot was developed for Python 3. Please use '
                      'Version 3.6 or higher.')
        sys.exit(1)

    settings = Settings()
    if args['--token']:
        settings.token = args.pop('--token')
    if not settings.token:
        settings.token = input('enter token:')
    if not settings.token:
        logging.error('no token provided')
        sys.exit(1)
    settings.save()

    app = App(settings, Cogs(), command_prefix='.', version='0.1')
    logging.info('Starting bot')
    app.run(settings.token)


if __name__ == '__main__':
    main()
