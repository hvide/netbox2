from __future__ import annotations
import logging

import typing

from pynetbox import api
from pynetbox.core.query import RequestError
import pandas as pd

from app.rows import BackToBack, CircuitTermination


logger = logging.getLogger()


class NetboxClient(api):
    def __init__(self, url: str, token: str) -> NetboxClient:
        super(NetboxClient, self).__init__(url, token)

        logger.info("Netbox Client Client successfully initialized")

    def create_circuit(self, data: typing.Type[CircuitTermination]):

        try:
            circuit = self.circuits.circuits.get(cid=data.cid)
        except ValueError as e:
            logger.warning(
                f"There is already more then one circuit with name: {data.cid}: {e}")
            return None

        if circuit is None:
            circuit_id = self.circuits.circuits.create(data.to_dict('circuit'))
            circuit = self.circuits.circuits.get(cid=circuit_id)
            logger.info(
                f"Circiut: {circuit.cid} Has been created. - http://netbox.bsonetwork.net/circuits/circuits/{circuit.id}/")
            return circuit.id
        else:
            logger.info(
                f"Circiut: {circuit.cid} Already exist. - http://netbox.bsonetwork.net/circuits/circuits/{circuit.id}/")

            return circuit.id

    def create_termination(self, data: typing.Type[CircuitTermination]) -> int:

        termination = self.circuits.circuit_terminations.create(
            data.to_dict('termination'))

        logger.info(
            f"Termination ID: {termination.id} Has been created.")
        return termination.id

    def create_cable(self, data: typing.Type[CircuitTermination | BackToBack]) -> int:

        try:
            cable = self.dcim.cables.create(data.to_dict('cable'))

            logger.info(
                f"Cable {cable} with ID: {cable.id} Has been created.")

            return cable
        except RequestError as e:
            logger.warning(
                f"Something was wrong while creating the cable. Please check devices and ports: {e}")
            return None

    def get_available_termination_side(self, data) -> str:

        termination_a_id, termination_z_id = self._get_circuit_terminations(
            data.circuit_id)

        if termination_a_id is None:
            term_side = "A"
            return term_side

        elif termination_z_id is None:

            termination_a = self.circuits.circuit_terminations.get(
                termination_a_id)

            if termination_a.cable is None:
                logger.warning("Termination exist but not connected.")
                return None

            elif termination_a.cable_peer.display == str(data.port) and \
                    termination_a.cable_peer.device.id == data.device_id:
                logger.warning("This termination/cable already exist.")
                return None

            else:
                term_side = "Z"
                return term_side

        else:
            logger.warning(f"Skipping Termination/Cable for {data.cid}.")
            return None

    def _get_circuit_terminations(self, circuit_id: int):

        circuit = self.circuits.circuits.get(circuit_id)

        termination_a_id = None
        termination_z_id = None

        if circuit.termination_a is not None:
            termination_a_id = circuit.termination_a.id

        if circuit.termination_z is not None:
            termination_z_id = circuit.termination_z.id

        return termination_a_id, termination_z_id

    def create_device_bulk(self, serials: typing.List, device_type: typing.List):

        keys = ['serial', 'device_type']

        devices = [dict(zip(keys, l)) for l in zip(serials, device_type)]

        data = []

        for device in devices:

            dict = {
                'device_role': 26,
                'device_type': device['device_type'],
                'serial': device['serial'],
                'site': 118,
                'rack': 424,
                'custom_fields': {'Odoo Device ID': 'Missing'}
            }

            data.append(dict)

        new_devices = self.dcim.devices.create(data)

        for new_device in new_devices:
            print(new_device.url)

        return new_devices
