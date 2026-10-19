// Compiled against actual guestKey. Local events only; no posting or VM.
@main struct GuestKeyTests {
    @MainActor static func main() async throws {
        for code:UInt16 in [0,49,123,124,125,126] {
            for ms in [0,1,300,5000] {
                var events=[NSEvent](),pauses=[UInt32]()
                try await guestKey(code:code,characters:"",modifiers:[.command,.shift],holdMS:ms,windowNumber:42,
                    deliver:{events.append($0)},pause:{pauses.append($0)})
                precondition(events.map{$0.type} == [.flagsChanged,.flagsChanged,.keyDown,.keyUp,.flagsChanged,.flagsChanged])
                precondition(events.map{$0.keyCode} == [55,56,code,code,56,55])
                precondition(events.map{$0.modifierFlags.intersection(.deviceIndependentFlagsMask)} == [.command,[.command,.shift],[.command,.shift],[.command,.shift],.command,[]])
                precondition(events[0].modifierFlags.rawValue & 0x8 != 0)
                precondition(events[1].modifierFlags.rawValue & 0xA == 0xA)
                precondition(events.last!.modifierFlags.rawValue == 0)
                precondition(events.allSatisfy{$0.windowNumber==42})
                precondition(events.filter{$0.type == .keyDown || $0.type == .keyUp}.allSatisfy{!$0.isARepeat})
                precondition(pauses.reduce(0,+)==UInt32(ms==0 ? 30:ms)*1000+50_000)
            }
        }
        for code:UInt16 in [55,56,58,59] {
            var events=[NSEvent]()
            try await guestKey(code:code,characters:"",modifiers:[],holdMS:300,windowNumber:42,deliver:{events.append($0)},pause:{_ in})
            precondition(events.map{$0.type} == [.flagsChanged,.flagsChanged])
            precondition(!events.first!.modifierFlags.isEmpty && events.last!.modifierFlags.isEmpty)
        }
        for ms in [-1,5001] {
            var delivered=false
            do{try await guestKey(code:49,characters:"",modifiers:[],holdMS:ms,windowNumber:42,deliver:{_ in delivered=true},pause:{_ in});preconditionFailure("Invalid hold accepted")}
            catch{precondition(!delivered)}
        }
        print("Guest key events passed: modifier flags, chords, arrows, holds, reverse release, bounds")
    }
}
