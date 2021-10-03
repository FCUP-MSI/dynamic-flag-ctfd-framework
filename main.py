import sched
import time

from multiprocessing import Process
import multiprocessing_logging

from docker import from_env
import logging
from secrets import token_hex

from ctfd_api import CTFDClient
from os import getenv

scheduler = None
logging.basicConfig(level=logging.INFO)
log = logging.getLogger()
multiprocessing_logging.install_mp_handler(log)


def process_challenges(challenges):
    challenges_db = {}

    for i in challenges:
        challenges_db[i["name"]] = i["id"]

    return challenges_db


def process_flags(flags):
    flags_db = {}
    for i in flags:
        if i["challenge_id"] in flags_db.keys():
            flags_db[i["challenge_id"]].append(i["id"])
        else:
            flags_db[i["challenge_id"]] = [i["id"]]

    return flags_db


def search_for_new_containers(ctfd_client):
    docker_client = from_env()
    while True:
        evs = docker_client.events(decode=True)
        for ev in evs:
            try:
                if ev[u'status'] == u'start':
                    cont = docker_client.containers.get(ev[u'id'])
                    if cont.labels["dynamic-label"]:
                        log.info(f"Container was started - {cont.name}")
                        challenges = process_challenges(ctfd_client.get_challenges())
                        flags_by_challenge = process_flags(ctfd_client.get_flags())
                        deploy_container(cont, ctfd_client, challenges, flags_by_challenge)
            except KeyError:
                pass


def deploy_container(c, ctfd_client, challenges, flags_by_challenge):
    challenge_name = ""
    flag_localization = ""
    flag_script = ""
    user = "root"

    for k, v in c.labels.items():
        if k == "challenge-name":
            challenge_name = v
        elif k == "flag-localization":
            flag_localization = v
        elif k == "flag-script":
            flag_script = v

    if not challenge_name:
        log.warning(f"challenge_name not defined on {c.name}")
        return

    try:
        challenge_id = challenges[challenge_name]
    except KeyError:
        log.warning(f"Challenge - {challenge_name} - not found ")
        return

    if not flag_localization and not flag_script:
        log.warning(f"neither flag_localization or flag_script is defined")
        return

    new_flag = "flag{%s}" % token_hex(16)

    if flag_localization:
        _, s = c.exec_run("/bin/sh -c 'cat >" + flag_localization + "'", stdout=False, stderr=False, stdin=True,
                          socket=True, tty=True)
        s._sock.send(new_flag.encode())
        s._sock.send(b"\n\x04")
        s._sock.close()
        s.close()
    else:
        result, _ = c.exec_run([flag_localization, new_flag])
        if result != 0:
            log.warning(f"Error running command {flag_localization} on {c.name}")
            return

    ctfd_client.add_flag(challenge_id, new_flag)

    try:
        flags = flags_by_challenge[challenge_id]
        if len(flags) > 1:  # this is to ensure there are two flags
            flags.sort()
            ctfd_client.delete_flag(flags[0])
    except KeyError:
        pass

    log.info(f"Challenge flag from {challenge_name} was updated.")


def deploy_flags(ctfd_client, interval):
    challenges = process_challenges(ctfd_client.get_challenges())
    flags_by_challenge = process_flags(ctfd_client.get_flags())
    docker_client = from_env()
    containers = docker_client.containers.list(filters={"label": "dynamic-label=true"})
    for c in containers:
        deploy_container(c, ctfd_client, challenges, flags_by_challenge)

    scheduler.enter(interval * 60, 1, deploy_flags, (ctfd_client, interval))


def main():
    global scheduler

    keys = ["CTFD_URL", "TOKEN"]
    config = {}

    for i in keys:
        resul = getenv(i)
        if resul is None:
            log.fatal(i + " isn't defined!")
            exit(1)
        else:
            config[i] = resul

    config["TIME_INTERVAL"] = float(getenv("TIME_INTERVAL", "5"))

    ctfd_client = CTFDClient(config["TOKEN"], config["CTFD_URL"])

    scheduler = sched.scheduler(time.time, time.sleep)

    deploy_flags(ctfd_client, config["TIME_INTERVAL"])

    log.info("Start installing  flags")

    Process(target=search_for_new_containers, args=(ctfd_client,)).start()
    scheduler.run()


if __name__ == '__main__':
    main()
