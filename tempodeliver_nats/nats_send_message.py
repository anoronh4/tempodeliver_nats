import argparse, sys
import asyncio
import json
import os
import signal
from nats.aio.client import Client as NATS
import ssl
import configparser


def show_usage():
    usage = """
nats-req SUBJECT [-d DATA] [-s SERVER]
Example:
nats-req hello -d world -s nats://127.0.0.1:4222 -s nats://127.0.0.1:4223
"""
    print(usage)


def show_usage_and_die():
    show_usage()
    sys.exit(1)


async def run(loop):
    parser = argparse.ArgumentParser()

    # e.g. nats-req hello -d "world" -s nats://127.0.0.1:4222 -s nats://127.0.0.1:4223
    parser.add_argument("subject", default="hello", nargs="?")
    parser.add_argument("-d", "--data", default="hello world")
    parser.add_argument("-s", "--servers", default=[], action="append")
    parser.add_argument("--creds", default="")
    parser.add_argument("--cert")
    parser.add_argument("--key")
    parser.add_argument("--cfg")
    args = parser.parse_args()

    nc = NATS()

    async def error_cb(e):
        print("Error:", e)

    async def closed_cb():
        print("Connection to NATS is closed.")

    async def reconnected_cb():
        print(f"ReConnected to NATS at {nc.connected_url.netloc}...")

    options = {"error_cb": error_cb, "closed_cb": closed_cb, "reconnected_cb": reconnected_cb}
    
    if len(args.creds) > 0:
        print("using creds")
        options["user_credentials"] = args.creds

    config_dict = dict()
    section_header='default'
    if args.cfg:
        config_parser = configparser.RawConfigParser()
        try:
            config_parser.read(args.cfg)
            section_header=config_parser.sections()[0]
        except configparser.MissingSectionHeaderError as m:
            with open(args.cfg,'r') as f:
                cfg_content = '[default]\n' + f.read()
            config_parser.read_string(cfg_content) 
        for i in config_parser[section_header]:
            config_dict[i] = config_parser.get(section_header,i)

                
        options["user"] = config_dict['nats.consumer_name']
        options["password"] = config_dict['nats.consumer_password']
        options["servers"] = config_dict['nats.url']


    if args.cert and args.key:
        print("Creating context based on provided cert and key")
        #ssl._create_default_https_context = ssl._create_unverified_context
        ssl_ctx = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
        ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
        ssl_ctx.load_cert_chain(certfile=args.cert,keyfile=args.key)
        
        options["tls"] = ssl_ctx

    try:
        print("connecting")
        if len(args.servers) > 0:
            options["servers"] = args.servers

        print(options)
        await nc.connect(**options)
    except Exception as e:
        print("error connecting")
        print(e)
        show_usage_and_die()

    print(f"Connected to NATS at {nc.connected_url.netloc}...")
    # msg = await nc.request(args.subject, args.data.encode())
    # subject = msg.subject
    # reply = msg.reply
    # data = msg.data.decode()
    # print("Received a message on '{subject} {reply}': {data}".format(
    #     subject=subject, reply=reply, data=data))
    with open(args.data, "r") as f:
        data = json.load(f)
        data_str = json.dumps(data)
    print(data_str)

    await nc.publish(args.subject, data_str.encode())
    await nc.close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(run(loop))
    finally:
        loop.close()
