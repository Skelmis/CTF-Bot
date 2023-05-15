import logging
import os

import disnake
from alaric import Document, AQ
from alaric.comparison import EQ
from disnake.ext import commands
from disnake.ext.commands import LargeIntConversionFailure
from motor.motor_asyncio import AsyncIOMotorClient

from user import User

# TODO Add some form of audio flag?
bot = commands.InteractionBot(test_guilds=[1107616043372916827])
log = logging.getLogger(__name__)
logging.basicConfig(
    format="%(levelname)-7s | %(asctime)s | %(filename)12s:%(funcName)-12s | %(message)s",
    datefmt="%I:%M:%S %p %d/%m/%Y",
    level=logging.INFO,
)
gateway_logger = logging.getLogger("disnake")
gateway_logger.setLevel(logging.WARNING)

client = AsyncIOMotorClient(os.environ["DB"])
user_db: Document = Document(client["tech_expo_ctf"], "users", converter=User)
role_ids = [1107618760157831191, 1107618751450448002, 1107618758471725074]
flags = {
    "n0t_hidd3n_w3ll",  # /color role_id: 1107618898326597712
    "1n_pl41n_s1t3",  # My github readme
    "3x4mp13_f14g",  # #info flag
    "W31c0m3_t0_my_s1te",  # skelmis.co.nz
    "p1ay1n6_w1th_f1r3",  # /emojis emoji: :fire:
}


@bot.event
async def on_ready():
    log.info("Online")
    await bot.change_presence(activity=disnake.Game("with fire"))


@bot.event
async def on_slash_command_error(
    interaction: disnake.ApplicationCommandInteraction, exception: disnake.HTTPException
):
    exception = getattr(exception, "original", exception)
    if isinstance(exception, LargeIntConversionFailure):
        return await interaction.send(
            "The role id needs to be a number.", ephemeral=True
        )

    await interaction.send("Something went wrong.", ephemeral=True)
    raise exception


async def role_ids_complete(inter, string: str) -> list[str]:
    string = string.lower()
    return [str(lang) for lang in role_ids if string in str(lang).lower()]


@bot.slash_command(description="Set your color role!", name="color")
async def set_color(
    interaction: disnake.GuildCommandInteraction,
    role_id: commands.LargeInt = commands.Param(
        autocomplete=role_ids_complete,
        description="The color role you want",
    ),
):
    await interaction.response.defer(ephemeral=True, with_message=True)
    if role_id in role_ids:
        role: disnake.Role = interaction.guild.get_role(role_id)
        await interaction.author.edit(roles=[role])
        return await interaction.send(
            f"I've set your role to {role.name}!", ephemeral=True
        )

    elif role_id == 1107618898326597712:
        log.info(
            "%s(%s) unlocked the secret tunnel",
            interaction.author.name,
            interaction.author.id,
        )
        role: disnake.Role = interaction.guild.get_role(role_id)
        await interaction.author.edit(roles=[role, *interaction.author.roles])
        return await interaction.send("Secret tunnel unlocked!", ephemeral=True)

    return await interaction.send("Something went wrong.", ephemeral=True)


@bot.slash_command(description="Verify your flags!", name="verify")
async def verify_flag(
    interaction: disnake.GuildCommandInteraction,
    flag: str = commands.Param(
        description="The flag to verify. (Bit between CTF{ and })"
    ),
):
    await interaction.response.defer(ephemeral=True, with_message=True)
    if flag not in flags:
        return await interaction.send("That doesn't look like a flag.", ephemeral=True)

    user: User | None = await user_db.find(AQ(EQ("_id", interaction.author.id)))
    if user is None:
        user: User = User(interaction.author.id, [])
        await user_db.insert(user)

    if flag in user.flags:
        return await interaction.send("You already have this flag.", ephemeral=True)

    user.flags.append(flag)
    await user_db.change_field_to(user, "flags", user.flags)
    await interaction.send(
        "That's another flag under the belt, congrats!", ephemeral=True
    )
    log.info(
        "%s(%s) just found the flag %s",
        interaction.author.name,
        interaction.author.id,
        flag,
    )


@bot.slash_command(description="Whats my favorite emoji?", name="emojis")
async def emoji_check(interaction: disnake.GuildCommandInteraction, emoji: str):
    await interaction.response.defer(ephemeral=True, with_message=True)
    if emoji == "🔥":
        return await interaction.send(
            "Absolutely :fire:\n\n`CTF{p1ay1n6_w1th_f1r3}`", ephemeral=True
        )

    await interaction.send(":cold_face: maybe next time :cold_face: ", ephemeral=True)


@bot.slash_command(description="Check your flag count.", name="count")
async def count(interaction: disnake.GuildCommandInteraction):
    await interaction.response.defer(ephemeral=True, with_message=True)
    total = len(flags)
    user: User | None = await user_db.find(AQ(EQ("_id", interaction.author.id)))
    if user is None:
        return await interaction.send(f"You have 0/{total} flags.", ephemeral=True)

    await interaction.send(f"You have {len(user.flags)}/{total} flags.", ephemeral=True)


@bot.slash_command(description="Flag leaderboard.", name="leaderboard")
async def leaderboard(interaction: disnake.GuildCommandInteraction):
    await interaction.response.defer(ephemeral=True, with_message=True)
    users: list[User] = await user_db.get_all({})
    users = sorted(users, key=lambda u: len(u.flags), reverse=True)
    embed = disnake.Embed(
        title="Leaderboard",
        description="\n".join(
            f"<@{u._id}>: {len(u.flags)} flag{'s' if len(u.flags) != 1 else ''}"
            for u in users
        ),
    )
    await interaction.send(embed=embed, ephemeral=True)


bot.run(os.environ["TOKEN"])
