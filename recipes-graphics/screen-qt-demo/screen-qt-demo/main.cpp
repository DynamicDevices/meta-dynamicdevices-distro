#include <QGuiApplication>
#include <QQmlApplicationEngine>
#include <QQuickWindow>
#include <QSGRendererInterface>

int main(int argc, char *argv[])
{
    QGuiApplication app(argc, argv);
    QQuickWindow::setGraphicsApi(QSGRendererInterface::OpenGL);

    QQmlApplicationEngine engine;
    engine.loadFromModule("ActiveESL.Screen", "Main");
    if (engine.rootObjects().isEmpty())
        return 1;

    return app.exec();
}
