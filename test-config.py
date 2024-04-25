global config

# Addresses of devices with which to test.
config['devices'] = {}
config['devices']['AWG5014B'] = {
	'address': {'ip_address': '192.0.2.123'},
	'manufacturer': 'Tektronix',
	'model': 'AWG5014B',
}
config['devices']['DM34410A'] = {
	'address': {'gpib_board': 0, 'gpib_pad': 1},
	'manufacturer': 'Agilent',
	'model': '34410A',
}
config['devices']['VoltageSource'] = {
	'address': {'usb_resource': 'USB0::0x3923::0x7166::01234567::RAW'},  #This is the wrong address
	'manufacturer': 'IQC',
	'model': 'Voltage source',
}
config['devices']['ch6VoltageSource'] = {
	'address': {'usb_resource': 'USB0::0x3923::0x7166::01300DB9::RAW'},
	'manufacturer': 'IQC',
	'model': 'ch6 Voltage source',
}
config['devices']['TC335'] = {
	'address': {'gpib_board': 0, 'gpib_pad': 1}, #This address is wrong.
	'manufacturer': 'Lakeshore',
	'model': '335 Temperature Controller',
}
config['devices']['Model4G'] = {
	'address': {'gpib_board': 0, 'gpib_pad': 23},
	'manufacturer': 'Cryomagnetics',
	'model': 'Model 4G',
}
