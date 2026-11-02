import QtQuick
import QtTest
import "../../../quickshell"
Item {
 width:700;height:500
 ResizeFrame{id:frame;x:50;y:50;width:400;height:300}
 SignalSpy{id:spy;target:frame;signalName:"resized"}
 TestCase {
  name:"FloatingResizeFrame";when:windowShown
  function test_corner_math_and_minimums(){
   compare(frame.rectangle("se",50,40,400,300).width,450)
   compare(frame.rectangle("nw",50,40,400,300).width,350)
   compare(frame.rectangle("nw",50,40,400,300).height,260)
   compare(frame.rectangle("w",2000,0,400,300).width,120)
   compare(frame.rectangle("n",0,2000,400,300).height,100)
  }
  function test_left_button_drag_needs_no_modifier(){
   spy.clear();let handle=findChild(frame,"resize-handle-se")
   mousePress(handle,5,5,Qt.LeftButton,Qt.NoModifier)
   verify(frame.dragging)
   mouseMove(handle,40,30,50)
   mouseRelease(handle,40,30,Qt.LeftButton,Qt.NoModifier)
   verify(!frame.dragging);verify(spy.count>=1)
   let last=spy.signalArguments[spy.count-1]
   compare(last[0],435);compare(last[1],325);compare(last[4],true)
  }
 }
}
