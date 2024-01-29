import bech32
import json
import sys

DENOM = "ugovgen"
BECH32_PREFIX = "govgen"


def calculate_weight(votes):
    if not votes:
        return 0
    # options 3 and 4 are respectively No and NWV
    return sum(float(vote['weight'])
               for vote in votes if vote['option'] in [3, 4])


def process_address_data(item):
    address = item['Address']
    total_amount = 0

    if item['Vote']:
        staked_amount = float(item['StakedAmount'])
        final_weight = calculate_weight(item['Vote'])
        if final_weight > 0:
            total_amount = staked_amount * final_weight
    elif item['Delegations']:
        amounts = []
        for delegation in item['Delegations']:
            delegation_amount = float(delegation['Amount'])
            delegation_amount *= calculate_weight(delegation['Vote'])
            if delegation_amount > 0:
                amounts.append(delegation_amount)
        total_amount = sum(amounts)

    if int(total_amount) > 0:
        # convert bech32 prefix
        p, addrRaw = bech32.bech32_decode(address)
        address = bech32.bech32_encode(BECH32_PREFIX, addrRaw)

        return {"address": address, "coins": [
            {"denom": DENOM, "amount": str(int(total_amount))}]}
    else:
        return None


def process_json_data(json_data):
    processed_data = [process_address_data(item) for item in json_data]
    balances = [data for data in processed_data if data]
    total_supply = sum(int(data['coins'][0]['amount']) for data in balances)
    return {
        "balances": balances,
        "supply": [{
            "denom": DENOM,
            "amount": str(total_supply)
        }]}


def main():
    if len(sys.argv) != 3:
        print("Usage: python govgen-distribution.py <input_file.json> <output_file.json>")
        sys.exit(1)

    input_file, output_file = sys.argv[1:3]

    try:
        with open(input_file, 'r') as f:
            json_data = json.load(f)
    except Exception as e:
        print(f"Error reading input file: {e}")
        sys.exit(1)

    results = process_json_data(json_data)

    try:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=4)
    except Exception as e:
        print(f"Error writing output file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
