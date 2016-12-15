from pytest import raises
from unittest.mock import patch


def test_input_serialization(ffill_uri, user_pub):
    from bigchaindb.common.transaction import Input
    from cryptoconditions import Fulfillment

    expected = {
        'owners_before': [user_pub],
        'fulfillment': ffill_uri,
        'fulfills': None,
    }
    input = Input(Fulfillment.from_uri(ffill_uri), [user_pub])
    assert input.to_dict() == expected


def test_input_deserialization_with_uri(ffill_uri, user_pub):
    from bigchaindb.common.transaction import Input
    from cryptoconditions import Fulfillment

    expected = Input(Fulfillment.from_uri(ffill_uri), [user_pub])
    ffill = {
        'owners_before': [user_pub],
        'fulfillment': ffill_uri,
        'fulfills': None,
    }
    input = Input.from_dict(ffill)

    assert input == expected


def test_input_deserialization_with_invalid_input(user_pub):
    from bigchaindb.common.transaction import Input

    ffill = {
        'owners_before': [user_pub],
        'fulfillment': None,
        'fulfills': None,
    }
    with raises(TypeError):
        Input.from_dict(ffill)


def test_input_deserialization_with_invalid_fulfillment_uri(user_pub):
    from bigchaindb.common.exceptions import InvalidSignature
    from bigchaindb.common.transaction import Input

    ffill = {
        'owners_before': [user_pub],
        'fulfillment': 'an invalid fulfillment',
        'fulfills': None,
    }
    with raises(InvalidSignature):
        Input.from_dict(ffill)


def test_input_deserialization_with_unsigned_fulfillment(ffill_uri, user_pub):
    from bigchaindb.common.transaction import Input
    from cryptoconditions import Fulfillment

    expected = Input(Fulfillment.from_uri(ffill_uri), [user_pub])
    ffill = {
        'owners_before': [user_pub],
        'fulfillment': Fulfillment.from_uri(ffill_uri),
        'fulfills': None,
    }
    input = Input.from_dict(ffill)

    assert input == expected


def test_output_serialization(user_Ed25519, user_pub):
    from bigchaindb.common.transaction import Output

    expected = {
        'condition': {
            'uri': user_Ed25519.condition_uri,
            'details': user_Ed25519.to_dict(),
        },
        'public_keys': [user_pub],
        'amount': 1,
    }

    cond = Output(user_Ed25519, [user_pub], 1)

    assert cond.to_dict() == expected


def test_output_deserialization(user_Ed25519, user_pub):
    from bigchaindb.common.transaction import Output

    expected = Output(user_Ed25519, [user_pub], 1)
    cond = {
        'condition': {
            'uri': user_Ed25519.condition_uri,
            'details': user_Ed25519.to_dict()
        },
        'public_keys': [user_pub],
        'amount': 1,
    }
    cond = Output.from_dict(cond)

    assert cond == expected


def test_output_hashlock_serialization():
    from bigchaindb.common.transaction import Output
    from cryptoconditions import PreimageSha256Fulfillment

    secret = b'wow much secret'
    hashlock = PreimageSha256Fulfillment(preimage=secret).condition_uri

    expected = {
        'condition': {
            'uri': hashlock,
        },
        'public_keys': None,
        'amount': 1,
    }
    cond = Output(hashlock, amount=1)

    assert cond.to_dict() == expected


def test_output_hashlock_deserialization():
    from bigchaindb.common.transaction import Output
    from cryptoconditions import PreimageSha256Fulfillment

    secret = b'wow much secret'
    hashlock = PreimageSha256Fulfillment(preimage=secret).condition_uri
    expected = Output(hashlock, amount=1)

    cond = {
        'condition': {
            'uri': hashlock
        },
        'public_keys': None,
        'amount': 1,
    }
    cond = Output.from_dict(cond)

    assert cond == expected


def test_invalid_output_initialization(cond_uri, user_pub):
    from bigchaindb.common.transaction import Output

    with raises(TypeError):
        Output(cond_uri, user_pub)


