import hashlib
import json
from time import time
from uuid import uuid4
from datetime import date

from flask import Flask, jsonify, request
from flask_cors import CORS


class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_transactions = []

        # create genesis block
        self.new_block(previous_hash=1, proof=100)
    
    def new_transaction(self, sender, recipient, amount):
        t_date = date.today().strftime("%m/%d/%Y")
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'date': t_date
        })
        return self.last_block['index'] + 1
    
    def new_block(self, proof, previous_hash=None):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.last_block)
        }
        self.current_transactions = [] # resets current transactions for that block
        self.chain.append(block) # add block to the chain
        return block
    
    def hash(self, block):
        block_string = json.dumps(block, sort_keys=True) # creates string representation of previous block
        hash_of_block_string = hashlib.sha256(block_string.encode())
        new_hash = hash_of_block_string.hexdigest() # returns 32 byte hash
        return new_hash
    
    @staticmethod # doesn't need to be called, bound to the class, not object
    def valid_proof(block_string, proof):
        guess = f'{block_string}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()

        return guess_hash[:6] == '000000'

    @property
    def last_block(self):
        return self.chain[-1]


app = Flask(__name__)
CORS(app)

node_id = str(uuid4()).replace('-', '')

blockchain = Blockchain()

@app.route('/test', methods=['GET'])
def test():
    return jsonify('hello'), 200

@app.route('/mine', methods=['POST'])
def mine():
    # check to see that a proof and an identifier were sent
    data = request.get_json()
    if data['proof'] and data['id']:
        proof = data['proof']
        miner_id = data['id']

        # make a string of the last block on the chain
        last_block_string = json.dumps(blockchain.last_block, sort_keys=True)
        # run the blockstring and the submitted proof through the function
        valid_submission = blockchain.valid_proof(last_block_string, proof)
        if valid_submission:
            # make a new block, reward the miner
            blockchain.new_transaction("server", miner_id, 1)
            previous_hash = blockchain.hash(blockchain.last_block)
            new_block = blockchain.new_block(proof, previous_hash)
            response = {
                'message': 'New Block Forged',
                'block': new_block
            }
            return jsonify(response), 200
        else:
            response = {
                'message': 'Proof valid but already submitted'
            }
            return jsonify(response), 400
    else:
        response = {
            'error': 'Invalid submission. Requires proof and miner_id'
        }
        return jsonify(response), 400

@app.route('/last_block', methods=['GET'])
def last_block():
    response = {
    'last_block': blockchain.last_block
    }
    return jsonify(response), 200

@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        # TODO: Return the chain and its current length
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def receive_transaction():
    data = request.get_json()
    required = ['sender', 'recipient', 'amount']

    if not all(k in data for k in required):
        ## error
        response = { 'message': 'Missing values'}
        return jsonify(response), 400
    
    index = blockchain.new_transaction(data['sender'], data['recipient'], data['amount'])
    response = { 'message': f'Transaction will be added to block at index {index}'}
    return jsonify(response), 201


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)