# Docker Game Server Manager

A Python CLI utility for managing Docker Compose game servers and sending maintenance notifications through a Discord webhook.

The script automatically discovers game-server containers using Docker labels, retrieves their associated Compose files, and provides commands to start, stop, restart, or rebuild either a specific game server or multiple servers.

## Features

* Automatically discovers Docker game-server containers
* Uses Docker labels instead of hardcoded container names
* Retrieves the Docker Compose file associated with each container
* Start game servers
* Stop game servers
* Restart game servers
* Rebuild game-server images
* Operate on a single server or all discovered servers
* Optionally operate only on currently running containers
* Configurable maintenance warning period
* Discord webhook notifications before and after operations
* Supports stopped containers through `docker ps -a`

## Requirements

* Python 3
* Docker
* Docker Compose v2
* A Discord webhook
* Python virtual environment recommended

Python dependencies:

```text
requests
python-dotenv
```

Install them with:

```bash
pip install -r requirements.txt
```

## Docker Container Labels

Game-server containers must include the following labels:

```yaml
labels:
  type: game
  game: valheim
```

For example:

```yaml
services:
  valheim:
    image: example/valheim-server
    container_name: valheim-server

    labels:
      type: game
      game: valheim
```

The `type=game` label identifies containers managed by this script.

The `game` label provides the logical server name used by the CLI.

For example:

```text
game=valheim
game=minecraft
game=palworld
```

This allows commands such as:

```bash
python gamesMessages.py start -s valheim
```

Docker Compose automatically provides metadata that the script uses to locate the container's Compose configuration.

The script reads:

```text
com.docker.compose.project.config_files
```

to determine which Compose file belongs to each game server.

## Environment Configuration

Create a `.env` file in the project directory:

```text
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your-webhook
```

Do not commit this file.

Add the following to `.gitignore`:

```gitignore
.env
.venv/
__pycache__/
```

The webhook URL should be treated as a secret. Anyone with access to it can send messages through the webhook.

## Virtual Environment

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

General syntax:

```bash
python gamesMessages.py <command> [options]
```

Available commands:

```text
start
stop
restart
rebuild
```

### Options

#### Select a server

```text
-s SERVER
--server SERVER
```

Runs the requested operation against a single game server.

Example:

```bash
python gamesMessages.py start -s valheim
```

Without `--server`, the operation applies to all discovered game servers.

#### Maintenance Delay

```text
-t MINUTES
--time MINUTES
```

Sets the delay between the initial Discord maintenance notification and the Docker operation.

The default is:

```text
10 minutes
```

Example:

```bash
python gamesMessages.py restart -s minecraft -t 5
```

This sends a Discord warning, waits five minutes, restarts Minecraft, and sends a completion message.

For immediate execution:

```bash
python gamesMessages.py restart -s minecraft -t 0
```

#### Running Containers Only

```text
-r
--running
```

Limits supported operations to currently running game containers.

Example:

```bash
python gamesMessages.py restart --running
```

The `start` command still searches all known game containers so that stopped servers can be discovered and started.

## Examples

### Start All Game Servers

```bash
python gamesMessages.py start
```

Default behavior:

```text
1. Discover all game containers
2. Send Discord maintenance message
3. Wait 10 minutes
4. Start stopped game servers
5. Report results to Discord
```

### Start One Server

```bash
python gamesMessages.py start -s palworld
```

### Start One Server After a One-Minute Warning

```bash
python gamesMessages.py start -s palworld -t 1
```

### Stop One Server

```bash
python gamesMessages.py stop -s valheim
```

### Stop All Running Game Servers

```bash
python gamesMessages.py stop --running
```

### Restart One Server

```bash
python gamesMessages.py restart -s minecraft -t 5
```

If the selected server is stopped, the script starts it instead.

### Restart All Running Servers

```bash
python gamesMessages.py restart --running
```

### Rebuild One Server

```bash
python gamesMessages.py rebuild -s palworld
```

The rebuild operation runs the equivalent of:

```bash
docker compose -f <compose-file> up -d --build
```

### Rebuild All Running Game Servers

```bash
python gamesMessages.py rebuild --running
```

## Docker Commands

The script currently maps operations to the following Docker Compose commands.

### Start

```bash
docker compose -f <compose-file> up -d
```

### Stop

```bash
docker compose -f <compose-file> stop
```

`stop` is used instead of `down` so the container remains available to `docker ps -a`.

This preserves the container labels and Compose metadata needed for automatic discovery.

### Restart

```bash
docker compose -f <compose-file> restart
```

If a server is currently stopped, the script uses the start operation instead.

### Rebuild

```bash
docker compose -f <compose-file> up -d --build
```

This rebuilds the image and creates or recreates the service as necessary.

## Server Discovery

The script discovers servers using Docker:

```bash
docker ps -a \
  --filter "label=type=game" \
  --format '{{.Label "game"}}|{{.Names}}|{{.Label "com.docker.compose.project.config_files"}}|{{.State}}'
```

This produces information similar to:

```text
valheim|valheim-server|/srv/valheim/compose.yaml|running
minecraft|minecraft-server|/srv/minecraft/compose.yaml|exited
palworld|palworld-server|/srv/palworld/compose.yaml|running
```

The script converts this information into an internal dictionary keyed by game name.

Conceptually:

```python
{
    "valheim": {
        "container_name": "valheim-server",
        "compose_file": "/srv/valheim/compose.yaml",
        "status": "running"
    },
    "minecraft": {
        "container_name": "minecraft-server",
        "compose_file": "/srv/minecraft/compose.yaml",
        "status": "exited"
    }
}
```

This means container names and Compose paths do not need to be hardcoded into the Python script.

## Discord Notifications

The script sends notifications when an operation is scheduled.

Example:

```text
Restart command sent to valheim minecraft and palworld in 10 minutes
```

After the Docker operation completes, another notification reports the result.

Example:

```text
Successfully restarted valheim
```

Failures are also reported:

```text
Failed to restart valheim
```

## Project Structure

A basic project layout can look like:

```text
game-server-manager/
├── gamesMessages.py
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```

Example `requirements.txt`:

```text
requests
python-dotenv
```

## Security

Do not hardcode Discord webhook URLs into the source code.

Do not commit `.env` files.

If a Discord webhook URL is accidentally exposed, regenerate the webhook immediately.

Docker permissions should also be considered carefully. A user capable of controlling the Docker daemon effectively has administrative control over the host.

## Current Limitations

* Server state is based on Docker container state rather than application-level health.
* A running container does not necessarily mean the game server is ready to accept players.
* Compose projects using multiple Compose configuration files may require additional handling.
* Discord notification failures do not currently prevent Docker operations.
* Docker command failures are reported using process return codes.

## Possible Future Improvements

* Docker health-check integration
* Verify game ports are accepting connections
* Discord bot integration
* Start and stop servers directly from Discord
* Server status command
* Terminal autocomplete for discovered game servers
* Better logging
* Graceful handling of Discord connection failures
* Refresh container state after maintenance delays
* systemd service/timer integration

## License

This project is intended primarily as a personal homelab and game-server management utility.