def test_generate_output_split_half_recursive(user_pub, user2_pub,
                                                  user3_pub):
    from bigchaindb.common.transaction import Output
    from cryptoconditions import Ed25519Fulfillment, ThresholdSha256Fulfillment

    expected_simple1 = Ed25519Fulfillment(public_key=user_pub)
    expected_simple2 = Ed25519Fulfillment(public_key=user2_pub)
    expected_simple3 = Ed25519Fulfillment(public_key=user3_pub)

    expected = ThresholdSha256Fulfillment(threshold=2)
    expected.add_subfulfillment(expected_simple1)
    expected_threshold = ThresholdSha256Fulfillment(threshold=2)
    expected_threshold.add_subfulfillment(expected_simple2)
    expected_threshold.add_subfulfillment(expected_simple3)
    expected.add_subfulfillment(expected_threshold)

    cond = Output.generate([user_pub, [user2_pub, expected_simple3]], 1)
    assert cond.fulfillment.to_dict() == expected.to_dict()


def test_generate_outputs_split_half_single_owner(user_pub, user2_pub,
                                                     user3_pub):
    from bigchaindb.common.transaction import Output
    from cryptoconditions import Ed25519Fulfillment, ThresholdSha256Fulfillment

    expected_simple1 = Ed25519Fulfillment(public_key=user_pub)
    expected_simple2 = Ed25519Fulfillment(public_key=user2_pub)
    expected_simple3 = Ed25519Fulfillment(public_key=user3_pub)

    expected = ThresholdSha256Fulfillment(threshold=2)
    expected_threshold = ThresholdSha256Fulfillment(threshold=2)
    expected_threshold.add_subfulfillment(expected_simple2)
    expected_threshold.add_subfulfillment(expected_simple3)
    expected.add_subfulfillment(expected_threshold)
    expected.add_subfulfillment(expected_simple1)

    cond = Output.generate([[expected_simple2, user3_pub], user_pub], 1)
    assert cond.fulfillment.to_dict() == expected.to_dict()


def test_generate_outputs_flat_ownage(user_pub, user2_pub, user3_pub):
    from bigchaindb.common.transaction import Output
    from cryptoconditions import Ed25519Fulfillment, ThresholdSha256Fulfillment

    expected_simple1 = Ed25519Fulfillment(public_key=user_pub)
    expected_simple2 = Ed25519Fulfillment(public_key=user2_pub)
    expected_simple3 = Ed25519Fulfillment(public_key=user3_pub)

    expected = ThresholdSha256Fulfillment(threshold=3)
    expected.add_subfulfillment(expected_simple1)
    expected.add_subfulfillment(expected_simple2)
    expected.add_subfulfillment(expected_simple3)

    cond = Output.generate([user_pub, user2_pub, expected_simple3], 1)
    assert cond.fulfillment.to_dict() == expected.to_dict()


def test_generate_output_single_owner(user_pub):
    from bigchaindb.common.transaction import Output
    from cryptoconditions import Ed25519Fulfillment

    expected = Ed25519Fulfillment(public_key=user_pub)
    cond = Output.generate([user_pub], 1)

    assert cond.fulfillment.to_dict() == expected.to_dict()


def test_generate_output_single_owner_with_output(user_pub):
    from bigchaindb.common.transaction import Output
    from cryptoconditions import Ed25519Fulfillment

    expected = Ed25519Fulfillment(public_key=user_pub)
    cond = Output.generate([expected], 1)

    assert cond.fulfillment.to_dict() == expected.to_dict()


def test_generate_output_invalid_parameters(user_pub, user2_pub,
                                                user3_pub):
    from bigchaindb.common.transaction import Output

    with raises(ValueError):
        Output.generate([], 1)
    with raises(TypeError):
        Output.generate('not a list', 1)
    with raises(ValueError):
        Output.generate([[user_pub, [user2_pub, [user3_pub]]]], 1)
    with raises(ValueError):
        Output.generate([[user_pub]], 1)


