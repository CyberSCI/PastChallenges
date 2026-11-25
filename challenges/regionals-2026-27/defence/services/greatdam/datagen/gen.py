import random
from datetime import timedelta
from faker import Faker

if __name__ == "__main__":
    text = ""

    fake = Faker()

    levels = ["INFO", "INFO", "INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"]

    for i in range(900):
        log = fake.ipv4_private(network=False, address_class="c") + "\n"
        num_lines = random.randint(20, 100)

        for line in range(num_lines):
            level = random.choice(levels)
            size = random.randint(120, 50_000)
            user = fake.user_name()
            timestamp = fake.date_time_between(start_date="-1d", end_date="now")

            log += f"{timestamp:%Y-%m-%d %H:%M:%S} [{level:<8}]: {size} {user}\n"

        filename = fake.unique.file_name(extension="log")

        with open(f"logs/{filename}", "w") as f:
            f.write(log)
