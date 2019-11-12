from docopt import docopt
from pyHS100 import Discover, SmartPlug
import subprocess
import re
import sys
import os
import signal

GLOBAL_PROC = None

def sig_term_handler(signal, frame):
	if GLOBAL_PROC:
		GLOBAL_PROC.kill()

	raise SystemExit('Exiting Cog_test script')
	return

def main():
	if __name__ == '__main__':
		args = docopt("""
	cog_test.

	A python test program for Cognitive System interview.

	The program requires Openwrt, Wireless adapter(Configured as AP), and
	TP-Link Smartplug.

	The program use Openwrt's tool "iw" to detect wireless device connection
	and parse its MAC address. If the MAC address matches the program input
	argument, the program will turn on the SmartPlug. If the target MAC
	address left the AP, the program will turn off the SmartPlug.

	Limitation: Script will only run on OpenWrt with only one smartPlug
	            being connected to the AP.

		    This script also only beent tested with one HS105.

	Caveat: "iw event -f" displays multiple message when STA is disconnected
	        Therefore, the output of this program reflects the behavior from
		"iw event -f"

	Usage:
		cog_test.py [options] <mac_address>

	Options:
		-h --help Show this screen.

	""")

		# Register signal
		signal.signal(signal.SIGINT, sig_term_handler)
	
		usr_mac = args['<mac_address>'].lower()

		# Check input argument
		if check_mac(usr_mac):
			raise ValueError("Input Error (MAC Address)")

		# Check OS & Distro
		if bool(is_os_valid()):
			pass
		else:
			raise RunTimeError("Script must be run on OpenWrt")

		# Get Wireless Dev
		dev_name = get_wireless_dev()

		if dev_name is None:
			raise RuntimeError(r"Wireless not up or not configured"
					   r" as AP")

		# Initialize plug object
		plug_ip = get_plug_ip()

		if plug_ip is None:
			raise RuntimeError("Smartplug is not detected")
		else:
			plug = SmartPlug(plug_ip)

		# Using "iw" pipe result if STA is being added or deleted
		GLOBAL_PROC = subprocess.Popen(["iw", "event", "-f"],\
						stdin = subprocess.PIPE,\
						stdout =subprocess.PIPE);

		# Regex for iw output and for MAC address
		iwRegx = re.compile(r'(\bnew\b)|(\bdel\b)|'
			    r'((([a-fA-F\d]){2}:){5}'
			    r'(([a-fA-F\d]){2}))')

		# Check if the desired MAC has already been connected
		if bool(is_mac_exist(usr_mac, dev_name)):
			plug.turn_on()
		else:
			plug.turn_off()

		print("Script is ready! Waiting for", usr_mac, "action!")

		# Main running loop
		while True:
			output =  GLOBAL_PROC.stdout.readline()
			m = iwRegx.findall(output.decode('utf-8'))
			if m:
				for i in m[0]:
					if i:
						act = i

				mac = m[1][2]
	
			if mac == usr_mac:
				if act == "new":
					print(usr_mac, "has connected")
					plug.turn_on()
				elif act == "del":
					print(usr_mac, "has disconnected")
					plug.turn_off()
				else:
					pass

def check_mac(mac):
	macRegx = re.compile(r'((([a-fA-F\d]){2}:){5}'
			     r'(([a-fA-F\d]){2}))')

	# Sanitize input argument using MAC regex
	if macRegx.match(mac) is None:
		return -1
	else:
		return 0

def get_plug_ip():

	print("Checking TP-Link Smartplug connection...")

	# Check smartplug connection
	sp_dict = Discover.discover();

	if bool(sp_dict):
		for sp_ip in sp_dict:
			return sp_ip
	else:
		pass

def is_os_valid():

	print("Checking if OS is valid...")

	# Check OS type
	if (os.uname().sysname != "Linux"):
		return False
	else:
		pass

	# os.uname() doesn't not contain distro name in OpenWrt
	# Hence the extra query

	proc = subprocess.Popen(["cat", "/proc/version"],\
				stdin = subprocess.PIPE,\
				stdout =subprocess.PIPE);

	output =  proc.stdout.readline()

	if (output.decode("utf-8").find('OpenWrt') == -1):
		return False
	else:
		return True

def is_mac_exist(mac, dev):
	print("Checking if MAC has already been connected...")

	proc = subprocess.Popen(["iwinfo", dev, "assoclist"],\
				stdin = subprocess.PIPE,\
				stdout =subprocess.PIPE);

	while True:
		output =  proc.stdout.readline()

		if not output:
			return False

		if (output.decode("utf-8").lower().find(mac) == -1):
			pass
		else:
			return True

def get_wireless_dev():
	
	up_flag = None
	ap_flag = None

	up_str = '"up": true'
	ap_str = '"mode": "ap"'	
	dev_str = "ifname"

	print("Checking wireless adapter...")

	proc = subprocess.Popen(["wifi", "status"],\
				stdin = subprocess.PIPE,\
				stdout =subprocess.PIPE);

	while True:
		output =  proc.stdout.readline()

		output = output.decode("utf-8").lower()

		if not output:
			break

		if (output.find(up_str) == -1):
			pass
		else:
			up_flag = True

		if (output.find(ap_str) == -1):
			pass
		else:
			ap_flag = True

		if (output.find(dev_str) == -1):
			pass
		else:
			dev = output.split(':')
			dev = re.search('"(.*)"', dev[1])
			dev = dev.group(1)

	if (up_flag) and (ap_flag):
		return dev
main()
