# macOS guest audio assessment

Assessed against the installed macOS 27 SDK and Apple's public documentation on
2026-10-19. No VM configuration, host routing, audio device, driver or host setting
was changed. Default QuietWing guests still have **no audio devices**;
`audio_capture` is false. Lack of a device is not evidence that an application
produced silence or that its AudioContext/worklet failed.

## What Virtualization.framework supports

- `VZVirtioSoundDeviceConfiguration` can expose an output stream to a guest.
- [`VZVirtioSoundDeviceOutputStreamConfiguration.sink`](https://developer.apple.com/documentation/virtualization/vzvirtiosounddeviceoutputstreamconfiguration/sink)
  defaults to nil: the framework **suppresses/discards** that stream. This is a
  documented way to offer an output without playing it on host speakers, but it
  does not return PCM samples or prove nonzero sound.
- [`VZHostAudioOutputStreamSink`](https://developer.apple.com/documentation/virtualization/vzhostaudiooutputstreamsink)
  plays to the host's default output device (the AudioQueueNewOutput route). It
  cannot be used for QuietWing's never-play-on-host requirement.
- The public [`VZAudioOutputStreamSink`](https://developer.apple.com/documentation/virtualization/vzaudiooutputstreamsink)
  base has unavailable initializers and no sample callback/file/buffer API. The
  SDK exposes only the host-output subclass. A custom capture sink relying on
  private implementation/subclass hooks is not a supported solution.

## Safe options for future work

1. **Preferred candidate, not yet validated:** a per-session opt-in virtio output
   with `sink = nil`, plus recording **inside the guest** (CoreAudio process tap
   or ScreenCaptureKit audio) to a private guest file/shared transfer directory.
   Recording might need guest permission and guest OS/device compatibility work.
   Bound duration/bytes, atomic owned output, generation checks, silence/level
   measurements, error handling and save/restore acceptance would all be needed.
   It verifies rendered guest audio data, not physical speaker audibility.
2. **Application-level export:** an authorized app can export rendered PCM/WAV
   or internal levels through the existing bridge. This measures its render path,
   not general OS/device output, and must be labelled accordingly.
3. A host virtual loopback/default-output route plus the host sink is **not** an
   acceptable implementation here: it changes host routing/installs components
   and risks speaker leakage on route loss. Host muting is not an isolation gate.

Adding a sound device changes the VM hardware configuration. Existing encrypted
saved memory is configuration-bound; it cannot be assumed restorable after this
change. Never discard/cold-boot a stateful guest to try it. First obtain an
explicit protected-state migration decision and validate preservation separately.
Consequently this is not a small safe capture-only change to an existing saved
guest. No opt-in recording capability is advertised or shipped by this work.
