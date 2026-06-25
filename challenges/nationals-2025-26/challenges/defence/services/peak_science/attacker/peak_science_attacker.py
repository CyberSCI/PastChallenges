import math
import random
import socket
import os

from siege.attacker.attacker import Attacker
from siege.core.attack_result import AttackResult

messages = [
    "Oh Hi Mark !",
    "hello everynyan",
    "Good Morning Vietnam"
]

folder = os.path.dirname(os.path.abspath(__file__))

def recv_all(sock, chunk_size=4096):
    data = b''
    while True:
        chunk = sock.recv(chunk_size)
        if not chunk:
            break
        data += chunk
    return data.decode('utf-8')


class PeakScienceAttacker(Attacker):

    def submit_request(self, point_solution: int, initial_value: float, x: int, y: int, current_value: float,
                       delta_time: float, max_step: int, k: float, command: str = None):
        parts = [
            str(point_solution),
            str(initial_value),
            str(x),
            str(y),
            str(current_value),
            str(delta_time),
            str(max_step),
            str(k),
        ]
        if command is not None:
            parts.append(command)

        input_str = "\n".join(parts)

        # print("INPUT")
        # print(input_str)
        #
        # print("\n\n")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            s.connect((self.host, self.port))
            s.sendall(input_str.encode('utf-8'))
            s.shutdown(socket.SHUT_WR)
            return_message = recv_all(s)
            return return_message

    def compare_return_to_expected_result(self, return_message: str, path_to_expected_result: str, input_message: str = None):
        file_content: list[str]
        with open(f"{folder}/{path_to_expected_result}", "rt") as f:
            file_content = f.readlines()

        if input_message is not None:
            file_content = [s.replace("{}", input_message) for s in file_content]

        # print("OUTPUT", path_to_expected_result)
        # print(file_content)
        # print(return_message)

        return_message_array = [m for m in return_message.split("\n") if len(m) > 0]
        if len(file_content) - 1 != len(return_message_array):
            return False

        minus_return_code = file_content[1:]
        return all([str.strip(minus_return_code[i]) == str.strip(return_message_array[i]) for i in range(len(minus_return_code))])

    def base_tests(self):
        reqs = [
            self.submit_request(2, 0, 0, 0, 0, 0, 0, 0),
            self.submit_request(21, 0, 0, 0, 0, 0, 0, 0),

            self.submit_request(3, 0, 0, 0, 0, 0, 0, 0),
            self.submit_request(3, 0, 4, 0, 0, 0, 0, 0),
            self.submit_request(3, 0, 1, 0, 0, 0, 0, 0),
            self.submit_request(3, 0, 1, 4, 0, 0, 0, 0),

            self.submit_request(3, 0, 1, 1, 0, 0, -1, 0),
            self.submit_request(3, 0, 1, 1, 0, 0, 11, 0),

            self.submit_request(3, 0, 1, 1, 0, 0, 0, 0),
            self.submit_request(3, 0, 1, 1, 0, 0.6, 0, 0),

            self.submit_request(3, 0, 1, 1, 0, 0.5, 0, -0.1),
            self.submit_request(3, 0, 1, 1, 0, 0.5, 0, 1.1),
        ]

        rets = [
            "base.ps.out",
            "base.ps.out",

            "base.xy.out",
            "base.xy.out",
            "base.xy.out",
            "base.xy.out",

            "base.step.out",
            "base.step.out",

            "base.dt.out",
            "base.dt.out",

            "base.k.out",
            "base.k.out"
        ]

        for i in range(len(reqs)):
            if not self.compare_return_to_expected_result(reqs[i], rets[i]):
                return False
        return True

    def standard_request(self):
        ps = random.randint(3, 20)
        max_cv = 35 if ps > 8 else 15
        rm = self.submit_request(
            ps,
            random.random() * 2,
            random.randint(1, ps),
            random.randint(1, ps),
            random.random() * max_cv,
            0.5,
            random.randint(0, 3),
            random.random(),
        )
        if not self.compare_return_to_expected_result(rm, "std.out"):
            return AttackResult.RESULT_FAILURE
        return AttackResult.RESULT_SUCCESS

    def inf_bypass(self):
        ps = random.randint(3, 20)
        input_message = messages[random.randint(0, len(messages) - 1)]
        rm = self.submit_request(
            ps,
            random.random() * 2 + 9,
            random.randint(1, ps),
            random.randint(1, ps),
            -math.inf,
            0.5,
            random.randint(0, 5),
            random.random(),
            f"echo '{input_message}'"
            )
        if not self.compare_return_to_expected_result(rm, "good.1.out.2", input_message):
            return AttackResult.RESULT_FAILURE
        return AttackResult.RESULT_SUCCESS

    def nan_attack(self):
        ps = random.randint(3, 20)
        randoms = [
            random.random() * 2 + 9,
            random.random() * 10 + 95,
            0.5,
            random.random(),
        ]
        randoms[random.randint(0, 3)] = math.nan
        rm = self.submit_request(
            ps,
            randoms[0],
            random.randint(1, ps),
            random.randint(1, ps),
            randoms[1],
            randoms[2],
            random.randint(0, 5),
            randoms[3],
            f"echo '{messages[random.randint(0, len(messages) - 1)]}'"
        )
        if not self.compare_return_to_expected_result(rm, "bad.1.out"):
            return AttackResult.RESULT_SUCCESS
        return AttackResult.RESULT_FAILURE

    def low_deviation_high_energy(self):
        ps = random.randint(3, 20)
        mean_energy = random.random() * 10 + 95
        rm = self.submit_request(
            ps,
            mean_energy - 5,
            random.randint(1, ps),
            random.randint(1, ps),
            mean_energy,
            0.5,
            0,
            random.random(),
        )
        if not self.compare_return_to_expected_result(rm, "std.out"):
            return AttackResult.RESULT_SUCCESS
        return AttackResult.RESULT_FAILURE

    def low_deviation_low_energy(self):
        return self.standard_request()

    def high_deviation_high_energy(self):
        ps = random.randint(3, 20)
        mean_energy = random.random() * 10 + 95
        rm = self.submit_request(
            ps,
            mean_energy,
            random.randint(1, ps),
            random.randint(1, ps),
            mean_energy + 100,
            0.5,
            0,
            random.random(),
        )
        if not self.compare_return_to_expected_result(rm, "good.2.out.2"):
            return AttackResult.RESULT_FAILURE
        return AttackResult.RESULT_SUCCESS

    def equilibrium(self):
        ps = random.randint(3, 20)
        mean_energy = random.random() * 10
        input_message = messages[random.randint(0, len(messages) - 1)]
        rm = self.submit_request(
            ps,
            mean_energy,
            random.randint(1, ps),
            random.randint(1, ps),
            mean_energy,
            0.5,
            random.randint(0, 5),
            random.random(),
            f"echo '{input_message}'"
        )
        if not self.compare_return_to_expected_result(rm, "good.3.out", input_message):
            return AttackResult.RESULT_FAILURE
        return AttackResult.RESULT_SUCCESS

    def badly_named_variables(self):
        ps = random.randint(3, 20)
        rm = self.submit_request(
            ps,
            random.random() * 2 + 9,
            random.randint(1, ps),
            random.randint(1, ps),
            random.random() * 10 + 50,
            0.5,
            random.randint(0, 2),
            random.random(),
            f"echo '{messages[random.randint(0, len(messages) - 1)]}'"
        )
        if not self.compare_return_to_expected_result(rm, "std.out"):
            return AttackResult.RESULT_SUCCESS
        return AttackResult.RESULT_FAILURE

    def benign_request(self, id: int, tick: int, sequence_no: int):
        random.seed(tick ** (sequence_no + 1))
        #random.seed(122 ** 3)
        print(tick, sequence_no)
        try:
            if not self.base_tests():
                return AttackResult.RESULT_FAILURE
            if id == 1:
                return self.standard_request()
            if id == 2:
                results = [
                    self.high_deviation_high_energy(),
                    self.low_deviation_low_energy()
                ]
                if all([x == AttackResult.RESULT_SUCCESS for x in results]):
                    return AttackResult.RESULT_SUCCESS
                else:
                    return AttackResult.RESULT_FAILURE
            if id == 3:
                return self.equilibrium()
            return AttackResult.RESULT_FAILURE
        except Exception as e:
            print(e)
            return AttackResult.RESULT_DOWN

    def malicious_request(self, id: int, tick: int, sequence_no: int):
        random.seed(tick ** (sequence_no + 1))
        print(tick, sequence_no)
        try:
            if id == 1:
                return self.nan_attack()
            if id == 2:
                return self.low_deviation_high_energy()
            if id == 3:
                return self.badly_named_variables()
            return AttackResult.RESULT_FAILURE
        except Exception as e:
            return AttackResult.RESULT_DOWN
