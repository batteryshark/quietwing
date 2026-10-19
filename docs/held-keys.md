# Bounded held keys

QuietWing 0.4.2 adds a supported hold duration to the public input command.
Earlier releases and already running older workers do not supply it.
The released implementation is Windows-only, through an authenticated ParaDesk
child. Development Mac VM owners now support the same bounded duration/receipt
contract, as described below. Linux and older owners refuse holds.

```sh
quietwing input --id work --expect-generation TOKEN --key ENTER --hold-ms 120
quietwing input --id work --expect-generation TOKEN --key CTRL+LEFT --hold-ms 250
```

A positive duration is an integer from 1 to 5000 milliseconds. All keys in a
chord are pressed, held, then released in reverse order in one worker request.
Physical scan codes and extended-key flags are used for held input. Omitted or
zero duration keeps the existing tap behavior. There is no persistent key-down
state or separate key-up call for an agent to forget. Already-down keys are
refused, so cleanup does not adopt keys owned by another input source. Chords
contain at most eight distinct supported keys; use ASCII key names/aliases.

The worker retains the generation, authenticated provider connection, native
non-console/session/desktop and runtime audio checks. It rechecks the boundary
throughout a hold and before release. Caller/SSH disconnection does not cancel a
request already executing in the worker: the bounded operation still attempts
its own release. Duration is elapsed wall time, with guard and delivery overhead;
it is not a game-frame schedule. Successful results include `heldMs`,
`elapsedMs` and `released: true`. Ordinary exceptions and partial down-injection
attempt guarded release before reporting failure. Holds are never replayed.

A changed/secure desktop, failed native release or abrupt worker termination can
prevent cleanup. Boundary checks take precedence over cleanup; a failed guarded
release reports `KEY_RELEASE_UNCONFIRMED`, never a successful release or a retarget
to the human desktop. A forcibly killed process cannot run its `finally` block.
Inspect the original session before retrying; do not kill/rebind workers during
an active hold. No crash-proof or frame-accurate input guarantee is claimed.

## Development macOS VM owners

`vmhost-r9-guest-keyboard` advertises `key_hold: true`. Keys go only to the owned,
offscreen `VZVirtualMachineView`. Chords support command, shift, option and control
modifiers plus one ordinary key; standalone modifiers, Space, arrows and navigation
keys are supported too. Modifiers use `flagsChanged` events with the left-device
bits, rather than ordinary key events or aggregate flags alone. The owner yields
between reports so down/up do not collapse into one unpaced USB state update.

One generation-bound operation presses, holds and releases in reverse order.
Input, bridge mutations and lifecycle requests are refused while it is active;
status/capture remain available. Caller disconnection does not cancel release.
Omitted/zero taps use 30 ms down time; positive holds accept 1–5000 ms. Results
include `heldMs`, `elapsedMs` and `released: true`. Owner/VM crashes cannot promise
release. No persistent down/up API, synthetic autorepeat or frame schedule exists.
Save/stop, install updated QuietWing, run `quietwing build`, resume and explicitly
rebind the consumer. No guest bridge replacement or settings change is needed.

## Windows upgrade and shared consumer use

The live worker must advertise `session.capabilities.key_hold: true` (also present
in its descriptor). Updating files alone does not replace a running worker.
The new CLI refuses `REATTACH_REQUIRED` before sending a hold to an older worker.
Save its owned apps and explicitly stop/attach with the updated helper when the
worker's owner is ready. Stop closes its owned apps; it retains the authenticated
native child and hidden viewer. Do not restart/reconnect ParaDesk to enable this.

The corresponding computer-ctrl contract adds `key` input `hold_ms`, e.g.:

```json
{"keys":"Return","hold_ms":120}
```

Or `cctl --session work key --keys Return --hold-ms 120`. A hold requires
`repeat=1` and an isolated provider advertising `key_hold`; unsupported direct-host,
Linux or old-worker paths refuse it. Development Mac VM owners advertising the
capability accept it too. Existing tap calls remain compatible.
A successful consumer response verifies the provider's hold and release receipt.
No game is launched and no host input, policy, firewall, RDP or credential setting
is changed by adding or installing this feature. Original-game compatibility
still needs that project's ordinary-controls pilot.
