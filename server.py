#!/usr/bin/env python
version = "1.0"

#DNS Proxy (TCP < - > TCP/TLS)
#For the good people@n26
#by Francisco Fregona

################################################################################
# Imports
################################################################################
import socket
import ssl
import sys
import argparse
import logging


################################################################################
# Definitions
################################################################################
CALocation = "/etc/ssl/certs/ca-certificates.crt"

# Dictionary containing other DNS/TLS services to choose from.
# Set cloudflare's 1.1.1.1 as the default but offer with command line options.
# TODO: On failure to reach or resolve, try the next server in this list.
Providers = {
"Cloudflare1": ("cloudflare-dns.com","1.1.1.1", 853),
"Cloudflare2": ("cloudflare-dns.com","1.0.0.1", 853),
"Quad91": ("https://www.quad9.net","9.9.9.9", 853),
"Quad92": ("https://www.quad9.net","149.112.112.112", 853),
"CleanBrowsing1": ("https://cleanbrowsing.org","185.228.168.168", 853),
"CleanBrowsing2": ("https://cleanbrowsing.org","185.228.168.169", 853)
}

SelectedProvider = ""

# Defaults. Overwriten below.
DNSServerURL = "cloudflare-dns.com"
DNSServerIP =  "1.1.1.1"
DNSServerPort = 853
#Port and address this server will listen to. Standard DNS port is 53.
ServicePort = 53
# A bind address of 0.0.0.0 means it will listen/serve con all interfaces.
# TODO: Add an option for this parameter.
bindAddress = '0.0.0.0'


################################################################################
# Conveniences
################################################################################
# Time saving: to aid in the debug, the server process prints its own IP address
# and port before starting with the rest.
def printIPandPort():
	import subprocess
	serverIp = subprocess.check_output(["hostname", "-I"])
	logging.info(serverIp)
	logging.info("Listening on port {0}".format(ServicePort))



################################################################################
# Main
################################################################################
# Parameters and logging first.
if __name__ == "__main__":
	parser = argparse.ArgumentParser(
		description="DNS Proxy for N26's SRE Challenge.",
		epilog="TCP -> TCP/TLS. (c)FranciscoFregona@gmail.com. Sep/18")
	parser.add_argument('-v','--version', #
		action='version',
		version='%(prog)s version ' + version,
		help='Prints program version and exits.'
		)
	parser.add_argument('-d',
		type=str,
		choices=["CRITICAL","ERROR","WARNING","INFO","DEBUG","NOTSET"],
		required=False,
		help='(Optional) Show debug information.',
		dest='debug',
		default='CRITICAL'
		)
	parser.add_argument('-p',
		# nargs='?',
		type=int,
		dest='ServicePort',
		required=False,
		default=53,
		help='Port of service for the clients. Default: 53',
		)
	parser.add_argument('-P', 
		type=str,
		choices=["Cloudflare1","Cloudflare2","Quad91","Quad92",\
				"CleanBrowsing1","CleanBrowsing2"],
		required=False,
		default="Cloudflare1",
		dest="SelectedProvider",
		help="""(Optional) Select the provider for the DNS/TLS Service.
		\tChoices are:
		\t\tCloudflare1 (default, 1.1.1.1),
		\t\tCloudflare2,
		\t\tQuad91,
		\t\tQuad92,
		\t\tCleanBrowsing1,
		\t\tCleanBrowsing2
		""",
		)

################################################################################
# Parameters
################################################################################
	args =  parser.parse_args()
	
	debugs = {
		"CRITICAL": logging.CRITICAL,
		"ERROR": logging.ERROR,
		"WARNING": logging.WARNING,
		"INFO": logging.INFO,
		"DEBUG": logging.DEBUG,
		"NOTSET": logging.NOTSET,
	}

	logging.basicConfig(level=debugs[args.debug])


	logging.info("""Parameters received:
		debug: {}
		ServicePort: {}
		SelectedProvider: {}
		""".format(args.debug, args.ServicePort, args.SelectedProvider))

	query = ''
	response = ''

	################################################################################
	# Preparations for the connections
	################################################################################

	DNSServerURL = Providers[args.SelectedProvider][0]
	DNSServerIP =  Providers[args.SelectedProvider][1]
	DNSServerPort = Providers[args.SelectedProvider][2]
	ServicePort = args.ServicePort

	printIPandPort()
	
	# Preparation for the client side, contacting cloudflare servers
	try:
		context = ssl.SSLContext(ssl.PROTOCOL_TLS)
		context.verify_mode = ssl.CERT_REQUIRED
		context.check_hostname = True
		context.load_verify_locations(CALocation)
	except socket.error, msg:
		print "Failed to create client socket. Error Code: " + \
				str(msg[0]) + ' Message ' + msg[1]
		sys.exit()


	# Preparation for the server side, listening for the client
	try:
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		logging.debug("Socket created")
	except socket.error, msg:
		print "Failed to create client socket. Error Code: " + \
				str(msg[0]) + ' Message ' + msg[1]
		sys.exit()
	# Bind socket to local host and port
	try:
		logging.debug("Trying with port {0}".format(ServicePort))
		sock.bind((bindAddress, ServicePort))
		sock.listen(1)
		clientConnection, clientAddress = sock.accept()
		logging.debug('Connection address: {0}'.format(clientAddress))
	except socket.error , msg:
		print "Bind failed. Error Code : " + str(msg[0]) + " Message " + msg[1]
		sys.exit()
	logging.debug("Socket bind complete")
	################################################################################
	# Main loop
	################################################################################
	while 1:
		query = clientConnection.recv(1024)
		if not query: break
		logging.debug("Received {0} bytes from {1}\nContaining: {2}".format(len(query),\
				clientAddress, bytes(query)))
		# Connecting...
		try:
			serverConnection = context.wrap_socket(socket.socket(socket.AF_INET),\
				server_hostname=DNSServerURL)
			serverConnection.connect((DNSServerIP, DNSServerPort))
			serverConnection.sendall(query)
			while 1:
				response = serverConnection.recv(1024)
				if not response: break
				clientConnection.sendall(response)
				logging.debug("received data:", response)
				clientConnection.close()
				break
		except socket.error, msg:
			print "Failed while contacting DNS provider. Error Code: " + \
					str(msg[0]) + " Message " + msg[1]
			sys.exit()
		serverConnection.close()
		break

