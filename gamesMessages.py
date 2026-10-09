#!/usr/bin/env python3
import requests
import sys
import subprocess
import argparse
import time
import os
from dotenv import load_dotenv
import docker_commands

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

def do_docker(mode,containers,server,sleep_time,webhook_url):
    servers = containers
    if server:
        if server not in containers:
            exit(1)
        else:
            servers = {server: containers[server]}
    message = "Sending " + mode + " command to "
    length = len(servers)
    for index, (game, server) in enumerate(servers.items()):
        if length == 1:
            message += game
            break
        if index == length - 1:
            message += "and " + game
        else:
            message += game + " "
    if sleep_time == 0:
        message += " in 1 second"
        sleep_time = 1
    else:
        if sleep_time == 1:
            message += " in 1 minute"
        else:
            message += " in " + sleep_time + " minutes"
        sleep_time *= 60
    send_discord(webhook_url,message)
    time.sleep(sleep_time)
    for game, server in servers.items():
        message = ""
        if mode == "start":
            if server["status"] == "running":
                message += game + " already running"
                send_discord(webhook_url,message)
                break
        elif mode in ["stop","restart","rebuild"]:
            if server["status"] == "exited":
                if mode == "stop":
                    message += game + " already stopped"
                    send_discord(webhook_url,message)
                    break
                else:
                    message += game + " stopped, starting server"
                    send_discord(webhook_url,message)
        status = docker_commands.run_compose_command(mode,server["compose_file"])
        if status == 0:
            message = "Successful " + mode + " on " + game + " 🚀"
        else:
            message = "Failed to " + mode + " " + game 
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


def main():
    args = parse_args()
    load_dotenv()
    containers = docker_commands.get_containers(args.running)
    webhook_url = os.getenv("discord_webhook_url")
    if args.mode in ["start","stop","rebuild","restart"]:
        do_docker(args.mode,containers,args.server,args.time,webhook_url)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
