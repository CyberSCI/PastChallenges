# jenotes

**Author:** _tyler_

**Category:** pwn

## Description

A pwn challenge based on 

### Files

release_files/jenotes.tar.xz

### Host
```
10.0.2.81
```
## Part 1

_Copy this section as many times as there are separate flags/steps in your challenge. They will be separate challenges in CTFd._

**CTFd name:** jenotes

### CTFd Description

We've vibecoded our own completely secure tiny notes service. Since we know you guys love poisoning the tcache, we took it away! Courtesy of a fun allocator from 2012.

Every note is 64 bytes and contains absolutely no heap metadata. No heap exploitation for you!

```
nc 10.0.2.81 1341
```

### Depends on

N/A

### Flag

<details>
<summary>(expand to read)</summary><br>

cybersci{j3m4ll0c_run_h34d3r_c0rrupt3d!}

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

Main bug is a 12 byte out of bounds write (OOB) in edit().

Main solve stages:
1. Fill run 1 regions
2. Add another item/allocation, which is now in run 2
3. Call edit(31), which you can use the OOB to corrupt run 2's header so that R2->regs_minelm = -2
4. Add(32), which returns a region from run 1 (because of the negative regs_minelm). We can now corrupt the region to use show() and edit() to leak and corrupt the global offset table (GOT) entry for atoi()
5. Use that GOT overwrite to call system('/bin/sh')

</details>

## Setup instructions

docker build -t jenotes_chal .

docker run -d --restart always -p 1341:1341 --name jenotes jenotes_chal
