// Compiled with the actual guestDrag function by run_guest_drag_test.py.
// Records local NSEvents only. No VM, desktop acquisition or event posting.
@main struct GuestDragTests {
    @MainActor static func main() throws {
        for button in [1,2,3] {
            var events=[NSEvent]();var sleeps=[UInt32]()
            let count=try guestDrag(["drag":[10.0,20.0,310.0,220.0],"button":button],windowNumber:42,
                deliver:{events.append($0)},pause:{sleeps.append($0)})
            let types:[NSEvent.EventType]=button==1 ? [.leftMouseDown,.leftMouseDragged,.leftMouseUp]:button==2 ? [.otherMouseDown,.otherMouseDragged,.otherMouseUp]:[.rightMouseDown,.rightMouseDragged,.rightMouseUp]
            precondition(count==22 && events.count==22)
            precondition(events.first!.type==types[0] && events.last!.type==types[2])
            precondition(events.dropFirst().dropLast().allSatisfy{$0.type==types[1]})
            precondition(events.allSatisfy{$0.windowNumber==42 && $0.modifierFlags.isEmpty})
            precondition(events.allSatisfy{$0.buttonNumber==(button==1 ? 0:button==3 ? 1:2)}, "button \(button): \(events.map{$0.buttonNumber})")
            precondition(events.first!.locationInWindow==NSPoint(x:10,y:748))
            precondition(events.last!.locationInWindow==NSPoint(x:310,y:548))
            for (i,e) in events.dropFirst().dropLast().enumerated(){
                precondition(abs(e.locationInWindow.x-(10+300*Double(i+1)/20))<0.001)
                precondition(abs(e.locationInWindow.y-(748-200*Double(i+1)/20))<0.001)
            }
            precondition(sleeps.reduce(0,+)==350_000)
            precondition(events.last!.pressure==0)
        }
        let invalid:[[String:Any]] = [
            ["drag":[0.0,0.0,1024.0,1.0]],["drag":[0.0,0.0,1.0,768.0]],
            ["drag":[-1.0,0.0,1.0,1.0]],["drag":[0.0,Double.nan,1.0,1.0]],
            ["drag":[0.0,0.0,Double.infinity,1.0]],["drag":[0.0,0.0,1.0]],
            ["drag":[0.0,0.0,1.0,1.0],"button":4]
        ]
        for request in invalid {
            var delivered=false
            do{_ = try guestDrag(request,windowNumber:42,deliver:{_ in delivered=true},pause:{_ in})
                preconditionFailure("Invalid drag accepted")
            }catch{precondition(!delivered)}
        }
        var edge=[NSEvent]()
        _ = try guestDrag(["drag":[0.0,0.0,1023.0,767.0]],windowNumber:42,deliver:{edge.append($0)},pause:{_ in})
        precondition(edge.first!.locationInWindow==NSPoint(x:0,y:768))
        precondition(edge.last!.locationInWindow==NSPoint(x:1023,y:1))
        print("Guest drag local NSEvent tests passed (all buttons, interpolation, bounds, release)")
    }
}
