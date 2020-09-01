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

"""Books cog"""

import logging
import discord
from discord.ext import commands


class BooksCog(commands.Cog):
    """
    This cog is for commands that are related to retrieve info from books.
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="monster", aliases=['m'])
    async def monster(self, ctx, mid: str):
        """Searches a monster in the book."""
        monster_book = self.bot.app_settings.monster_book
        monsters = self.bot.library.search(monster_book)
        if not monsters:
            await ctx.send(f'monster manual "{monster_book}" not found')
            return

        monster = monsters.search(mid)
        if not monster:
            await ctx.send(f'"{mid}" not found')
            return
        name = f'{monster.Name} [**{monster.Id}**]'
        embed = discord.Embed(title=name) \
            .add_field(name="AC", value=monster.AC) \
            .add_field(name="HD", value=monster.HD) \
            .add_field(name="Move", value=monster.Move) \
            .add_field(name="Attacks", value=monster.Attacks) \
            .add_field(name="Damage", value=monster.Damage) \
            .add_field(name="# Appearing (In Lair)", value=monster.Number) \
            .add_field(name="Save As", value=monster.Save) \
            .add_field(name="Morale", value=monster.Morale) \
            .add_field(name="Treasure", value=monster.Treasure) \
            .add_field(name="Alignment", value=monster.Alignment) \
            .add_field(name="XP", value=monster.XP)

        if monster.Notes:
            embed.add_field(name="Notes", value=monster.Notes, inline=False)

        await ctx.send(embed=embed)

    @commands.command(name="mlist", aliases=['ml'])
    async def mlist(self, ctx):
        """Lists monster book."""
        monster_book = self.bot.app_settings.monster_book
        monsters = self.bot.library.search(monster_book)
        if not monsters:
            await ctx.send(f'monster manual "{monster_book}" not found')
            return

        output = monsters.index()
        logging.debug("listed %d monsters", len(output))

        index = sorted(list(output), key=lambda item: item.Name)
        for cursor in range(0, len(index), 25):
            embed = discord.Embed(title=f'Monster Book. From {cursor+1} to {cursor+25}')
            for monster in index[cursor:cursor+25]:
                embed.add_field(name=monster.Name, value=monster.Id)
            await ctx.send(embed=embed)

    @commands.is_owner()
    @commands.command(name="rollt", aliases=['rt'])
    async def rollt(self, ctx, table_book: str):
        """Searches a table and rolls on it."""
        table = self.bot.library.search(table_book)
        if not table:
            await ctx.send(f'table "{table_book}" not found')
            return

        result, explanation = table.roll()
        if not result:
            await ctx.send('something went wrong')
            return

        embed = discord.Embed(title=table.title) \
            .add_field(name="Result", value=result, inline=False) \
            .add_field(name="Explanation", value="\n".join(explanation), inline=False)

        await ctx.send(embed=embed)


def setup(bot):
    """Installs the cog"""
    bot.add_cog(BooksCog(bot))
