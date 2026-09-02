cmake_minimum_required(VERSION 3.21)

project(screen-qt-demo VERSION 1.0 LANGUAGES CXX)

find_package(Qt6 6.8 REQUIRED COMPONENTS Quick)
qt_standard_project_setup(REQUIRES 6.8)

qt_add_executable(screen-qt-demo main.cpp)

qt_add_qml_module(screen-qt-demo
    URI ActiveESL.Screen
    VERSION 1.0
    QML_FILES Main.qml
)

target_link_libraries(screen-qt-demo PRIVATE Qt6::Quick)

install(TARGETS screen-qt-demo RUNTIME DESTINATION bin)

