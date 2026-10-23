import QtQuick
import QtTest
import "../../quickshell/lock-preview"
Rectangle {
 id:canvas;width:1120;height:720;color:"#17283a"
 QtObject {id:stub;property var colors:({bg:"#17283a",bg_modules:"#203447",fg:"#f3e7d0",fg_dim:"#b9c6cf",accent:"#81b5d5"})}
 LockscreenConcept {id:concept;shell:stub}
 TestCase {
  name:"LockConcepts";when:windowShown
  function test_render_two_concepts_without_locking() {
   let done=false
   concept.split=false;wait(80)
   canvas.grabToImage(r=>{r.saveToFile("/tmp/niri-lock-concept-central.png");done=true});tryVerify(()=>done)
   done=false;concept.split=true;wait(80)
   canvas.grabToImage(r=>{r.saveToFile("/tmp/niri-lock-concept-split.png");done=true});tryVerify(()=>done)
  }
 }
}