def test_invalid_transaction_initialization():
    from bigchaindb.common.transaction import Transaction, Asset

    with raises(ValueError):
        Transaction(operation='invalid operation', asset=Asset())
    with raises(TypeError):
        Transaction(operation='CREATE', asset='invalid asset')
    with raises(TypeError):
        Transaction(
            operation='CREATE',
            asset=Asset(),
            outputs='invalid outputs'
        )
    with raises(TypeError):
        Transaction(
            operation='CREATE',
            asset=Asset(),
            outputs=[],
            inputs='invalid inputs'
        )
    with raises(TypeError):
        Transaction(
            operation='CREATE',
            asset=Asset(),
            outputs=[],
            inputs=[],
            metadata='invalid metadata'
        )


def test_create_default_asset_on_tx_initialization():
    from bigchaindb.common.transaction import Transaction, Asset
    from bigchaindb.common.exceptions import ValidationError
    from .util import validate_transaction_model

    with patch.object(Asset, 'validate_asset', return_value=None):
        tx = Transaction(Transaction.CREATE, None)
    expected = Asset()
    asset = tx.asset

    expected.data_id = None
    asset.data_id = None
    assert asset == expected

    # Fails because no asset hash
    with raises(ValidationError):
        validate_transaction_model(tx)


def test_transaction_serialization(user_input, user_output, data, data_id):
    from bigchaindb.common.transaction import Transaction, Asset
    from bigchaindb.common.exceptions import ValidationError
    from .util import validate_transaction_model

    tx_id = 'l0l'

    expected = {
        'id': tx_id,
        'version': Transaction.VERSION,
        # NOTE: This test assumes that Inputs and Outputs can
        #       successfully be serialized
        'inputs': [user_input.to_dict()],
        'outputs': [user_output.to_dict()],
        'operation': Transaction.CREATE,
        'metadata': None,
        'asset': {
            'id': data_id,
            'divisible': False,
            'updatable': False,
            'refillable': False,
            'data': data,
        }
    }

    tx = Transaction(Transaction.CREATE, Asset(data, data_id), [user_input],
                     [user_output])
    tx_dict = tx.to_dict()
    tx_dict['id'] = tx_id
    tx_dict['asset']['id'] = data_id

    assert tx_dict == expected

    # Fails because asset id is not a uuid4
    with raises(ValidationError):
        validate_transaction_model(tx)


def test_transaction_deserialization(user_input, user_output, data, uuid4):
    from bigchaindb.common.transaction import Transaction, Asset
    from .util import validate_transaction_model

    expected_asset = Asset(data, uuid4)
    expected = Transaction(Transaction.CREATE, expected_asset, [user_input],
                           [user_output], None, Transaction.VERSION)

    tx = {
        'version': Transaction.VERSION,
        # NOTE: This test assumes that Inputs and Outputs can
        #       successfully be serialized
        'inputs': [user_input.to_dict()],
        'outputs': [user_output.to_dict()],
        'operation': Transaction.CREATE,
        'metadata': None,
        'asset': {
            'id': uuid4,
            'divisible': False,
            'updatable': False,
            'refillable': False,
            'data': data,
        }
    }
    tx_no_signatures = Transaction._remove_signatures(tx)
    tx['id'] = Transaction._to_hash(Transaction._to_str(tx_no_signatures))
    tx = Transaction.from_dict(tx)

    assert tx == expected

    validate_transaction_model(tx)


def test_tx_serialization_with_incorrect_hash(utx):
    from bigchaindb.common.transaction import Transaction
    from bigchaindb.common.exceptions import InvalidHash

    utx_dict = utx.to_dict()
    utx_dict['id'] = 'a' * 64
    with raises(InvalidHash):
        Transaction.from_dict(utx_dict)
    utx_dict.pop('id')


def test_invalid_input_initialization(user_input, user_pub):
    from bigchaindb.common.transaction import Input

    with raises(TypeError):
        Input(user_input, user_pub)
    with raises(TypeError):
        Input(user_input, tx_input='somethingthatiswrong')


def test_transaction_link_serialization():
    from bigchaindb.common.transaction import TransactionLink

    tx_id = 'a transaction id'
    expected = {
        'txid': tx_id,
        'output': 0,
    }
    tx_link = TransactionLink(tx_id, 0)

    assert tx_link.to_dict() == expected


def test_transaction_link_serialization_with_empty_payload():
    from bigchaindb.common.transaction import TransactionLink

    expected = None
    tx_link = TransactionLink()

    assert tx_link.to_dict() == expected


