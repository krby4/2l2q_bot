#!/usr/bin/env python3
import subprocess
import json

def start(server,rebuild=True):
    containers = get_containers(False)
    if server not in containers:
        message = f"{server} is not a valid game to start"
        return message
    start_game = containers[server]
    if start_game["status"] == "running":
        message = f"{server} is already running"
        return message
    conflicts = []
    for game,container in containers.items():
        if game == server:
                continue
        if container["status"] != "running":
                continue
        for port in start_game["ports"]:
            if port in container["ports"]:
                conflicts.append((port,game))
    if not conflicts:
        if not rebuild:
            process = run_compose_command("start",start_game["compose_file"])
            # subprocess.run(["docker","compose","-f",start_game["compose_file"],"up","-d"])
        else:
            process = run_compose_command("rebuild",start_game["compose_file"])
            # subprocess.run(["docker","compose","-f",start_game["compose_file"],"up","-d","--build"])
        if process == 0:
            message = f"Successfully started {server}"
            return message
        else:
            message = f"Start command failed on {server}, try again soon or contact admin"
            return message
    else:
        message = f"Could not start {server}. Conflicting ports are "
        length = len(conflicts)
        for index, conflict in enumerate(conflicts):
            message += conflict[1]  + " on port " + conflict[0]
            if index != length-1:
                message += " "
        return message

def running_server_command(mode,server):
    if mode not in ["stop","restart","rebuild"]:
        return f"{mode} not a valid command"
    containers = get_containers(True)
    if server not in containers:
        message = f"{server} is not a valid game to {mode}"
        return message
    running_game = containers[server]
    if running_game["status"] != "running":
        return f"{server} is stopped"
    if mode == "stop":
        process = run_compose_command("stop",running_game["compose_file"])
        mode_message = "stopped"
    elif mode == "restart":
        process = run_compose_command("restart",running_game["compose_file"])
        mode_message = "restarted"
    elif mode == "rebuild":
        process = run_compose_command("rebuild",running_game["compose_file"])
        mode_message = "rebuilt"
    if process == 0:
        return f"Successfully {mode_message} {server}"
    else:
        return f"{mode} command not successful on {server}, try again"

def run_compose_command(mode,compose_file):
    if mode == "start":
        process = subprocess.run(["docker","compose","-f",compose_file,"up","-d"])
        return process.returncode 
    elif mode == "stop":
        process = subprocess.run(["docker","compose","-f",compose_file,"stop"])
        return process.returncode
    elif mode == "restart":
        process = subprocess.run(["docker","compose","-f",compose_file,"restart"])
        return process.returncode
    elif mode == "rebuild":
        process = subprocess.run(["docker","compose","-f",compose_file,"up","-d","--build"])
        return process.returncode
    else:
        return


def get_containers(running_only=False):
    if running_only:
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
    for game, server in servers.items():
        output = subprocess.run(["docker", "inspect","--format","{{json .HostConfig.PortBindings}}",server["container_name"]],capture_output=True,text=True)
        ports = json.loads(output.stdout)
        host_ports = []
        for port,bindings in ports.items():
            for binding in bindings:
                host_ports.append(binding["HostPort"])
        server["ports"] = host_ports
    return servers