#!/usr/bin/env python3
import requests
import sys
import subprocess
import argparse
import time
import os
from dotenv import load_dotenv

def parse_args():
    parser = argparse.ArgumentParser(description="Start,Stop,Rebuild. Defaults to all")
    subparsers = parser.add_subparsers(dest="mode",required=True,help="Start,Stop,Rebuild. Defaults to all running containers")
    start_parser = subparsers.add_parser("start", help="start all or some servers")
    stop_parser = subparsers.add_parser("stop", help="stop all or some servers")
    restart_parser = subparsers.add_parser("restart", help="restart all or some servers")
    rebuild_parser = subparsers.add_parser("rebuild", help="rebuild all or some servers")
    for sub in [start_parser, stop_parser, restart_parser, rebuild_parser]: 
        sub.add_argument("-s","--server",help="Which server to start,stop, or reboot")
        sub.add_argument("-t","--time",help="Time in minutes",type=int,default=10)
        sub.add_argument("-r","--running",help="Gets only running containers",action="store_true")
    return parser.parse_args()

def start(compose_file):
    process = subprocess.run(["docker","compose","-f",compose_file,"up","-d"])
    return process.returncode

def stop(compose_file):
    process = subprocess.run(["docker","compose","-f",compose_file,"stop"])
    return process.returncode

def restart(compose_file):
    process = subprocess.run(["docker","compose","-f",compose_file,"restart"])
    return process.returncode

def rebuild(compose_file):
    process = subprocess.run(["docker","compose","-f",compose_file,"up","-d","--build"])
    return process.returncode

def do_start(args,containers,webhook_url):
    servers = containers
    if args.server:
        if args.server not in containers:
            exit(1)
        else:
            servers = {args.server: containers[args.server]}
    message = "Start command sent to "
    length = len(servers)
    for index, (game, server) in enumerate(servers.items()):
        if length == 1:
            message += game
            break
        if index == length - 1:
            message += "and " + game
        else:
            message += game + " "
    message += " in " + str(args.time) + " minutes"
    send_discord(webhook_url,message)
    time.sleep(args.time * 60)
    for game, server in servers.items():
        if server["status"] == "running":
            message = game + " already running"
        else:
            status = start(server["compose_file"])
            if status == 0:
                message = "Successfully started " + game + "🚀"
            else:
                message = "Failed to start " + game 
        send_discord(webhook_url,message)
    return

def do_stop(args,containers,webhook_url):
    servers = containers
    if args.server:
        if args.server not in containers:
            exit(1)
        else:
            servers = {args.server: containers[args.server]}
    message = "Stop command sent to "
    length = len(servers)
    for index, (game, server) in enumerate(servers.items()):
        if length == 1:
            message += game
            break
        if index == length - 1:
            message += "and " + game
        else:
            message += game + " "
    message += " in " + str(args.time) + " minutes"
    send_discord(webhook_url,message)
    time.sleep(args.time * 60)
    for game, server in servers.items():
        if server["status"] == "exited":
            message = game + " already stopped"
        else:
            status = stop(server["compose_file"])
            if status == 0:
                message = "Successfully stopped " + game
            else:
                message = "Failed to stop " + game 
        send_discord(webhook_url,message)
    return

def do_restart(args,containers,webhook_url):
    servers = containers
    if args.server:
        if args.server not in containers:
            exit(1)
        else:
            servers = {args.server: containers[args.server]}
    message = "Restart command sent to "
    length = len(servers)
    for index, (game, server) in enumerate(servers.items()):
        if length == 1:
            message += game
            break
        if index == length - 1:
            message += "and " + game
        else:
            message += game + " "
    message += " in " + str(args.time) + " minutes"
    send_discord(webhook_url,message)
    time.sleep(args.time * 60)
    for game, server in servers.items():
        if server["status"] == "exited":
            message = game + " stopped, starting server"
            status = start(server["compose_file"])
            if status == 0:
                message = "Successfully restarted " + game
            else:
                message = "Failed to restart " + game 
        else:
            status = restart(server["compose_file"])
            if status == 0:
                message = "Successfully restarted " + game
            else:
                message = "Failed to restart " + game 
        send_discord(webhook_url,message)
    return

def do_rebuild(args,containers,webhook_url):
    servers = containers
    if args.server:
        if args.server not in containers:
            exit(1)
        else:
            servers = {args.server: containers[args.server]}
    message = "Rebuild command sent to "
    length = len(servers)
    for index, (game, server) in enumerate(servers.items()):
        if length == 1:
            message += game
            break
        if index == length - 1:
            message += "and " + game
        else:
            message += game + " "
    message += " in " + str(args.time) + " minutes"
    send_discord(webhook_url,message)
    time.sleep(args.time * 60)
    for game, server in servers.items():
        if server["status"] == "exited":
            message = game + " stopped, starting server"
            send_discord(webhook_url,message)
            status = rebuild(server["compose_file"])
            if status == 0:
                message = "Successfully built and started " + game
            else:
                message = "Failed to rebuild or start " + game 
        else:
            status = rebuild(server["compose_file"])
            if status == 0:
                message = "Successfully rebuilt " + game
            else:
                message = "Failed to rebuild " + game 
        send_discord(webhook_url,message)
    return

def send_discord(webhook,message):
    payload = {
        "content": message
    }
    response = requests.post(webhook,json=payload)
    print(message)
    if 199 < response.status_code < 300:
        return True
    else:
        return False

def get_containers(args):
    if args.running and args.mode != "start":
        output = subprocess.run(
            [
            "docker","ps","--filter","label=type=game",
            "--format",'{{.Label "game"}}|{{.Names}}|{{.Label "com.docker.compose.project.config_files"}}|{{.State}}',
            ], capture_output=True,text=True
        ).stdout.splitlines()
    else:
        output = subprocess.run(
            [
            "docker","ps","-a","--filter","label=type=game",
            "--format",'{{.Label "game"}}|{{.Names}}|{{.Label "com.docker.compose.project.config_files"}}|{{.State}}',
            ], capture_output=True,text=True
        ).stdout.splitlines()
    servers = {}
    for line in output:
        game, container_name, compose_file, status = line.split("|")
        servers[game] = {
            "container_name": container_name,
            "compose_file": compose_file,
            "status": status
        }
    return servers

def main():
    args = parse_args()
    load_dotenv()
    containers = get_containers(args)
    webhook_url = os.getenv("discord_webhook_url")
    if args.mode == "start":
        do_start(args,containers,webhook_url)
    elif args.mode == "stop":
        do_stop(args,containers,webhook_url)
    elif args.mode == "rebuild":
        do_rebuild(args,containers,webhook_url)
    elif args.mode == "restart":
        do_restart(args,containers,webhook_url)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
