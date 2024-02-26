import json
import os
import sys
import bech32
import pprint


DENOM = "ugovgen"
VALIDATOR_INITIAL_BALANCE = 25000000
BECH32_PREFIX = "govgen"


def new_account_balance(address, denom, balance):
    return {
        "address": address,
        "coins": [
            {"denom": denom, "amount": str(balance)}
        ]
    }


def new_genesis_account(address):
    return {
        "@type": "/cosmos.auth.v1beta1.BaseAccount",
        "address": address,
        "pub_key": None,
        "account_number": "0",
        "sequence": "0"
    }


def load_json(filename):
    with open(filename, 'r') as file:
        return json.load(file)


def save_json(data, filename):
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)


def check_gentx_compliance(gentx, gentx_path):
    messages = gentx['body']['messages']
    moniker = gentx_path
    for msg in messages:
        if msg['@type'] == "/cosmos.staking.v1beta1.MsgCreateValidator":
            commission = msg['commission']
            moniker = msg['description']['moniker']
            min_self_delegation = msg['min_self_delegation']

            # Check commission rates and min_self_delegation
            if (commission['rate'] != "0.000000000000000000" or
                commission['max_rate'] != "0.000000000000000000" or
                commission['max_change_rate'] != "0.000000000000000000" or
                    min_self_delegation != "1"):
                print(f"WARNING: {moniker}'s gentx does not comply with the "
                      "format requirements and will be ignored.\n"
                      f"  - commission: {commission}\n"
                      f"  - min_self_delegation: {min_self_delegation}\n")
                return False
    if len(messages) > 1:
        print(f"WARNING: {moniker} submitted a gentx with more than 1 message")
        return False
    return True


def is_valid_peer_memo(memo):
    import re
    pattern = r'^[0-9a-fA-F]+@[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+:[0-9]+$'
    return bool(re.match(pattern, memo))


def process_gentxs(
        genesis_path,
        gentxs_folder,
        genesis_out_path,
        denom,
        initial_balance):
    peers = list()

    genesis = load_json(genesis_path)
    accounts = genesis.get('app_state', {}).get('auth', {}).get('accounts', [])
    balances = genesis.get('app_state', {}).get('bank', {}).get('balances', [])
    total_supply = int(genesis['app_state']['bank']['supply'][0]['amount'])
    if genesis['app_state']['bank']['supply'][0]['denom'] != denom:
        invalid_denom = genesis['app_state']['bank']['supply'][0]['denom']
        raise Exception(f'invalid denom {invalid_denom} found in bank supply')
    if len(genesis['app_state']['bank']['supply']) > 1:
        raise Exception('supply for GovGen is supposed to only have one coin')

    # dictionary to quickly check if an account exists and its balance
    accounts_dict = {acc['address']: acc for acc in balances}
    for acc in accounts:
        if acc['address'] not in accounts_dict:
            raise Exception(f'account {acc["address"]} exists in genesis but '
                            'does not have balance')

    for gentx_name in os.listdir(gentxs_folder):
        if not gentx_name.endswith('.json'):
            continue

        gentx_path = os.path.join(gentxs_folder, gentx_name)
        gentx = load_json(gentx_path)

        validator_address = gentx['body']['messages'][0]['validator_address']
        delegator_address = gentx['body']['messages'][0]['delegator_address']

        # sanity check
        if not check_gentx_compliance(gentx, gentx_path):
            # skip validator ad it did not comply with requirements
            continue

        # check delegator address is validator address
        _, addrRaw = bech32.bech32_decode(validator_address)
        if delegator_address != bech32.bech32_encode(BECH32_PREFIX, addrRaw):
            print(f"WARNING: {gentx['description']['moniker']} is using an "
                  "unmatching delegator address")

        peer_info = gentx['body']['memo'] if is_valid_peer_memo(
            gentx['body']['memo']) else None

        # Find the index in the balances list
        balance_index = next((i for i, item in enumerate(
            balances) if item["address"] == delegator_address), None)

        if balance_index is not None:
            # account exists, check if it needs topping off
            account_balance_info = balances[balance_index]
            account_balance = int(account_balance_info['coins'][0]['amount'])

            if account_balance_info['coins'][0]['denom'] != denom:
                invalid_denom = account_balance_info['coins'][0]['denom']
                raise Exception(
                    f'invalid denom {invalid_denom} found for address {delegator_address}')
            if len(account_balance_info['coins']) > 1:
                raise Exception(
                    f'genesis balance for address {delegator_address} expects only one coin type.')

            if account_balance < initial_balance:
                balances[balance_index] = new_account_balance(
                    delegator_address, denom, initial_balance)
                top_off_amount = initial_balance - account_balance
                total_supply += top_off_amount
        else:
            new_account = new_genesis_account(delegator_address)
            balance = new_account_balance(
                delegator_address, denom, initial_balance)
            accounts.append(new_account)
            balances.append(balance)
            total_supply += initial_balance
            accounts_dict[delegator_address] = new_account

        genesis['app_state']['genutil']['gen_txs'].append(gentx)
        if peer_info:
            peers.append(peer_info)

    genesis['app_state']['bank']['supply'][0]['amount'] = str(total_supply)
    save_json(genesis, genesis_out_path)

    return peers


def main():
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print("Usage: python govgen-collect-gentxs.py <input-genesis.json> "
              "</path/to/gentxs> [output.json]")
        sys.exit(1)

    input_genesis_path, gentxs_folder_path = sys.argv[1:3]
    output_file_path = sys.argv[3] if len(sys.argv) > 3 else "genesis.json"
    peers = process_gentxs(
        input_genesis_path,
        gentxs_folder_path,
        output_file_path,
        DENOM,
        VALIDATOR_INITIAL_BALANCE)
    print("collected peers: ")
    pprint.pprint(peers)


if __name__ == "__main__":
    main()
