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
# pylint: disable=too-many-locals
#

"""Dice cog"""

import logging
import rolldice
import discord
from discord.enums import ChannelType
from discord.ext import commands


def roll_attributes(method: str):
    """roll attributes and provides a score"""
    output = []
    die = "3d6"
    nscores = 6
    if method == "inorder+":
        die = '4d6K3'
    elif method == "ve":
        die = "3d6"
        nscores = 7
    elif method == "heroic":
        die = '4d6K3'
        nscores = 7

    for _ in range(nscores):
        result, explanation = rolldice.roll_dice(die)
        output += [{"score": result, "details": explanation.replace("~~", " ▾")}]

    scores = [int(row['score']) for row in output]
    count = sum(map(lambda x: x < 9, scores))
    score = 0
    if count < 2:
        score = sum(scores)
    if len(output) > 6:
        output = sorted(output, key=lambda k: int(k['score']), reverse=True)
        score = score - int(output[-1]['score'])
    return output, score, die


def modifier_ve(score: int, attr: str) -> str:  # pylint: disable=unused-argument
    """computes an attribute modifier with Vieja Escuela rules"""
    result = ""
    if score > 17:
        result = "+2"
    elif score > 14:
        result = "+1"
    elif score > 6:
        result = ""
    elif score > 3:
        result = "-1"
    elif score > 0:
        result = "-2"

    if result:
        return f" ({result})"
    return ""


def modifier_ose(score: int, attr: str) -> str:  # pylint: disable=unused-argument
    """computes an attribute modifier with Old School Essential rules"""
    result = ""
    if score > 17:
        result = "+3"
    elif score > 15:
        result = "+2"
    elif score > 12:
        result = "+1"
    elif score > 8:
        result = ""
    elif score > 5:
        result = "-1"
    elif score > 3:
        result = "-2"
    elif score > 0:
        result = "-3"

    if result:
        return f" ({result})"
    return ""


def modifier(system: str, score: int, attr: str = '') -> str:
    """computes an attribute modifier"""
    systems = {
                've': modifier_ve,
                'ose': modifier_ose,
              }
    return systems[system](score, attr)


def format_attribute(system: str, die: str, score: str, details: str,
                     attr: str = '') -> str:
    """format attribute result"""
    prefix = ""
    if attr:
        prefix = f"{attr}:    "
    mod = modifier(system, int(score), attr)
    return f'{die} -> **{prefix}{score}{mod}** <- {details}'


def check_for_notes(library, attr: str, score: int):  # pylint: disable=unused-argument
    """Searches for additional info for character creation in the library"""
    return []


class DiceCog(commands.Cog):
    """This cog is for commands that are related rolling die."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="roll", aliases=['r'])
    async def roll(self, ctx, *, arg: str = "1d20"):
        """Roll the specified dice or default to d20."""
        die = arg
        try:
            result, explanation = rolldice.roll_dice(die)
            await ctx.send(f'{die} -> **{result}** <- {explanation}')
        except (rolldice.DiceGroupException) as err:
            await ctx.send(f'ERROR: {err}')
            logging.exception(err)

    ATTR_PREFIXES = ['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA']

    @commands.command(name="rollcharacter", aliases=['rc'])
    async def rollcharacter(self, ctx, *, name: str = ""):
        """Roll a character."""
        if not name:
            name = ctx.author.display_name

        method = self.bot.app_settings.attributes
        # ensure that stats aren't terribly bad
        attributes = []
        score = 0
        die = ''
        while score < self.bot.app_settings.score_threshold:
            attributes, score, die = roll_attributes(method)

        output = []
        system = self.bot.app_settings.system
        notes = ['Assign the attribute values as you wish.']
        if len(output) == 6:
            output = [format_attribute(system, die, row['score'], row['details'], attr)
                      for attr, row in zip(self.ATTR_PREFIXES, attributes)]
            for attr, row in zip(self.ATTR_PREFIXES, attributes):
                notes += check_for_notes(self.bot.library, attr, int(row['score']))
        else:
            output = [format_attribute(system, die, row['score'], row['details'])
                      for row in attributes]

        if not notes:
            notes = ['Assign the attribute values as you wish.']

        iam = ctx.author.display_name
        icon = ctx.author.avatar_url
        embed = discord.Embed(title='Character') \
            .add_field(name="Ability Scores:", value="\n".join(output), inline=False) \
            .add_field(name="Notes:", value="\n".join(notes)) \
            .set_footer(text=iam, icon_url=icon)

        if self.bot.app_settings.opengame == 'yes':
            await ctx.send(embed=embed)
        else:
            for channel in self.bot.get_all_channels():
                if channel.type == ChannelType.text and channel.name.startswith('dm'):
                    await channel.send(embed=embed)
            await ctx.author.send(embed=embed)


def setup(bot):
    """Installs the cog"""
    bot.add_cog(DiceCog(bot))