def test_transaction_link_deserialization():
    from bigchaindb.common.transaction import TransactionLink

    tx_id = 'a transaction id'
    expected = TransactionLink(tx_id, 0)
    tx_link = {
        'txid': tx_id,
        'output': 0,
    }
    tx_link = TransactionLink.from_dict(tx_link)

    assert tx_link == expected


def test_transaction_link_deserialization_with_empty_payload():
    from bigchaindb.common.transaction import TransactionLink

    expected = TransactionLink()
    tx_link = TransactionLink.from_dict(None)

    assert tx_link == expected


def test_transaction_link_empty_to_uri():
    from bigchaindb.common.transaction import TransactionLink

    expected = None
    tx_link = TransactionLink().to_uri()

    assert expected == tx_link


def test_transaction_link_to_uri():
    from bigchaindb.common.transaction import TransactionLink

    expected = 'path/transactions/abc/conditions/0'
    tx_link = TransactionLink('abc', 0).to_uri('path')

    assert expected == tx_link


def test_cast_transaction_link_to_boolean():
    from bigchaindb.common.transaction import TransactionLink

    assert bool(TransactionLink()) is False
    assert bool(TransactionLink('a', None)) is False
    assert bool(TransactionLink(None, 'b')) is False
    assert bool(TransactionLink('a', 'b')) is True
    assert bool(TransactionLink(False, False)) is True


def test_asset_link_serialization():
    from bigchaindb.common.transaction import AssetLink

    data_id = 'a asset id'
    expected = {
        'id': data_id,
    }
    asset_link = AssetLink(data_id)

    assert asset_link.to_dict() == expected


def test_asset_link_serialization_with_empty_payload():
    from bigchaindb.common.transaction import AssetLink

    expected = None
    asset_link = AssetLink()

    assert asset_link.to_dict() == expected


def test_asset_link_deserialization():
    from bigchaindb.common.transaction import AssetLink

    data_id = 'a asset id'
    expected = AssetLink(data_id)
    asset_link = {
        'id': data_id
    }
    asset_link = AssetLink.from_dict(asset_link)

    assert asset_link == expected


def test_asset_link_deserialization_with_empty_payload():
    from bigchaindb.common.transaction import AssetLink

    expected = AssetLink()
    asset_link = AssetLink.from_dict(None)

    assert asset_link == expected


def test_cast_asset_link_to_boolean():
    from bigchaindb.common.transaction import AssetLink

    assert bool(AssetLink()) is False
    assert bool(AssetLink('a')) is True
    assert bool(AssetLink(False)) is True


def test_eq_asset_link():
    from bigchaindb.common.transaction import AssetLink

    asset_id_1 = 'asset_1'
    asset_id_2 = 'asset_2'

    assert AssetLink(asset_id_1) == AssetLink(asset_id_1)
    assert AssetLink(asset_id_1) != AssetLink(asset_id_2)


def test_add_input_to_tx(user_input):
    from bigchaindb.common.transaction import Transaction, Asset

    with patch.object(Asset, 'validate_asset', return_value=None):
        tx = Transaction(Transaction.CREATE, Asset(), [], [])
    tx.add_input(user_input)

    assert len(tx.inputs) == 1


def test_add_input_to_tx_with_invalid_parameters():
    from bigchaindb.common.transaction import Transaction, Asset

    with patch.object(Asset, 'validate_asset', return_value=None):
        tx = Transaction(Transaction.CREATE, Asset())
    with raises(TypeError):
        tx.add_input('somewronginput')


def test_add_output_to_tx(user_output):
    from bigchaindb.common.transaction import Transaction, Asset
    from .util import validate_transaction_model

    with patch.object(Asset, 'validate_asset', return_value=None):
        tx = Transaction(Transaction.CREATE, Asset())
    tx.add_output(user_output)

    assert len(tx.outputs) == 1

    validate_transaction_model(tx)


def test_add_output_to_tx_with_invalid_parameters():
    from bigchaindb.common.transaction import Transaction, Asset

    with patch.object(Asset, 'validate_asset', return_value=None):
        tx = Transaction(Transaction.CREATE, Asset(), [], [])
    with raises(TypeError):
        tx.add_output('somewronginput')


