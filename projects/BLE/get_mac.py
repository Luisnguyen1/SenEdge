import subprocess

def get_mac_from_ip(ip):
    try:
        pid = subprocess.Popen(["arp", "-n", ip], stdout=subprocess.PIPE)
        s = pid.communicate()[0].decode()
        lines = s.split('\n')
        for line in lines:
            if ip in line:
                return line.split()[2]  # Tùy hệ điều hành, có thể là cột 2 hoặc 3
        return None
    except Exception as e:
        return None

print(get_mac_from_ip("192.168.1.1"))