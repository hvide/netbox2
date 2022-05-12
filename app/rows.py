from __future__ import annotations
import logging
import sys

import typing
from xmlrpc.client import Boolean

logger = logging.getLogger()


class CircuitTermination:
    def __init__(self, nb, data: typing.Dict) -> CircuitTermination:

        # Circuit
        self.cid = data['cid']
        self.provider_name = data['provider_name']
        self.circuit_type_name = data['type_name']
        self.circuit_status = data['status']
        self.site_name = data['site_name']
        self.device = data['device']
        self.port = data['port']
        self.circuit_description = data['cid']
        self.circuit_custom_fields = {"Odoo Link ID": "Missing"}
        self.tenant = 4

        try:
            self.provider = (nb.circuits.providers.get(
                name=self.provider_name)).id
        except AttributeError as e:
            logger.error(
                f"Could not find any Provider with name: {self.provider_name}: {e}")
            sys.exit(1)

        try:
            self.circuit_type = (nb.circuits.circuit_types.get(
                name=self.circuit_type_name)).id
        except AttributeError as e:
            logger.error(
                f"Could not find any Circuit Type with name: {self.circuit_type_name}: {e}")
            sys.exit(1)

        try:
            self.site = (
                nb.dcim.sites.get(name=self.site_name)).id
        except AttributeError as e:
            logger.error(
                f"Could not find any Site type with name: {self.site_name}: {e}")
            sys.exit(1)

        # Termination
        self.circuit_id = None
        self.term_side = None
        self.speed = data['port_speed'] * 1000000
        self.xconnect_id = data['xconnect_id']

        # Cable
        termination_type = {
            'I': 'dcim.interface',
            'F': 'dcim.frontport',
            'R': 'dcim.rearport',
        }

        self.termination_a_type = 'circuits.circuittermination'
        self.termination_a_id = None

        self.device_id = self._get_device_id(nb, data['device'])

        try:

            if data['port_type'] == 'I':
                self.termination_b_id = (nb.dcim.interfaces.get(
                    name=self.port, device_id=self.device_id)).id
                self.termination_b_type = 'dcim.interface'
            elif data['port_type'] == 'F':
                self.termination_b_id = (nb.dcim.front_ports.get(
                    name=self.port, device_id=self.device_id)).id
                self.termination_b_type = 'dcim.frontport'
            elif data['port_type'] == 'R':
                self.termination_b_id = (nb.dcim.rear_ports.get(
                    name=self.port, device_id=self.device_id)).id
                self.termination_b_type = 'dcim.rearport'
            else:
                logger.error(
                    f"Couldn't retreive termination_b values from Port ID: {self.port}, Device ID: {self.device_id}")

        except AttributeError as e:
            logger.error(
                f"Could not find the termination_b_id: Port: {self.port} Device: {self.device_id}: {e}")
            sys.exit(1)

        self.cable_type = 'smf'
        self.cable_status = 'connected'
        self.cable_color = 'ffeb3b'
        self.cable_id = None

        logger.info(
            f"Row object for circuit {self.cid} successfully initialized.")

    def _get_device_id(self, nb, device):
        try:
            if device.isdigit():
                return int(device)
            else:
                return (nb.dcim.devices.get(name=self.device)).id
        except AttributeError as e:
            logger.error(
                f"Could not find the Device: {device}: {e}")
            sys.exit(1)

    def set_circuit_id(self, circuit_id: str) -> Boolean:
        self.circuit_id = circuit_id
        self.circuit_url = f"http://netbox.bsonetwork.net/circuits/circuits/{circuit_id}/"
        logger.debug(f"Circuit ID side has been set to {circuit_id}")
        return True

    def set_termination_side(self, term_side: str) -> Boolean:
        self.term_side = term_side
        logger.debug(f"term_side has been set to {term_side}")
        return True

    def set_termination_a_id(self, termination_a_id: str) -> Boolean:
        self.termination_a_id = termination_a_id
        logger.debug(f"termination_a_id has been set to {termination_a_id}")
        return True

    def set_cable_id(self, cable_id: str) -> Boolean:
        self.cable_id = cable_id
        logger.debug(f"cable_id has been set to {cable_id}")
        return True

    def to_dict(self, object_type: typing.Type[CircuitTermination]) -> typing.Dict:

        if object_type == "circuit":
            return {
                'cid': self.cid,
                'provider': self.provider,
                'type': self.circuit_type,
                'status': self.circuit_status,
                'tenant': self.tenant,
                'description': self.circuit_description,
                'custom_fields': self.circuit_custom_fields,
            }

        elif object_type == "termination":
            return {
                'circuit': self.circuit_id,
                'term_side': self.term_side,
                'site': self.site,
                'port_speed': self.speed,
                'xconnect_id': self.xconnect_id,
                'description': self.xconnect_id,
            }

        elif object_type == "cable":
            return {
                'termination_a_type': self.termination_a_type,
                'termination_a_id': self.termination_a_id,
                'termination_b_type': self.termination_b_type,
                'termination_b_id': self.termination_b_id,
                'type': self.cable_type,
                'status': self.cable_status,
                'color': self.cable_color,
            }
        else:
            return None

    def __repr__(self) -> str:
        return self.cid