def test_sign_with_invalid_parameters(utx, user_priv):
    with raises(TypeError):
        utx.sign(None)
    with raises(TypeError):
        utx.sign(user_priv)


def test_validate_tx_simple_create_signature(user_input, user_output, user_priv):
    from copy import deepcopy
    from bigchaindb.common.crypto import PrivateKey
    from bigchaindb.common.transaction import Transaction, Asset
    from .util import validate_transaction_model

    tx = Transaction(Transaction.CREATE, Asset(), [user_input], [user_output])
    expected = deepcopy(user_output)
    expected.fulfillment.sign(str(tx).encode(), PrivateKey(user_priv))
    tx.sign([user_priv])

    assert tx.inputs[0].to_dict()['fulfillment'] == \
        expected.fulfillment.serialize_uri()
    assert tx.inputs_valid() is True

    validate_transaction_model(tx)


def test_invoke_simple_signature_fulfillment_with_invalid_params(utx,
                                                                 user_input):
    from bigchaindb.common.exceptions import KeypairMismatchException

    with raises(KeypairMismatchException):
        invalid_key_pair = {'wrong_pub_key': 'wrong_priv_key'}
        utx._sign_simple_signature_fulfillment(user_input,
                                               0,
                                               'somemessage',
                                               invalid_key_pair)


def test_sign_threshold_with_invalid_params(utx, user_user2_threshold_input,
                                            user3_pub, user3_priv):
    from bigchaindb.common.exceptions import KeypairMismatchException

    with raises(KeypairMismatchException):
        utx._sign_threshold_signature_fulfillment(user_user2_threshold_input,
                                                  0,
                                                  'somemessage',
                                                  {user3_pub: user3_priv})
    with raises(KeypairMismatchException):
        user_user2_threshold_input.owners_before = ['somewrongvalue']
        utx._sign_threshold_signature_fulfillment(user_user2_threshold_input,
                                                  0,
                                                  'somemessage',
                                                  None)


def test_validate_input_with_invalid_parameters(utx):
    from bigchaindb.common.transaction import Transaction

    input_conditions = [out.fulfillment.condition_uri for out in utx.outputs]
    tx_dict = utx.to_dict()
    tx_dict = Transaction._remove_signatures(tx_dict)
    tx_serialized = Transaction._to_str(tx_dict)
    valid = utx._input_valid(utx.inputs[0], tx_serialized, input_conditions)
    assert not valid


def test_validate_multiple_inputs(user_input, user_output, user_priv):
    from copy import deepcopy

    from bigchaindb.common.crypto import PrivateKey
    from bigchaindb.common.transaction import Transaction, Asset
    from .util import validate_transaction_model

    tx = Transaction(Transaction.CREATE, Asset(divisible=True),
                     [user_input, deepcopy(user_input)],
                     [user_output, deepcopy(user_output)])

    expected_first = deepcopy(tx)
    expected_second = deepcopy(tx)
    expected_first.inputs = [expected_first.inputs[0]]
    expected_second.inputs = [expected_second.inputs[1]]

    expected_first_bytes = str(expected_first).encode()
    expected_first.inputs[0].fulfillment.sign(expected_first_bytes,
                                                    PrivateKey(user_priv))
    expected_second_bytes = str(expected_second).encode()
    expected_second.inputs[0].fulfillment.sign(expected_second_bytes,
                                               PrivateKey(user_priv))
    tx.sign([user_priv])

    assert tx.inputs[0].to_dict()['fulfillment'] == \
        expected_first.inputs[0].fulfillment.serialize_uri()
    assert tx.inputs[1].to_dict()['fulfillment'] == \
        expected_second.inputs[0].fulfillment.serialize_uri()
    assert tx.inputs_valid() is True

    validate_transaction_model(tx)


