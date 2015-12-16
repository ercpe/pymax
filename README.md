# pymax

[![Build Status](https://travis-ci.org/ercpe/pymax.svg?branch=master)](https://travis-ci.org/ercpe/pymax) [![Coverage Status](https://coveralls.io/repos/ercpe/pymax/badge.svg?branch=master&service=github)](https://coveralls.io/github/ercpe/pymax?branch=master)


# Usage

## Discovery

To find any cube in your network:

    from pymax.cube import Discovery
    
    response = Discovery().discover()
    print(response)

To find a specific cube in your network:

    from pymax.cube import Discovery
    response = Discovery().discover(cube_serial=u'LEQ1154727', discovery_type=Discovery.DISCOVERY_TYPE_NETWORK_CONFIG)
    print(response)
    >>> LEQ1154727: IP: 10.10.10.153, Netmask: 255.255.255.0, Gateway: 10.10.10.1, DNS1: 10.10.10.1, DNS2: 0.0.0.0


## Connecting

    from pymax.cube import Cube, Connection
    
    cube = Cube('192.168.1.123')
    # or
    cube = Cube('192.168.1.123', 62910)
    # or
    cube = Cube(address='192.168.1.123', port=62910)
    # or
    cube = Cube(Connection(('192.168.1.123', 62910))
   
    try:
        cube.connect()
        
        # fun code here
    finally:
        cube.disconnect()


The `Cube` object implements a context manager, so it's easier to write:

    from pymax.cube import Cube
    
    with Cube('192.168.1.123') as cube:
        # fun code here

or, together with a discovery query:

    response = Discovery().discover(cube_serial=u'LEQ1154727', discovery_type=Discovery.DISCOVERY_TYPE_NETWORK_CONFIG)
    with Cube(response.ip_address) as cube:
    	print(cube)

## Basic Usage

    with Cube(response.ip_address) as cube:
    	for room in cube.rooms:
    		print("%s:" % room.name)
    		for device in room.devices:
    			print("  %s (%s), serial: %s" % (device.name, device.type, device.serial))


## Protocol

Resources:

* [https://github.com/Bouni/max-cube-protocol](https://github.com/Bouni/max-cube-protocol)
* [http://www.domoticaforum.eu/viewtopic.php?f=66&t=6654](http://www.domoticaforum.eu/viewtopic.php?f=66&t=6654)

## License

See LICENSE.txt
