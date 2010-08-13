import socket
import select
import struct
import time
import operator
import random
from jaraco.util import QuickTimer

def calculate_checksum(bytes):
	r"""
	Calculate a 16-bit checksum on the bytes.
	
	In partucilar, the 16-bit one's complement of
	the one's complement sum of all 16-bit words
	
	>>> calculate_checksum('ABCD\n')
	31089
	"""
	# null pad bytes to ensure 16-bit values
	if len(bytes) % 2:
		bytes = ''.join((bytes, '\x00'))
	n_values = len(bytes)/2
	values = struct.unpack('%dH' % n_values, bytes)
	sum = reduce(operator.add, values)
	sum = (sum >> 16) + (sum & 0xffff)
	sum += (sum >> 16)
	return (~sum) & 0xffff

def pack_echo_header(id, data, sequence=1):
	ICMP_ECHO_REQUEST = 8
	code = 0
	sequence = 1
	tmp_header = struct.pack('bbHHh', ICMP_ECHO_REQUEST, code, 0, id, sequence)
	checksum = calculate_checksum(tmp_header + data)
	return struct.pack('bbHHh', ICMP_ECHO_REQUEST, code, checksum, id, sequence)

def ping(dest_addr, timeout = 2):
	"""
	Send an ICMP Echo request to a host and return how long it takes.
	
	Raise socket.timeout if no response is received within timeout.
	
	>>> ping('127.0.0.1')
	datetime.timedelta(...)
	"""
	icmp_proto = socket.getprotobyname('icmp')
	icmp_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp_proto)
	icmp_port = 1
	id = random.randint(0,2**16-1)
	data = struct.pack("d", time.clock())+'Q'*192
	data = data[:192]
	header = pack_echo_header(id, data)
	packet = header + data
	icmp_socket.sendto(packet, (dest_addr, icmp_port))
	
	timer = QuickTimer()
	read_fs, write_fs, ex_fs = select.select([icmp_socket], [], [], timeout)
	delay = timer.Stop()
	if not read_fs:
		raise socket.timeout('timed out')

	packet, addr = icmp_socket.recvfrom(1024)
	header = packet[20:28]
	type, code, checksum, recv_id, sequence = struct.unpack('bbHHh', header)
	if recv_id != id:
		raise socket.error('transmission failure ({recv_id} != {id})'.format(**vars()))
	return delay

def wait_for_host(host):
	while True:
		try:
			ping(host)
			break
		except socket.error:
			pass
	import datetime
	return datetime.datetime.now()

		