import asyncio
import sys
from pathlib import Path
import contextlib
import docker
import tempfile
import os

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from common.client import Client
from common.constants import *

class LandlordClient(Client):
    def __init__(self):
        super().__init__("landlord")
        self.active = asyncio.Event()
        self.nonce = 0
        self.invoice_task = None
        self.INVOICE_INTERVAL = 5

        self.container = None
        self.container_port = 22  
        self.host_port = 45180
        self.docker_client = docker.DockerClient(base_url='unix://var/run/docker.sock')

    async def start_container(self):
        self.logger.info("starting container...")

        try:
            ssh_image = "rastasheep/ubuntu-sshd:18.04"
            self.docker_client.images.pull(ssh_image)

            pub_key = "temporary field" # will inject actual ssh key later

            key_dir = tempfile.mkdtemp()
            auth_key_path = os.path.join(key_dir, "authorized_keys")

            with open(auth_key_path, "w") as f:
                f.write(pub_key)

            os.chmod(auth_key_path, 0o600)
            os.chmod(key_dir, 0o700)

            self.container = self.docker_client.containers.run(
                ssh_image,
                detach=True,
                ports={f"{self.container_port}/tcp": self.host_port},
                volumes={
                    key_dir: {
                        "bind": "/root/.ssh",
                        "mode": "rw"
                    }
                },
                tty=True
            )

            self.container.exec_run(["chown", "-R", "root:root", "/root/.ssh"])

            self.container.exec_run("bash -c 'echo root:docker123 | chpasswd'")
            self.container.exec_run("sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config")

            self.logger.info(f"container started on host port {self.host_port}")

        except Exception as e:
            self.logger.error(f"❌ Failed to start container: {e}")
    
    async def stop_container(self):
        self.logger.info("stopping container...")
        if self.container:
            try:
                self.container.stop()
                self.container.remove()
                self.logger.info("container stopped and removed.")
            except Exception as e:
                self.logger.warning(f"Failed to stop/remove container: {e}")

    async def invoice_loop(self):
        try:
            while self.active.is_set():
                invoice = {
                    "action": SIGN,
                    "payload": {
                        "nonce": self.nonce,
                        "channel_id": self.channel
                    }
                }

                sigL = self.sign(invoice[PAYLOAD])
                invoice[PAYLOAD][LANDLORDSIG] = sigL

                await self.send_message(invoice)
                self.logger.info("sent invoice to renter...")

                self.nonce += 1
                await asyncio.sleep(20)
        except asyncio.CancelledError:
            self.logger.info("send invoices cancelled...")
            raise
    
    async def stop(self):
        self.logger.info("shutdown initiated for landlord client...")

        if self.invoice_task:
            self.invoice_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.invoice_task

        if self.active.is_set():
            self.active.clear()

        await self.stop_container()

        if self.websocket:
            stop_msg = {"action": STOPRENTAL}
            await self.send_message(stop_msg)
            await self.websocket.close()

        self.logger.info("landlord client shutdown complete!")

    async def run(self):
        self.logger.info(f"active is set: {self.active.is_set()}")
        async for raw in self.websocket:
            message = self.deserialize(raw)
            action = message[ACTION]

            if action == STARTRENTAL and not self.active.is_set():
                self.logger.info("starting rental...")
                self.channel = int(message[CHANNELID], 16)
                await self.start_container()
                self.active.set()
                self.invoice_task = asyncio.create_task(self.invoice_loop())
            elif action == STOPRENTAL and self.active.is_set():
                self.logger.info("stopping rental...")
                self.channel = None
                self.active.clear()
                if self.invoice_task:
                    self.invoice_task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await self.invoice_task
                await self.stop_container()
                self.nonce = 0
            elif action == SIGN:
                self.logger.info(f"got signed invoice: {message[PAYLOAD]}")
                self.invoices.append(message[PAYLOAD])
            else:
                self.logger.warning("got an unknown action!")