class BackToBack:
    def __init__(self, nb, data: typing.Dict) -> BackToBack:

        # self.device_a = data['device_a']
        # self.port_a = data['port_a']
        # self.port_a_type = data['port_a_type']
        # self.device_b = data['device_b']
        # self.port_b = data['port_b']
        # self.port_b_type = data['port_b_type']
        self.cable_type = 'smf'
        self.cable_status = 'connected'
        self.cable_color = 'ffeb3b'

        self.a_end = {'device': data['device_a'],
                      'port': data['port_a'], 'port_type': data['port_a_type']}
        self.b_end = {'device': data['device_b'],
                      'port': data['port_b'], 'port_type': data['port_b_type']}

        terminations_id = []
        terminations_type = []

        for end in self.a_end, self.b_end:

            device_id = self._get_device_id(nb, end['device'])

            try:
                if end['port_type'] == 'I':
                    terminations_id.append((nb.dcim.interfaces.get(
                        name=end['port'], device_id=device_id)).id)
                    terminations_type.append('dcim.interface')
                elif end['port_type'] == 'F':
                    terminations_id.append((nb.dcim.front_ports.get(
                        name=end['port'], device_id=device_id)).id)
                    terminations_type.append('dcim.frontport')
                elif end['port_type'] == 'R':
                    terminations_id.append((nb.dcim.rear_ports.get(
                        name=end['port'], device_id=device_id)).id)
                    terminations_type.append('dcim.rearport')
                else:
                    logger.error(
                        f"Couldn't retreive termination_b values from Port ID: {end['port']}, Device ID: {end['device_id']}")

            except AttributeError as e:
                logger.error(
                    f"Could not find the termination_b_id: Port: {end['port']} Device: {end['device_id']}: {e}")
                sys.exit(1)

        self.termination_a_type = terminations_type[0]
        self.termination_a_id = terminations_id[0]
        self.termination_b_type = terminations_type[1]
        self.termination_b_id = terminations_id[1]

    def _get_device_id(self, nb, device):
        try:
            if device.isdigit():
                return int(device)
            else:
                return (nb.dcim.devices.get(name=device)).id
        except AttributeError as e:
            logger.error(
                f"Could not find the Device: {device}: {e}")
            sys.exit(1)

    def to_dict(self, object_type: typing.Type[BackToBack]) -> typing.Dict:

        if object_type == "cable":
            return {
                'termination_a_type': self.termination_a_type,
                'termination_a_id': self.termination_a_id,
                'termination_b_type': self.termination_b_type,
                'termination_b_id': self.termination_b_id,
                'type': self.cable_type,
                'status': self.cable_status,
                'color': self.cable_color,
            }
