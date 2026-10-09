#!/usr/bin/env python3
import discord
import os
from dotenv import load_dotenv
from discord import app_commands
import docker_commands
import asyncio
import random

# .env variable loading
load_dotenv()
# token = os.getenv("discord_client_token")
guild_ids = [
    int(guild_id)
    for guild_id in os.getenv("guild_ids").split(",")
]
user_ids = {
    int(user_id)
    for user_id in os.getenv("user_ids").split(",")
}
guilds = [
    discord.Object(id=guild_id)
    for guild_id in guild_ids
]
# initialization
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# helper functions
async def authorized_user(interaction: discord.Interaction):
    if interaction.user.id not in user_ids:
        await interaction.response.send_message(
            "You are not authorized for this command", ephemeral=True)
        return False
    return True

async def game_name_autocomplete(
    interaction: discord.Interaction,
    current: str
):
    containers = await asyncio.to_thread(
        docker_commands.get_containers,
        False
    )

    choices = []

    for game in containers:
        if current.lower() in game.lower():
            choices.append(
                app_commands.Choice(
                    name=game,
                    value=game
                )
            )

    return choices[:25]

# discord functions

@tree.command(name="ping", description="Are you alive", guilds=guilds)
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("2l2Q bot running")

@tree.command(name="start",description="Start a server",guilds=guilds)
@app_commands.autocomplete(name=game_name_autocomplete)
@app_commands.check(authorized_user)
async def start(interaction: discord.Interaction, name: str, rebuild: bool = True):
    await interaction.response.defer()
    message = await asyncio.to_thread(docker_commands.start,name,rebuild)
    await interaction.followup.send(message)

@tree.command(name="stop",description="Stop a server",guilds=guilds)
@app_commands.autocomplete(name=game_name_autocomplete)
@app_commands.check(authorized_user)
async def stop(interaction: discord.Interaction, name: str):
    await interaction.response.defer()
    message = await asyncio.to_thread(docker_commands.running_server_command,"stop",name)
    await interaction.followup.send(message)

@tree.command(name="restart",description="Restart a server",guilds=guilds)
@app_commands.autocomplete(name=game_name_autocomplete)
@app_commands.check(authorized_user)
async def restart(interaction: discord.Interaction, name: str):
    await interaction.response.defer()
    message = await asyncio.to_thread(docker_commands.running_server_command,"restart",name)
    await interaction.followup.send(message)

@tree.command(name="rebuild",description="Rebuild a server",guilds=guilds)
@app_commands.autocomplete(name=game_name_autocomplete)
@app_commands.check(authorized_user)
async def rebuild(interaction: discord.Interaction, name: str):
    await interaction.response.defer()
    message = await asyncio.to_thread(docker_commands.running_server_command,"rebuild",name)
    await interaction.followup.send(message)

@tree.command(name="status", description="Status of games containers", guilds=guilds)
@app_commands.autocomplete(name=game_name_autocomplete)
async def status(interaction: discord.Interaction, name: str | None = None, running: bool = False):
    containers = await asyncio.to_thread(docker_commands.get_containers,running)
    if not containers:
        await interaction.response.send_message(
            "No game containers running, try starting one"
        )
        return
    if name and name not in containers:
        await interaction.response.send_message(
            f"{name} not installed on the server. Submit a [github issue](https://github.com/krby4/2l2q_games_server/issues) to get it added"
        )
        return
    if name:
        container_status = containers[name]["status"]
        await interaction.response.send_message(f"{name} is {container_status}")
    else:
        message = ""
        size = len(containers)
        for index, (game, container) in enumerate(containers.items()):
            message += f'{game} is {container["status"]}'
            if index != size -1:
                message += '\n'
        await interaction.response.send_message(message)

# client events
@client.event
async def on_ready():
    for guild in guilds:
        synced = await tree.sync(guild=guild)
        print(f"Synced {len(synced)} commands")
    # synced = await tree.sync(guild=guild)
    
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.lower().startswith("bitch"):
        num = random.randint(1,5)
        if num == 1:
            await message.channel.send("No u a bitch")
        elif num == 2:
            await message.channel.send("Careful, this is a Christian discord server")
client.run(os.getenv("discord_client_token"))
