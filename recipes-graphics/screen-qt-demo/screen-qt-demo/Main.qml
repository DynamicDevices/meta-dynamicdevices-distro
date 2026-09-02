import QtQuick

Window {
    id: root
    visible: true
    visibility: Window.FullScreen
    color: "#10243b"
    title: "Active Edge Qt Test"

    property int touchCount: 0

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#10243b" }
            GradientStop { position: 1.0; color: "#00a6a6" }
        }
    }

    Column {
        anchors.centerIn: parent
        spacing: 24

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "ACTIVE EDGE"
            color: "white"
            font.pixelSize: 72
            font.bold: true
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "Qt 6 • Wayland • OpenGL ES"
            color: "white"
            font.pixelSize: 34
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: root.touchCount === 0 ? "Touch the screen" : "Touches: " + root.touchCount
            color: "#ffd166"
            font.pixelSize: 42
        }
    }

    MultiPointTouchArea {
        anchors.fill: parent
        minimumTouchPoints: 1
        maximumTouchPoints: 10
        onPressed: points => root.touchCount += points.length
    }
}

