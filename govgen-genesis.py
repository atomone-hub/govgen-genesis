import json
import sys


def new_genesis_account(address):
    return {
        "@type": "/cosmos.auth.v1beta1.BaseAccount",
        "address": address,
        "pub_key": None,
        "account_number": "0",
        "sequence": "0"
    }


def get_final_genesis(genesis, bank_balances_supply):
    balances = bank_balances_supply["balances"]
    accounts = [new_genesis_account(acct["address"]) for acct in balances]
    genesis["app_state"]["auth"]["accounts"] = accounts
    genesis["app_state"]["bank"]["balances"] = balances
    genesis["app_state"]["bank"]["supply"] = bank_balances_supply["supply"]


def main():
    if len(sys.argv) != 3:
        print("Usage: python govgen-genesis.py <base-genesis.json> "
              "<bank-balances-supply.json> [output.json]")
        sys.exit(1)

    base_genesis_file, bank_balances_supply_file = sys.argv[1:3]
    output_file = sys.argv[3] if len(sys.argv) > 3 else "genesis.json"

    try:
        with open(base_genesis_file, 'r') as f:
            genesis = json.load(f)
        with open(bank_balances_supply_file, 'r') as f:
            bank_balances_supply = json.load(f)
    except Exception as e:
        print(f"Error reading input files: {e}")
        sys.exit(1)

    get_final_genesis(genesis, bank_balances_supply)

    try:
        with open(output_file, 'w') as f:
            json.dump(genesis, f, indent=4)
    except Exception as e:
        print(f"Error writing output file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
