pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
Rectangle {
    id:concept
    required property var shell
    property bool split:false
    property string wallpaper:Qt.resolvedUrl("../../assets/themes/ancient-odyssey/wallpaper.jpg")
    width:1120;height:720;radius:28;clip:true;color:shell.colors.bg
    Image {anchors.fill:parent;source:concept.wallpaper;fillMode:Image.PreserveAspectCrop}
    Rectangle {anchors.fill:parent;color:Qt.alpha(concept.shell.colors.bg,0.52)}
    Text {x:36;y:28;text:concept.split?"Б · Часы слева, вход справа":"А · Центральная композиция";font.pixelSize:14;color:concept.shell.colors.fg}
    Rectangle {
        x:parent.width-163;y:20;width:127;height:36;radius:18;color:Qt.alpha(concept.shell.colors.bg_modules,0.9)
        Text {anchors.centerIn:parent;text:"󰂄  78 %  ·  ru";color:concept.shell.colors.fg;font.pixelSize:12}
    }
    Column {
        x:concept.split?64:(concept.width-width)/2;y:concept.split?118:78
        width:concept.split?480:360;spacing:8
        Text {width:parent.width;text:"21:30";horizontalAlignment:concept.split?Text.AlignLeft:Text.AlignHCenter;font.pixelSize:concept.split?112:94;font.weight:Font.Light;color:concept.shell.colors.fg}
        Text {width:parent.width;text:"Четверг, 22 октября";horizontalAlignment:concept.split?Text.AlignLeft:Text.AlignHCenter;font.pixelSize:20;color:concept.shell.colors.fg}
        Text {visible:concept.split;width:parent.width;text:"Хороший вечер, Андрей";font.pixelSize:14;color:concept.shell.colors.fg_dim}
    }
    Rectangle {
        id:login
        x:concept.split?concept.width-430:(concept.width-width)/2
        y:concept.split?100:290;width:concept.split?365:390;height:concept.split?380:234
        radius:32;color:Qt.alpha(concept.shell.colors.bg_modules,0.95)
        border.width:1;border.color:Qt.alpha(concept.shell.colors.fg,0.17)
        Column {
            anchors {fill:parent;margins:28} spacing:16
            Rectangle {
                width:concept.split?88:54;height:width;radius:concept.split?30:18
                anchors.horizontalCenter:parent.horizontalCenter;color:Qt.alpha(concept.shell.colors.accent,0.19)
                rotation:concept.split?12:0
                Text {anchors.centerIn:parent;text:"А";font.pixelSize:concept.split?38:25;color:concept.shell.colors.accent;rotation:-parent.rotation}
            }
            Text {width:parent.width;text:"Андрей";horizontalAlignment:Text.AlignHCenter;font.pixelSize:22;font.weight:Font.DemiBold;color:concept.shell.colors.fg}
            Text {visible:concept.split;width:parent.width;text:"С возвращением";horizontalAlignment:Text.AlignHCenter;color:concept.shell.colors.fg_dim;font.pixelSize:13}
            Rectangle {
                width:parent.width;height:48;radius:16;color:Qt.alpha(concept.shell.colors.bg,0.85)
                border.width:1;border.color:concept.shell.colors.accent
                Text {x:16;anchors.verticalCenter:parent.verticalCenter;text:"Пароль";color:concept.shell.colors.fg_dim;font.pixelSize:14}
                Text {anchors {right:parent.right;rightMargin:16;verticalCenter:parent.verticalCenter} text:"→";color:concept.shell.colors.accent;font.pixelSize:22}
            }
            Text {visible:concept.split;width:parent.width;text:"Нажми Enter для входа";horizontalAlignment:Text.AlignHCenter;font.pixelSize:11;color:concept.shell.colors.fg_dim}
        }
    }
    Rectangle {
        x:concept.split?64:36;y:concept.height-168;width:concept.split?475:290;height:112
        radius:24;color:Qt.alpha(concept.shell.colors.bg_modules,0.9)
        Row {
            anchors {fill:parent;margins:18} spacing:16
            Rectangle {
                width:74;height:74;radius:20;color:Qt.alpha(concept.shell.colors.accent,0.17)
                Text {anchors.centerIn:parent;text:"♫";font.pixelSize:36;color:concept.shell.colors.accent}
            }
            Column {
                width:parent.width-90;spacing:8
                Text {text:"МУЗЫКА · ПРИМЕР";color:concept.shell.colors.fg_dim;font.pixelSize:10}
                Text {width:parent.width;text:"Вечерний плейлист";elide:Text.ElideRight;color:concept.shell.colors.fg;font.pixelSize:14}
                Rectangle {width:parent.width;height:3;radius:2;color:Qt.alpha(concept.shell.colors.fg,0.14);Rectangle {width:parent.width*0.37;height:3;radius:2;color:concept.shell.colors.accent}}
            }
        }
    }
    Rectangle {
        x:concept.split?login.x:concept.width-306;y:concept.split?concept.height-190:102
        width:concept.split?365:270;height:concept.split?134:168;radius:24
        color:Qt.alpha(concept.shell.colors.bg_modules,0.94)
        Column {
            anchors {fill:parent;margins:20} spacing:12
            Text {text:"УВЕДОМЛЕНИЯ · ПРИМЕР";color:concept.shell.colors.fg_dim;font.pixelSize:10}
            Text {width:parent.width;text:"Календарь";color:concept.shell.colors.fg;font.pixelSize:14;font.weight:Font.DemiBold}
            Text {width:parent.width;text:"Завтра · Практика в университете";wrapMode:Text.Wrap;color:concept.shell.colors.fg_dim;font.pixelSize:12}
        }
    }
    Text {anchors {bottom:parent.bottom;bottomMargin:18;horizontalCenter:parent.horizontalCenter} text:"МАКЕТ · тестовые данные · пароль вводить не нужно";color:concept.shell.colors.fg_dim;font.pixelSize:11}
}
