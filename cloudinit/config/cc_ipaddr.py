# vi: ts=4 expandtab

import os
import subprocess
from cloudinit.settings import PER_INSTANCE, PER_ALWAYS

frequency = PER_ALWAYS

def __get_system_nics__():
    pfd = subprocess.Popen(['ip', 'link'], stdout=subprocess.PIPE)
    pfd = subprocess.Popen(['grep', '-v', 'link/'], stdin=pfd.stdout, stdout=subprocess.PIPE)
    pfd = subprocess.Popen(['grep', '-v', 'lo:'], stdin=pfd.stdout, stdout=subprocess.PIPE)
    pfd = subprocess.Popen(['awk', '{print $2}'], stdin=pfd.stdout, stdout=subprocess.PIPE)
    pfd = subprocess.Popen(['sed', 's/://g'], stdin=pfd.stdout, stdout=subprocess.PIPE)
    ret = pfd.wait()
    out = pfd.stdout.readlines()
    nic_list = []
    for o in out: nic_list.append(o.replace('\n', ''))
    return nic_list

def handle(name, _cfg, _cloud, log, _args):

    if 'ipaddr' not in _cfg: return
    if not isinstance(_cfg['ipaddr'], list): return
    ipaddr_list = _cfg['ipaddr']
    nic_list = __get_system_nics__()
    
    os.system('service NetworkManager stop')
    for nic in nic_list: os.system('ip link set dev %s down' % nic)

    for ipaddr in ipaddr_list:
        if 'name' in ipaddr:
            name = ipaddr['name']
        elif 'ifnum' in ipaddr:
            try: name = nic_list[ipaddr['ifnum']]
            except: continue
        else: continue
        
        try: mode = ipaddr['mode']
        except: continue
        
        os.system('ip link set dev %s up' % name)
        
        if mode == 'dhcp':
            os.system('/sbin/dhclient -1 -q -lf /var/lib/dhclient/dhclient--%s.lease -pf /var/run/dhclient-%s.pid %s' % (name, name, name))
        elif mode == 'static':
            try: addr = ipaddr['address']
            except: continue
            os.system('ip addr add %s dev %s' % (addr, name))
            try: gw = ipaddr['gateway']
            except: pass
            else: os.system('route add default gw %s' % gw)
        elif mode == 'none':
            pass
