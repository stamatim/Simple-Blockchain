import hashlib
import json
from time import time
from urllib.parse import urlparse
import requests


class Blockchain(object):
    def __init__(self):
        """
        Initialize class attributes and create a genesis block
        """
        # Create class variables
        self.chain = []
        self.transactions = []
        self.nodes = set()

        # Create genesis block
        self.new_block(prev_hash=1, proof=100)

    def new_block(self, proof, prev_hash=None):
        """
        Create a new Block in the Blockchain
        :param proof: <int> The proof given by the Proof of Work algorithm
        :param prev_hash: (Optional) <str> Hash of previous Block
        :return: <dict> New Block
        """

        # Construct a new block
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.transactions,
            'proof': proof,
            'prev_hash': prev_hash or self.hash(self.chain[-1])
        }

        # Reset the list of transactions
        self.transactions.clear()

        # Append the new block to the existing chain
        self.chain.append(block)

        return block

    def new_transaction(self, sender, receiver, amount):
        """
        Creates a new transaction to go into the next mined Block
        :param sender: <str> Address of the Sender
        :param receiver: <str> Address of the Recipient
        :param amount: <int> Amount
        :return: <int> The index of the Block that will hold this transaction
        """

        # Add to the transaction array
        self.transactions.append({
            'sender': sender,
            'receiver': receiver,
            'amount': amount
        })

        return self.last_block['index'] + 1

    @property
    def last_block(self):
        """
        :return: The last block on the current chain
        """
        return self.chain[-1]

    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a Block
        :param block: <dict> Block
        :return: <str>
        """

        # Order dictionary to ensure consistent hashes
        block_string = json.dumps(block, sort_keys=True,).encode()
        return hashlib.sha3_256()

    def proof_of_work(self, last_proof):
        """
        Simple Proof of Work Algorithm:
        - Find a number p' such that hash(pp') contains leading 4 zeroes, where p is the previous p'
        - p is the previous proof, and p' is the new proof
        :param last_proof: <int>
        :return: <int>
        """

        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        Validates the Proof: Does hash(last_proof, proof) contain 4 leading zeroes?
        :param last_proof: <int> Previous Proof
        :param proof: <int> Current Proof
        :return: <bool> True if correct, False if not.
        """

        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha3_256(guess).hexdigest()

        return guess_hash[:4] == "0000"

    def register_node(self, address):
        """
        Add a new node to the list of nodes
        :param address: <str> Address of node. Eg. 'http://192.168.0.5:3000'
        :return: None
        """

        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid
        :param chain: <list> A blockchain
        :return: <bool> True if valid, False if not
        """

        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n-------------\n")

            # Check that the hash of the block is correct
            if block['prev_hash'] != self.hash(last_block):
                return False

            # Check that the Proof of Work is correct
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        """
        This is our Consensus Algorithm, it resolves conflicts
        by replacing our chain with the longest one in the network.
        :return: <bool> True if our chain was replaced, False if not
        """

        neighbors = self.nodes
        new_chain = None

        # Search for chains longer than current
        max_length = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbors:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            return True

        return False