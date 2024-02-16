# GovGen Genesis

This repo is dedicated to the creation of the GovGen genesis using data from
Cosmos Hub proposal [#848](https://www.mintscan.io/cosmos/proposals/848)

It relies on the work provided in https://github.com/atomone-hub/genesis/pull/103, 
and follows the guidelines defined in https://github.com/atomone-hub/genesis/issues/71

*NOTE*: check out `requirements.txt` for additional Python packages requirements.


## Base Genesis - params

Created a `base-genesis.json` that contains the genesis parameters starting from 
the state export of the Cosmos Hub at [block 18010658](https://www.mintscan.io/cosmos/block/18010658),
which is when proposal [#848](https://www.mintscan.io/cosmos/proposals/848)
is finalized and comes into effect.

This base genesis includes the following changes:

- **x/bank**: disabled `sendTx` for `ugovgen` (and by default on the chain)
- **x/distribution**: community tax, proposer reward and bonus all set to 0
- **x/mint**: inflation disabled, no new $GOVGEN token minting
- **x/gov**: 
	- deposit amount raised to 5000 $GOVGEN, 
	- voting period is replaced by 3 new different voting periods:
           - for text proposal: 365 days
           - for parameter change proposal: 14 days
           - for software upgrade proposal: 28 days
           - if the proposal is none of the above: 2 days
	- quorum raised to 50% 
	- pass threshold increased to 2/3
- **x/staking**: reduced validators to 30 (tentatively)


**NOTE**: genesis time currently set at "1970-01-01T00:00:00Z"


## GovGen token distribution

The `govgen-distribution.py` Python script takes as input the result of the 
analysis performed in https://github.com/atomone-hub/genesis/pull/103, i.e.
the resulting `accounts.json` and calculates the $GOVGEN distribution based on
votes and delegations associated with each address. It specifically accounts 
for votes marked as options 3 (No) and 4 (NWV) to determine each address's 
token allocation, summing amounts from either direct votes - if present - or 
votes inherited from delegations. The output is a JSON file listing eligible 
addresses with their respective $GOVGEN (`ugovgen`) amounts, and the total 
supply of these tokens. 
Addresses are also converted to have the `govgen` Bech32 prefix.

The script takes two arguments: the input JSON file and the desired output 
file's path. 
Designed specifically for a predetermined data structure and voting criteria, 
it assumes the numerical values in the input JSON are correctly formatted for 
processing. As mentioned, the format is the one defined in 
https://github.com/atomone-hub/genesis/pull/103.


## Putting it all together

The `govgen-genesis.py` Python script takes as input the JSON file produced by 
the `govgen-distribution.py` script and the base genesis file, and outputs a 
genesis file that is the result of the combination of the two.

The third argument for the script is optional and specifies the output genesis
JSON file, which by default is simply `genesis.json`.

---

The resulting `genesis.json` should be almost ready for usage. 
It would need validators and a proper genesis time, plus any further 
modification needed.