import json
import os
import sys

DENOM = "ugovgen"
VALIDATOR_INITIAL_BALANCE = 25000000


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


def process_gentxs(genesis_path, gentxs_folder, genesis_out_path, denom, initial_balance):
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

        delegator_address = gentx['body']['messages'][0]['delegator_address']

        # sanity check: 


        # Find the index in the balances list
        balance_index = next((i for i, item in enumerate(balances) if item["address"] == delegator_address), None)

        if balance_index is not None:
            # account exists, check if it needs topping off
            account_balance_info = balances[balance_index]
            account_balance = int(account_balance_info['coins'][0]['amount'])

            if account_balance_info['coins'][0]['denom'] != denom:
                invalid_denom = account_balance_info['coins'][0]['denom']
                raise Exception(f'invalid denom {invalid_denom} found for address {delegator_address}')
            if len(account_balance_info['coins']) > 1:
                raise Exception(f'genesis balance for address {delegator_address} expects only one coin type.')

            if account_balance < initial_balance:
                balances[balance_index] = new_account_balance(delegator_address, denom, initial_balance)
                top_off_amount = initial_balance - account_balance
                total_supply += top_off_amount
        else:
            new_account = new_genesis_account(delegator_address)
            balance = new_account_balance(delegator_address, denom, initial_balance)
            accounts.append(new_account)
            balances.append(balance)
            total_supply += initial_balance
            accounts_dict[delegator_address] = new_account

        genesis['app_state']['genutil']['gen_txs'].append(gentx)

    genesis['app_state']['bank']['supply'][0]['amount'] = str(total_supply)
    save_json(genesis, genesis_out_path)


def main():
    if len(sys.argv) != 3:
        print("Usage: python govgen-collect-gentxs.py <input-genesis.json> "
              "</path/to/gentxs> [output.json]")
        sys.exit(1)

    input_genesis_path, gentxs_folder_path = sys.argv[1:3]
    output_file_path = sys.argv[3] if len(sys.argv) > 3 else "genesis.json"
    process_gentxs(input_genesis_path, gentxs_folder_path, output_file_path, DENOM, VALIDATOR_INITIAL_BALANCE)


if __name__ == "__main__":
    main()