def test_validate_tx_threshold_create_signature(user_user2_threshold_input,
                                                user_user2_threshold_output,
                                                user_pub,
                                                user2_pub,
                                                user_priv,
                                                user2_priv):
    from copy import deepcopy

    from bigchaindb.common.crypto import PrivateKey
    from bigchaindb.common.transaction import Transaction, Asset
    from .util import validate_transaction_model

    tx = Transaction(Transaction.CREATE, Asset(), [user_user2_threshold_input],
                     [user_user2_threshold_output])
    expected = deepcopy(user_user2_threshold_output)
    expected.fulfillment.subconditions[0]['body'].sign(str(tx).encode(),
                                                       PrivateKey(user_priv))
    expected.fulfillment.subconditions[1]['body'].sign(str(tx).encode(),
                                                       PrivateKey(user2_priv))
    tx.sign([user_priv, user2_priv])

    assert tx.inputs[0].to_dict()['fulfillment'] == \
        expected.fulfillment.serialize_uri()
    assert tx.inputs_valid() is True

    validate_transaction_model(tx)


def test_multiple_input_validation_of_transfer_tx(user_input, user_output,
                                                  user_priv, user2_pub,
                                                  user2_priv, user3_pub,
                                                  user3_priv):
    from copy import deepcopy
    from bigchaindb.common.transaction import (Transaction, TransactionLink,
                                               Input, Output, Asset)
    from cryptoconditions import Ed25519Fulfillment
    from .util import validate_transaction_model

    tx = Transaction(Transaction.CREATE, Asset(divisible=True),
                     [user_input, deepcopy(user_input)],
                     [user_output, deepcopy(user_output)])
    tx.sign([user_priv])

    inputs = [Input(cond.fulfillment, cond.public_keys,
                    TransactionLink(tx.id, index))
              for index, cond in enumerate(tx.outputs)]
    outputs = [Output(Ed25519Fulfillment(public_key=user3_pub), [user3_pub]),
               Output(Ed25519Fulfillment(public_key=user3_pub), [user3_pub])]
    transfer_tx = Transaction('TRANSFER', tx.asset, inputs, outputs)
    transfer_tx = transfer_tx.sign([user_priv])

    assert transfer_tx.inputs_valid(tx.outputs) is True

    validate_transaction_model(tx)


def test_validate_inputs_of_transfer_tx_with_invalid_params(
        transfer_tx, cond_uri, utx, user2_pub, user_priv):
    from bigchaindb.common.transaction import Output
    from cryptoconditions import Ed25519Fulfillment

    invalid_out = Output(Ed25519Fulfillment.from_uri('cf:0:'), ['invalid'])
    assert transfer_tx.inputs_valid([invalid_out]) is False
    invalid_out = utx.outputs[0]
    invalid_out.public_key = 'invalid'
    assert transfer_tx.inputs_valid([invalid_out]) is True

    with raises(TypeError):
        assert transfer_tx.inputs_valid(None) is False
    with raises(AttributeError):
        transfer_tx.inputs_valid('not a list')
    with raises(ValueError):
        transfer_tx.inputs_valid([])
    with raises(TypeError):
        transfer_tx.operation = "Operation that doesn't exist"
        transfer_tx.inputs_valid([utx.outputs[0]])


def test_create_create_transaction_single_io(user_output, user_pub, data, uuid4):
    from bigchaindb.common.transaction import Transaction, Asset
    from .util import validate_transaction_model

    expected = {
        'outputs': [user_output.to_dict()],
        'metadata': data,
        'asset': {
            'id': uuid4,
            'divisible': False,
            'updatable': False,
            'refillable': False,
            'data': data,
        },
        'inputs': [
            {
                'owners_before': [
                    user_pub
                ],
                'fulfillment': None,
                'fulfills': None
            }
        ],
        'operation': 'CREATE',
        'version': 1,
    }

    asset = Asset(data, uuid4)
    tx = Transaction.create([user_pub], [([user_pub], 1)], data, asset)
    tx_dict = tx.to_dict()
    tx_dict['inputs'][0]['fulfillment'] = None
    tx_dict.pop('id')

    assert tx_dict == expected

    validate_transaction_model(tx)


def test_validate_single_io_create_transaction(user_pub, user_priv, data):
    from bigchaindb.common.transaction import Transaction, Asset

    tx = Transaction.create([user_pub], [([user_pub], 1)], data, Asset())
    tx = tx.sign([user_priv])
    assert tx.inputs_valid() is True


