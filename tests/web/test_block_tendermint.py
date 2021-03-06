# Copyright BigchainDB GmbH and BigchainDB contributors
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

import pytest

from bigchaindb.models import Transaction
from bigchaindb.lib import Block

BLOCKS_ENDPOINT = '/api/v1/blocks/'

pytestmark = pytest.mark.tendermint


@pytest.mark.bdb
@pytest.mark.usefixtures('inputs')
def test_get_block_endpoint(tb, client, alice):
    import copy
    b = tb
    tx = Transaction.create([alice.public_key], [([alice.public_key], 1)], asset={'cycle': 'hero'})
    tx = tx.sign([alice.private_key])

    # with store_bulk_transactions we use `insert_many` where PyMongo
    # automatically adds an `_id` field to the tx, therefore we need the
    # deepcopy, for more info see:
    # https://api.mongodb.com/python/current/faq.html#writes-and-ids
    tx_dict = copy.deepcopy(tx.to_dict())
    b.store_bulk_transactions([tx])

    block = Block(app_hash='random_utxo',
                  height=31,
                  transactions=[tx.id])
    b.store_block(block._asdict())

    res = client.get(BLOCKS_ENDPOINT + str(block.height))
    expected_response = {'height': block.height, 'transactions': [tx_dict]}
    assert res.json == expected_response
    assert res.status_code == 200


@pytest.mark.bdb
@pytest.mark.usefixtures('inputs')
def test_get_block_returns_404_if_not_found(client):
    res = client.get(BLOCKS_ENDPOINT + '123')
    assert res.status_code == 404

    res = client.get(BLOCKS_ENDPOINT + '123/')
    assert res.status_code == 404


@pytest.mark.bdb
def test_get_block_containing_transaction(tb, client, alice):
    b = tb
    tx = Transaction.create([alice.public_key], [([alice.public_key], 1)], asset={'cycle': 'hero'})
    tx = tx.sign([alice.private_key])
    b.store_bulk_transactions([tx])

    block = Block(app_hash='random_utxo',
                  height=13,
                  transactions=[tx.id])
    b.store_block(block._asdict())

    res = client.get('{}?transaction_id={}'.format(BLOCKS_ENDPOINT, tx.id))
    expected_response = [block.height]
    assert res.json == expected_response
    assert res.status_code == 200


@pytest.mark.bdb
def test_get_blocks_by_txid_endpoint_returns_empty_list_not_found(client):
    res = client.get(BLOCKS_ENDPOINT + '?transaction_id=')
    assert res.status_code == 200
    assert len(res.json) == 0

    res = client.get(BLOCKS_ENDPOINT + '?transaction_id=123')
    assert res.status_code == 200
    assert len(res.json) == 0


@pytest.mark.bdb
def test_get_blocks_by_txid_endpoint_returns_400_bad_query_params(client):
    res = client.get(BLOCKS_ENDPOINT)
    assert res.status_code == 400

    res = client.get(BLOCKS_ENDPOINT + '?ts_id=123')
    assert res.status_code == 400
    assert res.json == {
        'message': {
            'transaction_id': 'Missing required parameter in the JSON body or the post body or the query string'
        }
    }

    res = client.get(BLOCKS_ENDPOINT + '?transaction_id=123&foo=123')
    assert res.status_code == 400
    assert res.json == {
        'message': 'Unknown arguments: foo'
    }

    res = client.get(BLOCKS_ENDPOINT + '?transaction_id=123&status=123')
    assert res.status_code == 400
    assert res.json == {
        'message': 'Unknown arguments: status'
    }
