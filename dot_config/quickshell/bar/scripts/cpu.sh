#!/usr/bin/env bash
# CPU usage %
read -r _ u n s i w x y z _ </proc/stat
t1=$((u+n+s+i+w+x+y+z)); idle1=$i
sleep 0.2
read -r _ u n s i w x y z _ </proc/stat
t2=$((u+n+s+i+w+x+y+z)); idle2=$i
dt=$((t2-t1)); di=$((idle2-idle1))
printf '%d%%\n' "$(( dt>0 ? (dt-di)*100/dt : 0 ))"
