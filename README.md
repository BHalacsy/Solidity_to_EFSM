# Solidity to EFSM converter

Converts a Solidity smart contract into an Extended Finite State Machine (EFSM)
module (`.wmod`) for verification in Supremica. The pipeline compiles the contract
with `solc`, walks the AST, and emits one EFSM per public/external function plus
the supporting `assignMsg`, transfer, attacker, and progress-spec automata.

## Running

```bash
python3 xml_generator.py
```

Output is written to `output/output_YYYY_MM_DD_HH_MM/` as a `.wmod` Supremica
module named after the contract.

Prerequisites: `solc` must be available. The default binary is
`/home/balint/bin/solc` (Solidity 0.8.x). See `select_solc` in `json_contract.py`
if you have multiple solc versions.

## What to change per contract

Three places control the run. All are plain edits to the source.

### 1. Target contract, in `json_contract.py`

```python
contract_file = os.path.join(PROJECT_DIR, 'smart_contracts', 'AkuAuction_simplified.sol')
```

Point this at any file in `smart_contracts/`. Each file is expected to contain a
single contract, and the first contract in the file is used automatically. If a
file has multiple contracts, pass the name with
`process_contract_in_memory(target_contract=...)`.

### 2. Attacker spec and progress spec, in `xml_generator.py`


```python
attacker_model = generate_attacker_model("processRefund", "project")
progress_spec_model = generate_spec("claimProjectFundsX")
```

`generate_attacker_model(function_name, address_name)` builds a spec that blocks
the transfer to that address inside that function. `generate_spec(event_name)`
builds the progress spec requiring the given event to keep occurring, usually a
function name with `X` appended.

To run without an attacker or progress spec, comment out the matching
`ComponentList.append(...)` line.

### 3. Override variable ranges, in `xml_generator.py`

Integer variables default to range `[0, 1]`. Widen counters or timestamps that
need a larger domain:

```python
override_variable_range('timestamp', 0, 3)
override_variable_range('expiresAt', 0, 3, initial=2)
override_variable_range('totalForAuction', 0, 3, initial=3)
```

`override_variable_range(var_name, lo, hi, initial=None)` sets the range to
`[lo, hi]` and the initial value (defaults to `lo`). These names are
contract-specific, so replace the block when switching contracts. A name that does
not exist in the current contract just prints a warning and is skipped.

## Changes made in this fork

Portability:

- `solc` invocation switched from the hardcoded Windows path to `select_solc()`.
- Output written to a relative `output/` folder, files named after the contract.
- Module name derived from the contract filename.

Solidity 0.8.x support:

- Handles `constructor` and `receive` function kinds.
- Handles `Return` statements and empty function bodies.
- `external` functions included alongside `public`.
- `if` without `else` handled correctly.

Modelling:

- `assignMsg` rewritten to set `sender` and `value` via explicit per-combination
  assignments instead of a guard.
- Time-advance modelling: an `advanceTime` self-loop increments `timestamp` or
  `now` for time-gated contracts. The `timestamp` case previously emitted an empty
  variable name, producing an invalid action; this is now fixed.
- Constructor scan recovers `msg.sender` address initialisations and pads the
  address domain when multiple variables alias the deployer, as in King.
- `auto_fix_primed_guards()` splits sender-indexed mapping guards into one edge per
  address.
- `override_variable_range()` helper for widening integer domains.
- Automatic attacker and progress spec generators. (taken from automatic_spec branch already implemented)
- VariableComponents not referenced in any guard or action are suppressed to avoid
  Supremica disconnected-automaton warnings.
