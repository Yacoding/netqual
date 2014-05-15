import subprocess
import tempfile

def shell_cmd(arr):
	if subprocess.call(arr) != 0:
		raise RuntimeError("Command failed")

def bash_cmd(s):
	ret = subprocess.call(s, shell=True)
	if ret != 0:
		raise RuntimeError("Command failed with code {0}".format(ret))

def enable_ipv4_routing():
	open("/proc/sys/net/ipv4/ip_forward", "w").write("1")

# System structure
WAN_IF="ethwan"
PASSTHROUGH_IF="ethpass"
LANMON_IF="ethlanmon"
WLANMON_IF="ethwlanmon"
OOB_IF="usb0"

def clear_net():
	# First disable all interfaces to avoid security breaches
	# as we bring down the firewall

	shell_cmd(["ifconfig", WAN_IF, "down"])
	shell_cmd(["ifconfig", PASSTHROUGH_IF, "down"])

	shell_cmd(["iptables", "-P", "INPUT", "ACCEPT"])
	shell_cmd(["iptables", "-P", "OUTPUT", "ACCEPT"])

	shell_cmd(["iptables", "-F", "INPUT"])
	shell_cmd(["iptables", "-F", "OUTPUT"])
	shell_cmd(["iptables", "-F", "FORWARD"])
	shell_cmd(["iptables", "-t", "nat", "-F", "POSTROUTING"])
	bash_cmd("killall dhclient || true")
	bash_cmd('pkill -f "^udhcpd -S /tmp" || true')

def udhcpd(iface, lower, upper, dns, router):
	config_file="""start {lower}
end {upper}
interface {iface}
option subnet 255.255.255.0
option dns {dns}
option router {router}
""".format(lower=lower, upper=upper, iface=iface, dns=dns, router=router)

	f = tempfile.NamedTemporaryFile(delete=False)
	f.write(config_file)
	f.flush()
	name = f.name

	shell_cmd(["udhcpd", "-S", name]) 

def main():
	bash_cmd("echo none >/sys/class/leds/beaglebone\:green\:usr0/trigger")
	bash_cmd("echo 1 >/sys/class/leds/beaglebone\:green\:usr0/brightness")
	clear_net()

	# Setup firewall
	shell_cmd(["iptables", "-P", "INPUT", "DROP"])
	shell_cmd(["iptables", "-P", "OUTPUT", "DROP"])
	shell_cmd(["iptables", "-P", "FORWARD", "DROP"])

	# Allow anything on oob interface
	shell_cmd(["iptables", "-A", "INPUT", "-i", OOB_IF, "-j", "ACCEPT"])
	shell_cmd(["iptables", "-A", "OUTPUT", "-o", OOB_IF, "-j", "ACCEPT"])

	# Allow all traffic on wan interface
	shell_cmd(["iptables", "-A", "OUTPUT", "-o", WAN_IF, "-j", "ACCEPT"])
	shell_cmd(["iptables", "-A", "INPUT", "-i", WAN_IF, "-m", "state", "--state", "ESTABLISHED,RELATED", "-j", "ACCEPT"])

	# Allow all traffic on passthrough interface
	shell_cmd(["iptables", "-A", "OUTPUT", "-o", PASSTHROUGH_IF, "-j", "ACCEPT"])
	shell_cmd(["iptables", "-A", "INPUT", "-i", PASSTHROUGH_IF, "-m", "state", "--state", "ESTABLISHED,RELATED", "-j", "ACCEPT"])
	shell_cmd(["iptables", "-A", "INPUT", "-i", PASSTHROUGH_IF, "-p", "udp", "--dport", "bootps", "-j", "ACCEPT"])
	shell_cmd(["iptables", "-A", "INPUT", "-i", PASSTHROUGH_IF, "-p", "tcp", "--dport", "ssh", "-j", "ACCEPT"])

	shell_cmd(["iptables", "-t", "nat", "-A", "POSTROUTING", "-o", WAN_IF, "-j", "MASQUERADE"])
	shell_cmd(["iptables", "-A", "FORWARD", "-i", PASSTHROUGH_IF, "-o", WAN_IF, "-j", "ACCEPT"])
	shell_cmd(["iptables", "-A", "FORWARD", "-i", WAN_IF, "-o", PASSTHROUGH_IF, "-m", "state", "--state", "RELATED,ESTABLISHED", "-j", "ACCEPT"])

	# lanmon is just for our outbound traffic
	shell_cmd(["iptables", "-A", "OUTPUT", "-o", LANMON_IF, "-j", "ACCEPT"])
	shell_cmd(["iptables", "-A", "INPUT", "-i", LANMON_IF, "-m", "state", "--state", "ESTABLISHED,RELATED", "-j", "ACCEPT"])

	# DMZ
	#shell_cmd(["iptables", "-t", "nat", "-A", "PREROUTING", "-i", "ethwan", "-j", "DNAT", "--to-destination", "10.254.0.2"])

	enable_ipv4_routing()

	shell_cmd(["dhclient", WAN_IF])
	shell_cmd(["dhclient", "-e", "IF_METRIC=50", LANMON_IF])
	shell_cmd(["ifconfig", PASSTHROUGH_IF, "up", "10.254.0.1", "netmask", "255.255.255.0"])
	# FIXME: use dns from dhcp
	udhcpd(PASSTHROUGH_IF, "10.254.0.2", "10.254.0.2", "8.8.8.8", "10.254.0.1")

	bash_cmd("echo 0 >/sys/class/leds/beaglebone\:green\:usr0/brightness")

main()