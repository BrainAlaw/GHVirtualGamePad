import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: window
    width: 1160; height: 840
    minimumWidth: 940; minimumHeight: 740
    visible: true
    title: "GHVirtualGamePad"
    color: "#10141f"
    palette.windowText: "#e6eaf2"
    palette.text: "#e6eaf2"
    palette.button: "#283348"
    palette.buttonText: "#e6eaf2"
    palette.base: "#1b2232"
    palette.highlight: "#63dfb3"
    property var actions: ["green", "red", "yellow", "blue", "orange", "strum_up", "strum_down", "start", "select", "up", "down", "left", "right", "extra", "whammy"]
    property var labels: ["Green → A", "Red → B", "Yellow → Y", "Blue → X", "Orange → LB", "Strum up → ↑", "Strum down → ↓", "Start", "Select → Back", "D-pad ↑", "D-pad ↓", "D-pad ←", "D-pad →", "Extra → RB", "Whammy → Right Y"]
    property var fretColors: ["#4bd48e", "#f4657b", "#f4d66d", "#68a7ff", "#fca765"]
    onActiveChanged: if (!active) bridge.releaseDemoKeys()

    function beginMapping(functionId) {
        bridge.learn(functionId)
        demoInput.forceActiveFocus()
    }

    component GuitarButton: Button {
        required property string functionId
        objectName: "guitar-" + functionId
        enabled: !bridge.isRunning
        highlighted: bridge.learningAction === functionId || !!bridge.pad.buttons[functionId]
        onClicked: window.beginMapping(functionId)
        ToolTip.visible: hovered
        ToolTip.text: "Map " + functionId
    }

    Shortcut { sequence: "Ctrl+Escape"; onActivated: bridge.stop() }

    ColumnLayout {
        anchors.fill: parent; anchors.margins: 26; spacing: 14
        RowLayout {
            ColumnLayout {
                Label { text: "GH / VIRTUAL GAMEPAD"; font.pixelSize: 25; font.bold: true }
                Label { text: "Two devices. Two players. Your mappings."; color: "#91a0b9" }
            }
            Item { Layout.fillWidth: true }
            Label { text: bridge.demoMode ? "SIMULATION" : (bridge.windowsMode ? "WINDOWS / XBOX 360" : "LINUX / EVDEV"); color: "#63dfb3" }
        }
        RowLayout {
            Repeater {
                model: 2
                Button {
                    required property int index
                    Layout.fillWidth: true
                    text: "PLAYER " + (index + 1) + (bridge.assignments[index] ? "   • assigned" : "   • no device")
                    highlighted: bridge.player === index
                    onClicked: { bridge.setPlayer(index); demoInput.forceActiveFocus() }
                }
            }
        }
        RowLayout {
            Label { text: "Input device" }
            ComboBox {
                id: devices
                Layout.fillWidth: true; textRole: "label"; model: bridge.devices
                enabled: !bridge.isRunning
                currentIndex: {
                    for (let i = 0; i < bridge.devices.length; ++i)
                        if (bridge.devices[i].id === bridge.deviceChoices[bridge.player]) return i
                    return -1
                }
                onActivated: index => { bridge.selectDevice(index); demoInput.forceActiveFocus() }
            }
            Button { text: "Save profiles"; onClicked: bridge.save() }
            Button { visible: !bridge.demoMode && !bridge.windowsMode; text: "Enable device access"; enabled: !bridge.isRunning && devices.currentIndex > 0; onClicked: setupDialog.open() }
            Button { text: "Diagnostics"; onClicked: bridge.exportReport() }
        }
        RowLayout {
            Layout.fillHeight: true; spacing: 22
            Rectangle {
                Layout.preferredWidth: 420; Layout.fillHeight: true; color: "#181f2e"; radius: 18
                Label { anchors.top: parent.top; anchors.topMargin: 18; anchors.horizontalCenter: parent.horizontalCenter; text: "CLICK A CONTROL TO MAP IT"; color: "#91a0b9"; font.pixelSize: 12 }
                Item {
                    id: guitar
                    width: 380; height: 440
                    anchors.centerIn: parent
                    Canvas {
                        anchors.fill: parent
                        onPaint: {
                            let c = getContext("2d"); c.clearRect(0,0,width,height)
                            c.fillStyle = "#e8e9ed"; c.strokeStyle = "#687386"; c.lineWidth = 4
                            c.beginPath(); c.moveTo(166,247)
                            c.bezierCurveTo(142,205,96,210,91,244)
                            c.bezierCurveTo(93,282,104,288,76,313)
                            c.bezierCurveTo(8,365,76,435,172,433)
                            c.bezierCurveTo(278,440,323,395,288,340)
                            c.bezierCurveTo(255,290,293,294,285,265)
                            c.bezierCurveTo(255,288,228,259,213,243)
                            c.closePath(); c.fill(); c.stroke()
                            c.fillStyle = "#202329"; c.lineWidth = 2
                            c.beginPath(); c.moveTo(163,25); c.lineTo(210,13); c.lineTo(223,29)
                            c.lineTo(212,76); c.lineTo(212,273); c.lineTo(171,273)
                            c.lineTo(171,76); c.lineTo(160,65); c.closePath(); c.fill(); c.stroke()
                            for (let y=89; y<270; y+=17) { c.strokeStyle="#3b404a"; c.beginPath(); c.moveTo(173,y); c.lineTo(210,y); c.stroke() }
                            for (let y=34; y<64; y+=13) { c.fillStyle="#515862"; c.beginPath(); c.arc(176,y,3,0,Math.PI*2); c.fill(); c.beginPath(); c.arc(203,y-3,3,0,Math.PI*2); c.fill() }
                        }
                    }
                    Column {
                        x: 169; y: 82; spacing: 7
                        Repeater {
                            model: 5
                            Rectangle {
                                required property int index
                                property string action: window.actions[index]
                                width: 46; height: 23; radius: 5
                                color: window.fretColors[index]
                                opacity: bridge.pad.buttons[action] ? 1.0 : 0.55
                                border.width: bridge.learningAction === action ? 3 : 1
                                border.color: "white"
                                MouseArea { anchors.fill: parent; enabled: !bridge.isRunning; cursorShape: Qt.PointingHandCursor; onClicked: window.beginMapping(parent.action) }
                            }
                        }
                    }
                    Column {
                        x: 153; y: 294
                        GuitarButton { functionId: "strum_up"; width: 76; height: 30; text: "▲" }
                        GuitarButton { functionId: "strum_down"; width: 76; height: 30; text: "▼" }
                    }
                    Item {
                        x: 93; y: 232; width: 75; height: 75
                        GuitarButton { functionId: "up"; x: 25; y: 0; width: 25; height: 25; text: "↑" }
                        GuitarButton { functionId: "left"; x: 0; y: 25; width: 25; height: 25; text: "←" }
                        GuitarButton { functionId: "right"; x: 50; y: 25; width: 25; height: 25; text: "→" }
                        GuitarButton { functionId: "down"; x: 25; y: 50; width: 25; height: 25; text: "↓" }
                    }
                    GuitarButton { functionId: "extra"; x: 238; y: 276; text: "Extra"; width: 57; height: 28 }
                    GuitarButton { functionId: "select"; x: 104; y: 380; text: "Select"; width: 65; height: 30 }
                    GuitarButton { functionId: "start"; x: 104; y: 347; text: "Start"; width: 65; height: 30 }
                    Rectangle {
                        x: 220; y: 389; width: 75; height: 9; radius: 4
                        rotation: -75 + bridge.pad.whammy * 35; transformOrigin: Item.Left
                        color: bridge.learningAction === "whammy" ? "#63dfb3" : "#c8d2e1"
                        MouseArea { anchors.fill: parent; anchors.margins: -10; enabled: !bridge.isRunning; onClicked: window.beginMapping("whammy") }
                    }
                    GuitarButton { functionId: "whammy"; x: 183; y: 401; width: 84; height: 25; text: "Whammy" }
                }
            }
            ColumnLayout {
                Layout.fillWidth: true; Layout.fillHeight: true; spacing: 8
                Label { text: "MAPPING / PLAYER " + (bridge.player+1); font.bold: true; font.pixelSize: 16 }
                Label { text: bridge.isRunning ? "Stop controllers to edit mappings." : "Click a function or its binding, then press the device key."; color: "#91a0b9" }
                ScrollView {
                    id: mappingScroll
                    objectName: "mappingScroll"
                    rightPadding: 18
                    Layout.fillHeight: true; Layout.fillWidth: true
                    clip: true
                    ColumnLayout {
                        width: mappingScroll.availableWidth; spacing: 3
                        Repeater {
                            model: window.actions.length
                            RowLayout {
                                id: mappingRow
                                required property int index
                                property string functionId: window.actions[index]
                                Layout.fillWidth: true
                                Button {
                                    objectName: "mapping-" + mappingRow.functionId
                                    Layout.preferredWidth: 180; Layout.preferredHeight: 29
                                    text: window.labels[index]
                                    highlighted: bridge.learningAction === mappingRow.functionId || !!bridge.pad.buttons[mappingRow.functionId]
                                    enabled: !bridge.isRunning
                                    onClicked: window.beginMapping(mappingRow.functionId)
                                }
                                Button {
                                    objectName: "binding-" + mappingRow.functionId
                                    Layout.fillWidth: true; Layout.minimumWidth: 0; Layout.preferredHeight: 29
                                    flat: true
                                    enabled: !bridge.isRunning
                                    text: bridge.bindings[mappingRow.functionId] ? ((bridge.bindings[mappingRow.functionId].kind === 1 ? "KEY " : "AXIS ") + bridge.bindings[mappingRow.functionId].code) : "Not mapped — click to assign"
                                    onClicked: window.beginMapping(mappingRow.functionId)
                                }
                                ToolButton { objectName: "clear-" + mappingRow.functionId; text: "×"; enabled: !bridge.isRunning; onClicked: bridge.clearBinding(mappingRow.functionId) }
                            }
                        }
                    }
                }
                Label { text: "WHAMMY / DIGITAL → ANALOG"; color: "#91a0b9" }
                ProgressBar { Layout.fillWidth: true; from: 0; to: 1; value: bridge.pad.whammy }
                RowLayout {
                    Label { text: "Press (ms)" }
                    SpinBox { from: 10; to: 10000; stepSize: 10; value: bridge.riseMs; editable: true; enabled: !bridge.isRunning; onValueModified: bridge.setTiming(value, bridge.returnMs) }
                    Label { text: "Return (ms)" }
                    SpinBox { from: 10; to: 10000; stepSize: 10; value: bridge.returnMs; editable: true; enabled: !bridge.isRunning; onValueModified: bridge.setTiming(bridge.riseMs, value) }
                }
            }
        }
        Rectangle {
            visible: bridge.demoMode
            Layout.fillWidth: true; height: 60; radius: 10; color: "#202d3c"
            RowLayout {
                anchors.fill: parent; anchors.margins: 10
                Label { Layout.fillWidth: true; text: "SIMULATOR · A S D F G = frets · arrows = strum / D-pad\nEnter = Start · Backspace = Select · hold Space = whammy"; color: "#c0cfdf" }
                Button { text: "Demo bindings"; enabled: !bridge.isRunning; onClicked: { bridge.demoDefaults(); demoInput.forceActiveFocus() } }
                Button { text: "Focus keyboard"; onClicked: demoInput.forceActiveFocus() }
            }
        }
        RowLayout {
            Label { Layout.fillWidth: true; Layout.minimumWidth: 0; wrapMode: Text.WrapAnywhere; text: bridge.status; color: "#becbe0" }
            Button { visible: bridge.learningAction !== ""; text: "Cancel mapping"; onClicked: bridge.cancelLearn() }
            Button {
                text: bridge.isRunning ? "STOP / RELEASE DEVICES" : (bridge.demoMode ? "START SIMULATION" : "START CONTROLLERS")
                highlighted: true
                onClicked: { bridge.toggle(); demoInput.forceActiveFocus() }
            }
        }
        Label { text: "Stop: Ctrl+Esc while this window is focused. Closing the app releases devices. Start Moonlight after the controllers."; color: "#718098"; font.pixelSize: 11 }
    }
    Item {
        id: demoInput
        focus: true
        Keys.onPressed: event => { if (!event.isAutoRepeat) bridge.demoKey(event.key, true); event.accepted = true }
        Keys.onReleased: event => { if (!event.isAutoRepeat) bridge.demoKey(event.key, false); event.accepted = true }
    }
    Dialog {
        id: setupDialog
        title: "Enable Linux device access"
        anchors.centerIn: parent
        modal: true
        standardButtons: Dialog.Ok | Dialog.Cancel
        Label { width: 430; wrapMode: Text.Wrap; text: "This installs a udev rule for the selected USB receiver at its current port and enables virtual gamepad creation for the active desktop user. Choose the guitar receiver, not your everyday keyboard. Administrator authentication follows." }
        onAccepted: bridge.setupDevice(devices.currentIndex)
    }
}
