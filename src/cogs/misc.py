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

"""Miscellaneous cog"""

import logging
import platform
import discord
from discord.ext import commands


class MiscCog(commands.Cog):
    """
    This cog is for commands that are related mainly to Discord.
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ping", help='Ping/pong test.')
    async def ping(self, ctx):
        """Ping/pong test command."""
        logging.info("ping")
        await ctx.send('pong')

    @commands.command(name="info", aliases=['inf', 'i'], help='Show bot details.')
    async def get_bot_info(self, ctx):
        """
        Gather some basic information about this bot and then format it into
        an embed. This embed is then sent to Discord chat.
        """
        app_info = await self.bot.application_info()

        python_version = platform.python_version()
        discord_wrapper_version = discord.__version__
        bot_name = app_info.name
        bot_settings = self.bot.app_settings.details()
        bot_owner = app_info.owner
        image_url = self.bot.user.avatar_url

        bot_source_info = [f"Python {python_version}",
                           f"Using discord.py v{discord_wrapper_version}",
                           'Source in [Github]'
                           '(https://github.com/adn770/ve-bot)']

        title = f"{bot_name} v{self.bot.version_number}"
        embed = discord.Embed(title=title, color=discord.Color(0x8c9eff)) \
            .add_field(name="Settings", value=bot_settings, inline=False) \
            .add_field(name="Developer", value=bot_owner, inline=False) \
            .add_field(name="Source made with",
                       value="\n".join(bot_source_info), inline=False) \
            .set_thumbnail(url=image_url)
        await ctx.send(embed=embed)

    @commands.command(name="me", help='Show my details.')
    async def get_user_info(self, ctx):
        """
        Fetch data about the author who invokes this command. This data is
        then formatted into an embed, which is sent to Discord chat.
        """
        author_roles = []
        author = ctx.author

        full_username = str(author)
        display_name = author.display_name
        author_id = author.id
        top_role = str(author.top_role)
        guild_roles = author.roles
        icon_url = author.avatar_url

        # Add role names to a list, and escape every role starting with
        # @ to prevent mention formats
        for role in guild_roles:
            role_name = role.name
            if role_name.startswith("@"):
                role_name = f"\\{role_name}"
            author_roles.append(role_name)

        embed = discord.Embed(title=full_username).set_thumbnail(url=icon_url) \
            .add_field(name="Display name", value=display_name) \
            .add_field(name="Id", value=author_id) \
            .add_field(name="Top role", value=top_role) \
            .add_field(name="All roles", value=", ".join(sorted(author_roles)))

        await ctx.send(embed=embed)

    @commands.is_owner()
    @commands.command(name="delete", aliases=['del'])
    async def delete(self, ctx, number: int = 2):
        """Deletes msgs in the channel for the specified limit (default 2)"""
        await ctx.channel.purge(limit=int(number))


def setup(bot):
    """Installs the cog"""
    bot.add_cog(MiscCog(bot))