def test_create_create_transaction_multiple_io(user_output, user2_output, user_pub,
                                               user2_pub):
    from bigchaindb.common.transaction import Transaction, Asset, Input

    # a fulfillment for a create transaction with multiple `owners_before`
    # is a fulfillment for an implicit threshold condition with
    # weight = len(owners_before)
    input = Input.generate([user_pub, user2_pub]).to_dict()
    expected = {
        'outputs': [user_output.to_dict(), user2_output.to_dict()],
        'metadata': {
            'message': 'hello'
        },
        'inputs': [input],
        'operation': 'CREATE',
        'version': 1
    }
    asset = Asset(divisible=True)
    tx = Transaction.create([user_pub, user2_pub],
                            [([user_pub], 1), ([user2_pub], 1)],
                            asset=asset,
                            metadata={'message': 'hello'}).to_dict()
    tx.pop('id')
    tx.pop('asset')

    assert tx == expected


def test_validate_multiple_io_create_transaction(user_pub, user_priv,
                                                 user2_pub, user2_priv):
    from bigchaindb.common.transaction import Transaction, Asset
    from .util import validate_transaction_model

    tx = Transaction.create([user_pub, user2_pub],
                            [([user_pub], 1), ([user2_pub], 1)],
                            metadata={'message': 'hello'},
                            asset=Asset(divisible=True))
    tx = tx.sign([user_priv, user2_priv])
    assert tx.inputs_valid() is True

    validate_transaction_model(tx)


def test_create_create_transaction_threshold(user_pub, user2_pub, user3_pub,
                                             user_user2_threshold_output,
                                             user_user2_threshold_input, data,
                                             uuid4):
    from bigchaindb.common.transaction import Transaction, Asset

    expected = {
        'outputs': [user_user2_threshold_output.to_dict()],
        'metadata': data,
        'asset': {
            'id': uuid4,
            'divisible': False,
            'updatable': False,
            'refillable': False,
            'data': data,
        },
        'inputs': [
            {
                'owners_before': [
                    user_pub,
                ],
                'fulfillment': None,
                'fulfills': None,
            },
        ],
        'operation': 'CREATE',
        'version': 1
    }
    asset = Asset(data, uuid4)
    tx = Transaction.create([user_pub], [([user_pub, user2_pub], 1)],
                            data, asset)
    tx_dict = tx.to_dict()
    tx_dict.pop('id')
    tx_dict['inputs'][0]['fulfillment'] = None

    assert tx_dict == expected


def test_validate_threshold_create_transaction(user_pub, user_priv, user2_pub,
                                               data):
    from bigchaindb.common.transaction import Transaction, Asset
    from .util import validate_transaction_model

    tx = Transaction.create([user_pub], [([user_pub, user2_pub], 1)],
                            data, Asset())
    tx = tx.sign([user_priv])
    assert tx.inputs_valid() is True

    validate_transaction_model(tx)


def test_create_create_transaction_with_invalid_parameters(user_pub):
    from bigchaindb.common.transaction import Transaction

    with raises(TypeError):
        Transaction.create('not a list')
    with raises(TypeError):
        Transaction.create([], 'not a list')
    with raises(ValueError):
        Transaction.create([], [user_pub])
    with raises(ValueError):
        Transaction.create([user_pub], [])
    with raises(ValueError):
        Transaction.create([user_pub], [user_pub])
    with raises(ValueError):
        Transaction.create([user_pub], [([user_pub],)])


def test_outputs_to_inputs(tx):
    inputs = tx.to_inputs([0])
    assert len(inputs) == 1
    input = inputs.pop()
    assert input.owners_before == tx.outputs[0].public_keys
    assert input.fulfillment == tx.outputs[0].fulfillment
    assert input.fulfills.txid == tx.id
    assert input.fulfills.output == 0


