"""Keep WSL page cache of the weights and release files small while the batch runs.

Usage: python evict_cache.py PID DIR...   (exits when PID exits)
"""
import os
import sys
import time

# Under WSL2 a process can allocate roughly as much GPU memory as Windows has
# free RAM minus ~4.5 GiB, and guest page cache counts against that RAM.
pid, roots = int(sys.argv[1]), sys.argv[2:]
while os.path.exists(f'/proc/{pid}'):
    for root in roots:
        for directory, _, names in os.walk(root):
            for name in names:
                path = os.path.join(directory, name)
                try:
                    fd = os.open(path, os.O_RDONLY)
                except OSError:
                    continue
                os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)
                os.close(fd)
    time.sleep(2)
