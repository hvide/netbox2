#!/usr/local/bin/python3
import logging
import os

from dotenv import load_dotenv

from app.utils import csv_to_dict
from app.nbclient import NetboxClient
from app.rows import CircuitTermination, BackToBack

logger = logging.getLogger()

logger.setLevel(logging.INFO)  # Overall minimum logging level

# Configure the logging messages displayed in the Terminal
stream_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(levelname)s :: %(message)s')
stream_handler.setFormatter(formatter)
# Minimum logging level for the StreamHandler
stream_handler.setLevel(logging.DEBUG)

# Configure the logging messages written to a file
file_handler = logging.FileHandler('info.log')
file_handler.setFormatter(formatter)
# Minimum logging level for the FileHandler
file_handler.setLevel(logging.DEBUG)

logger.addHandler(stream_handler)
logger.addHandler(file_handler)

load_dotenv()

DIR = os.path.dirname(os.path.realpath(__file__)) + '/'
API_TOKEN = os.getenv('API_TOKEN')
URL = os.getenv('URL')
CSV = DIR + 'data/' + 'dev_to_pp.csv'
# CSV = DIR + 'data/' + 'back_to_back.csv'


if __name__ == '__main__':

    nb = NetboxClient(url=URL, token=API_TOKEN)

    data = csv_to_dict(CSV)

    results = []
    # Loop through data
    for item in data:
        if item['row_type'] == "ct":
            row = CircuitTermination(nb, item)

            circuit_id = nb.create_circuit(row)

            if circuit_id is None:
                results.append((row.cid, None, False))
                continue

            row.set_circuit_id(circuit_id)

            term_side = nb.get_available_termination_side(row)

            if term_side is None:
                # logger.warning(
                #     f"Something went wrong with this termianton/cable. Skipping to next row...")
                results.append((row.cid, row.circuit_url, False))
                continue

            row.set_termination_side(term_side)
            termination_a_id = nb.create_termination(row)
            row.set_termination_a_id(termination_a_id)

            cable = nb.create_cable(row)
            row.set_cable_id = cable.id

            results.append((row.cid, row.circuit_url, True))

        elif item['row_type'] == "bb":

            row = BackToBack(nb, item)

            cable = nb.create_cable(row)
            if cable is None:
                # logger.warning(
                #     f"Something went wrong while creating this cable. Skipping to next row...")
                results.append((cable, row.a_end, False))
                continue
            row.cable_id = cable.id
            row.cable_url = f"https://netbox.bsonetwork.net/dcim/cables/{cable.id}/"
            results.append((cable, row.cable_url, True))

        else:
            logger.info("'row_type' has to be 'ct' or 'bb'. Skipping...")

    logger.info("No more data to process...")

    print('')
    for result in results:
        print(f"{result[2]} - {result[0]} - {result[1]}")
