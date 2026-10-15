# Architecture

QuietWing is one module with a versioned command interface and three native
adapters. [CONTRACT.md](../CONTRACT.md) and [the descriptor schema](../session.schema.json)
define the interface.

```text
Agent harness
    |
computer-ctrl: --session NAME
    | versioned JSON over local CLI, optionally wrapped in SSH
QuietWing dispatcher
    +-- Linux: owned Xvfb + private HOME/D-Bus/PulseAudio
    +-- Windows: worker inside a verified ParaDesk child
    +-- macOS: Virtualization.framework guest + guest bridge
```

The dispatcher selects only its local OS, preserves literal arguments, validates
the adapter envelope, and adds a portable descriptor. Failure never selects the
human desktop. SSH is an outer transport.

Each adapter owns prerequisites, acquisition, native input/capture, process
identity checks, and cleanup. Generation checks happen inside lifetime/dispatch
protection before delivery. Callers pin generation and explicitly rebind after
replacement.

Computer-ctrl owns MCP tools, coordinate frames, image/OCR handling, target
controller/artifact paths, and supported-tool filtering. Neither project imports
the other's source. Their seam is an executable argument array and descriptor v1.

The wheel includes native source. Compilers write to private cache/state, never
the installed package. Backend `DESKHELPER_*` environment names, cache paths,
native bundle identifiers, and ownership markers retain their 0.2 names so
existing saved guests and authenticated sessions keep their identity. There is
one CLI, `quietwing`, and no parallel environment-variable family.

The Python import package is `quietwing`; the installed entry point is
`quietwing.cli:entrypoint`. `cli.py` also runs directly from a source checkout.
Native acceptance scripts are development tools. Raw evidence/state are ignored
and excluded from distributions.