def test_create_transfer_transaction_single_io(tx, user_pub, user2_pub,
                                               user2_output, user_priv, uuid4):
    from copy import deepcopy
    from bigchaindb.common.crypto import PrivateKey
    from bigchaindb.common.transaction import Transaction, Asset
    from bigchaindb.common.util import serialize
    from .util import validate_transaction_model

    expected = {
        'outputs': [user2_output.to_dict()],
        'metadata': None,
        'asset': {
            'id': uuid4,
        },
        'inputs': [
            {
                'owners_before': [
                    user_pub
                ],
                'fulfillment': None,
                'fulfills': {
                    'txid': tx.id,
                    'output': 0
                }
            }
        ],
        'operation': 'TRANSFER',
        'version': 1
    }
    inputs = tx.to_inputs([0])
    asset = Asset(None, uuid4)
    transfer_tx = Transaction.transfer(inputs, [([user2_pub], 1)], asset=asset)
    transfer_tx = transfer_tx.sign([user_priv])
    transfer_tx = transfer_tx.to_dict()

    expected_input = deepcopy(inputs[0])
    expected['id'] = transfer_tx['id']
    expected_input.fulfillment.sign(serialize(expected).encode(),
                                    PrivateKey(user_priv))
    expected_ffill = expected_input.fulfillment.serialize_uri()
    transfer_ffill = transfer_tx['inputs'][0]['fulfillment']

    assert transfer_ffill == expected_ffill

    transfer_tx = Transaction.from_dict(transfer_tx)
    assert transfer_tx.inputs_valid([tx.outputs[0]]) is True

    validate_transaction_model(transfer_tx)


def test_create_transfer_transaction_multiple_io(user_pub, user_priv,
                                                 user2_pub, user2_priv,
                                                 user3_pub, user2_output):
    from bigchaindb.common.transaction import Transaction, Asset

    asset = Asset(divisible=True)
    tx = Transaction.create([user_pub], [([user_pub], 1), ([user2_pub], 1)],
                            asset=asset, metadata={'message': 'hello'})
    tx = tx.sign([user_priv])

    expected = {
        'outputs': [user2_output.to_dict(), user2_output.to_dict()],
        'metadata': None,
        'inputs': [
            {
                'owners_before': [
                    user_pub
                ],
                'fulfillment': None,
                'fulfills': {
                    'txid': tx.id,
                    'output': 0
                }
            }, {
                'owners_before': [
                    user2_pub
                ],
                'fulfillment': None,
                'fulfills': {
                    'txid': tx.id,
                    'output': 1
                }
            }
        ],
        'operation': 'TRANSFER',
        'version': 1
    }

    transfer_tx = Transaction.transfer(tx.to_inputs(),
                                       [([user2_pub], 1), ([user2_pub], 1)],
                                       asset=tx.asset)
    transfer_tx = transfer_tx.sign([user_priv, user2_priv])

    assert len(transfer_tx.inputs) == 2
    assert len(transfer_tx.outputs) == 2

    assert transfer_tx.inputs_valid(tx.outputs) is True

    transfer_tx = transfer_tx.to_dict()
    transfer_tx['inputs'][0]['fulfillment'] = None
    transfer_tx['inputs'][1]['fulfillment'] = None
    transfer_tx.pop('asset')
    transfer_tx.pop('id')

    assert expected == transfer_tx


def test_create_transfer_with_invalid_parameters(user_pub):
    from bigchaindb.common.transaction import Transaction, Asset

    with raises(TypeError):
        Transaction.transfer({}, [], Asset())
    with raises(ValueError):
        Transaction.transfer([], [], Asset())
    with raises(TypeError):
        Transaction.transfer(['fulfillment'], {}, Asset())
    with raises(ValueError):
        Transaction.transfer(['fulfillment'], [], Asset())
    with raises(ValueError):
        Transaction.transfer(['fulfillment'], [user_pub], Asset())
    with raises(ValueError):
        Transaction.transfer(['fulfillment'], [([user_pub],)], Asset())


def test_cant_add_empty_output():
    from bigchaindb.common.transaction import Transaction, Asset

    with patch.object(Asset, 'validate_asset', return_value=None):
        tx = Transaction(Transaction.CREATE, None)
    with raises(TypeError):
        tx.add_output(None)


def test_cant_add_empty_input():
    from bigchaindb.common.transaction import Transaction, Asset

    with patch.object(Asset, 'validate_asset', return_value=None):
        tx = Transaction(Transaction.CREATE, None)
    with raises(TypeError):
        tx.add_input(None)
